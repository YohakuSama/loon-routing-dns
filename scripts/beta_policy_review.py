#!/usr/bin/env python3
"""Build the single reversible balanced ad filter from locked, reviewed inputs."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rules(data: bytes) -> list[str]:
    return [s.strip() for s in data.decode("utf-8").splitlines()
            if s.strip() and not s.lstrip().startswith(("#", ";", "//"))]


def matches(rule: str, host: str) -> bool:
    kind, value = rule.split(",")
    return host == value if kind == "DOMAIN" else host == value or host.endswith("." + value)


def render(root: Path = ROOT) -> tuple[Path, bytes]:
    spec = json.loads((root / "rules/beta/balanced_decisions.json").read_text())
    policy = json.loads((root / "rules/beta/policy_overrides.json").read_text())
    source = (root / spec["baseline_path"]).read_bytes()
    if spec.get("schema_version") != 1 or hashlib.sha256(source).hexdigest() != spec["baseline_sha256"]:
        raise ValueError("unreviewed balanced-filter baseline")
    original = rules(source)
    excluded = [r["rule"] for r in spec["excluded_rules"]]
    if len(excluded) != len(set(excluded)) or any(original.count(r) != 1 for r in excluded):
        raise ValueError("reviewed filter exclusion missing or duplicated")
    merged = [r for r in original if r not in excluded]
    merged.extend(policy["adblock_local_rules"])
    merged.extend(row["rule"] for row in spec["privacy_additions"])
    merged = list(dict.fromkeys(merged))
    for rule in merged:
        if not rule.startswith(("DOMAIN,", "DOMAIN-SUFFIX,")) or rule.count(",") != 1:
            raise ValueError("unsupported balanced-filter matcher")
    for host in spec["critical_function_hosts"]:
        if any(matches(r, host) for r in merged):
            raise ValueError("critical certificate/login/payment host blocked: " + host)
    path = root / "rules/beta" / policy["version"] / "AdBlockBalanced.list"
    data = ("# LoonKit " + policy["version"] + " balanced AdBlock; disable this one resource to restore service routing\n"
            + "\n".join(merged) + "\n").encode()
    return path, data


def check(root: Path = ROOT) -> dict:
    path, data = render(root)
    if not path.is_file() or path.read_bytes() != data:
        raise ValueError("balanced AdBlock differs from reviewed inputs")
    return {"sha256": hashlib.sha256(data).hexdigest(), "matchers": len(rules(data))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(check(), sort_keys=True))
