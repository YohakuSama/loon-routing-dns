#!/usr/bin/env python3
"""Validate every active beta resource, not just the historical overlay count."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URI = re.compile(r"https://raw\.githubusercontent\.com/YohakuSama/loonkit/(?P<sha>[a-f0-9]{40})/(?P<path>[A-Za-z0-9_./-]+)\Z")


def section(profile: str, name: str) -> str:
    hit = re.search(r"(?m)^\[" + re.escape(name) + r"\]$", profile)
    if not hit:
        raise ValueError("missing Loon section: " + name)
    text = profile[hit.end():]
    tail = re.search(r"(?m)^\[[^\]]+\]$", text)
    return text[:tail.start()] if tail else text


def remote_entries(profile: str) -> list[dict]:
    result = []
    for line in section(profile, "Remote Rule").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        uri, *flags = [x.strip() for x in line.split(",")]
        match = URI.fullmatch(uri)
        if not match or ".." in match["path"].split("/"):
            raise ValueError("remote rules must use reviewed repository commit URLs")
        options = dict(x.split("=", 1) for x in flags if "=" in x)
        if len(options) != len(flags) or options.get("enabled") != "true":
            raise ValueError("invalid or disabled public beta resource")
        if not options.get("policy") or not options.get("tag"):
            raise ValueError("resource lacks policy or tag")
        result.append({"uri": uri, "commit": match["sha"], "path": match["path"], **options})
    if len({r["tag"] for r in result}) != len(result):
        raise ValueError("duplicate remote resource tag")
    return result


def resource_records(meta: dict) -> dict[str, dict]:
    records = list(meta["overlay_rules"].values()) + [meta["china_direct"], meta["adblock"]]
    records += list(meta.get("upstream_overlays", {}).values())
    result = {}
    for row in records:
        if row["uri"] in result:
            raise ValueError("duplicate manifest resource URI")
        result[row["uri"]] = row
    return result


def content_rules(raw: bytes) -> list[str]:
    return [r.strip() for r in raw.decode("utf-8").splitlines()
            if r.strip() and not r.lstrip().startswith(("#", ";", "//"))]


def validate(root: Path = ROOT, *, remote: bool = False) -> dict:
    meta = json.loads((root / "build/beta_manifest.json").read_text())
    profile = (root / "beta/LoonKit.lcf").read_bytes()
    if meta.get("configuration_entry") != "beta/LoonKit.lcf":
        raise ValueError("beta entry must be isolated from production")
    if hashlib.sha256(profile).hexdigest() != meta["configuration_sha256"]:
        raise ValueError("beta profile checksum mismatch")
    if hashlib.sha256((root / "build/baselines/v6.5.4/LoonKit.lcf").read_bytes()).hexdigest() != meta["original_production_config_sha256"]:
        raise ValueError("formal configuration changed during beta work")
    text = profile.decode()
    if text.splitlines()[0] != "# LoonKit " + meta["version"] + " · BETA TEST ONLY":
        raise ValueError("beta version and manifest differ")
    records = resource_records(meta)
    published = json.loads((root / "build/baselines/v6.5.4/release_manifest.json").read_text())["rules"]
    formal = {row["path"]: row for row in published.values()}
    entries = remote_entries(text)
    used = set()
    checks = []
    formal_count = 0
    for entry in entries:
        raw = (root / entry["path"]).read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if entry["uri"] in records:
            used.add(entry["uri"])
            expected = records[entry["uri"]]
            if sha != expected["sha256"] or len(content_rules(raw)) != expected["matcher_count"]:
                raise ValueError("beta asset hash/count differs: " + entry["path"])
        elif entry["commit"] == meta["production_release_commit"] and entry["path"] in formal:
            formal_count += 1
            if sha != formal[entry["path"]]["sha256"]:
                raise ValueError("historical formal asset changed")
        else:
            raise ValueError("undeclared beta resource: " + entry["uri"])
        checks.append({**entry, "sha256": sha})
    if used != set(records) or formal_count != meta["production_rule_refs_preserved"]:
        raise ValueError("manifest resource set differs from active profile")
    if len(entries) != meta["runtime_remote_count"]:
        raise ValueError("unexpected active beta source count")
    for group, item in meta.get("upstream_overlays", {}).items():
        if not any(r["uri"] == item["uri"] and r["policy"] == group for r in entries):
            raise ValueError("upstream overlay lost its reviewed service owner")
    if remote:
        def verify(row):
            with urllib.request.urlopen(row["uri"], timeout=40) as response:
                if not URI.fullmatch(response.geturl()):
                    raise ValueError("resource redirected outside immutable repository URL")
                data = response.read(8 * 1024 * 1024 + 1)
            if len(data) > 8 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise ValueError("published immutable bytes differ: " + row["path"])
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(verify, checks))
    return {"version": meta["version"], "resources": len(checks), "remote_verified": remote,
            "configuration_sha256": meta["configuration_sha256"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(remote=args.remote), sort_keys=True))
