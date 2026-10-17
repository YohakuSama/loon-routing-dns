#!/usr/bin/env python3
"""Validate the separate HelloBike compatibility review profile (stdlib only)."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "Loon_Routing_DNS.lcf"
REVIEW = ROOT / "reviews" / "Loon_Routing_DNS_HelloBike_Review.lcf"
OWN_DOMAINS = ROOT / "rules" / "custom" / "HelloBike.list"

def section(doc, name):
    match = re.search(r"(?m)^\[" + re.escape(name) + r"\]\s*$", doc)
    assert match, f"missing [{name}]"
    next_section = re.search(r"(?m)^\[[^\]]+\]\s*$", doc[match.end():])
    return doc[match.end():match.end() + next_section.start()] if next_section else doc[match.end():]

def uncommented(text):
    return [s.strip() for s in text.splitlines() if s.strip() and not s.lstrip().startswith("#")]

def main():
    original = ORIGINAL.read_text(encoding="utf-8")
    review = REVIEW.read_text(encoding="utf-8")
    assert review.startswith("# Loon Routing DNS v4.5.0-hello-review")
    assert section(review, "General") == section(original, "General"), "General or DNS changed"
    assert section(review, "Remote Rule") == section(original, "Remote Rule"), "upstream rule subscriptions changed"
    assert section(review, "Plugin") == section(original, "Plugin"), "plugin references changed"
    assert section(review, "Remote Proxy") == section(original, "Remote Proxy"), "private proxy field changed"
    orig_groups = uncommented(section(original, "Proxy Group"))
    reviewed_groups = uncommented(section(review, "Proxy Group"))
    assert len(orig_groups) == 33 and len(reviewed_groups) == 34
    assert len([s for s in reviewed_groups if s.startswith("HelloBike = select,DIRECT,")]) == 1
    assert len([s for s in reviewed_groups if s.startswith("AdBlock = select,DIRECT,REJECT,")]) == 1
    assert len([s for s in reviewed_groups if s.startswith("Final = select,")]) == 1
    keep = [s for s in reviewed_groups if not s.startswith(("HelloBike = ", "AdBlock = "))]
    assert keep == [s for s in orig_groups if not s.startswith("AdBlock = ")], "unrelated strategy group mutated"
    orig_rule_lines = uncommented(section(original, "Rule"))
    new_rule_lines = uncommented(section(review, "Rule"))
    overrides = new_rule_lines[:7]
    expected = [
        "DOMAIN-SUFFIX,hello-inc.com,HelloBike",
        "DOMAIN-SUFFIX,hellobike.com,HelloBike",
        "DOMAIN-SUFFIX,helloglobal.com,HelloBike",
        "DOMAIN-SUFFIX,amap.com,DIRECT",
        "DOMAIN-SUFFIX,autonavi.com,DIRECT",
        "DOMAIN-SUFFIX,alipay.com,DIRECT",
        "DOMAIN-SUFFIX,alipayobjects.com,DIRECT",
    ]
    assert overrides == expected, "compatibility override changed"
    assert new_rule_lines[7:] == orig_rule_lines, "other local rules were altered"
    matches = set()
    for line in new_rule_lines:
        bits = line.split(",")
        if bits[0].startswith("DOMAIN"):
            key = (bits[0], bits[1])
            assert key not in matches, "duplicate local match: " + str(key)
            matches.add(key)
    own = uncommented(OWN_DOMAINS.read_text(encoding="utf-8"))
    assert own == [s.rsplit(",", 1)[0] for s in expected[:3]], "self-maintained registry diverges"
    assert review.count("\n[Remote Rule]\n") == 1
    assert len(uncommented(section(review, "Remote Rule"))) == 28
    print("HelloBike profile OK: 34 groups, 28 remote lists, 7 precise additions, unchanged DNS/plugin.")
if __name__ == "__main__":
    main()
