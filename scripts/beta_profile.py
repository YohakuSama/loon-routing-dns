#!/usr/bin/env python3
"""Render beta from its immutable v6.5.4 baseline and reviewed policy."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import beta_assets
import beta_domestic_rules
import beta_policy_review
from beta_channel import ROOT, content_rules, remote_entries, section


def _replace(text, label, body):
    pattern = r"(?ms)^\[" + re.escape(label) + r"\]\n.*?(?=^\[|\Z)"
    return re.sub(pattern, lambda _: "[" + label + "]\n" + body.strip() + "\n\n", text, count=1)


def render(asset_commit: str, root: Path = ROOT) -> tuple[bytes, dict]:
    if not re.fullmatch(r"[a-f0-9]{40}", asset_commit):
        raise ValueError("assets must be committed before profile generation")
    meta = json.loads((root / "build/beta_manifest.json").read_text())
    stable = (root / "build/baselines/v6.5.4/LoonKit.lcf").read_bytes()
    if hashlib.sha256(stable).hexdigest() != meta["original_production_config_sha256"]:
        raise ValueError("formal baseline changed; explicit template migration required")
    spec = json.loads((root / "rules/beta/policy_overrides.json").read_text())
    routine = meta.get("upstream_overlays", {})
    version = meta["version"] if routine else spec["version"]
    source = stable.decode()
    source = source.replace(source.splitlines()[0], "# LoonKit " + version + " · BETA TEST ONLY", 1)
    source = source.replace("[General]", "# 测试渠道；DNS 保持默认 AliDNS。\n# 关闭广告拦截：停用 Beta-AdBlock-Balanced 远程规则即可恢复服务分流。\n[General]", 1)
    source = source.replace("interface-mode = auto", "interface-mode = auto\nsni-sniffing = true", 1)
    source = source.replace("AdBlock = select,REJECT,DIRECT,", "AdBlock = select,REJECT,Proxy,", 1)
    resources = {}
    overlay_bytes = beta_assets.render(root)
    ad_path, ad_bytes = beta_policy_review.render(root)
    domestic_path, domestic_bytes = beta_domestic_rules.render(root)

    def resource(path, data):
        rel = Path(path).relative_to(root).as_posix() if Path(path).is_absolute() else str(path)
        return {"uri": "https://raw.githubusercontent.com/YohakuSama/loonkit/" + asset_commit + "/" + rel,
                "source_commit": asset_commit, "sha256": hashlib.sha256(data).hexdigest(),
                "matcher_count": len(content_rules(data))}

    for path, data in overlay_bytes.items():
        resources[Path(path).stem] = resource(path, data)
    ad = resource(ad_path, ad_bytes)
    domestic = resource(domestic_path, domestic_bytes)
    rows = []
    group_tags = {}

    def add(uri, policy, tag, group):
        rows.append(uri + ", policy=" + policy + ", tag=" + tag + ", enabled=true")
        group_tags.setdefault(group, []).append(tag)

    add(ad["uri"], "AdBlock", "Beta-AdBlock-Balanced", "AdBlock")
    for group, item in sorted(routine.items()):
        add(item["uri"], group, "Beta-Upstream-" + group, group)
    for group in spec["service_groups"]:
        add(resources["Service-" + group]["uri"], group, "Beta-Service-" + group, group)
    original = remote_entries(stable.decode())
    by_tag = {r["tag"]: r for r in original}
    for name, policy in [("DomesticCore", "DIRECT")]:
        old = by_tag["Our-" + name]
        add(old["uri"], policy, old["tag"], name)
    add(resources["DomesticSupplement"]["uri"], "DIRECT", "Beta-DomesticSupplement", "DomesticCore")
    add(resources["AIScoped"]["uri"], "AI", "Beta-AIScoped", "AI")
    add(resources["SharedInfrastructure"]["uri"], "Proxy", "Beta-SharedInfrastructure", "SharedInfrastructure")
    add(by_tag["Our-AppleOTA"]["uri"], "Apple", "Our-AppleOTA", "AppleOTA")
    add(resources["SteamCN"]["uri"], "DIRECT", "Beta-SteamCN", "SteamCN")
    add(resources["SteamGlobal"]["uri"], "Steam", "Beta-SteamGlobal", "Steam")
    replaced = {"Our-AdBlock", "Our-DomesticCore", "Our-AI", "Our-AppleOTA", "Our-SteamCN", "Our-ChinaDirect"}
    for row in original:
        if row["tag"] not in replaced:
            name = Path(row["path"]).stem
            group = "動畫瘋" if name == "AnimeCrazy" else name
            add(row["uri"], row["policy"], row["tag"], group)
    add(domestic["uri"], "DIRECT", "Beta-ChinaDirect-Scoped", "ChinaDirect")
    source = _replace(source, "Remote Rule", "# 按审核后的服务归属和优先级生成。\n" + "\n".join(rows))
    local = spec["local_priority_rules"]
    source = _replace(source, "Rule", "# 仅保留资源访问及跨平台 AI 的必要优先例外。\n"
                      + "\n".join(local) + "\nGEOIP,CN,DIRECT,no-resolve\nFINAL,Final")
    profile = source.encode()
    meta.update(version=version, configuration_entry="beta/LoonKit.lcf",
                configuration_sha256=hashlib.sha256(profile).hexdigest(),
                immutable_overlay_commit=asset_commit, candidate_source_commit=meta["candidate_source_commit"] if routine else asset_commit,
                overlay_rules=resources, adblock=ad, china_direct={**domestic,
                    "removed_count": 62, "decisions_path": "rules/beta/domestic_decisions.json"},
                runtime_remote_count=len(rows), production_rule_refs_preserved=22,
                source_group_tags={k:v for k,v in group_tags.items() if k != "SharedInfrastructure"},
                upstream_overlays=routine, generator="scripts/beta_profile.py")
    runtime = {r["tag"]:r for r in remote_entries(source)}
    meta["source_group_counts"] = {group:len(set().union(*[
        set(content_rules((root / runtime[tag]["path"]).read_bytes())) for tag in tags]))
        for group,tags in meta["source_group_tags"].items()}
    # Upstream overlays are already included in group_tags by add(), so the
    # next source review and reproducible renderer see the same active baseline.
    meta["acceptance"] = {"ci": "PENDING_EXACT_CANDIDATE_CHECKS", "device": "NEW_RULE_DELTA_REVIEW_REQUIRED" if routine else "NEW_CHANGES_REQUIRE_TARGETED_ACCEPTANCE",
                          "minimum_observation_days": 7, "promotion": "BLOCKED"}
    meta["limitations"] = [
        "Prior owner feedback reported no issues but did not identify an exact tested SHA or all scenarios.",
        "AliDNS and App-level plain DNS fallback settings are unchanged; no zero-leak claim.",
        "New beta.4 single-filter, shared-owner and Apple selector changes require targeted device checks.",
        "ChinaDirect historical remainder is not a geographic certification of every destination."]
    return profile, meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-commit", required=True)
    parser.add_argument("--write", action="store_true", required=True)
    args = parser.parse_args()
    profile, meta = render(args.asset_commit)
    (ROOT / "beta/LoonKit.lcf").write_bytes(profile)
    (ROOT / "build/beta_manifest.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"version":meta["version"], "configuration_sha256":meta["configuration_sha256"]}))
