#!/usr/bin/env python3
"""Read-only, deterministic comparison of Git-pinned Loon routing baselines.

Legacy remote bodies are unknown at the historic observation time. They are
NEVER replaced with contemporary upstream bytes for per-rule comparison.
"""
import argparse
from collections import Counter, defaultdict
import ipaddress
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
IP_KINDS = frozenset({"IP-CIDR", "IP-CIDR6", "SRC-IP", "SRC-IP-CIDR", "GEOIP", "IP-ASN"})


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_rule(line, default_policy=None):
    """Canonical matcher IDs retain match type, policy and no-resolve flag."""
    line = line.strip()
    if not line or line.startswith(("#", "//", ";")):
        return None
    parts = [v.strip() for v in line.split(",")]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError("malformed Loon rule: " + line)
    kind, value = parts[:2]
    kind = kind.upper()
    if kind == "FINAL" and default_policy is None:
        if len(parts) != 2:
            raise ValueError("malformed FINAL: " + line)
        return {"kind": kind, "value": "*", "policy": value,
                "no_resolve": False, "ip_related": False}
    if kind in ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"):
        value = value.lower().rstrip(".")
    elif kind in ("IP-CIDR", "IP-CIDR6", "SRC-IP-CIDR"):
        network = ipaddress.ip_network(value, strict=False)
        if kind in ("IP-CIDR", "IP-CIDR6") and (kind == "IP-CIDR6") != (network.version == 6):
            raise ValueError("IP family mismatch: " + line)
        value = str(network)
    elif kind == "SRC-IP":
        value = str(ipaddress.ip_address(value))
    elif kind == "GEOIP":
        value = value.upper()
    elif kind == "IP-ASN":
        value = value.upper().removeprefix("AS")
        if not value.isdigit():
            raise ValueError("malformed IP-ASN: " + line)
    attributes = parts[2:]
    no_resolve = any(p.lower() == "no-resolve" for p in attributes)
    extras = [p for p in attributes if p.lower() != "no-resolve"]
    if default_policy is None:
        if not extras:
            raise ValueError("missing policy: " + line)
        policy = extras.pop(0)
    else:
        policy = default_policy
    if extras:
        raise ValueError("unsupported attributes: " + line)
    return {"kind": kind, "value": value, "policy": policy,
            "no_resolve": no_resolve, "ip_related": kind in IP_KINDS}


def matcher_id(rule):
    return rule["kind"], rule["value"]


def exact_id(rule):
    return rule["kind"], rule["value"], rule["no_resolve"]


def compare_rule_sets(before, after):
    """Compare exact rules only; DOMAIN is not DOMAIN-SUFFIX or KEYWORD."""
    a = {(exact_id(r), r["policy"]) for r in before}
    b = {(exact_id(r), r["policy"]) for r in after}
    key = lambda x: (x[0][0], x[0][1], x[0][2], x[1])
    render = lambda x: {"kind": x[0][0], "value": x[0][1],
                        "no_resolve": x[0][2], "policy": x[1]}
    matched = defaultdict(lambda: {"before": set(), "after": set()})
    for label, rows in (("before", before), ("after", after)):
        for row in rows:
            matched[matcher_id(row)][label].add((row["policy"], row["no_resolve"]))
    conflicts = [
        {"kind": k[0], "value": k[1],
         "before": [list(x) for x in sorted(v["before"])],
         "after": [list(x) for x in sorted(v["after"])]}
        for k, v in sorted(matched.items())
        if v["before"] and v["after"] and v["before"] != v["after"]
    ]
    return {
        "added": [render(x) for x in sorted(b - a, key=key)],
        "removed": [render(x) for x in sorted(a - b, key=key)],
        "policy_or_no_resolve_conflicts": conflicts,
        "kinds_before": dict(sorted(Counter(r["kind"] for r in before).items())),
        "kinds_after": dict(sorted(Counter(r["kind"] for r in after).items())),
        "ip_rules_before": sum(r["ip_related"] for r in before),
        "ip_rules_after": sum(r["ip_related"] for r in after),
        "no_resolve_before": sum(r["no_resolve"] for r in before),
        "no_resolve_after": sum(r["no_resolve"] for r in after),
    }


