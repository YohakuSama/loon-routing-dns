#!/usr/bin/env python3
"""Offline vNext Loon rule compiler. Frozen publication snapshots are inputs, not upstream downloads.

This intentionally does NOT pretend snapshot line numbers identify original upstream lines:
source_candidates are possible original contributors, not proven per-line provenance.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vnext_source_lock import check_lock

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "refactor" / "vnext"
GENERATED = BASE / "generated"
REPORTS = BASE / "reports"
MANIFEST = BASE / "engine_manifest.json"
SNAP = ROOT / "rules" / "snapshots" / "phase03" / "generated"
PRODUCTION_CONFIG = ROOT / "LoonKit.lcf"
KINDS = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "IP-CIDR", "IP-CIDR6", "IP-ASN", "USER-AGENT"}
DOMAIN_RX = re.compile(r"^[a-z0-9*._-]+$", re.I)
# The following domain ownership decisions are audited exceptions, not a diagnostic proxy whitelist.
AD_ANCHORS = ("admob.com", "doubleclick.com", "app-measurement.com", "ads-twitter.com")
AD_SAFETY_ROOTS = ("stripe.com", "paypal.com", "auth0.com", "microsoftonline.com",
                   "apple.com", "icloud.com", "cloudfront.net", "akamaized.net",
                   "akamaihd.net", "accounts.google.com", "login.live.com")
SHARED_PLATFORM_ROOTS = ("cloudfront.net", "akamaized.net", "akamaihd.net",
                         "fastly.net", "stripe.com", "auth0.com", "segment.io")
AI_EXCEPTION_HOSTS = ("gemini.google.com", "aistudio.google.com",
                      "generativeai.googleapis.com", "copilot.microsoft.com")


def load_manifest(path: Path = MANIFEST) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    groups = data["active_groups"]
    if len(groups) != len(set(groups)) or not groups or "ProxyProtect" in groups:
        raise ValueError("unsafe, duplicate or empty active groups")
    if set(groups) & set(data["inactive_groups"]):
        raise ValueError("active/inactive overlap")
    return data


def normalize(raw: str) -> str | None:
    line = raw.strip().lstrip("\ufeff")
    if not line or line.startswith(("#", ";", "//")):
        return None
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 2:
        raise ValueError("rule has fewer than two columns: " + line[:100])
    kind, value = parts[:2]
    kind = kind.upper()
    if kind not in KINDS or not value or len(parts) > 3:
        raise ValueError("unsupported rule: " + line[:100])
    if len(parts) == 3 and (parts[2].lower() != "no-resolve" or kind not in {"IP-CIDR", "IP-CIDR6", "IP-ASN"}):
        raise ValueError("unsupported flags: " + line[:100])
    if kind.startswith("DOMAIN"):
        value = value.rstrip(".").lower()
        if not DOMAIN_RX.fullmatch(value):
            raise ValueError("invalid domain: " + line[:100])
    if kind in {"IP-CIDR", "IP-CIDR6"}:
        net = ipaddress.ip_network(value, strict=False)
        if (net.version == 6) != (kind == "IP-CIDR6"):
            raise ValueError("IP family mismatch: " + line[:100])
        value = str(net)
    if kind == "IP-ASN":
        if not re.fullmatch(r"(?:AS)?[0-9]+", value, re.I):
            raise ValueError("invalid ASN: " + line[:100])
        value = str(int(value.upper().removeprefix("AS")))
    suffix = ",no-resolve" if kind in {"IP-CIDR", "IP-CIDR6", "IP-ASN"} else ""
    return kind + "," + value + suffix


def fields(rule: str) -> tuple[str, str]:
    p = rule.split(",")
    return p[0], p[1]


def is_covered(host: str, root: str) -> bool:
    return host == root or host.endswith("." + root)


def covers_domain(rule: str, host: str) -> bool:
    kind, value = fields(rule)
    return ((kind == "DOMAIN" and host == value)
            or (kind == "DOMAIN-SUFFIX" and is_covered(host, value))
            or (kind == "DOMAIN-KEYWORD" and value in host))


def filter_rule(group: str, rule: str, protected: tuple[str, ...],
                keywords: dict | None = None,
                shared_roots: tuple[str, ...] = (),
                shared_keywords: dict | None = None) -> tuple[str | None, str | None, str]:
    kind, value = fields(rule)
    if group in {"ChinaDirect", "DomesticCore", "SteamCN", "AppleOTA"}:
        if any(covers_domain(rule, x) for x in protected):
            return None, "DIRECT_PROTECTED_DOMAIN", "FINAL (policy-dependent)"
        if group == "ChinaDirect":
            if kind == "DOMAIN-KEYWORD":
                if value == ".tmall.com":
                    return "DOMAIN-SUFFIX,tmall.com", "DIRECT_KEYWORD_NARROWED", "DIRECT (scoped suffix)"
                if keywords and value in keywords.get("ChinaDirect", {}):
                    scoped = keywords["ChinaDirect"][value]
                    if not scoped.startswith("DOMAIN-SUFFIX,") or normalize(scoped) != scoped:
                        raise ValueError("unsafe ChinaDirect business suffix: " + repr(scoped))
                    return scoped, "BRAND_KEYWORD_SCOPED_TO_SUFFIX", scoped
                return None, "DIRECT_KEYWORD_UNPROVEN", "GEOIP CN or FINAL"
            if kind == "DOMAIN-SUFFIX" and "." not in value and value != "cn":
                return None, "DIRECT_SINGLE_LABEL_UNPROVEN", "GEOIP CN or FINAL"
            if kind in {"IP-CIDR", "IP-CIDR6"}:
                net = ipaddress.ip_network(value)
                # Do not assume broad upstream AS/range ownership establishes mainland DIRECT.
                minimum = 24 if net.version == 4 else 48
                if net.prefixlen < minimum:
                    return None, "DIRECT_WIDE_IP_UNPROVEN", "GEOIP CN for IP destinations or FINAL"
    if (kind == "DOMAIN-KEYWORD" and shared_keywords
            and value in shared_keywords.get(group, ())):
        return None, "MULTITENANT_SHARED_KEYWORD_ISOLATED", "precise owner or FINAL"
    if kind == "DOMAIN-KEYWORD" and keywords and value in keywords.get(group, {}):
        scoped = keywords[group][value]
        if not scoped.startswith("DOMAIN-SUFFIX,") or normalize(scoped) != scoped:
            raise ValueError("invalid reviewed keyword decision " + repr(scoped))
        return scoped, "BRAND_KEYWORD_SCOPED_TO_SUFFIX", scoped
    if group == "AdBlock":
        if kind not in {"DOMAIN", "DOMAIN-SUFFIX"}:
            return None, "ADBLOCK_NON_DOMAIN_MATCH", "FINAL"
        if any(is_covered(value, x) for x in AD_SAFETY_ROOTS):
            return None, "ADBLOCK_SHARED_CRITICAL_SERVICE", "platform owner or FINAL"
    if group in {"Google", "Twitter", "ChinaDirect"} and kind in {"DOMAIN", "DOMAIN-SUFFIX"}:
        if value in AD_ANCHORS or (kind == "DOMAIN" and any(is_covered(value, a) for a in AD_ANCHORS)):
            return None, "ADVERTISING_REASSIGNED", "AdBlock (REJECT or DIRECT)"
    if group not in {"AdBlock", "ChinaDirect"} and kind == "DOMAIN-SUFFIX" and value in SHARED_PLATFORM_ROOTS:
        return None, "SHARED_INFRASTRUCTURE_ISOLATED", "FINAL"
    if kind == "DOMAIN-SUFFIX" and value in shared_roots:
        return None, "MULTITENANT_SHARED_ROOT_ISOLATED", "precise platform domain or FINAL"
    if group == "AI" and kind == "IP-ASN":
        return None, "AI_BROAD_ASN", "FINAL"
    return rule, None, group


def choose_exact_owners(candidates: dict[str, dict[str, set[tuple[str, int]]]],
                        trace: list[dict], active: list[str]) -> None:
    # No PUBLISH_ORDER ownership. Identical predicates with different effects are
    # quarantined unless a narrow, explicit service or ad domain proves ownership.
    reverse: dict[str, list[str]] = defaultdict(list)
    for group, records in candidates.items():
        for rule in records:
            reverse[rule].append(group)
    for rule, groups in sorted(reverse.items()):
        if len(groups) < 2:
            continue
        kind, value = fields(rule)
        owner = None
        if kind in {"DOMAIN", "DOMAIN-SUFFIX"} and value in AD_ANCHORS and "AdBlock" in groups:
            owner = "AdBlock"
        elif kind in {"DOMAIN", "DOMAIN-SUFFIX"} and value in AI_EXCEPTION_HOSTS and "AI" in groups:
            owner = "AI"
        elif set(groups).issubset({"DomesticCore", "ChinaDirect", "SteamCN", "AppleOTA"}):
            owner = next(g for g in ("DomesticCore", "SteamCN", "AppleOTA", "ChinaDirect") if g in groups)
        # Else isolate all cross-policy exact collisions, rather than choosing the first source.
        for group in groups:
            if group != owner:
                reason = "CROSS_POLICY_EXACT_QUARANTINE" if owner is None else "EXACT_BUSINESS_OWNER"
                for file, lineno in sorted(candidates[group][rule]):
                    trace.append({"action": "REMOVED", "group": group, "rule": rule, "origin": file,
                                  "line": lineno, "reason": reason, "replacement": owner or "FINAL",
                                  "compatibility": "POLICY_CHANGE_REQUIRES_RUNTIME_REVIEW"})
                del candidates[group][rule]



def verify_immutable_sources(root: Path, manifest: dict) -> None:
    """Reject altered frozen snapshots, without requiring network or rewriting baselines."""
    pinned = manifest.get("frozen_git_blob_sha1")
    if not isinstance(pinned, dict) or len(pinned) < 44:
        raise ValueError("missing immutable snapshot attestations")
    for relative, expected in sorted(pinned.items()):
        if not (relative.startswith("rules/snapshots/phase03/generated/") or relative.startswith("rules/custom/")
                or relative == "rules/ProxyProtect.list"):
            raise ValueError("untrusted frozen file path: " + relative)
        file = root / relative
        data = file.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
        if actual != expected:
            raise ValueError(f"frozen input changed: {relative} (expected {expected}, got {actual})")


def quarantine_ip_overlaps(groups: dict, trace: list[dict]) -> None:
    """Mitigate confirmed broad provider collisions without assuming Loon IP precedence.

    17/8 Apple, 74.125/16 Google: candidate ChinaDirect exceptions are
    narrower but still collide with distinct platform selectors.
    AWS multi-tenant supernets in Whatsapp overlap dedicated Netflix IPs.
    Preserve dedicated small service IPs and log every isolated predicate.
    """
    platform_nets = []
    for owner in ("Apple", "Google"):
        for rule in groups.get(owner, {}):
            if rule.startswith(("IP-CIDR,", "IP-CIDR6,")):
                platform_nets.append((owner, ipaddress.ip_network(fields(rule)[1])))
    netflix_nets = [ipaddress.ip_network(fields(rule)[1])
                    for rule in groups.get("Netflix", {})
                    if rule.startswith(("IP-CIDR,", "IP-CIDR6,"))]
    removals = []
    for rule in groups.get("ChinaDirect", {}):
        if rule.startswith(("IP-CIDR,", "IP-CIDR6,")):
            ip_net = ipaddress.ip_network(fields(rule)[1])
            owners = sorted({owner for owner, outer in platform_nets
                             if ip_net.version == outer.version and ip_net.subnet_of(outer)})
            if owners:
                removals.append(("ChinaDirect", rule, "DIRECT_IP_PLATFORM_OVERLAP",
                                 "platform policy: " + "|".join(owners)))
    for rule in groups.get("Whatsapp", {}):
        if rule.startswith(("IP-CIDR,", "IP-CIDR6,")):
            broad = ipaddress.ip_network(fields(rule)[1])
            nested = any(n.version == broad.version and n.subnet_of(broad)
                         and n != broad for n in netflix_nets)
            if nested:
                removals.append(("Whatsapp", rule, "MULTITENANT_IP_NET_OVERLAP",
                                 "domain-scoped Whatsapp or FINAL"))
    for group, rule, reason, fallback in removals:
        for file, line in sorted(groups[group].pop(rule)):
            trace.append({"action": "REMOVED", "group": group, "rule": rule,
                          "origin": file, "line": line, "reason": reason,
                          "replacement": fallback,
                          "compatibility": "IP MATCH CHANGE REQUIRES DEVICE TEST"})


def compile_rules(root: Path = ROOT) -> dict[str, str]:
    cfg = load_manifest(root / "refactor/vnext/engine_manifest.json")
    verify_immutable_sources(root, cfg)
    check_lock(root)
    active, inactive = cfg["active_groups"], cfg["inactive_groups"]
    guardrails = json.loads((root / "rules/routing_guardrails.json").read_text(encoding="utf-8"))
    protected = tuple(guardrails["protected_proxy_domains"])
    groups: dict[str, dict[str, set[tuple[str, int]]]] = {g: defaultdict(set) for g in active}
    trace: list[dict] = []
    before, reasons = Counter(), Counter()
    raw_total = 0
    flag_changes: list[dict] = []
    old_rules_by_group: dict[str, set[str]] = {}
    source_catalog = json.loads((root / "rules/sources.json").read_text(encoding="utf-8"))["sources"]
    source_groups = defaultdict(list)
    local_evidence = defaultdict(list)
    source_inventory = []
    for source in source_catalog:
        source_groups[source["group"]].append(source["id"])
        enabled = source["group"] in active
        verified_local = source.get("role") == "local"
        source_inventory.append({
            "source_id": source["id"], "original_group": source["group"],
            "original_role": source.get("role", "upstream"),
            "input_kind": "HISTORIC_UPSTREAM_NOT_FETCHED" if not verified_local else "IMMUTABLE_LOCAL_FILE",
            "candidate_status": ("GROUP_DISABLED_FINAL_FALLBACK" if not enabled else
                                 "FROZEN_LOCAL_SOURCE_VERIFIABLE" if verified_local else
                                 "FROZEN_MERGED_SNAPSHOT_ONLY_SOURCE_NOT_ATTRIBUTABLE"),
            "historic_source_url": source.get("url"), "historic_local_path": source.get("path"),
            "line_level_origin_proven": bool(verified_local),
            "verified_candidate_lines": 0,
            "snapshot_group_active": enabled,
        })
        if verified_local:
            path = root / source["path"]
            for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                normalized = normalize(raw)
                if normalized:
                    local_evidence[(source["group"], normalized)].append((
                        source["id"], source["path"], line_number))

    for group in active + inactive:
        filename = "AnimeCrazy" if group == "動畫瘋" else group
        path = root / "rules/snapshots/phase03/generated" / (filename + ".list")
        if not path.is_file():
            raise FileNotFoundError(path)
        old_set = set()
        for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            rule = normalize(raw)
            if not rule:
                continue
            raw_total += 1
            if rule.startswith(("IP-CIDR,", "IP-CIDR6,", "IP-ASN,")) and raw.strip() != rule:
                flag_changes.append({"group": group, "snapshot_file": "rules/generated/" + filename + ".list",
                                     "snapshot_line": n, "original": raw.strip(),
                                     "candidate": rule, "effect": "IP_LITERAL_MATCH_ONLY_NO_DNS_PRE_RESOLVE"})
            before[group] += 1
            old_set.add(rule)
            origin = "rules/generated/" + filename + ".list"
            if group in inactive:
                reason, replacement, outcome = "SOURCE_DISABLED", "FINAL", None
            else:
                outcome, reason, replacement = filter_rule(
                    group, rule, protected, cfg.get("reviewed_keyword_narrowing", {}),
                    tuple(cfg.get("reviewed_multi_tenant_suffixes", [])),
                    cfg.get("reviewed_multi_tenant_keywords", {}))
            if outcome:
                groups[group][outcome].add((origin, n))
                if outcome != rule:
                    trace.append({"action": "REMOVED", "group": group, "rule": rule,
                                  "origin": origin, "line": n, "reason": reason,
                                  "replacement": outcome, "compatibility": "NARROWER_MATCH"})
            else:
                trace.append({"action": "REMOVED", "group": group, "rule": rule,
                              "origin": origin, "line": n, "reason": reason,
                              "replacement": replacement, "compatibility": "BEHAVIOR_MAY_CHANGE"})
                reasons[reason] += 1
        old_rules_by_group[group] = old_set
    # The legacy ProxyProtect list is a separate 17-rule subscription, outside
    # the 33 generated snapshots. Record every retired rule individually.
    proxy_path = root / "rules/ProxyProtect.list"
    proxy_origin = proxy_path.relative_to(root).as_posix()
    proxy_original = set()
    for lineno, raw in enumerate(proxy_path.read_text(encoding="utf-8").splitlines(), 1):
        rule = normalize(raw)
        if not rule:
            continue
        proxy_original.add(rule)
        before["ProxyProtect"] += 1
        trace.append({"action": "REMOVED", "group": "ProxyProtect", "rule": rule,
                      "origin": proxy_origin, "line": lineno,
                      "reason": "INDEPENDENT_PROXYPROTECT_RETIRED",
                      "replacement": "service owner or FINAL",
                      "compatibility": "FINAL=DIRECT MAY NOW DIRECT THIS DESTINATION"})
    old_rules_by_group["ProxyProtect"] = proxy_original
    # Explicit advertising classification, with reviewable virtual provenance.
    for domain in AD_ANCHORS:
        rule = "DOMAIN-SUFFIX," + domain
        if rule not in groups["AdBlock"]:
            groups["AdBlock"][rule].add(("refactor/vnext/engine_manifest.json", 0))
    choose_exact_owners(groups, trace, active)
    quarantine_ip_overlaps(groups, trace)
    # Drop within-group DOMAIN covered by suffix only if not explicitly contested.
    for group, records in groups.items():
        suffixes = {fields(r)[1] for r in records if r.startswith("DOMAIN-SUFFIX,")}
        for rule in list(records):
            kind, value = fields(rule)
            if kind == "DOMAIN" and any(".".join(value.split(".")[i:]) in suffixes for i in range(len(value.split(".")))):
                for file, line in sorted(records[rule]):
                    trace.append({"action": "REMOVED", "group": group, "rule": rule, "origin": file,
                                  "line": line, "reason": "SAME_POLICY_SUFFIX_COVERAGE",
                                  "replacement": group, "compatibility": "SAME_POLICY"})
                del records[rule]
    # Generated artifacts are stable across runs and independent from network availability.
    files = {}
    for group in active:
        filename = "AnimeCrazy" if group == "動畫瘋" else group
        header = ("# LoonKit vNext candidate only - NOT a production subscription",
                  "# frozen input: rules/generated/" + filename + ".list",
                  "# reconstructed snapshot provenance: reports/provenance.tsv")
        files["refactor/vnext/generated/" + filename + ".list"] = "\n".join(
            [*header, *sorted(groups[group])]
        ) + "\n"
    # Independently verify exact locally maintained lines against retained
    # candidate rules. This proves local contributions only, not upstream ancestry.
    verified = ["group\trule\tverified_source_id\tlocal_file\tlocal_line\tsnapshot_file\tsnapshot_line"]
    evidence_counts = Counter()
    for group in active:
        for rule, origins in sorted(groups[group].items()):
            for source_id, local_path, lineno in sorted(local_evidence.get((group, rule), ())):
                evidence_counts[source_id] += 1
                for snapshot_path, snapshot_line in sorted(origins):
                    verified.append("\t".join([group, rule, source_id, local_path, str(lineno),
                                                snapshot_path, str(snapshot_line)]))
    files["refactor/vnext/reports/verified_local_provenance.tsv"] = "\n".join(verified) + "\n"
    for item in source_inventory:
        item["verified_candidate_lines"] = evidence_counts[item["source_id"]]
    files["refactor/vnext/reports/sources.vnext.candidate.json"] = json.dumps({
        "original_source_count": len(source_catalog),
        "candidate_input_kind": "26_FROZEN_GROUP_COMPOSITES_NOT_UPSTREAM_REBUILD",
        "entries": source_inventory,
        "warning": "Upstream IDs are merely historic candidates, never claimed as line-level proof"
    }, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    # Trace every retained rule to snapshot file and line. Original upstream
    # source ids are only POSSIBLE contributors for a merged snapshot.
    prov = ["group\trule\tsnapshot_file\tsnapshot_line\tpossible_upstream_source_ids"]
    for group in active:
        for rule, origins in sorted(groups[group].items()):
            for path, line in sorted(origins):
                prov.append("\t".join((group, rule, path, str(line), "|".join(source_groups[group]))))
    files["refactor/vnext/reports/provenance.tsv"] = "\n".join(prov) + "\n"
    trace.sort(key=lambda x: (x["group"], x["rule"], x["origin"], x["line"], x["reason"]))
    files["refactor/vnext/reports/removed_or_modified.jsonl"] = "".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in trace)
    result = {}
    new_total = 0
    for group in active:
        result[group] = len(groups[group])
        new_total += result[group]
    # Compare by group and predicate, not just file size.
    original = {(group, rule) for group, rules in old_rules_by_group.items() for rule in rules}
    candidate = {(group, rule) for group, records in groups.items() for rule in records}
    added = sorted(candidate - original)
    removed = sorted(original - candidate)
    files["refactor/vnext/reports/ip_no_resolve_changes.jsonl"] = "".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in flag_changes)
    # Full classification-specific ledgers accompany the complete removal ledger.
    for key, selected in (
        ("direct_changes", [x for x in trace if x["group"] in {"ChinaDirect", "DomesticCore", "AppleOTA", "SteamCN"}]),
        ("adblock_changes", [x for x in trace if x["group"] == "AdBlock" or x["reason"] == "ADVERTISING_REASSIGNED"]),
        ("proxyprotect_impact", [x for x in trace if x["group"] == "ProxyProtect"]),
    ):
        files["refactor/vnext/reports/" + key + ".jsonl"] = "".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in selected)
    old_owners, new_owners = defaultdict(set), defaultdict(set)
    for group, rule in original:
        old_owners[rule].add(group)
    for group, rule in candidate:
        new_owners[rule].add(group)
    ownership = []
    for rule in sorted(set(old_owners) | set(new_owners)):
        old_groups, new_groups = sorted(old_owners[rule]), sorted(new_owners[rule])
        if old_groups != new_groups:
            ownership.append({"rule": rule, "original_groups": old_groups,
                              "candidate_groups": new_groups, "fallback": "FINAL if absent"})
    files["refactor/vnext/reports/ownership_changes.jsonl"] = "".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in ownership)
    # Cross-policy parent/child domain overlap: record predicate-level ambiguities,
    # not just two exact-equal strings. No unsupported Loon precedence is assumed.
    suffix_owners = defaultdict(list)
    for group, records in groups.items():
        for rule in records:
            if rule.startswith("DOMAIN-SUFFIX,"):
                suffix_owners[fields(rule)[1]].append((group, rule))
    ancestry = []
    for group, records in groups.items():
        for rule in records:
            kind, value = fields(rule)
            if kind not in {"DOMAIN", "DOMAIN-SUFFIX"}:
                continue
            labels = value.split(".")
            for offset in range(0 if kind == "DOMAIN" else 1, len(labels)):
                ancestor = ".".join(labels[offset:])
                for other_group, other_rule in suffix_owners.get(ancestor, ()):
                    if other_group != group:
                        ancestry.append({"child_group": group, "child_rule": rule,
                                         "parent_group": other_group, "parent_rule": other_rule,
                                         "status": "REQUIRES_RUNTIME_TEST",
                                         "note": "Matcher class and local/remote priority must be validated"})
    ancestry.sort(key=lambda x: (x["child_group"], x["child_rule"],
                                  x["parent_group"], x["parent_rule"]))
    files["refactor/vnext/reports/domain_parent_child_conflicts.jsonl"] = "".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in ancestry)
    # DOMAIN-KEYWORD has intentionally non-boundary-scoped semantics. Keep every
    # remaining non-DIRECT keyword visible for later business review.
    kw_risks = []
    for group, records in groups.items():
        for rule in records:
            if rule.startswith("DOMAIN-KEYWORD,"):
                value = fields(rule)[1]
                kw_risks.append({"group": group, "rule": rule,
                                 "risk": "GLOBAL_SUBSTRING_MATCH",
                                 "severity": "HIGH" if len(value) <= 4 else "REVIEW",
                                 "status": "REQUIRES_RUNTIME_TEST"})
    kw_risks.sort(key=lambda x: (x["group"], x["rule"]))
    files["refactor/vnext/reports/domain_keyword_risks.jsonl"] = "".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in kw_risks)
    # Detect nested IP nets that route through distinct policies. No O(n^2)
    # full cross-product; compare each network to its exact supernet prefixes.
    network_owners = defaultdict(list)
    for group, records in groups.items():
        for rule in records:
            if rule.startswith(("IP-CIDR,", "IP-CIDR6,")):
                network_owners[fields(rule)[1]].append((group, rule))
    ip_overlap = []
    for value, owners in network_owners.items():
        net = ipaddress.ip_network(value)
        for prefixlen in range(net.prefixlen):
            parent = str(net.supernet(new_prefix=prefixlen))
            for outer_group, outer_rule in network_owners.get(parent, ()):
                for inner_group, inner_rule in owners:
                    if inner_group != outer_group:
                        ip_overlap.append({"inner_group": inner_group, "inner_rule": inner_rule,
                                           "outer_group": outer_group, "outer_rule": outer_rule,
                                           "status": "REQUIRES_RUNTIME_TEST"})
    ip_overlap.sort(key=lambda x: (x["inner_group"], x["inner_rule"],
                                   x["outer_group"], x["outer_rule"]))
    files["refactor/vnext/reports/ip_network_overlaps.jsonl"] = "".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in ip_overlap)
    files["refactor/vnext/reports/added.jsonl"] = "".join(
        json.dumps({"group": g, "rule": r, "reason": "NEW_OR_RECLASSIFIED"},
                   ensure_ascii=False, sort_keys=True) + "\n" for g, r in added)
    report = {
        "status": "OFFLINE_CANDIDATE_NOT_DEVICE_VERIFIED",
        "baseline_rule_count_stage03": 206505,
        "legacy_proxyprotect_rule_count": len(proxy_original),
        "baseline_count_from_selected_snapshot_groups": raw_total,
        "candidate_rule_count": new_total,
        "baseline_upstream_source_count": len(source_catalog),
        "candidate_frozen_snapshot_input_count": len(active),
        "source_count_comparison_warning": "87 upstream feeds vs active group snapshots are NOT equivalent provenance units",
        "active_groups": active, "inactive_groups_fall_through_final": inactive,
        "before_groups": dict(sorted(before.items())), "after_groups": result,
        "added_predicate_group_count": len(added), "removed_predicate_group_count": len(removed),
        "ownership_changes": len(ownership), "ip_no_resolve_changes": len(flag_changes),
        "active_remote_upstream_sources": 0,
        "verified_local_source_line_mappings": sum(evidence_counts.values()),
        "source_status": "26 frozen group snapshots, not 26 independently verifiable upstream feeds",
        "adblock_anchors": list(AD_ANCHORS),
        "domain_parent_child_ambiguities": len(ancestry),
        "domain_keyword_review_count": len(kw_risks),
        "reviewed_keyword_narrowing_count": sum(1 for x in trace if x["reason"] == "BRAND_KEYWORD_SCOPED_TO_SUFFIX"),
        "cross_policy_nested_ip_networks": len(ip_overlap),
        "removed_or_modified_origin_lines": len(trace),
        "isolation_causes": dict(sorted(Counter(item["reason"] for item in trace).items())),
        "new_rules": [{"group": g, "rule": r} for g, r in added[:100]],
        "removed_examples": [{"group": g, "rule": r} for g, r in removed[:100]],
        "asn_fixed": ["AS132203", "AS32934", "AS211157", "AS44907", "AS59930", "AS62014", "AS62041"],
        "proxyprotect_independent_subscription": False,
        "main_modified": False,
        "dns_tun_changed": False,
        "candidate_only": True,
        "engine_status": "STATIC_CANDIDATE_GENERATED",
        "release": "NOT_READY_FOR_PRODUCTION",
        "remaining_risks": [
            "Frozen published snapshot cannot prove original upstream per-line owner",
            "Cross-policy suffix and keyword overlap needs device matching evaluation",
            "User-selected FINAL=DIRECT will direct-route unmatched traffic",
            "ASN no-resolve must be evaluated against device DNS/IP literal flows",
            "AdBlock REJECT/DIRECT and authentication/payment need functional tests",
        ],
    }
    files["refactor/vnext/reports/diff_summary.json"] = json.dumps(
        report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    profile = (root / "refactor/vnext/templates/LoonKit.legacy-seed.lcf").read_text(encoding="utf-8")
    start = profile.index("[Remote Rule]")
    end = profile.index("\n[Rule]", start)
    rule_order = cfg["subscription_order"]
    if set(rule_order) != set(active) or len(rule_order) != len(active):
        raise ValueError("subscription_order must exactly cover candidate groups")
    remote = ["[Remote Rule]",
              "# CANDIDATE ONLY: git refactor/loonkit-vnext, NOT main nor production"]
    for group in rule_order:
        filename = "AnimeCrazy" if group == "動畫瘋" else group
        policy = "DIRECT" if group in {"ChinaDirect", "DomesticCore", "AppleOTA", "SteamCN"} else group
        remote.append("https://raw.githubusercontent.com/YohakuSama/loonkit/refactor/loonkit-vnext/"
                      "refactor/vnext/generated/" + filename + ".list, policy=" + policy
                      + ", tag=vNext-" + filename + ", enabled=true")
    candidate_profile = profile[:start] + "\n".join(remote) + "\n" + profile[end:]
    candidate_profile = candidate_profile.replace(
        "# LoonKit v5.10.0", "# LoonKit vNext candidate (UNRELEASED; do not auto-subscribe)", 1)
    candidate_profile = candidate_profile.replace(
        "# Historical verified local service rules. Diagnostic protections moved to rules/ProxyProtect.list.",
        "# Reviewed local service exceptions. No independent diagnostic proxy subscription.", 1)
    # Keep seven legacy overseas selectors functionally reachable for narrowly
    # scoped, owned service roots. Other auxiliary endpoints still need devices.
    scoped_overseas = cfg.get("reviewed_overseas_inline_minimal", {})
    if set(scoped_overseas) != set(inactive):
        raise ValueError("every inactive overseas selector needs an explicit scoped disposition")
    additions = []
    for group in inactive:
        for host in scoped_overseas[group]:
            if not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", host):
                raise ValueError("unscoped overseas hostname")
            additions.append("DOMAIN-SUFFIX," + host + "," + group)
    if len(additions) != len(set(additions)):
        raise ValueError("duplicate overseas candidate inline rule")
    # Official Loon rule precedence: local predicates outrank subscribed ones.
    # Preserve user-selectable AdBlock for precise ads under restored local roots.
    # These selectors remain AdBlock (REJECT/DIRECT), never unconditional REJECT.
    local_adblock = []
    for rule in sorted(groups["AdBlock"]):
        kind, value = fields(rule)
        if kind in {"DOMAIN", "DOMAIN-SUFFIX"} and any(
                is_covered(value, host) for hosts in scoped_overseas.values() for host in hosts):
            local_adblock.append(rule + ",AdBlock")
    marker = "GEOIP,CN,DIRECT,no-resolve\n"
    if candidate_profile.count(marker) != 1:
        raise ValueError("unexpected candidate GEOIP terminator")
    candidate_profile = candidate_profile.replace(
        marker,
        "# Minimal overseas service selector compatibility; candidate only.\n"
        + "# Scoped AdBlock overrides precede local overseas service roots.\n"
        + "\n".join([*local_adblock, *additions]) + "\n" + marker, 1)
    files["refactor/vnext/LoonKit.vNext.Candidate.lcf"] = candidate_profile
    return files


def write_outputs(files: dict[str, str], root: Path = ROOT, check: bool = False) -> None:
    problems = []
    for name, content in sorted(files.items()):
        dest = root / name
        if check:
            if not dest.is_file() or dest.read_text(encoding="utf-8") != content:
                problems.append(name)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
    if problems:
        raise RuntimeError("candidate outputs out of date: " + ", ".join(problems))



def simulate_domain(host: str, files: dict[str, str], *, final_choice: str = "Final",
                    adblock_choice: str = "REJECT") -> dict:
    """Deliberately LIMITED static simulator: domain rules only, no IP DNS/TUN/UA/plugin.

    Consult Loon on-device for ties across matcher classes, IP ASN routing and
    conflicting suffixes. Local profile domain rules are checked before remote
    lists; the explicit candidate remote list order is used within subscriptions.
    """
    host = host.strip(".").lower()
    if not re.fullmatch(r"[a-z0-9.-]+", host) or "." not in host:
        raise ValueError("expected a valid dotted hostname")
    if adblock_choice not in {"REJECT", "DIRECT"}:
        raise ValueError("AdBlock selector must be REJECT or DIRECT")
    config = files["refactor/vnext/LoonKit.vNext.Candidate.lcf"]
    local_rules = config.split("\n[Rule]\n", 1)[1].split("\n[Plugin]", 1)[0].splitlines()
    for raw in local_rules:
        p = [x.strip() for x in raw.split(",")]
        if len(p) < 3 or p[0] not in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
            continue
        if covers_domain(p[0] + "," + p[1], host):
            effective = adblock_choice if p[2] == "AdBlock" else p[2]
            return {"policy": p[2], "effective": effective, "layer": "local",
                    "matched": p[0] + "," + p[1], "simulator": "DOMAIN_ONLY"}
    cfg = load_manifest()
    for group in cfg["subscription_order"]:
        filename = "AnimeCrazy" if group == "動畫瘋" else group
        contents = files["refactor/vnext/generated/" + filename + ".list"]
        for raw in contents.splitlines():
            if raw and not raw.startswith("#") and covers_domain(raw, host):
                policy = "DIRECT" if group in {"ChinaDirect", "DomesticCore", "SteamCN", "AppleOTA"} else group
                effective = adblock_choice if policy == "AdBlock" else policy
                return {"policy": policy, "effective": effective, "layer": "remote",
                        "matched": raw, "simulator": "DOMAIN_ONLY"}
    return {"policy": "Final", "effective": final_choice, "layer": "final",
            "matched": "FINAL,Final", "simulator": "DOMAIN_ONLY"}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="assert generated files match compiler")
    args = parser.parse_args()
    files = compile_rules()
    write_outputs(files, check=args.check)
    print(json.loads(files["refactor/vnext/reports/diff_summary.json"])["candidate_rule_count"])


if __name__ == "__main__":
    main()
