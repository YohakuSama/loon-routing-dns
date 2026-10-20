#!/usr/bin/env python3
"""Read-only upstream candidate review. Never writes into the repository.

Normalize trusted-format upstream sources, make reproducible candidates and
audit ALL changes against the pinned production rules. Neither a candidate nor
a green CI authorizes automatic publication.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left
from collections import Counter, defaultdict
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import sys
from urllib import request
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from rule_engine import (normalize, fields, covers_domain, AD_SAFETY_ROOTS,
                         SHARED_PLATFORM_ROOTS, is_covered)

MAX_SOURCE = 30_000_000
UPSTREAMS = {
    ("blackmatrix7", "ios_rule_script"),
    ("v2fly", "domain-list-community"),
    ("felixonmars", "dnsmasq-china-list"),
}
FORMAT_NAMES = {"loon", "domainset", "v2fly", "dnsmasq"}
DIRECT_GROUPS = {"ChinaDirect", "DomesticCore", "SteamCN", "AppleOTA"}
HIGH_RISK_KINDS = {"DOMAIN-KEYWORD", "IP-CIDR", "IP-CIDR6", "IP-ASN", "USER-AGENT"}
HOST = re.compile(r"^[a-z0-9.-]+$", re.I)
# Conservative guards, NOT a substitute for a current Public Suffix List.
# Unknown two-level public suffixes remain subject to manual review.
COMMON_SECOND_LEVEL = {"co", "com", "net", "org", "gov", "ac", "edu"}
RESERVED_ROOTS = {"localhost", "local", "internal", "test", "invalid", "example"}
# Multi-tenant parent domains can represent unrelated customers; proposals for
# their entire suffix are rejected, while subdomains remain reviewable.
MULTITENANT_ROOTS = set(SHARED_PLATFORM_ROOTS) | {
    "appspot.com", "blogspot.com", "github.io", "pages.dev", "workers.dev",
    "vercel.app", "netlify.app", "herokuapp.com", "azurewebsites.net"
}
MAX_RULE_LENGTH = 256


def _validate_matcher(rule: str) -> str:
    """Reject obviously unsafe matchers before they enter a candidate preview."""
    kind, value = fields(rule)
    if len(rule) > MAX_RULE_LENGTH:
        raise ValueError("oversized matcher")
    if kind in {"DOMAIN", "DOMAIN-SUFFIX"}:
        parts = value.split(".")
        if (len(parts) < 2 or not HOST.fullmatch(value)
                or any(not x or len(x) > 63 or x.startswith("-")
                       or x.endswith("-") for x in parts)
                or parts[-1] in RESERVED_ROOTS):
            raise ValueError("invalid or private/reserved domain matcher")
        if kind == "DOMAIN-SUFFIX" and (
            (len(parts) == 2 and len(parts[-1]) == 2
             and parts[0] in COMMON_SECOND_LEVEL) or value in MULTITENANT_ROOTS):
            raise ValueError("public-suffix or multi-tenant scope blocks unrelated domains")
    elif kind == "DOMAIN-KEYWORD":
        if len(value) < 4 or "*" in value or value in {"http", "https", "cdn", "api"}:
            raise ValueError("generic/unbounded keyword")
    elif kind in {"IP-CIDR", "IP-CIDR6"}:
        net = ipaddress.ip_network(value)
        if net.prefixlen < (8 if net.version == 4 else 24):
            raise ValueError("IP match is excessively broad")
    return rule


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(text: str) -> str:
    rule = normalize(text)
    if rule is None:
        raise ValueError("empty or comment rule")
    return rule


def source_line(source: dict, line: str) -> str | None:
    """Parse only supported inputs. Never silently reinterpret regex or include."""
    raw = line.strip().lstrip("\ufeff")
    if not raw or raw.startswith(("#", ";", "//")):
        return None
    fmt = source["format"]
    if fmt == "loon":
        if raw.upper().startswith("DOMAIN-SET,"):
            raise ValueError("unsupported DOMAIN-SET matcher")
        # Raw Loon rule source (not a Loon config with a third policy column).
        return _validate_matcher(canonical(raw))
    if fmt == "domainset":
        if raw.startswith("+."):
            raw = raw[2:]
        elif raw.startswith("."):
            # Strip exactly one documented domain-set prefix; do not hide
            # malformed inputs such as '..example.org' by lstrip().
            raw = raw[1:]
        if "," in raw or " " in raw or not HOST.fullmatch(raw):
            raise ValueError("unrecognized domain set entry")
        return _validate_matcher(canonical("DOMAIN-SUFFIX," + raw))
    if fmt == "v2fly":
        parts = raw.split()
        if len(parts) > 2 or not parts:
            raise ValueError("unexpected v2fly tokens")
        if len(parts) == 2:
            if not parts[1].startswith("@"):
                raise ValueError("unexpected v2fly attribute")
            attrs = parts[1][1:].lower().split(",")
            if any(x in source.get("skip_attrs", []) for x in attrs):
                return None
        match = parts[0]
        if match.startswith("include:") or match.startswith("regexp:"):
            raise ValueError("v2fly include/regexp requires explicit review")
        if match.startswith("full:"):
            return _validate_matcher(canonical("DOMAIN," + match[5:]))
        if match.startswith("domain:"):
            return _validate_matcher(canonical("DOMAIN-SUFFIX," + match[7:]))
        if match.startswith("keyword:"):
            return _validate_matcher(canonical("DOMAIN-KEYWORD," + match[8:]))
        if ":" in match:
            raise ValueError("unknown v2fly matcher")
        return _validate_matcher(canonical("DOMAIN-SUFFIX," + match))
    if fmt == "dnsmasq":
        m = re.fullmatch(r"(?:server|address)=/([^/]+)/[^/\s]+", raw)
        if not m:
            raise ValueError("unsupported dnsmasq directive")
        return _validate_matcher(canonical("DOMAIN-SUFFIX," + m.group(1)))
    raise ValueError("unknown source format")


def parse_source(source: dict, blob: bytes) -> tuple[set[str], dict]:
    if source.get("format") not in FORMAT_NAMES:
        raise ValueError("unknown format")
    if not blob or len(blob) > MAX_SOURCE:
        raise ValueError("empty or oversized input")
    text = blob.decode("utf-8-sig")
    result: set[str] = set()
    issues: list[dict] = []
    invalid = 0
    for number, raw in enumerate(text.splitlines(), 1):
        try:
            rule = source_line(source, raw)
            if rule:
                result.add(rule)
        except (ValueError, TypeError) as exc:
            invalid += 1
            if len(issues) < 15:
                issues.append({"line": number, "reason": str(exc), "snippet": raw[:120]})
    minimum = int(source.get("min_rules", 1))
    return result, {"rules": len(result), "invalid_count": invalid,
                    "invalid_samples": issues,
                    "minimum_satisfied": len(result) >= minimum,
                    "source_duplicates": max(0, sum(1 for x in text.splitlines()
                        if x.strip() and not x.lstrip().startswith(("#", ";", "//"))) - invalid - len(result))}


def _local_path(root: Path, rel: str) -> Path:
    if not rel.startswith("rules/custom/"):
        raise ValueError("only declared local custom rule paths are supported")
    p = (root / rel).resolve()
    if not p.is_relative_to(root.resolve()) or not p.is_file():
        raise ValueError("invalid local rule source")
    return p


def fetch_source(source: dict, root: Path = ROOT) -> bytes:
    if source.get("url"):
        parsed = urlsplit(source["url"])
        pieces = parsed.path.strip("/").split("/")
        if (parsed.scheme != "https" or parsed.hostname != "raw.githubusercontent.com"
                or len(pieces) < 4 or tuple(pieces[:2]) not in UPSTREAMS
                or parsed.username or parsed.password or parsed.query or parsed.fragment):
            raise ValueError("untrusted upstream URL")
        req = request.Request(source["url"], headers={"User-Agent": "LoonKit-Review/2"})
        with request.urlopen(req, timeout=25) as response:
            if urlsplit(response.geturl()).hostname != "raw.githubusercontent.com":
                raise ValueError("unexpected upstream redirect")
            blob = response.read(MAX_SOURCE + 1)
        if not blob or len(blob) > MAX_SOURCE:
            raise ValueError("upstream source empty or oversized")
        return blob
    return _local_path(root, source["path"]).read_bytes()


def _parents(domain: str):
    p = domain.split(".")
    for i in range(len(p)):
        yield ".".join(p[i:])


def _same_policy_reduce(rules: set[str]) -> tuple[set[str], int]:
    """Only remove redundant exact domains covered by a suffix IN SAME group.

    Never auto-coalesce CIDR ranges, rewrite suffixes, or remove keywords.
    """
    suffixes = {fields(r)[1] for r in rules if r.startswith("DOMAIN-SUFFIX,")}
    kept = {r for r in rules if not (r.startswith("DOMAIN,") and
        any(x in suffixes for x in _parents(fields(r)[1])))}
    return kept, len(rules) - len(kept)


def _overlap_index(published: dict[str, set[str]]):
    # Sorted domain keys allow O(log n) lookup of a child under a new suffix.
    lookup: dict[str, set[str]] = defaultdict(set)
    for group, rules in published.items():
        for rule in rules:
            kind, value = fields(rule)
            if kind in {"DOMAIN", "DOMAIN-SUFFIX"}:
                lookup[value].add((group, kind))
    # Reverse labels so all child names of a suffix are contiguous.
    return lookup, sorted(".".join(reversed(host.split("."))) for host in lookup)


def _semantic_expansion(rule: str, group: str, baseline: dict[str, set[str]],
                        lookup: dict[str, set[str]], sorted_domains: list[str]):
    kind, value = fields(rule)
    if kind not in {"DOMAIN", "DOMAIN-SUFFIX"}:
        return []
    risks = set()
    for p in _parents(value):
        for other, match_kind in lookup.get(p, ()):
            # An exact DOMAIN,parent.example does not match its children.
            if other != group and (p == value or match_kind == "DOMAIN-SUFFIX"):
                risks.add(other)
    if kind == "DOMAIN-SUFFIX":
        prefix = ".".join(reversed(value.split("."))) + "."
        i = bisect_left(sorted_domains, prefix)
        while i < len(sorted_domains) and sorted_domains[i].startswith(prefix):
            original_host = ".".join(reversed(sorted_domains[i].split(".")))
            risks.update(g for g, _ in lookup[original_host] if g != group)
            i += 1
    return sorted(risks)


def _ip_overlap_index(published: dict[str, set[str]]) -> dict:
    """Index IPv4/IPv6 CIDRs for precise cross-policy overlap analysis."""
    index = {4: {"prefix": defaultdict(set), "starts": []},
             6: {"prefix": defaultdict(set), "starts": []}}
    for group, rules in published.items():
        for rule in rules:
            kind, value = fields(rule)
            if kind not in {"IP-CIDR", "IP-CIDR6"}:
                continue
            net = ipaddress.ip_network(value)
            idx = index[net.version]
            start = int(net.network_address)
            stop = int(net.broadcast_address)
            idx["prefix"][(net.prefixlen, start)].add(group)
            idx["starts"].append((start, stop, group))
    for family in index.values():
        family["starts"].sort()
    return index


def _ip_collisions(rule: str, group: str, index: dict) -> list[str]:
    kind, value = fields(rule)
    if kind not in {"IP-CIDR", "IP-CIDR6"}:
        return []
    net = ipaddress.ip_network(value)
    bits = net.max_prefixlen
    start, end = int(net.network_address), int(net.broadcast_address)
    ix = index[net.version]
    groups = set()
    for prefix in range(net.prefixlen + 1):
        address = start if prefix == bits else (start >> (bits-prefix)) << (bits-prefix)
        groups.update(ix["prefix"].get((prefix, address), ()))
    entries = ix["starts"]
    i = bisect_left(entries, (start, -1, ""))
    while i < len(entries) and entries[i][0] <= end:
        groups.add(entries[i][2])
        i += 1
    return sorted(groups - {group})


def _domain_risk(rule: str, group: str, protected: tuple[str, ...]) -> list[str]:
    """Critical domains and shared hosts must never be auto-blocked or routed DIRECT."""
    kind, _ = fields(rule)
    tags = []
    if kind == "DOMAIN-SUFFIX" and fields(rule)[1] in SHARED_PLATFORM_ROOTS:
        tags.append("SHARED_INFRASTRUCTURE_SUFFIX_REVIEW")
    if group == "AdBlock":
        tags.append("ADBLOCK_NEW_RULE_REQUIRES_EVIDENCE")
        if kind not in {"DOMAIN", "DOMAIN-SUFFIX"}:
            tags.append("ADBLOCK_UNSAFE_MATCHER")
        if any(covers_domain(rule, host) for host in AD_SAFETY_ROOTS):
            tags.append("ADBLOCK_CRITICAL_SERVICE_OVERLAP")
        if any(covers_domain(rule, host) for host in SHARED_PLATFORM_ROOTS):
            tags.append("ADBLOCK_SHARED_HOSTING_OVERLAP")
    if group in DIRECT_GROUPS and any(covers_domain(rule, host) for host in protected):
        tags.append("DIRECT_PROTECTED_DOMAIN")
    return tags


def build_report(root: Path = ROOT, fetcher=None) -> tuple[dict, dict[str, bytes], dict]:
    """Return report, exact fetched snapshots, and full change record (no writes)."""
    root = Path(root)
    sources = json.loads((root / "rules/sources.json").read_text(encoding="utf-8"))["sources"]
    manifest = json.loads((root / "build/engine_manifest.json").read_text(encoding="utf-8"))
    active = manifest["active_groups"]
    if len(sources) != 87 or len(active) != 26:
        raise ValueError("source catalog or active policy set unexpectedly changed")
    groups: dict[str, set[str]] = {g: set() for g in active}
    provenance = defaultdict(set)
    snapshots: dict[str, bytes] = {}
    records = []
    fetcher = fetcher or (lambda item: fetch_source(item, root))
    invalid_groups = set()
    unique_ids = set()
    for source in sources:
        sid = source["id"]
        if sid in unique_ids or not re.fullmatch(r"[a-z0-9-]+", sid):
            raise ValueError("invalid or repeated source id")
        unique_ids.add(sid)
        row = {"id": sid, "group": source["group"], "format": source["format"],
               "enabled": bool(source.get("enabled", False)), "url": source.get("url")}
        try:
            data = fetcher(source)
            rules, parse = parse_source(source, data)
            row.update(parse)
            row.update(status="PARSED_FOR_REVIEW", sha256=digest(data), bytes=len(data))
            snapshots[sid] = data
            if parse["invalid_count"] or not parse["minimum_satisfied"]:
                row["status"] = "INCOMPLETE_NEEDS_MANUAL_REVIEW"
                invalid_groups.add(source["group"])
            if source["group"] in groups and row["enabled"]:
                groups[source["group"]].update(rules)
                for rule in rules:
                    provenance[(source["group"], rule)].add(sid)
        except (OSError, ValueError, UnicodeError) as exc:
            row.update(status="UNAVAILABLE_OR_INVALID", error=str(exc)[:150])
            invalid_groups.add(source["group"])
        records.append(row)

    baseline: dict[str, set[str]] = {}
    candidate: dict[str, set[str]] = {}
    for group in active:
        name = "AnimeCrazy" if group == "動畫瘋" else group
        path = root / "rules/releases/vNext-RC2" / (name + ".list")
        baseline[group] = {canonical(x) for x in path.read_text(encoding="utf-8").splitlines()
                           if x.strip() and not x.lstrip().startswith(("#", ";", "//"))}
        candidate[group], _ = _same_policy_reduce(groups[group])
    index, domains = _overlap_index(baseline)
    proposal_index, proposal_domains = _overlap_index(candidate)
    baseline_ip_index = _ip_overlap_index(baseline)
    proposal_ip_index = _ip_overlap_index(candidate)
    guarded = json.loads((root/"rules/routing_guardrails.json").read_text(encoding="utf-8"))["protected_proxy_domains"]
    group_report = {}
    deltas = {}
    full_risks = {}
    cross_owner = defaultdict(set)
    for group, rules in candidate.items():
        for rule in rules:
            cross_owner[rule].add(group)
    for group in active:
        after, before = candidate[group], baseline[group]
        added = sorted(after-before)
        removed = sorted(before-after)
        risk = Counter()
        risk_examples = []
        detailed_risks = {"additions": [], "removals": []}
        for rule in added:
            kind, _ = fields(rule)
            tags = []
            if kind in HIGH_RISK_KINDS:
                tags.append("BROAD_KEYWORD_OR_IP_REVIEW")
            if kind == "DOMAIN-SUFFIX":
                # New suffixes can unexpectedly route every subdomain.
                tags.append("NEW_SUFFIX_SCOPE_REVIEW")
            tags.extend(_domain_risk(rule, group, tuple(guarded)))
            if len(cross_owner[rule]) > 1:
                tags.append("CROSS_POLICY_EXACT_CONFLICT")
            other_groups = set(_semantic_expansion(rule, group, baseline, index, domains))
            candidate_groups = _semantic_expansion(rule, group, candidate,
                                                   proposal_index, proposal_domains)
            if candidate_groups:
                tags.append("CROSS_POLICY_CANDIDATE_DOMAIN_COVERAGE")
                other_groups.update(candidate_groups)
            ip_groups = _ip_collisions(rule, group, baseline_ip_index)
            ip_candidate_groups = _ip_collisions(rule, group, proposal_ip_index)
            if ip_groups or ip_candidate_groups:
                tags.append("CROSS_POLICY_IP_RANGE_OVERLAP")
                other_groups.update(ip_groups + ip_candidate_groups)
            if other_groups.intersection(set(_semantic_expansion(rule, group, baseline, index, domains))):
                tags.append("CROSS_POLICY_DOMAIN_COVERAGE")
            other_groups = sorted(other_groups)
            # Every added matcher remains quarantined, even without special risk flags.
            detailed_risks["additions"].append({
                "rule": rule,
                "reasons": sorted(set(tags)) if tags else ["NEW_RULE_REQUIRES_APPROVAL"],
                "source_ids": sorted(provenance.get((group, rule), ())),
                "other_groups": other_groups
            })
            for t in tags:
                risk[t] += 1
            if tags and len(risk_examples) < 30:
                risk_examples.append({"rule": rule, "reasons": tags, "other_groups": other_groups[:8]})
        # Removals are never silently applied, including upstream deletions.
        if removed:
            risk["REMOVALS_REQUIRE_APPROVAL"] = len(removed)
            detailed_risks["removals"] = [
                {"rule": rule, "reasons": ["UPSTREAM_REMOVAL_REQUIRES_APPROVAL"]}
                for rule in removed
            ]
        volume_shift = abs(len(after) - len(before)) / max(len(before), 1)
        if volume_shift > 0.20:
            risk["LARGE_SOURCE_VOLUME_DRIFT_REVIEW"] = 1
        full_risks[group] = detailed_risks
        group_report[group] = {
            "status": "INCOMPLETE_SOURCE_DATA" if group in invalid_groups else "REVIEW_ONLY",
            "publication_gate": "BLOCKED_UNTIL_EXPLICIT_APPROVAL",
            "emitted_preview": "UNCHANGED_PINNED_BASELINE",
            "change_review_required": bool(added or removed),
            "published_count": len(before), "candidate_count": len(after),
            "volume_change_percent": round(volume_shift * 100, 2),
            "added": len(added), "removed": len(removed),
            "same_policy_covered_domains": len(groups[group]) - len(after),
            "risk_categories": dict(sorted(risk.items())),
            "risk_examples": risk_examples,
            "added_sample": added[:20], "removed_sample": removed[:20],
        }
        deltas[group] = {"added": added, "removed": removed}
    full = json.dumps(deltas, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    report = {
        "schema_version": 1, "status": "REVIEW_ONLY_NEVER_PUBLISH",
        "source_count": len(sources), "active_groups": len(active),
        "snapshot_count": len(snapshots),
        "incomplete_sources": sum(x["status"] != "PARSED_FOR_REVIEW" for x in records),
        "incomplete_groups": sorted(invalid_groups & set(active)),
        "full_delta_sha256": digest(full), "sources": records,
        "groups": group_report,
        "publication_allowed": False,
        "preview_sha256_unchanged": True,
        "safety": [
            "Candidate .list files contain ONLY the unchanged pinned baseline, never unapproved upstream matchers.",
            "Additions and removals are recorded as data, not automatically incorporated.",
            "Candidates never replace pinned production URLs or locked inputs.",
            "Historical merged rule provenance is not fully reconstructable.",
            "Unknown directives and v2fly includes/regex are reported, not guessed.",
            "IP/keyword expansions, cross-policy coverage and any removals require review.",
            "No automatic tightening, widening, rule publication or source lock updates.",
        ],
    }
    return report, snapshots, {"deltas": deltas, "full_risk_audit": full_risks,
                               "rules": baseline,
                               "unapproved_proposals": candidate,
                               "source_ids_by_rule": provenance}


def write_review(output: Path, report: dict, snapshots: dict[str, bytes], data: dict,
                 root: Path = ROOT):
    folder = output.resolve()
    repo = root.resolve()
    if folder == repo or folder.is_relative_to(repo) or repo.is_relative_to(folder):
        raise ValueError("review must write outside repository")
    if output.is_symlink() or (output.exists() and any(output.iterdir())):
        raise ValueError("output directory must be empty and not a symlink")
    folder.mkdir(parents=True, exist_ok=True)
    (folder/"UPSTREAM_REVIEW.json").write_text(json.dumps(report, ensure_ascii=False,
        sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (folder/"FULL_DIFF.json").write_text(json.dumps(data["deltas"], ensure_ascii=False,
        sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (folder/"FULL_RISK_AUDIT.json").write_text(json.dumps(data["full_risk_audit"],
        ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    for sid, blob in sorted(snapshots.items()):
        dest = folder/"snapshots"/(sid+".txt")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)
    for group, rules in sorted(data["rules"].items()):
        dest = folder/"candidate"/(("AnimeCrazy" if group == "動畫瘋" else group)+".list")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("# UNCHANGED PINNED BASELINE - NOT A RULE UPDATE\n" +
            "\n".join(sorted(rules)) + "\n", encoding="utf-8")
    provenance = {g+"|"+r: sorted(ids) for (g, r), ids in sorted(
        data["source_ids_by_rule"].items()) if r in data["unapproved_proposals"].get(g, ())}
    (folder/"CANDIDATE_SOURCES.json").write_text(json.dumps(provenance, ensure_ascii=False,
        sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True,
                   help="empty directory outside checkout (e.g. $RUNNER_TEMP/upstream-review)")
    args = p.parse_args()
    result, snapshots, data = build_report()
    write_review(args.output, result, snapshots, data)
    print(json.dumps({"status": result["status"], "sources": result["source_count"],
        "incomplete_sources": result["incomplete_sources"],
        "incomplete_groups": result["incomplete_groups"],
        "candidate_delta_sha256": result["full_delta_sha256"]},
        sort_keys=True, ensure_ascii=False))
