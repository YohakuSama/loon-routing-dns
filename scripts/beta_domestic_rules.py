#!/usr/bin/env python3
"""Fail-closed generator: subtract only approved direct matchers from frozen ChinaDirect."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "rules/beta/domestic_decisions.json"

def render(root: Path = ROOT) -> tuple[Path, bytes]:
    policy = json.loads((root/"rules/beta/domestic_decisions.json").read_text(encoding="utf-8"))
    if policy["schema_version"] != 1 or not policy["reviewed_exclusions"]:
        raise ValueError("unreviewed direct-rule decisions")
    path = root/policy["upstream_baseline"]
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != policy["original_sha256"]:
        raise ValueError("baseline direct snapshot content changed")
    lines = [x for x in source.decode("utf-8").splitlines()
             if x and not x.startswith(("#", ";", "//"))]
    if len(lines) != policy["original_matchers"] or len(lines) != len(set(lines)):
        raise ValueError("baseline ChinaDirect matcher count or duplicates changed")
    exclusion = set()
    for decision in policy["reviewed_exclusions"]:
        if decision.get("matcher"):
            selected = [x for x in lines if x == decision["matcher"]]
        elif decision.get("kind") == "USER-AGENT":
            selected = [x for x in lines if x.startswith("USER-AGENT,")]
        else:
            raise ValueError("unsupported domestic exclusion decision")
        if len(selected) != decision["count"] or exclusion.intersection(selected):
            raise ValueError("unreviewed ChinaDirect exclusion changed")
        exclusion.update(selected)
    remaining = [x for x in lines if x not in exclusion]
    if len(remaining) != policy["expected_output_matchers"]:
        raise ValueError("unexpected direct matcher count")
    dest = root / "rules/beta" / policy["version"] / "ChinaDirect.list"
    data = ("# LoonKit " + policy["version"] + " generated ChinaDirect — immutable beta candidate; see rules/beta/domestic_decisions.json\n"
            + "\n".join(remaining) + "\n").encode("utf-8")
    return dest, data

def check(root: Path = ROOT):
    dest, expected = render(root)
    if not dest.is_file() or dest.read_bytes() != expected:
        raise ValueError("beta ChinaDirect is not bit-identical to reviewed decisions")
    return {"status":"MATCH", "sha256":hashlib.sha256(expected).hexdigest(),
            "matcher_count":len([x for x in expected.decode().splitlines() if x and not x.startswith("#")])}

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(check(), sort_keys=True))
