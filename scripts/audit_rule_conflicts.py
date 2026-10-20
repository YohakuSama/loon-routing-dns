#!/usr/bin/env python3
"""Stage-02 immutable-snapshot Loon audit. Stdlib only; never downloads sources.

Usage: python3 scripts/audit_rule_conflicts.py [--output DIR] [--check]
Outputs are deterministic and all input files are read-only.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import ipaddress
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = Path("audits/phase-02")
SOURCE_COMMIT = "f19421933d2177f95e7537f1208d990b3094f1f4"
TYPES = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
         "IP-CIDR", "IP-CIDR6", "IP-ASN", "USER-AGENT"}
IP_TYPES = {"IP-CIDR", "IP-CIDR6", "IP-ASN"}
DOMAIN_TYPES = {"DOMAIN", "DOMAIN-SUFFIX"}
KNOWN_AD = {"admob.com", "doubleclick.com", "app-measurement.com", "ads-twitter.com"}
SHARED_HINTS = ("cloudfront.net", "cloudflare.com", "amazonaws.com",
                "akamai", "fastly.net", "edgekey.net", "azureedge.net")
INTERNATIONAL = {"AI", "Google", "Microsoft", "Apple", "YouTube", "Netflix", "Disney",
                 "PrimeVideo", "Spotify", "TikTok", "Telegram", "Facebook",
                 "Whatsapp", "Instagram", "Discord", "Reddit", "Steam", "Paypal"}
DUMPS = dict(ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def encoded(value):
    return json.dumps(value, **DUMPS)


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False,
                               sort_keys=True) + "\n", encoding="utf-8")


def validate_snapshot():
    manifest = read_json("baselines/current/manifest.json")
    index = read_json("baselines/current/rule-index.json")
    assert manifest["source_commit"] == index["source_commit"] == SOURCE_COMMIT
    for item in manifest["files"]:
        # Phase 01 snapshot hashes remain anchored to the archived publication,
        # even after the root production configs migrate to RC2.
        historical = {"LoonKit.lcf": "refactor/vnext/templates/LoonKit.legacy-seed.lcf",
                      "LoonKit.PrivacyDNS.lcf": "refactor/vnext/templates/LoonKit.PrivacyDNS.legacy-seed.lcf",
                      ".github/workflows/composite-rules.yml": "refactor/vnext/templates/phase01-composite-rules.yml"}
        data = (ROOT / historical.get(item["path"], item["path"])).read_bytes()
        assert hashlib.sha256(data).hexdigest() == item["sha256"], item["path"]
        assert len(data) == item["bytes"], item["path"]
    assert len(index["subscriptions"]) == manifest["remote_subscription_count"], "subscription count"
    assert len(index["enabled_sources"]) == manifest["enabled_input_count"], "source count"
    return manifest, index


def parse_rule(raw, policy, file, number, group):
    fields = [s.strip() for s in raw.split(",")]
    kind = fields[0].upper()
    if kind not in TYPES or not (2 <= len(fields) <= 3):
        raise ValueError(f"unsupported or malformed published rule {file}:{number}: {raw[:120]}")
    value = fields[1]
    flag = len(fields) == 3 and fields[2].lower() == "no-resolve"
    if len(fields) == 3 and not flag:
        raise ValueError(f"unknown rule flag {file}:{number}")
    if flag and kind not in IP_TYPES:
        raise ValueError(f"unexpected flag {file}:{number}")
    if kind in DOMAIN_TYPES | {"DOMAIN-KEYWORD"}:
        value = value.lower().rstrip(".")
    if kind in {"IP-CIDR", "IP-CIDR6"}:
        net = ipaddress.ip_network(value, strict=False)
        if net.version != (6 if kind == "IP-CIDR6" else 4):
            raise ValueError(f"IP family mismatch {file}:{number}")
        value = str(net)
    if kind == "IP-ASN":
        value = value.upper().removeprefix("AS")
        if not value.isdigit():
            raise ValueError(f"invalid ASN {file}:{number}")
    return dict(rule_type=kind, rule_value=value, policy=policy, group=group,
                source_file=file, source_line=number, no_resolve=flag)


def scan_published(index):
    records, details = [], []
    for subscription in index["subscriptions"]:
        file = subscription["path"]
        expected_hash = subscription["sha256"]
        data = (ROOT / file).read_bytes()
        actual_hash = hashlib.sha256(data).hexdigest()
        if actual_hash != expected_hash:
            raise AssertionError(f"published blob changed: {file}")
        before = len(records)
        local_types = Counter()
        for number, raw in enumerate(data.decode("utf-8").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith(("#", "//", ";")):
                continue
            record = parse_rule(line, subscription["policy"], file, number,
                                subscription["group"])
            records.append(record)
            local_types[record["rule_type"]] += 1
        count = len(records) - before
        assert count == subscription["rule_count"], (file, count, subscription["rule_count"])
        assert dict(local_types) == subscription["rule_types"], (file, local_types)
        details.append(dict(source_file=file, group=subscription["group"],
                            policy=subscription["policy"], rules=count,
                            sha256=actual_hash, rule_types=dict(sorted(local_types.items()))))
    assert len(details) == 34
    return records, details


def rule_key(r):
    return (r["rule_type"], r["rule_value"], r["no_resolve"])


def locator(r):
    return {k: r[k] for k in ("rule_type", "rule_value", "policy", "group",
                             "source_file", "source_line", "no_resolve")}


def pair(a, b, kind):
    return {"category": kind, "left": locator(a), "right": locator(b),
            "same_policy": a["policy"] == b["policy"]}


def overlap_analysis(records):
    # Hash index: identical match conditions are never confused with ancestry.
    seen = defaultdict(list)
    for r in records:
        seen[rule_key(r)].append(r)
    exact_repeated = []
    cross_exact = []
    for key in sorted(seen):
        owners = seen[key]
        if len(owners) > 1:
            for r in owners[1:]:
                p = pair(owners[0], r, "EXACT")
                exact_repeated.append(p)
                if not p["same_policy"]:
                    cross_exact.append(p)

    # Also identify match-equivalent conditions with different no-resolve flags.
    same_condition = defaultdict(list)
    for r in records:
        same_condition[(r["rule_type"], r["rule_value"])].append(r)
    flag_variants = []
    for key in sorted(same_condition):
        owners = same_condition[key]
        if len({r["no_resolve"] for r in owners}) > 1:
            flag_variants.append(dict(condition=list(key), owners=[locator(r) for r in owners]))

    suffix = defaultdict(list)
    for r in records:
        if r["rule_type"] == "DOMAIN-SUFFIX":
            suffix[r["rule_value"]].append(r)
    ancestor = []
    for r in records:
        if r["rule_type"] not in DOMAIN_TYPES:
            continue
        parts = r["rule_value"].split(".")
        # DOMAIN-SUFFIX covers an exact DOMAIN of the same value, not vice versa.
        if r["rule_type"] == "DOMAIN":
            for other in suffix.get(r["rule_value"], ()):
                if other["policy"] != r["policy"]:
                    ancestor.append(pair(other, r, "EXACT_DOMAIN_COVERED_BY_SUFFIX"))
        for pos in range(1, len(parts)):
            for other in suffix.get(".".join(parts[pos:]), ()):
                if other["policy"] != r["policy"]:
                    ancestor.append(pair(other, r, "DOMAIN_SUFFIX_ANCESTRY"))

    # Keyword match is substring semantics, not substring==domain suffix equality.
    keywords = [r for r in records if r["rule_type"] == "DOMAIN-KEYWORD"]
    keywords.sort(key=lambda r: (r["rule_value"], r["source_file"], r["source_line"]))
    keyword_conflicts = []
    for r in records:
        if r["rule_type"] not in DOMAIN_TYPES:
            continue
        for kw in keywords:
            if kw["policy"] != r["policy"] and kw["rule_value"] in r["rule_value"]:
                keyword_conflicts.append(pair(kw, r, "KEYWORD_SUBSTRING_POSSIBLE"))

    # Prefix hash ancestry: O(sum(network prefix lengths)), not O(N**2).
    networks = {4: defaultdict(list), 6: defaultdict(list)}
    for r in records:
        if r["rule_type"] in {"IP-CIDR", "IP-CIDR6"}:
            net = ipaddress.ip_network(r["rule_value"])
            networks[net.version][net].append(r)
    network_conflicts = []
    for version in (4, 6):
        for net in sorted(networks[version], key=lambda n: (int(n.network_address), n.prefixlen)):
            node = net
            while node.prefixlen > 0:
                node = node.supernet()
                for upstream in networks[version].get(node, ()):
                    for child in networks[version][net]:
                        if child["policy"] != upstream["policy"]:
                            network_conflicts.append(pair(upstream, child, "IP_PREFIX_ANCESTRY"))
            local = networks[version][net]
            for i, first in enumerate(local):
                for second in local[i + 1:]:
                    if first["policy"] != second["policy"]:
                        network_conflicts.append(pair(first, second, "IP_SAME_NETWORK"))
    return {
        "published_exact_duplicates": exact_repeated,
        "published_cross_policy_exact": cross_exact,
        "same_match_different_flags": flag_variants,
        "domain_suffix_cross_policy_coverage": ancestor,
        "keyword_cross_policy_possible": keyword_conflicts,
        "ip_cross_policy_overlap": network_conflicts,
        "asn_to_prefix_status": "ASN_PREFIX_SNAPSHOT_UNAVAILABLE"
    }


def source_inventory(index, records):
    catalog = read_json("rules/sources.json")
    build = read_json("rules/generated/audit.json")
    legacy = read_json("baselines/legacy/sources.json")
    verified = read_json("rules/verified-routing-baseline.json")
    historical_urls = {e["url"] for e in legacy["remote_rules"]}
    assert len(verified["remote_rules"]) == len(legacy["remote_rules"]) == 28
    assert len(catalog["sources"]) == len(index["enabled_sources"]) == 87
    stats = {s["id"]: s for s in build.get("sources", [])}
    assert len(stats) == 87, "staged provenance summary incomplete"
    per_group = Counter(r["group"] for r in records)
    group_source_count = Counter(x["group"] for x in catalog["sources"] if x["enabled"])
    # CURRENT_UPSTREAM_REFERENCE: upstream repository LICENSE files verified separately.
    # This is not a per-entry legal conclusion and does not substitute for source provenance.
    licenses = {
        "blackmatrix7": ("GPL-2.0 (repository-level)",
                         "https://github.com/blackmatrix7/ios_rule_script/blob/master/LICENSE"),
        "v2fly": ("MIT (repository-level)",
                  "https://github.com/v2fly/domain-list-community/blob/master/LICENSE"),
        "felixonmars": ("WTFPL-2 (repository-level)",
                         "https://github.com/felixonmars/dnsmasq-china-list/blob/master/LICENSE"),
    }
    lines = []
    for s in catalog["sources"]:
        if not s["enabled"]:
            continue
        stat = stats.get(s["id"], {})
        url = s.get("url")
        org = url.split("/")[3] if url and "raw.githubusercontent.com/" in url else "YohakuSama"
        group = s["group"]
        historical = url in historical_urls if url else "UNVERIFIED_LOCAL_HISTORY"
        parsed = stat.get("parsed")
        duplicates = stat.get("duplicate_within_group")
        if not isinstance(parsed, int) or not isinstance(duplicates, int) or not 0 <= duplicates <= parsed:
            raise ValueError(f"invalid frozen source stats for {s['id']}")
        stage_unique = parsed - duplicates
        ratio = round(duplicates / parsed, 6) if parsed else 0.0
        if stage_unique == 0:
            decision, reason = "MERGE", "No incremental matcher in frozen staged ingestion; candidate for review, not safe-to-delete proof"
        elif historical is True:
            decision, reason = "KEEP", "Legacy subscription URL and positive staged contribution; business impact still needs verification"
        else:
            decision, reason = "INVESTIGATE", "Positive staged contribution; exact published output provenance unavailable"
        lines.append({
            "id": s["id"], "url": url, "path": s.get("path"), "maintainer_or_org": org,
            "original_license": (licenses[org][0] if org in licenses
                                 else "LOCAL_SELF_MAINTAINED_LICENSE_UNVERIFIED"),
            "license_documentation_url": licenses[org][1] if org in licenses else None,
            "license_evidence": "CURRENT_UPSTREAM_REFERENCE_NOT_RELEASE_PINNED",
            "original_rule_item_license": "UNKNOWN_THIRD_PARTY_DERIVATION",
            "format": s["format"], "group": group, "policy": s["policy"],
            "role": s.get("role"), "is_historical_remote_subscription": historical,
            "is_added_relative_to_historical_remotes": not historical if url else "UNKNOWN",
            "input_count_reported": parsed,
            "reported_intra_group_duplicates": duplicates,
            "stage_unique_added_before_pruning": stage_unique,
            "stage_duplicate_ratio": ratio,
            "stage_normalized_sha256": stat.get("normalized_sha256"),
            "stage_updated_header": stat.get("upstream_updated"),
            "same_group_source_count": group_source_count[group],
            "contribution_evidence_scope": "FROZEN_GENERATOR_AGGREGATE_PRE_PRUNING",
            "potential_zero_incremental_ingest": stage_unique == 0,
            "published_group_total": per_group.get(group, 0),
            "published_individual_contribution": None,
            "source_provenance": "SOURCE_PROVENANCE_INCOMPLETE",
            "shared_cdn_possible": (group in INTERNATIONAL or group == "AdBlock"),
            "high_risk_rules_verified_per_source": None,
            "substantial_duplication_per_source": (
                "STAGED_RATIO_GE_80_PERCENT" if ratio >= 0.8 else "STAGED_RATIO_LT_80_PERCENT"),
            "evidence_quality": "CATALOG_AND_STAGED_AGGREGATE_ONLY",
            "recommendation": decision,
            "recommendation_reason": reason,
        })
    assert len(lines) == 87
    assert sum(x["reported_intra_group_duplicates"] for x in lines) == build["duplicates_removed_within_group"]
    return {"evidence_scope": "PUBLISHED_SNAPSHOT",
            "historical_remote_contents": "HISTORICAL_CONTENT_UNAVAILABLE",
            "source_provenance": "SOURCE_PROVENANCE_INCOMPLETE",
            "source_recommendation_counts": dict(sorted(Counter(x["recommendation"] for x in lines).items())),
            "staged_total_parsed": sum(x["input_count_reported"] for x in lines),
            "staged_total_first_owner_credit": sum(x["stage_unique_added_before_pruning"] for x in lines),
            "staged_zero_incremental_sources": [x["id"] for x in lines if x["potential_zero_incremental_ingest"]],
            "sources": lines, "inactive_candidates": catalog.get("candidates", []),
            "prepublication": {k: build.get(k) for k in (
                "duplicates_removed_within_group", "cross_group_exact_pruned_count",
                "cross_group_different_policy_exact", "domain_suffix_ancestor_conflict_count",
                "quarantined_by_reason", "same_group_suffix_shadow_pruned",
                "cross_group_exact_pruned_samples", "cross_group_different_policy_samples")}}
            

def candidates(records, conflicts, inventory):
    missing = [locator(r) for r in records if r["rule_type"] in IP_TYPES and not r["no_resolve"]]
    direct = [r for r in records if r["policy"] == "DIRECT"]
    direct_keywords = [locator(r) for r in direct if r["rule_type"] == "DOMAIN-KEYWORD"]
    direct_wide_suffixes = [locator(r) for r in direct if r["rule_type"] == "DOMAIN-SUFFIX"
                            and r["rule_value"].count(".") == 0]
    direct_networks = Counter(r["rule_type"] for r in direct if r["rule_type"] in IP_TYPES)
    ad_candidates = [locator(r) for r in records
                     if r["group"] == "AdBlock" and
                     any(t == r["rule_value"] or r["rule_value"].endswith("." + t) for t in KNOWN_AD)]
    ad_control = {}
    for name in sorted(KNOWN_AD):
        ad_control[name] = [locator(r) for r in records
                            if r["rule_value"] == name and r["rule_type"] in DOMAIN_TYPES]
    risks = []
    def add(severity, category, r, trigger, effect, confidence="STATIC_CONFIRMED",
            runtime=True, recommendation="Manual review before changing rules"):
        n = len(risks) + 1
        risks.append({
            "risk_id": f"P02-{n:05d}", "severity": severity, "category": category,
            "rule": f'{r["rule_type"]},{r["rule_value"]}',
            "source_file": r["source_file"], "source_line": r["source_line"],
            "policy": r["policy"], "original_source": "SOURCE_PROVENANCE_INCOMPLETE",
            "affected_services": effect, "trigger_condition": trigger,
            "evidence": locator(r), "evidence_status": confidence,
            "evidence_confidence": "HIGH_FOR_STATIC_RULE_ONLY",
            "runtime_verification_required": runtime,
            "recommendation_phase": "03" if category.startswith("DIRECT") else "04",
            "recommendation": recommendation
        })
    for name in sorted(ad_control):
        for owner in ad_control[name]:
            if owner["group"] != "AdBlock":
                add("P1", "ADBLOCK_PLATFORM_OWNERSHIP", owner,
                    "Matching ad/tracker host falls under a platform rule; AdBlock is a later remote subscription",
                    name + ": advertising, tracking, measurement or related infrastructure",
                    recommendation="Review functional dependencies and source ownership; decide block/allow explicitly")
                if owner["policy"] == "DIRECT":
                    add("P1", "DIRECT_MEASUREMENT_INFRASTRUCTURE", owner,
                        "Domain is also covered by another service's suffix; local and remote precedence must be checked",
                        name + ": cross-region analytics and measurement",
                        recommendation="Validate priority and legitimate geographic business before any change")
    for r in records:
        if r["rule_type"] in IP_TYPES and not r["no_resolve"]:
            add("P1" if r["policy"] == "DIRECT" else "P2", "IP_NO_RESOLVE_MISSING",
                r, "Unmatched domain request reaches eligible IP/ASN rule",
                "Possible local name resolution; not proof of DNS leak",
                recommendation="Validate intended IP-only match; consider no-resolve after runtime tests")
        if r["policy"] == "DIRECT" and r["rule_type"] == "DOMAIN-KEYWORD":
            add("P2", "DIRECT_BROAD_KEYWORD", r,
                "Domain string contains keyword anywhere, regardless of registered-domain owner",
                "Potential unrelated international sites",
                recommendation="Review ownership and replace with explicit domain scope where justified")
        if r["policy"] == "DIRECT" and r["rule_type"] == "DOMAIN-SUFFIX" and "." not in r["rule_value"]:
            add("P1", "DIRECT_TOP_LEVEL_SUFFIX", r,
                "Any domain under this top-level suffix, including cross-border services",
                "All services under suffix; actual priority depends on Loon",
                recommendation="Review exceptions and routing priority; do not blindly delete")
    return {
        "missing_no_resolve": missing,
        "direct_keywords": direct_keywords,
        "direct_top_level_suffixes": direct_wide_suffixes,
        "direct_ip_rule_types": dict(sorted(direct_networks.items())),
        "adblock_anchors_present_in_adblock": ad_candidates,
        "adblock_anchor_ownership": ad_control,
        "published_cross_policy_exact": len(conflicts["published_cross_policy_exact"]),
        "prepublication_conflicts_unrecoverable": "SOURCE_PROVENANCE_INCOMPLETE",
        "runtime_dns_evidence": "RUNTIME_VERIFICATION_REQUIRED"
    }, risks


def markdown_reports(records, details, inventory, overlaps, risks, ip, output):
    counts = Counter(r["rule_type"] for r in records)
    sev = Counter(x["severity"] for x in risks)
    first = lambda n, arr: "\n".join(
        f'- `{x["source_file"]}:{x["source_line"]}` '
        f'`{x["rule_type"]},{x["rule_value"]}` → `{x["policy"]}`'
        for x in arr[:n]) or "- None found"
    index = [
        "# Phase 02 — frozen published snapshot audit",
        "", f"- Frozen source commit: `{SOURCE_COMMIT}`",
        "- Input: 34 indexed published .list subscriptions. Local GEOIP and FINAL reviewed separately.",
        f"- Published rules parsed: **{len(records):,}** across **{len(details)}** files.",
        "- All 87 enabled inputs inventoried, but exact post-filter source attribution is unavailable.",
        "- Historical remote bodies: `HISTORICAL_CONTENT_UNAVAILABLE`.",
        "- Runtime DNS packet captures: `RUNTIME_VERIFICATION_REQUIRED`.",
        "", "## Published matcher type totals", "",
        *[f"- {kind}: {value:,}" for kind, value in sorted(counts.items())],
        "", "## Risk register", "",
        *[f"- {k}: {sev[k]}" for k in ("P0", "P1", "P2", "P3")],
        "", "Full data: `data/normalized_rules.jsonl.gz`, other JSON datasets.",
        "Counts from the historical generator audit are INPUT-STAGE observations, not published errors.",
    ]
    docs = {
        "README.md": "\n".join(index),
        "SOURCE_AUDIT.md": "\n".join([
            "# Source audit", "", "87 catalog sources; all recorded in data/source_inventory.json.",
            f"Staged source recommendations: {encoded(inventory['source_recommendation_counts'])}",
            f"Staged parsed rows: {inventory['staged_total_parsed']:,}, first-owner matcher credit: {inventory['staged_total_first_owner_credit']:,}",
            f"Zero incremental sources in staged ingest: {len(inventory['staged_zero_incremental_sources'])}",
            "## Zero-incremental source MERGE review candidates (all)",
            *[f"- {x}" for x in inventory["staged_zero_incremental_sources"]],
            "This is frozen staged first-ingestion credit, NOT independently verified final published contribution.",
            "A zero count is order-dependent and does not prove a source can safely be removed.",
            "Staged per-source `parsed` counts are historical build-report claims, not retrievable raw inputs.",
            "No current upstream download was performed. Per-source final contribution cannot be reconstructed.",
            "Upstream repository-level licenses: blackmatrix7 GPL-2.0, v2fly MIT, felixonmars WTFPL-2.",
            "These CURRENT_UPSTREAM_REFERENCE license records do not prove original per-item rights.",
            "REMOVE_CANDIDATE requires independent provenance and business evidence.",
            "Frozen local sources have line-level nonexclusive matches in data/local_source_matches.json.",
            f"- Direct exact published condition matches: {sum(a['published_condition_matches'] for a in local_source_matches(records)['sources'])}.",
            f"- Additional same-group suffix coverage: {sum(a['same_group_suffix_covered'] for a in local_source_matches(records)['sources'])}.",
            "Local matches or coverage show surviving conditions but NOT which source deserves exclusive credit.",
            "Historical remotes are URL-level evidence only; their historical contents are unavailable.",
        ]),
        "DUPLICATE_AUDIT.md": "\n".join([
            "# Published duplicate audit", "",
            f"- Published exact repeated instances: {len(overlaps['published_exact_duplicates'])}.",
            f"- Published cross-policy exact instances: {len(overlaps['published_cross_policy_exact'])}.",
            f"- Equal conditions with different no-resolve status: {len(overlaps['same_match_different_flags'])}.",
            f"- Staged input in-group duplicates: {inventory['prepublication']['duplicates_removed_within_group']}.",
            f"- Staged cross-group exact pruned: {inventory['prepublication']['cross_group_exact_pruned_count']}.",
            "The staged counts do not represent published duplicates.",
        ]),
        "POLICY_CONFLICTS.md": "\n".join([
            "# Policy overlap audit", "",
            f"- Published cross-policy suffix ancestry pairs: {len(overlaps['domain_suffix_cross_policy_coverage'])}.",
            f"- Cross-policy keyword-substring candidate pairs: {len(overlaps['keyword_cross_policy_possible'])}.",
            f"- Cross-policy IP prefix overlaps: {len(overlaps['ip_cross_policy_overlap'])}.",
            "- DOMAIN and DOMAIN-SUFFIX are not identical matchers; suffix coverage respects label boundaries.",
            "- IP-ASN to CIDR cannot be mapped without a pinned ASN database.",
            "- Static overlaps do not establish which policy won on-device.",
            "- See data/policy_conflicts.json for every pair and both file locations.",
        ]),
        "CHINA_DIRECT_AUDIT.md": "\n".join([
            "# DIRECT risk audit", "",
            f"- Published DIRECT DOMAIN-KEYWORD entries: {len(ip['direct_keywords'])}.",
            f"- Published DIRECT top-level suffix entries: {len(ip['direct_top_level_suffixes'])}.",
            "All DIRECT CIDR, CIDR6, ASN examined for flags; see data/dns_risk_candidates.json.",
            "", "## DIRECT keywords (complete)", first(10000, ip["direct_keywords"]),
            "", "## Broad top-level suffixes (complete)", first(10000, ip["direct_top_level_suffixes"]),
            "", "Static classification is only a review candidate; service ownership and routing need verification.",
            "Previously quarantined browserleaks.com, whatismyip.com and keyword stripe are not presumed published.",
        ]),
        "ADBLOCK_AUDIT.md": "\n".join([
            "# AdBlock ownership and collateral-block risk", "",
            "AdvertisingLite is enabled; Advertising full is a disabled candidate, not a comparable input snapshot.",
            "Privacy/Hijacking may contribute supplemental domains, but per-source published output is untraceable.",
            "The generator only admits DOMAIN/DOMAIN-SUFFIX to AdBlock; keyword/IP exclusions alter coverage.",
            "Platform-first ownership means ad-related exact matches may be removed from AdBlock.",
            "The published anchor check confirms Google owns admob.com, doubleclick.com and",
            "app-measurement.com; Twitter owns ads-twitter.com; ChinaDirect has an exact",
            "app-measurement.com entry. That is a policy-risk candidate, not a proven bypass.",
            "AdBlock is configured as select,REJECT,DIRECT, so runtime selection matters.",
            "Do not infer that every telemetry domain should be blocked.",
            "", "## Required anchored domain conditions", "",
            *[f"- `{name}`: {encoded(ip['adblock_anchor_ownership'][name])}"
              for name in sorted(ip["adblock_anchor_ownership"])],
            "", "Suggested classification: BLOCK_CANDIDATE, ALLOW_CANDIDATE, CONFLICT, REVIEW_REQUIRED.",
        ]),
        "INTERNATIONAL_RULES.md": "\n".join([
            "# International route policy review", "",
            "Explicit service routing is useful only where geo-exit, isolation or node choice is intentional.",
            "Ordinary overseas traffic could use FINAL when routing requirements are identical, subject to testing.",
            "Shared CDN, auth, payment and telemetry infrastructure must not be assigned by string branding alone.",
            "Policy-specific tests are needed before any Stage-03 consolidation.",
            "Published groups can share auth, CDN and payment endpoints; inspect full overlap index.",
            "", "## Published group sizes", "",
            *[f"- {d['group']}: {d['rules']}" for d in details if d["group"] in INTERNATIONAL],
        ]),
        "DNS_ROUTING_RISKS.md": "\n".join([
            "# IP matching and DNS investigation", "",
            f"- IP rules lacking no-resolve: {len(ip['missing_no_resolve'])}.",
            "- The generator *adds* no-resolve to IP-CIDR/CIDR6, but preserves optional IP-ASN flags.",
            "- On a domain miss, IP-rule matching may involve local lookup; exact runtime execution is unverified.",
            "- Distinguish Loon DNS, app DoH, proxy remote DNS, local pre-resolution and reported recursive egress.",
            "- GEOIP,CN,DIRECT,no-resolve and FINAL in local [Rule] must be assessed against remote ordering.",
            "- These static findings neither demonstrate DNS leakage nor prove exposure of a device address.",
            "", "## Missing flags (complete)", first(10000, ip["missing_no_resolve"]),
            "", "RUNTIME_VERIFICATION_REQUIRED",
        ]),
        "GENERATOR_AUDIT.md": "\n".join([
            "# Generator review (read-only)", "",
            "- normalize: CIDR and CIDR6 always gain no-resolve even if upstream did not set it; ASN does not.",
            "- normalize: v2fly plain entries become suffix; dnsmasq records become suffix.",
            "- normalize: URL-REGEX, regexp and selected unsupported entries are omitted or quarantined.",
            "- generate: group dedup retains first owner; later source-origin details are dropped.",
            "- prune_suffix_redundancy: removes descendants only inside one group.",
            "- own_cross_group_duplicates: PUBLISH_ORDER first owner wins, with no business-domain adjudication.",
            "- Published files are lexically sorted; no original source order is maintained.",
            "- Shared-CDN ownership and AdBlock-vs-platform priority are not business-validated.",
            "- Loon docs: https://nsloon.bid/document/rule and https://nsloon.bid/document/ip_rule",
            "- Loon 3.0.3+ describes domain-first matching and then local DNS for unmatched domain queries.",
            "- The build report stores 100 examples for several conflict categories, not full prepublication records.",
        ]),
        "RISK_REGISTER.md": "\n".join([
            "# Risk register", "",
            "- Full entries: data/risk_register.json. No runtime finding is marked RUNTIME_CONFIRMED.",
            f"- P0: {sev['P0']}; P1: {sev['P1']}; P2: {sev['P2']}; P3: {sev['P3']}.",
            "", "## All P0/P1 entries", "",
            *[f"- {r['risk_id']} **{r['severity']}**: `{r['source_file']}:{r['source_line']}` "
              f"`{r['rule']}` — {r['category']}; {r['trigger_condition']}; "
              "runtime verification required."
              for r in risks if r["severity"] in ("P0", "P1")],
        ]),
        "PHASE03_RECOMMENDATIONS.md": "\n".join([
            "# Stage 03 recommendations (proposals only)", "",
            "1. First verify domain-prefix and IP-ASN direct routing risks on-device; do not change DNS settings.",
            "2. Audit platform vs AdBlock prepublication ownership with immutable upstream inputs and full provenance.",
            "3. Retain specialized streaming/AI exit groups only where required by actual node strategy.",
            "4. Consider merging overlapping ordinary international categories into FINAL after differential tests.",
            "5. Replace broad DIRECT keywords only after domain ownership and false-positive review.",
            "6. In Stage 04 redesign priority with deliberate shared-CDN / auth / payment ownership rules.",
            "7. Preserve source line mappings at normalization, filter, prune and publication steps.",
            "8. First-ingestion zero-contribution sources are MERGE review candidates, not deletion proof.",
            "9. Do not remove sources until final surviving rules are attributable to immutable inputs.",
            "10. No source is recommended for removal solely because it is newly added or has many rules.",
        ]),
    }
    for name, body in docs.items():
        (output / name).write_text(body + "\n", encoding="utf-8")


def local_source_matches(records):
    """Match immutable local input lines to published conditions (not exclusive origin proof).

    This only proves that a local source's matcher exists in the final output. Another
    remote source may have independently supplied the same matcher. Never infer sole credit.
    """
    catalog = read_json("rules/sources.json")
    published = {(r["group"], rule_key(r)) for r in records}
    suffixes = {(r["group"], r["rule_value"]): locator(r)
                for r in records if r["rule_type"] == "DOMAIN-SUFFIX"}
    outputs = []
    for source in catalog["sources"]:
        if source.get("role") != "local" or not source.get("enabled"):
            continue
        path = source["path"]
        entries = []
        for line_no, raw in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith(("#", ";", "//")):
                continue
            entry = parse_rule(line, source["policy"], path, line_no, source["group"])
            if entry["rule_type"] in {"IP-CIDR", "IP-CIDR6"}:
                entry["no_resolve"] = True  # existing frozen generator normalize behavior
            match = (source["group"], rule_key(entry)) in published
            coverage = None
            if not match and entry["rule_type"] in DOMAIN_TYPES:
                labels = entry["rule_value"].split(".")
                for pos in range(0, len(labels)):
                    coverage = suffixes.get((source["group"], ".".join(labels[pos:])))
                    if coverage:
                        break
            entries.append({"source_file": path, "source_line": line_no,
                            "rule_type": entry["rule_type"], "rule_value": entry["rule_value"],
                            "no_resolve": entry["no_resolve"],
                            "published_match_in_target_group": match,
                            "published_same_group_suffix_covers_condition": coverage,
                            "publication_match_status": (
                                "EXACT_MATCH" if match else
                                "SAME_GROUP_SUFFIX_COVERAGE" if coverage else "UNEXPLAINED"),
                            "provenance": "LOCAL_INPUT_AT_FROZEN_COMMIT_NONEXCLUSIVE_MATCH"})
        outputs.append({
            "source_id": source["id"], "source_file": path,
            "normalized_local_input_count": len(entries),
            "published_condition_matches": sum(e["published_match_in_target_group"] for e in entries),
            "same_group_suffix_covered": sum(e["publication_match_status"] == "SAME_GROUP_SUFFIX_COVERAGE" for e in entries),
            "unexplained_conditions": sum(e["publication_match_status"] == "UNEXPLAINED" for e in entries),
            "unmatched_conditions": sum(not e["published_match_in_target_group"] for e in entries),
            "per_rule": entries,
            "note": "Cannot prove sole source ownership without immutable remote source contents"
        })
    return {"evidence": "FROZEN_LOCAL_INPUT_VS_PUBLISHED_MATCH",
            "exclusive_attribution": "UNKNOWN",
            "sources": outputs}


def scan_local_rules(index):
    """Inspect local GEOIP/FINAL separately, since 206505 counts remote rule files only."""
    items = []
    for filename in index["configuration_files"]:
        path = filename if isinstance(filename, str) else filename["path"]
        section = ""
        legacy_profiles = {"LoonKit.lcf": "refactor/vnext/templates/LoonKit.legacy-seed.lcf",
                           "LoonKit.PrivacyDNS.lcf": "refactor/vnext/templates/LoonKit.PrivacyDNS.legacy-seed.lcf"}
        archived = legacy_profiles.get(path, path)
        for lineno, raw in enumerate((ROOT / archived).read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            if line.startswith("[") and line.endswith("]"):
                section = line
                continue
            if section != "[Rule]" or not line or line.startswith(("#", ";", "//")):
                continue
            parts = [part.strip() for part in line.split(",")]
            if parts[0] == "FINAL" and len(parts) == 2:
                policy, flag = parts[1], False
            elif parts[0] == "GEOIP" and len(parts) in (3, 4):
                policy = parts[2]
                flag = len(parts) == 4 and parts[3].lower() == "no-resolve"
            elif parts[0] in TYPES and len(parts) >= 3:
                policy = parts[2]
                flag = "no-resolve" in parts[3:]
            else:
                raise ValueError(f"unknown local rule: {path}:{lineno}")
            items.append({
                "source_file": path, "source_line": lineno, "rule_type": parts[0],
                "rule_value": parts[1] if parts[0] != "FINAL" else "",
                "policy": policy, "no_resolve": flag
            })
    assert any(r["rule_type"] == "GEOIP" for r in items)
    assert any(r["rule_type"] == "FINAL" for r in items)
    return items


def build(output):
    _, index = validate_snapshot()
    records, details = scan_published(index)
    overlaps = overlap_analysis(records)
    inventory = source_inventory(index, records)
    ip, risks = candidates(records, overlaps, inventory)
    data = output / "data"
    data.mkdir(parents=True, exist_ok=True)
    # mtime=0 removes timestamps, so reruns produce byte-for-byte identical data.
    rows = "".join(encoded(locator(r)) + "\n" for r in records).encode("utf-8")
    (data / "normalized_rules.jsonl.gz").write_bytes(gzip.compress(rows, compresslevel=9, mtime=0))
    dump(data / "published_file_inventory.json", details)
    dump(data / "local_rule_inventory.json", scan_local_rules(index))
    local_map = local_source_matches(records)
    dump(data / "local_source_matches.json", local_map)
    dump(data / "source_inventory.json", inventory)
    dump(data / "duplicate_report.json", {
        "published_exact_duplicates": overlaps["published_exact_duplicates"],
        "published_cross_policy_exact": overlaps["published_cross_policy_exact"],
        "same_match_different_flags": overlaps["same_match_different_flags"],
        "prepublication_input_stage_statistics": inventory["prepublication"]
    })
    dump(data / "policy_conflicts.json", {
        k: v for k, v in overlaps.items()
        if k not in {"published_exact_duplicates", "published_cross_policy_exact",
                     "same_match_different_flags"}
    })
    dump(data / "dns_risk_candidates.json", ip)
    dump(data / "risk_register.json", risks)
    type_counts = Counter(r["rule_type"] for r in records)
    summary = dict(snapshot_commit=SOURCE_COMMIT, scanned_subscriptions=len(details),
                   scanned_sources=len(inventory["sources"]), published_rules=len(records),
                   type_counts=dict(sorted(type_counts.items())),
                   published_exact_duplicates=len(overlaps["published_exact_duplicates"]),
                   published_cross_policy_exact=len(overlaps["published_cross_policy_exact"]),
                   published_domain_ancestry_pairs=len(overlaps["domain_suffix_cross_policy_coverage"]),
                   published_keyword_conflict_pairs=len(overlaps["keyword_cross_policy_possible"]),
                   published_ip_overlap_pairs=len(overlaps["ip_cross_policy_overlap"]),
                   missing_no_resolve=len(ip["missing_no_resolve"]),
                   risk_counts=dict(sorted(Counter(r["severity"] for r in risks).items())),
                   adblock_platform_ownership_risks=sum(
                       r["category"] == "ADBLOCK_PLATFORM_OWNERSHIP" for r in risks),
                   direct_broad_keywords=len(ip["direct_keywords"]),
                   source_recommendations=inventory["source_recommendation_counts"],
                   staged_zero_incremental_source_count=len(inventory["staged_zero_incremental_sources"]),
                   verified_local_source_file_count=len(local_map["sources"]),
                   local_input_rules_with_published_condition=sum(
                       a["published_condition_matches"] for a in local_map["sources"]),
                   local_input_rules_covered_by_published_suffix=sum(
                       a["same_group_suffix_covered"] for a in local_map["sources"]),
                   local_input_unexplained_conditions=sum(
                       a["unexplained_conditions"] for a in local_map["sources"]),
                   manual_source_review=sum(s["recommendation"] in ("INVESTIGATE", "MERGE")
                                            for s in inventory["sources"]),
                   provenance="SOURCE_PROVENANCE_INCOMPLETE",
                   runtime="RUNTIME_VERIFICATION_REQUIRED")
    dump(data / "summary.json", summary)
    markdown_reports(records, details, inventory, overlaps, risks, ip, output)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / OUT)
    parser.add_argument("--check", action="store_true",
                        help="Verify committed output is identical, without modifications")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            result = build(Path(tmp))
            actual = {str(p.relative_to(tmp)): p.read_bytes()
                      for p in Path(tmp).rglob("*") if p.is_file()}
            committed = {str(p.relative_to(args.output)): p.read_bytes()
                         for p in args.output.rglob("*") if p.is_file()}
            if actual != committed:
                raise SystemExit("AUDIT_DATA_DRIFT: run audit script and commit exact output")
    else:
        result = build(args.output)
    print(encoded(result))


if __name__ == "__main__":
    main()
