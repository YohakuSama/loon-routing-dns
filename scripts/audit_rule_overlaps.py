#!/usr/bin/env python3
"""Offline published-rule overlap audit. No network or runtime Loon API required.

Checks exact cross-group duplicates and domain suffix shadowing in configured
subscription order. Shadowing is reported, not automatically treated as a bug:
a more specific earlier policy can be intentional.
"""
from pathlib import Path
from collections import defaultdict
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "Loon_Routing_DNS.lcf"
GENERATED = ROOT / "rules" / "generated"


def run():
    body = CONF.read_text(encoding="utf-8")
    match = re.search(r"(?ms)^\[Remote Rule\]\s*\n(.*?)(?=^\[|\Z)", body)
    if not match:
        raise ValueError("missing Remote Rule section")
    groups = []
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        found = re.match(r"https://[^,]+/([A-Za-z0-9]+)\.list,\s*policy=([^,]+)", line)
        if not found:
            raise ValueError("invalid remote rule: " + line)
        groups.append((found.group(1), found.group(2)))
    seen = {}
    suffixes = defaultdict(list)
    duplicates = []
    shadowed = []
    for group, policy in groups:
        path = GENERATED / (group + ".list")
        if not path.is_file():
            raise ValueError("missing " + str(path))
        for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            rule = raw.strip()
            if not rule or rule.startswith(("#", ";", "//")):
                continue
            parts = rule.split(",")
            if len(parts) < 2:
                raise ValueError(f"{path}:{number}: malformed rule")
            kind, value = parts[:2]
            key = (kind, value)
            if key in seen and seen[key][0] != group:
                duplicates.append((group, rule, seen[key][0]))
            else:
                seen.setdefault(key, (group, policy))
            if kind in ("DOMAIN", "DOMAIN-SUFFIX"):
                labels = value.split(".")
                for idx in range(len(labels)):
                    parent = ".".join(labels[idx:])
                    for prev_group, prev_policy in suffixes.get(parent, []):
                        if prev_group != group and prev_policy != policy:
                            shadowed.append((group, rule, prev_group, parent))
                            break
                    if shadowed and shadowed[-1][:2] == (group, rule):
                        break
                if kind == "DOMAIN-SUFFIX":
                    suffixes[value].append((group, policy))
    print(f"Groups: {len(groups)}; exact cross-group duplicates: {len(duplicates)}")
    print(f"Potential earlier suffix overlaps: {len(shadowed)}")
    for group, rule, owner in duplicates[:12]:
        print(f"  DUPLICATE {group}: {rule} (first: {owner})")
    for group, rule, owner, parent in shadowed[:12]:
        print(f"  OVERLAP {group}: {rule} (earlier suffix {parent} in {owner})")
    # Exact duplicates are deterministic conflicts; suffix overlaps need review.
    if duplicates:
        raise SystemExit("FAIL: exact cross-group duplicates detected")
    print("PASS: no exact cross-group duplicates; review suffix overlaps above")


if __name__ == "__main__":
    run()
