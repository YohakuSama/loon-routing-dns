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

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "refactor" / "vnext"
GENERATED = BASE / "generated"
REPORTS = BASE / "reports"
MANIFEST = BASE / "engine_manifest.json"
SNAP = ROOT / "rules" / "generated"
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


def filter_rule(group: str, rule: str, protected: tuple[str, ...]) -> tuple[str | None, str | None, str]:
    kind, value = fields(rule)
    if group in {"ChinaDirect", "DomesticCore", "SteamCN", "AppleOTA"}:
        if any(covers_domain(rule, x) for x in protected):
            return None, "DIRECT_PROTECTED_DOMAIN", "FINAL (policy-dependent)"
        if group == "ChinaDirect":
            if kind == "DOMAIN-KEYWORD":
                if value == ".tmall.com":
                    return "DOMAIN-SUFFIX,tmall.com", "DIRECT_KEYWORD_NARROWED", "DIRECT (scoped suffix)"
                return None, "DIRECT_KEYWORD_UNPROVEN", "GEOIP CN or FINAL"
            if kind == "DOMAIN-SUFFIX" and "." not in value and value != "cn":
                return None, "DIRECT_SINGLE_LABEL_UNPROVEN", "GEOIP CN or FINAL"
            if kind in {"IP-CIDR", "IP-CIDR6"}:
                net = ipaddress.ip_network(value)
                # Do not assume broad upstream AS/range ownership establishes mainland DIRECT.
                minimum = 24 if net.version == 4 else 48
                if net.prefixlen < minimum:
                    return None, "DIRECT_WIDE_IP_UNPROVEN", "GEOIP CN for IP destinations or FINAL"
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


def compile_rules(root: Path = ROOT) -> dict[str, str]:
    cfg = load_manifest(root / "refactor/vnext/engine_manifest.json")
    active, inactive = cfg["active_groups"], cfg["inactive_groups"]
    guardrails = json.loads((root / "rules/routing_guardrails.json").read_text(encoding="utf-8"))
    protected = tuple(guardrails["protected_proxy_domains"])
    groups: dict[str, dict[str, set[tuple[str, int]]]] = {g: defaultdict(set) for g in active}
    trace: list[dict] = []
    before, reasons = Counter(), Counter()
    raw_total = 0
    old_rules_by_group: dict[str, set[str]] = {}
    source_catalog = json.loads((root / "rules/sources.json").read_text(encoding="utf-8"))["sources"]
    source_groups = defaultdict(list)
    for s in source_catalog:
        source_groups[s["group"]].append(s["id"])
    for group in active + inactive:
        filename = "AnimeCrazy" if group == "動畫瘋" else group
        path = root / "rules/generated" / (filename + ".list")
        if not path.is_file():
            raise FileNotFoundError(path)
        old_set = set()
        for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            rule = normalize(raw)
            if not rule:
                continue
            raw_total += 1
            before[group] += 1
            old_set.add(rule)
            origin = path.relative_to(root).as_posix()
            if group in inactive:
                reason, replacement, outcome = "SOURCE_DISABLED", "FINAL", None
            else:
                outcome, reason, replacement = filter_rule(group, rule, protected)
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
    # Explicit advertising classification, with reviewable virtual provenance.
    for domain in AD_ANCHORS:
        rule = "DOMAIN-SUFFIX," + domain
        if rule not in groups["AdBlock"]:
            groups["AdBlock"][rule].add(("refactor/vnext/engine_manifest.json", 0))
    choose_exact_owners(groups, trace, active)
    # Drop within-group DOMAIN covered by suffix only if not explicitly contested.
    for group, records in groups.items():
        suffixes = {fields(r)[1] for r in records if r.startswith("DOMAIN-SUFFIX,")}
        for rule in list(records):
            kind, value = fields(rule)
            if kind == "DOMAIN" and any(is_covered(value, suffix) for suffix in suffixes):
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
    files["refactor/vnext/reports/added.jsonl"] = "".join(
        json.dumps({"group": g, "rule": r, "reason": "NEW_OR_RECLASSIFIED"},
                   ensure_ascii=False, sort_keys=True) + "\n" for g, r in added)
    report = {
        "status": "OFFLINE_CANDIDATE_NOT_DEVICE_VERIFIED",
        "baseline_rule_count_stage03": 206505,
        "baseline_count_from_selected_snapshot_groups": raw_total,
        "candidate_rule_count": new_total,
        "baseline_upstream_source_count": len(source_catalog),
        "candidate_frozen_snapshot_input_count": len(active),
        "source_count_comparison_warning": "87 upstream feeds vs active group snapshots are NOT equivalent provenance units",
        "active_groups": active, "inactive_groups_fall_through_final": inactive,
        "before_groups": dict(sorted(before.items())), "after_groups": result,
        "added_predicate_group_count": len(added), "removed_predicate_group_count": len(removed),
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
    profile = (root / "LoonKit.lcf").read_text(encoding="utf-8")
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="assert generated files match compiler")
    args = parser.parse_args()
    files = compile_rules()
    write_outputs(files, check=args.check)
    print(json.loads(files["refactor/vnext/reports/diff_summary.json"])["candidate_rule_count"])


if __name__ == "__main__":
    main()