def make_report(root=ROOT):
    base = Path(root) / "baselines"
    old = read_json(base / "legacy/manifest.json")
    sources = read_json(base / "legacy/sources.json")
    new = read_json(base / "current/manifest.json")
    index = read_json(base / "current/rule-index.json")
    legacy = sources["remote_rules"]
    current = index["subscriptions"]
    old_local = [parse_rule(x["rule"]) for x in sources["local_rules"]]
    new_local = [parse_rule(x) for x in index["local_rules"]]
    old_urls = {x["url"] for x in legacy}
    new_urls = {x["url"] for x in current}
    total_types = Counter()
    for row in current:
        total_types.update(row["rule_types"])
    if old["historical_upstream_content_status"] != "HISTORICAL_CONTENT_UNAVAILABLE":
        raise ValueError("unsupported historic snapshot provenance: review required")
    return {
        "schema_version": 1,
        "legacy_commit": old["source_commit"],
        "current_commit": new["source_commit"],
        "counts": {
            "legacy_remote": len(legacy), "current_remote": len(current),
            "legacy_local": len(old_local), "current_local": len(new_local),
            "current_generated_groups": sum(x["group"] != "ProxyProtect" for x in current),
            "current_enabled_inputs": new["enabled_input_count"],
        },
        "source_changes": {
            "old_urls_only": sorted(old_urls - new_urls),
            "new_urls_only": sorted(new_urls - old_urls),
        },
        "order_before": [x["tag"] for x in legacy],
        "order_after": [x["group"] for x in current],
        "policy_before": [x["policy"] for x in legacy],
        "policy_after": [x["policy"] for x in current],
        "local_rule_diff": compare_rule_sets(old_local, new_local),
        "remote_rule_diff": {
            "status": "HISTORICAL_CONTENT_UNAVAILABLE",
            "added": None, "removed": None, "policy_conflicts": None,
            "reason": "Original upstream master URL bodies were not pinned at observation time",
        },
        "current_rule_types": dict(sorted(total_types.items())),
        "current_rule_counts": {x["group"]: x["rule_count"] for x in current},
        "current_ip_rules": sum(total_types[k] for k in IP_KINDS),
        "current_rule_no_resolve_count": "NOT_INDEXED",
        "known_risks": new["unresolved_questions"],
    }


def render_markdown(report):
    c = report["counts"]
    diff = report["local_rule_diff"]
    lines = [
        "# LoonKit — Phase 01 immutable baseline comparison", "",
        "Historical Git commit: " + report["legacy_commit"],
        "Current Git commit: " + report["current_commit"], "",
        f"- Remote subscriptions: {c['legacy_remote']} → {c['current_remote']}",
        f"- Local rules: {c['legacy_local']} → {c['current_local']}",
        f"- Generated groups: {c['current_generated_groups']}",
        f"- Current enabled inputs: {c['current_enabled_inputs']}", "",
        "## Historical subscription execution order", "",
        " → ".join(report["order_before"]), "",
        "## Current subscription execution order", "",
        " → ".join(report["order_after"]), "",
        "## Current emitted match types", "",
    ]
    lines += [f"- {k}: {v}" for k, v in report["current_rule_types"].items()]
    lines += [
        "", "## Verified local rule differences", "",
        f"- Added: {len(diff['added'])}",
        f"- Removed: {len(diff['removed'])}",
        f"- Policy or no-resolve changes: {len(diff['policy_or_no_resolve_conflicts'])}",
        f"- Historical/current local IP rules: {diff['ip_rules_before']}/{diff['ip_rules_after']}",
        f"- Historical/current local no-resolve: {diff['no_resolve_before']}/{diff['no_resolve_after']}", "",
        "## Explicit source URL additions and removals", "",
    ]
    for label, urls in report["source_changes"].items():
        lines.append(f"- {label} ({len(urls)}):")
        lines.extend("  - " + url for url in urls)
    lines += ["", "## Provenance limitation", "",
              "**HISTORICAL_CONTENT_UNAVAILABLE** for upstream rule-list bodies at the",
              "historic observation time. Remote per-rule additions, deletions,",
              "no-resolve differences and cross-policy conflicts are intentionally",
              "not inferred from modern upstream URLs.", "",
              "## Unresolved questions", ""]
    lines.extend("- " + q for q in report["known_risks"])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    result = make_report(args.root)
    markdown = render_markdown(result)
    if args.markdown_out:
        args.markdown_out.write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")
    if args.json_out:
        args.json_out.write_text(
            json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
