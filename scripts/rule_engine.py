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
from source_lock import check_lock

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "build"
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
        if not (relative.startswith("rules/inputs/") or relative.startswith("rules/custom/")
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
    cfg = load_manifest(root / "build/engine_manifest.json")
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
        path = root / "rules/inputs" / (filename + ".list")
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
        files["build/generated/" + filename + ".list"] = "\n".join(
            [*header, *sorted(groups[group])]
        ) + "\n"
    return files


if __name__ == "__main__":
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument('--check',action='store_true',required=True)
    a.parse_args()
    from verify_release import verify
    verify()
