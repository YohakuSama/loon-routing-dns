#!/usr/bin/env python3
"""Strict, read-only formal v6.0.0 integrity check."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib import request
from rule_engine import compile_rules
from source_lock import check_lock

ROOT = Path(__file__).resolve().parents[1]
RAW = "https://raw.githubusercontent.com/YohakuSama/loonkit/"
LINK = re.compile(r'https://raw[.]githubusercontent[.]com/YohakuSama/loonkit/([a-f0-9]{40})/([^,\s")]+)')
DNS = ("dns-server", "doh-server", "hijack-dns", "ip-mode", "ipv6-vif",
       "interface-mode", "skip-proxy", "bypass-tun", "real-ip")


def sha(content):
    return hashlib.sha256(content).hexdigest()


def section(profile, name):
    start = profile.index("[" + name + "]")
    end = profile.find("\n[", start+1)
    return profile[start:end if end >= 0 else None]


def verify(remote=False):
    spec = json.loads((ROOT/"build/release_spec.json").read_text())
    release = json.loads((ROOT/"build/release_manifest.json").read_text())
    checked = check_lock(ROOT)
    compiled = {key.removeprefix("build/generated/"): data.encode("utf-8")
                for key, data in compile_rules(ROOT).items()
                if key.startswith("build/generated/") and key.endswith(".list")}
    if spec["release_rules_dir"] != "rules/releases/vNext-RC2" or spec["source_snapshot_dir"] != "rules/inputs":
        raise ValueError("release input/output directory changed")
    if len(compiled) != len(release["rules"]) or len(compiled) != 26:
        raise ValueError("wrong number of published rule groups")
    total = 0
    for group, info in sorted(release["rules"].items()):
        name = group + ".list"
        if info["path"] != "rules/releases/vNext-RC2/" + name or name not in compiled:
            raise ValueError("rule or manifest path missing: " + group)
        data = (ROOT/info["path"]).read_bytes()
        if data != compiled[name] or sha(data) != info["sha256"]:
            raise ValueError("released rule differs from locked rebuild: " + group)
        count = sum(bool(line) and not line.startswith("#") for line in data.decode().splitlines())
        if count != info["rule_count"]:
            raise ValueError("rule count changed: " + group)
        total += count
    if total != release["remote_rule_count"] or total != 197765:
        raise ValueError("matcher total changed")
    if (ROOT/"LoonKit.PrivacyDNS.lcf").exists():
        raise ValueError("retired alternate profile reintroduced")
    data = (ROOT/"LoonKit.lcf").read_bytes()
    if sha(data) != release["profile_sha256"]["LoonKit.lcf"] or set(release["profile_sha256"]) != {"LoonKit.lcf"}:
        raise ValueError("protected standard profile changed or duplicate profile manifest exists")
    profile = data.decode("utf-8")
    if not profile.startswith("# LoonKit v6.0.0"):
        raise ValueError("unexpected production profile version")
    if (ROOT/"rules/generated").exists() or (ROOT/"rules/ProxyProtect.list").exists() or (ROOT/"rules/active_profile.json").exists():
        raise ValueError("retired compatibility rules reintroduced")
    if (ROOT/"plugins").exists():
        raise ValueError("obsolete plugin aliases reintroduced")
    for profile in (profile,):
        for key in DNS:
            if not re.search(r"(?m)^"+re.escape(key)+r"\s*=",section(profile,"General")):
                raise ValueError("missing DNS/TUN property: " + key)
        if "GEOIP,CN,DIRECT,no-resolve" not in section(profile,"Rule") or "FINAL,Final" not in section(profile,"Rule"):
            raise ValueError("GEOIP or FINAL selector missing")
        if "AdBlock = select,REJECT,DIRECT" not in section(profile,"Proxy Group"):
            raise ValueError("AdBlock selector not selectable")
        links = LINK.findall(profile)
        rules = [(ref,path) for ref,path in links if path.startswith("rules/releases/")]
        icons = [(ref,path) for ref,path in links if path.startswith("icons/")]
        plugins = [(ref,path) for ref,path in links if path.startswith("release/phase-07/assets/")]
        if len(rules)!=26 or len(set(path for _,path in rules))!=26 or len(icons)!=33:
            raise ValueError("wrong number of pinned rule/icon subscriptions")
        if plugins != [(spec["plugin_assets_commit"],"release/phase-07/assets/Network_Diagnostics.plugin")]:
            raise ValueError("plugin URL unexpectedly changed")
        for ref,path in links:
            if not (ROOT/path).is_file():
                raise ValueError("missing referenced asset: " + path)
            if path.startswith("rules/releases/") and (ref!=spec["release_assets_commit"] or path not in [v["path"] for v in release["rules"].values()]):
                raise ValueError("rule pinned ref changed")
            if path.startswith("icons/") and ref != spec["reviewed_auxiliary_commit"]:
                raise ValueError("icon pinned ref changed")
    plugin=(ROOT/release["plugin_path"]).read_bytes()
    if sha(plugin)!=release["plugin_sha256"]:
        raise ValueError("production pinned plugin hash changed")
    # Inspect the embedded immutable URLs as well as the top-level plugin link.
    # The diagnostic path is versioned to avoid stale Loon script caches.
    embedded = LINK.findall(plugin.decode("utf-8"))
    expected_script = "scripts/v20261020r2/network-diagnostics.js"
    if len(embedded) != 4 or sum(path == expected_script for _,path in embedded) != 2:
        raise ValueError("expected immutable scripts or plugin icon missing")
    for ref,path in embedded:
        if ref != spec["script_assets_commit"] or not path.startswith(("scripts/", "icons/")):
            raise ValueError("untrusted plugin script/icon reference: " + path)
        if not (ROOT / path).is_file():
            raise ValueError("missing plugin script/icon resource: " + path)
    if remote:
        for ref,path in sorted(set(LINK.findall(profile) + embedded)):
            if not path.startswith(("icons/","rules/releases/","release/phase-07/assets/","scripts/")):
                continue
            with request.urlopen(request.Request(RAW+ref+"/"+path,headers={"User-Agent":"LoonKit-Integrity/1"}),timeout=25) as response:
                live=response.read()
            if sha(live)!=sha((ROOT/path).read_bytes()):
                raise ValueError("Raw content changed: "+path)
    return {"release":"v6.0.0","rules":26,"matchers":total,"locked_inputs":checked["verified_frozen_inputs"],"profiles":1,"remote_checked":remote}


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--check",action="store_true",required=True)
    p.add_argument("--remote",action="store_true")
    a=p.parse_args()
    print(json.dumps(verify(a.remote),sort_keys=True))
