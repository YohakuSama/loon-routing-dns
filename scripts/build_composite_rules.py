#!/usr/bin/env python3
"""Stage Loon-native rule lists from reviewed sources. Standard library only.

Outputs never modify the active Loon_Routing_DNS.lcf. Publishing/activation
requires a separate review of routing, licensing and iPhone behavior.
"""
import argparse
from collections import defaultdict
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import sys
import urllib.request
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "rules" / "sources.json"
OUT = ROOT / "rules" / "generated"
ALLOWED_TYPES = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "IP-CIDR",
    "IP-CIDR6", "IP-ASN", "USER-AGENT",
}
DOMAIN_RE = re.compile(r"^[a-z0-9*._-]+$", re.I)
GROUP_NAMES = {"動畫瘋": "AnimeCrazy"}
MAX_FILE_BYTES = 35_000_000


def normalize(text, source_format="loon"):
    """Return (canonical rule, reason). Unknown types are quarantined."""
    line = text.strip().lstrip("\ufeff")
    if not line or line.startswith(("#", "//", ";")):
        return None, None
    if source_format == "domainset":
        if line.startswith("+."):
            line = line[2:]
            kind = "DOMAIN-SUFFIX"
        elif line.startswith("."):
            line = line[1:]
            kind = "DOMAIN-SUFFIX"
        else:
            kind = "DOMAIN"
        value = line.lower().rstrip(".")
        if not value or not DOMAIN_RE.fullmatch(value):
            return None, "invalid domain-set item"
        return kind + "," + value, None

    chunks = [p.strip() for p in line.split(",")]
    if len(chunks) < 2:
        return None, "malformed Loon rule"
    kind, value = chunks[0].upper(), chunks[1]
    if kind == "URL-REGEX":
        return None, "URL-REGEX excluded (may require MITM; separate review)"
    if kind not in ALLOWED_TYPES:
        return None, "unsupported rule type: " + kind
    if not value:
        return None, "empty match value"
    if kind.startswith("DOMAIN"):
        value = value.lower().rstrip(".")
        if not DOMAIN_RE.fullmatch(value):
            return None, "invalid domain value"
    if kind.startswith("IP-CIDR"):
        try:
            network = ipaddress.ip_network(value, strict=False)
        except ValueError:
            return None, "invalid IP network"
        if (network.version == 6) != (kind == "IP-CIDR6"):
            return None, "IP family mismatch"
        value = str(network)
        return kind + "," + value + ",no-resolve", None
    if kind == "IP-ASN":
        value = value.upper()
        if not re.fullmatch(r"(AS)?\d+", value):
            return None, "invalid ASN"
    # Non-IP match types should not carry a target policy from upstream.
    if len(chunks) > 2 and any(p and p.lower() != "no-resolve" for p in chunks[2:]):
        return None, "unexpected trailing fields"
    return kind + "," + value, None


def read_catalog(path=CATALOG):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    sources = [s for s in data["sources"] if s.get("enabled")]
    if len({s["id"] for s in sources}) != len(sources):
        raise ValueError("duplicate source ids")
    for s in sources:
        url = urlparse(s["url"])
        if (url.scheme != "https" or url.netloc != "raw.githubusercontent.com"
                or not url.path.startswith("/blackmatrix7/ios_rule_script/")):
            raise ValueError("unreviewed source URL: " + s["url"])
        if not re.fullmatch(r"[\w\u4e00-\u9fff-]+", s["group"]):
            raise ValueError("unsafe output group: " + s["group"])
        if s["format"] not in {"loon", "domainset"}:
            raise ValueError("unknown source format")
    return sources


def fetch_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": "LoonCompositeAudit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        blob = resp.read(MAX_FILE_BYTES + 1)
    if len(blob) > MAX_FILE_BYTES:
        raise ValueError("source exceeds maximum byte limit: " + url)
    return blob.decode("utf-8-sig")


