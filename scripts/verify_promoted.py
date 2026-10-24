#!/usr/bin/env python3
"""Version-specific, fail-closed verification of the v6.5.5 beta promotion."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
from urllib import request
import beta_channel
import verify_release as historical

ROOT = Path(__file__).resolve().parents[1]
RAW = "https://raw.githubusercontent.com/YohakuSama/loonkit/"
CANDIDATE_SHA = "fd1a01c6f8363a5dffaa1db9dbf044014c711fa48ea46e34a7c107180acbe0b7"
CANDIDATE_COMMIT = "adc567168eed8e21dc8d80aebc40b85f35fc1a1b"
ASSET_COMMIT = "1b54e079486a06a5cfff5c5f03016628a52a7701"


def active(data: bytes) -> bytes:
    return ("\n".join(line.strip() for line in data.decode("utf-8").splitlines()
                      if line.strip() and not line.lstrip().startswith("#")) + "\n").encode("utf-8")


def verify(remote: bool = False, root: Path = ROOT, historical_v655: bool = False) -> dict:
    spec = json.loads((root / "build/release_spec.json").read_text())
    published = json.loads((root / ("build/baselines/v6.5.5/release_manifest.json" if historical_v655 else "build/release_manifest.json")).read_text())
    baseline = json.loads((root / "build/baselines/v6.5.4/release_manifest.json").read_text())
    candidate = json.loads((root / "build/beta_manifest.json").read_text())
    if spec["stable_release_version"] != ("v6.5.6" if historical_v655 else "v6.5.5") or published["label"] != "v6.5.5":
        raise ValueError("unexpected release version")
    historical.check_public_checksums(root, published, spec)
    historical.check_lock(root)
    old_profile = (root / "build/baselines/v6.5.4/LoonKit.lcf").read_bytes()
    if historical.sha(old_profile) != "6bb6f4dc936e250fbff36763391a976a7f3d7bc833ea549c322832a9c3086a69":
        raise ValueError("v6.5.4 template was changed")
    if baseline["profile_sha256"] != {"LoonKit.lcf": historical.sha(old_profile)}:
        raise ValueError("historical publication manifest was changed")
    beta = (root / "beta/LoonKit.lcf").read_bytes()
    stable = (root / ("build/baselines/v6.5.5/LoonKit.lcf" if historical_v655 else "LoonKit.lcf")).read_bytes()
    if historical_v655 and historical.sha(stable) != "d97984a42e313e5b4fc81c26ce760fd4d1163275ad7278e3930cbce69dcf9f03":
        raise ValueError("v6.5.5 released profile baseline changed")
    if any((historical.sha(beta) != CANDIDATE_SHA,
            published.get("promoted_beta_config_sha256") != CANDIDATE_SHA,
            spec.get("promoted_beta_config_sha256") != CANDIDATE_SHA,
            candidate.get("configuration_sha256") != CANDIDATE_SHA,
            published.get("promoted_beta_commit_sha") != CANDIDATE_COMMIT,
            published.get("promoted_beta_asset_commit") != ASSET_COMMIT,
            spec.get("promoted_candidate_commit") != CANDIDATE_COMMIT)):
        raise ValueError("tested candidate is not preserved exactly")
    if not stable.startswith(b"# LoonKit v6.5.5\n") or active(stable) != active(beta):
        raise ValueError("effective Loon directives or routing order differ from tested candidate")
    if historical.sha(active(stable)) != spec["approved_runtime_directives_sha256"]:
        raise ValueError("approved non-comment runtime hash changed")
    if historical.sha(stable) != published["profile_sha256"]["LoonKit.lcf"]:
        raise ValueError("new stable configuration checksum mismatch")
    if any(ord(ch) > 127 for line in stable.decode().splitlines() if line.lstrip().startswith("#")
           for ch in line):
        raise ValueError("formal configuration comments must be English")
    if (root / "LoonKit.PrivacyDNS.lcf").exists():
        raise ValueError("retired alternate profile reintroduced")
    if candidate["immutable_overlay_commit"] != ASSET_COMMIT or candidate["runtime_remote_count"] != 36:
        raise ValueError("beta resource baseline changed")
    beta_channel.validate(root, remote=False)
    compiled = {key.removeprefix("build/generated/"): data.encode()
                for key, data in historical.compile_rules(root).items()
                if key.startswith("build/generated/") and key.endswith(".list")}
    if len(compiled) != 26 or len(baseline["rules"]) != 26:
        raise ValueError("historical frozen compiler contract changed")
    legacy_count = 0
    for group, row in baseline["rules"].items():
        raw = (root / row["path"]).read_bytes()
        if raw != compiled[group + ".list"] or historical.sha(raw) != row["sha256"]:
            raise ValueError("historical compiled asset differs: " + group)
        legacy_count += row["rule_count"]
    if legacy_count != 197765 or published.get("legacy_compiler_matcher_count") != 197765:
        raise ValueError("historical matcher contract changed")
    actual = beta_channel.remote_entries(stable.decode())
    expected = published.get("runtime_resources", [])
    if len(actual) != 36 or len(expected) != 36 or published.get("runtime_rule_count") != 36:
        raise ValueError("formal resource count changed")
    count = 0
    for a, e in zip(actual, expected):
        if (a["uri"], a["path"], a["policy"], a["tag"], a["commit"]) != (
            e["uri"], e["path"], e["policy"], e["tag"], e["commit"]):
            raise ValueError("resource order, ownership, tag or immutable SHA changed")
        body = (root / e["path"]).read_bytes()
        if historical.sha(body) != e["sha256"] or len(beta_channel.content_rules(body)) != e["matcher_count"]:
            raise ValueError("rule bytes or matcher count changed: " + e["path"])
        count += e["matcher_count"]
    if count != published["runtime_rule_matcher_count"] or count != published["remote_rule_count"]:
        raise ValueError("formal matcher sum changed")
    if "AdBlock = select,REJECT,Proxy," not in historical.section(stable.decode(), "Proxy Group"):
        raise ValueError("reviewed AdBlock proxy-pass option lost")
    if sum(x["policy"] == "AdBlock" for x in actual) != 1:
        raise ValueError("AdBlock must remain one resource")
    for key in historical.DNS:
        if re.search(r"(?m)^" + re.escape(key) + r"\s*=", historical.section(stable.decode(), "General")) is None:
            raise ValueError("missing DNS/TUN control: " + key)
    if "GEOIP,CN,DIRECT,no-resolve" not in stable.decode() or "FINAL,Final" not in stable.decode():
        raise ValueError("default routing guards missing")
    profile_links = historical.LINK.findall(stable.decode())
    icons = [(commit, path) for commit, path in profile_links if path.startswith("icons/")]
    plugins = [(commit, path) for commit, path in profile_links if path.endswith(".plugin")]
    if len(icons) != 33 or len(set(path for _, path in icons)) != 33:
        raise ValueError("expected 33 pinned icons")
    if set(icons) != {(spec["reviewed_auxiliary_commit"], f"icons/v20261021r1/{group}.png")
                     for group in ("Proxy","Auto","Fallback","AdBlock","Final","AI","Google","Microsoft","Apple",
                                   "YouTube","Netflix","Disney","PrimeVideo","Spotify","TikTok","Twitch","HBO",
                                   "Abema","AnimeCrazy","Dazn","BBC","Bilibili","Telegram","Whatsapp","Instagram",
                                   "Facebook","Twitter","Discord","Line","Reddit","Linkedin","Steam","Paypal")}:
        raise ValueError("icon pin or strategy mapping changed")
    if plugins != [(spec["plugin_assets_commit"], "release/Network_Diagnostics.plugin")]:
        raise ValueError("network diagnostics plugin pin changed")
    plugin = (root / "release/Network_Diagnostics.plugin").read_bytes()
    if historical.sha(plugin) != published["plugin_sha256"]:
        raise ValueError("plugin bytes changed")
    scripts = historical.LINK.findall(plugin.decode())
    if len(scripts) != 5:
        raise ValueError("embedded plugin assets differ")
    for commit, path in scripts:
        expected_commit = (spec["diagnostics_script_commit"] if path.endswith("/network-diagnostics.js") else
                           spec["node_script_commit"] if path.endswith("/node-intelligence.js") else
                           spec["unified_service_diagnostics_script_commit"] if path.endswith("/media-unlock.js") else
                           spec["script_assets_commit"])
        if commit != expected_commit or not (root / path).is_file():
            raise ValueError("plugin embedded asset drift: " + path)
    if remote:
        links = list({(a["commit"], a["path"]) for a in actual} | set(icons) | set(plugins) | set(scripts))
        def check(row):
            commit, path = row
            url = RAW + commit + "/" + path
            with request.urlopen(request.Request(url, headers={"User-Agent":"LoonKit-Release/1"}),timeout=30) as response:
                if response.geturl() != url:
                    raise ValueError("immutable asset redirected: " + path)
                blob = response.read(8 * 1024 * 1024 + 1)
            if len(blob) > 8 * 1024 * 1024 or historical.sha(blob) != historical.sha((root / path).read_bytes()):
                raise ValueError("immutable remote asset hash mismatch: " + path)
        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(check, links))
    return {"version":"v6.5.5", "tested_beta_sha256":CANDIDATE_SHA,
            "runtime_resources":len(actual), "runtime_matchers":count,
            "historical_compiled_rules":len(compiled), "remote_checked":remote}
