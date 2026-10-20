#!/usr/bin/env python3
"""Deterministic phase07 RC2 publishing build; NEVER pushes, merges, downloads or updates main.

The rules/releases/vNext-RC2 directory is an immutable staged output copied
byte-for-byte from the locked RC1 vNext compiler. The old rules/generated/
path is deliberately retained as a legacy compatibility feed and is NOT an input.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import vnext_rule_engine as engine

SPEC = ROOT / "release/phase-07/release_spec.json"
RC1 = ROOT / "release-candidate/phase-06/RC_MANIFEST.json"
RAW_ROOT = "https://raw.githubusercontent.com/YohakuSama/loonkit/"


def section(profile: str, name: str) -> str:
    start = profile.index("[" + name + "]\n")
    end = profile.find("\n[", start + len(name) + 3)
    return profile[start:end if end >= 0 else None]


def read_spec(root: Path = ROOT) -> dict:
    spec = json.loads((root / "release/phase-07/release_spec.json").read_text(encoding="utf-8"))
    if spec["rc_label"] != "vNext-RC2" or spec["stable_release_version"] is not None:
        raise ValueError("RC label cannot assert formal stable release")
    for key in ("release_assets_commit", "reviewed_auxiliary_commit", "historic_main_commit"):
        if re.fullmatch(r"[a-f0-9]{40}", spec[key]) is None:
            raise ValueError("invalid immutable Git ref: " + key)
    if spec["release_rules_dir"] != "rules/releases/vNext-RC2":
        raise ValueError("release path changed without approval")
    if spec["source_snapshot_dir"] != "rules/snapshots/phase03/generated":
        raise ValueError("release input path changed")
    return spec


def generate(root: Path = ROOT) -> dict[str, str]:
    spec = read_spec(root)
    rc1 = json.loads((root / "release-candidate/phase-06/RC_MANIFEST.json").read_text())
    candidate = engine.compile_rules(root)["refactor/vnext/LoonKit.vNext.Candidate.lcf"]
    remote = section(candidate, "Remote Rule")
    local = section(candidate, "Rule")
    plugin = (root / "release/phase-07/assets/Network_Diagnostics.plugin").read_text(encoding="utf-8")
    if ("/main/scripts/" in plugin or "/main/icons/" in plugin
            or spec["reviewed_auxiliary_commit"] not in plugin):
        raise ValueError("unreviewed dynamic plugin dependency")
    remote_lines = [x.strip() for x in remote.splitlines() if x.startswith("https://")]
    if len(remote_lines) != 26:
        raise ValueError("RC2 must retain 26 remote rule entries")
    stage = {}
    locked = {}
    for line in remote_lines:
        item = re.fullmatch(
            r"https://raw\.githubusercontent\.com/YohakuSama/loonkit/refactor/loonkit-vnext/"
            r"refactor/vnext/generated/([A-Za-z]+)\.list, policy=([^,]+), tag=vNext-([A-Za-z]+), enabled=true",
            line)
        if not item or item[1] != item[3]:
            raise ValueError("candidate remote source changed: " + line)
        filename, policy = item[1], item[2]
        origin = root / f"refactor/vnext/generated/{filename}.list"
        published = root / spec["release_rules_dir"] / (filename + ".list")
        if not published.is_file() or published.read_bytes() != origin.read_bytes():
            raise ValueError("RC2 released output differs from locked candidate: " + filename)
        data = published.read_bytes()
        rc_info = next((d for d in rc1["remote_rules"].values()
                        if d["path"].endswith("/" + filename + ".list")), None)
        digest = hashlib.sha256(data).hexdigest()
        if not rc_info or digest != rc_info["sha256"]:
            raise ValueError("RC1-reviewed SHA256 differs from release: " + filename)
        count = sum(bool(x) and not x.startswith("#") for x in data.decode("utf-8").splitlines())
        if count != rc_info["rule_count"]:
            raise ValueError("RC1-reviewed rule count differs from release: " + filename)
        url = RAW_ROOT + spec["release_assets_commit"] + "/" + spec["release_rules_dir"] + "/" + filename + ".list"
        stage[filename] = url + f", policy={policy}, tag=Our-{filename}, enabled=true"
        locked[filename] = {"path": published.relative_to(root).as_posix(),
                            "sha256": digest, "rule_count": count, "url": url,
                            "source_commit": spec["release_assets_commit"]}
    if sum(x["rule_count"] for x in locked.values()) != 197765:
        raise ValueError("RC2 snapshot total unexpectedly changed")
    if len(stage) != 26:
        raise ValueError("duplicate candidate groups")
    ordered = [re.search(r"/([A-Za-z]+)\.list,", x)[1] for x in remote_lines]
    listing = "[Remote Rule]\n# vNext-RC2 pinned content; not an auto-updating branch.\n"
    listing += "\n".join(stage[x] for x in ordered) + "\n"
    # Only migrate routing sections. Do not copy General, TUN, Proxy or DNS from
    # one profile to the other; each has a separate frozen original seed.
    plugin_url = RAW_ROOT + spec["release_assets_commit"] + "/release/phase-07/assets/Network_Diagnostics.plugin"
    outputs = {}
    for entry, seed in (
        ("LoonKit.lcf", "LoonKit.legacy-seed.lcf"),
        ("LoonKit.PrivacyDNS.lcf", "LoonKit.PrivacyDNS.legacy-seed.lcf"),
    ):
        base = (root / "refactor/vnext/templates" / seed).read_text(encoding="utf-8")
        body = base[:base.index("[Remote Rule]")].replace(
            "/main/icons/", "/" + spec["reviewed_auxiliary_commit"] + "/icons/")
        body = body.replace("# LoonKit v5.10.0", "# LoonKit vNext-RC2 - NOT RELEASED", 1)
        body += listing + "\n" + local.strip("\n") + "\n\n[Plugin]\n"
        body += plugin_url + ", enabled=true\n"
        if section(body, "General") != section(base, "General"):
            raise ValueError("profile-specific DNS/TUN General unexpectedly changed")
        if section(body, "Proxy Group") != section(base, "Proxy Group").replace(
                "/main/icons/", "/" + spec["reviewed_auxiliary_commit"] + "/icons/"):
            raise ValueError("user policy selectors changed")
        if "ProxyProtect" in section(body, "Remote Rule"):
            raise ValueError("retired runtime dependency returned")
        if section(body, "Rule").count("\nGEOIP,CN,DIRECT,no-resolve") != 1:
            raise ValueError("missing GEOIP terminator")
        if section(body, "Rule").count("\nFINAL,Final") != 1:
            raise ValueError("missing FINAL selector")
        inline = [x for x in section(body, "Rule").splitlines()
                  if x.startswith(("DOMAIN,", "DOMAIN-SUFFIX,", "DOMAIN-KEYWORD,",
                                   "IP-CIDR,", "IP-CIDR6,", "IP-ASN,", "GEOIP,", "FINAL,"))]
        if len(inline) != 106 or len(inline) != len(set(inline)):
            raise ValueError("candidate local rule count/uniqueness changed")
        if sum(x.endswith(",AdBlock") for x in inline) != 26:
            raise ValueError("26 overseas adblock precedence rules not preserved")
        if "/main/" in section(body, "Proxy Group") or "/main/" in section(body, "Plugin"):
            raise ValueError("auxiliary runtime URL is dynamic")
        if section(body, "Remote Proxy").strip() != "[Remote Proxy]\n# Add your own subscription definitions here. Never publish private URLs.":
            raise ValueError("private subscription or placeholder changed")
        outputs[entry] = body
        outputs["release/phase-07/" + entry.replace(".lcf", ".vNext-RC2.lcf")] = body
    if section(outputs["LoonKit.lcf"], "Rule") != section(outputs["LoonKit.PrivacyDNS.lcf"], "Rule"):
        raise ValueError("release profiles have different local routing")
    if section(outputs["LoonKit.lcf"], "Remote Rule") != section(outputs["LoonKit.PrivacyDNS.lcf"], "Remote Rule"):
        raise ValueError("release profiles have different remote subscriptions")
    manifest = {
        "schema_version": 1, "label": "vNext-RC2",
        "stage": "UNRELEASED_AWAITING_MAINTAINER_TEST_AND_APPROVAL",
        "source_snapshot_commit": spec["release_assets_commit"],
        "upstream_historical_lineage": "UNRECOVERABLE",
        "old_main_rollback_commit": spec["historic_main_commit"],
        "locked_inputs_path": "refactor/vnext/sources.lock.json",
        "rules": locked,
        "remote_subscription_count": len(locked),
        "remote_rule_count": sum(x["rule_count"] for x in locked.values()),
        "profile_sha256": {p: hashlib.sha256(v.encode("utf-8")).hexdigest()
                           for p, v in outputs.items()},
        "plugin_path": "release/phase-07/assets/Network_Diagnostics.plugin",
        "plugin_sha256": hashlib.sha256(plugin.encode("utf-8")).hexdigest(),
        "device_test": "NOT_EXECUTED",
        "licenses": "BLOCKED_REVIEW",
        "maintainer_approval": "NOT_EXECUTED",
    }
    outputs["release/phase-07/RC_MANIFEST.json"] = json.dumps(
        manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    return outputs


def run(check: bool) -> int:
    files = generate()
    stale = []
    for rel, data in sorted(files.items()):
        path = ROOT / rel
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != data:
                stale.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data, encoding="utf-8")
    if stale:
        raise RuntimeError("stale/unbuilt release profile or manifest: " + ", ".join(stale))
    print(f"Phase 07 {'CHECK' if check else 'BUILD'}: {len(files)} artifacts, pinned resources, 26 rules")
    return 0


def main() -> None:
    p = argparse.ArgumentParser()
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--build", action="store_true")
    a = p.parse_args()
    run(a.check)


if __name__ == "__main__":
    main()