def generate(sources, fetch=fetch_text):
    by_group = defaultdict(dict)
    owners = defaultdict(set)
    source_stats = []
    quarantined = defaultdict(int)
    quarantined_examples = []
    intra_dupes = 0
    for s in sources:
        body = fetch(s["url"])
        parsed = 0
        deduped = 0
        source_rules = set()
        for number, raw in enumerate(body.splitlines(), 1):
            rule, reason = normalize(raw, s["format"])
            if reason:
                quarantined[reason] += 1
                if len(quarantined_examples) < 50:
                    quarantined_examples.append({
                        "source": s["id"], "line": number, "reason": reason,
                        "value": raw[:180],
                    })
                continue
            if rule is None:
                continue
            parsed += 1
            source_rules.add(rule)
            key = s["group"]
            if rule in by_group[key]:
                intra_dupes += 1
                deduped += 1
            else:
                by_group[key][rule] = s["id"]
            owners[rule].add((s["group"], s["policy"]))
        if parsed < s["min_rules"]:
            raise ValueError(
                f'{s["id"]}: {parsed} parsed rules below min_rules={s["min_rules"]}; '
                "refusing partial upstream update"
            )
        update_match = re.search(r"(?m)^# UPDATED:\s*(\d{4}-\d{2}-\d{2})", body)
        source_stats.append({
            "id": s["id"], "group": s["group"], "policy": s["policy"],
            "normalized_sha256": hashlib.sha256(
                "\n".join(sorted(source_rules)).encode("utf-8")
            ).hexdigest(),
            "upstream_updated": update_match.group(1) if update_match else None,
            "parsed": parsed, "duplicate_within_group": deduped,
        })

    exact_conflicts = []
    same_policy_reused = 0
    exact_different_policy_count = 0
    for rule, targets in owners.items():
        if len(targets) < 2:
            continue
        if len({policy for _, policy in targets}) == 1:
            same_policy_reused += 1
        else:
            exact_different_policy_count += 1
            if len(exact_conflicts) < 100:
                exact_conflicts.append({
                    "rule": rule, "targets": sorted([list(t) for t in targets])
                })

    # DOMAIN exact/suffix ancestry with conflicting policy; samples only.
    suffixes = defaultdict(set)
    for rule, targets in owners.items():
        kind, _, val = rule.partition(",")
        if kind == "DOMAIN-SUFFIX":
            suffixes[val].update(policy for _, policy in targets)
    ancestor_conflicts = []
    ancestor_conflict_count = 0
    for rule, targets in owners.items():
        kind, _, val = rule.partition(",")
        if kind not in {"DOMAIN", "DOMAIN-SUFFIX"}:
            continue
        own_policies = {p for _, p in targets}
        parts = val.split(".")
        for offset in range(1, len(parts)):
            ancestor = ".".join(parts[offset:])
            if ancestor in suffixes and suffixes[ancestor] - own_policies:
                ancestor_conflict_count += 1
                if len(ancestor_conflicts) < 100:
                    ancestor_conflicts.append({
                        "rule": rule, "covers_with": "DOMAIN-SUFFIX," + ancestor,
                        "policies": sorted(own_policies | suffixes[ancestor])
                    })
                break

    output = {}
    for group, rules in sorted(by_group.items()):
        name = GROUP_NAMES.get(group, group)
        if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
            raise ValueError("unsafe output file name: " + name)
        contributors = [s["id"] for s in sources if s["group"] == group]
        header = [
            "# Loon staged composite rules: " + group,
            "# Sources: " + ", ".join(contributors),
            "# Review rules/README.md before enabling; upstream licensing applies.",
        ]
        output[name + ".list"] = "\n".join(header + sorted(rules)) + "\n"
    report = {
        "status": "STAGING_ONLY",
        "sources": source_stats,
        "group_sizes": {k: len(v) for k, v in sorted(by_group.items())},
        "duplicates_removed_within_group": intra_dupes,
        "cross_group_same_policy_repeated": same_policy_reused,
        "cross_group_different_policy_exact": exact_different_policy_count,
        "cross_group_different_policy_samples": exact_conflicts,
        "domain_suffix_ancestor_conflict_count": ancestor_conflict_count,
        "domain_suffix_ancestor_conflict_samples": ancestor_conflicts,
        "quarantined_by_reason": dict(sorted(quarantined.items())),
        "quarantined_examples": quarantined_examples,
        "notes": [
            "Cross-group duplicates are not deleted: groups may be independently enabled.",
            "Different-policy and ancestor conflicts require a routing priority review.",
            "Local [Rule] in Loon takes precedence over remote lists.",
            "No generated list is installed in the active configuration.",
        ],
    }
    return output, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default=str(CATALOG))
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    outputs, report = generate(read_catalog(args.catalog))
    dest = Path(args.out)
    old_report = dest / "audit.json"
    if old_report.exists():
        previous = json.loads(old_report.read_text(encoding="utf-8"))
        old_counts = {x["id"]: x["parsed"] for x in previous.get("sources", [])}
        for source in report["sources"]:
            prior = old_counts.get(source["id"])
            if prior and source["parsed"] < int(prior * 0.6):
                raise ValueError(
                    f'{source["id"]}: {source["parsed"]} vs previous {prior}; '
                    "more than 40% of rules disappeared; manual review required"
                )
    dest.mkdir(parents=True, exist_ok=True)
    for fname, content in outputs.items():
        (dest / fname).write_text(content, encoding="utf-8")
    (dest / "audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f'Staged {len(outputs)} groups from {len(report["sources"])} sources.')
    print(f'Duplicates removed within groups: {report["duplicates_removed_within_group"]}')
    print(f'Different-policy exact conflicts: {report["cross_group_different_policy_exact"]}')
    print(f'Quarantined unsupported/ambiguous lines: {sum(report["quarantined_by_reason"].values())}')


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, UnicodeError) as e:
        sys.exit("Rule stage failed (no config changed): " + str(e))
