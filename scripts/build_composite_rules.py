#!/usr/bin/env python3
"""Stage Loon-native rule lists from reviewed sources. Standard library only.

Outputs never modify the active LoonKit.lcf. Publishing/activation
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
GUARDRAILS = ROOT / "rules" / "routing_guardrails.json"


def protected_domains(config_path=GUARDRAILS):
    """Load explicit keep-out domains, shared by generator and regression tests."""
    data = json.loads(Path(config_path).read_text(encoding="utf-8"))
    domains = data["protected_proxy_domains"]
    if not isinstance(domains, list) or len(domains) < 5:
        raise ValueError("routing guardrails must protect at least five diagnostic domains")
    for d in domains:
        if not isinstance(d, str) or not re.fullmatch(r"[a-z0-9.-]+", d) or "." not in d:
            raise ValueError("invalid protected domain in routing guardrails: " + str(d))
    if len(domains) != len(set(domains)):
        raise ValueError("duplicate protected proxy domain in guardrails")
    return tuple(domains)


def direct_rule_matches_protected_domain(rule, domains=None):
    """Return a domain accidentally covered by a DIRECT rule, or None."""
    if domains is None:
        domains = protected_domains()
    kind, _, value = rule.partition(",")
    for domain in domains:
        if kind == "DOMAIN" and value == domain:
            return domain
        if kind == "DOMAIN-SUFFIX" and (domain == value or domain.endswith("." + value)):
            return domain
        if kind == "DOMAIN-KEYWORD" and value and value in domain:
            return domain
    return None

ALLOWED_TYPES = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "IP-CIDR",
    "IP-CIDR6", "IP-ASN", "USER-AGENT",
}
DOMAIN_RE = re.compile(r"^[a-z0-9*._-]+$", re.I)
GROUP_NAMES = {"動畫瘋": "AnimeCrazy"}
MAX_FILE_BYTES = 35_000_000
# Subscription order in the release profile. Exact cross-policy duplicates
# are owned by the earlier group; lower-priority copies cannot win at runtime.
PUBLISH_ORDER = (
    "DomesticCore", "AI", "AppleOTA", "SteamCN", "YouTube",
    "Netflix", "Disney", "PrimeVideo", "Spotify", "TikTok",
    "Twitch", "HBO", "Abema", "BBC", "Bilibili", "動畫瘋", "Dazn",
    "Telegram", "Whatsapp", "Instagram", "Facebook", "Twitter",
    "Discord", "Line", "Reddit", "Linkedin", "Google", "Microsoft",
    "Apple", "Steam", "Paypal", "AdBlock", "ChinaDirect",
)
# Advert/privacy safety: these selectors are excessively broad for an
# always-on blocker; precise domains/suffixes remain enabled.
ADBLOCK_ALLOWED = {"DOMAIN", "DOMAIN-SUFFIX"}
# Shared authentication/payment/telemetry providers must not route unrelated
# applications through a region-specific AI group. Keep AI-specific hosts.
AI_SHARED_ROOTS = {
    "algolia.net", "auth0.com", "identrust.com", "intercom.io",
    "intercomcdn.com", "launchdarkly.com", "observeit.net",
    "segment.io", "sentry.io", "stripe.com",
}
AI_SHARED_HOSTS = {"static.cloudflareinsights.com"}


def excluded_ai_rule(rule):
    kind, _, value = rule.partition(",")
    if kind == "IP-ASN":
        return "AI broad ASN omitted"
    if kind in {"DOMAIN", "DOMAIN-SUFFIX"} and (
        value in AI_SHARED_ROOTS or value in AI_SHARED_HOSTS
    ):
        return "AI shared-provider root omitted"
    return None
SOURCE_URL_PREFIXES = (
    "/blackmatrix7/ios_rule_script/",
    "/v2fly/domain-list-community/",
    "/felixonmars/dnsmasq-china-list/",
)


def normalize(text, source_format="loon", source=None):
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

    if source_format == "v2fly":
        # Inline domain annotations may contain human-readable # comments.
        line = line.split("#", 1)[0].strip()
        if not line:
            return None, None
        # Domain-list-community: plain=domain suffix, full:=DOMAIN,
        # keyword:=DOMAIN-KEYWORD. Includes must be explicitly registered
        # rather than expanding a large unrelated parent category.
        parts = line.split()
        if not parts:
            return None, None
        token, attrs = parts[0], parts[1:]
        if token.startswith("include:"):
            return None, "v2fly include not expanded (explicit sources only)"
        if token.startswith("regexp:"):
            return None, "v2fly regexp excluded (manual review)"
        if any(not attr.startswith("@") for attr in attrs):
            return None, "v2fly unrecognized annotation"
        skip = set(source.get("skip_attrs", [])) if source else set()
        tags = {a[1:] for a in attrs}
        if skip.intersection(tags):
            return None, None
        # Never silently route explicit CN content through international
        # proxy policy, even if an upstream source changes its annotations.
        if "cn" in tags and source and source.get("policy") != "DIRECT":
            return None, None
        if token.startswith("full:"):
            kind, value = "DOMAIN", token[5:]
        elif token.startswith("keyword:"):
            kind, value = "DOMAIN-KEYWORD", token[8:]
        elif ":" in token:
            return None, "v2fly unsupported token"
        else:
            kind, value = "DOMAIN-SUFFIX", token
        if not value or not DOMAIN_RE.fullmatch(value):
            return None, "v2fly invalid domain"
        return kind + "," + value.lower().rstrip("."), None

    if source_format == "dnsmasq":
        m = re.fullmatch(r"server=/([^/]+)/[^/]+", line)
        if not m:
            return None, "dnsmasq unsupported syntax"
        value = m.group(1).lower().rstrip(".")
        if not DOMAIN_RE.fullmatch(value):
            return None, "dnsmasq invalid domain"
        return "DOMAIN-SUFFIX," + value, None

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
    flags = chunks[2:]
    if flags and (kind not in {"IP-CIDR", "IP-CIDR6", "IP-ASN"}
                  or len(flags) != 1 or flags[0].lower() != "no-resolve"):
        return None, "unexpected trailing fields"
    if kind.startswith("IP-CIDR"):
        try:
            network = ipaddress.ip_network(value, strict=False)
        except ValueError:
            return None, "invalid IP network"
        if (network.version == 6) != (kind == "IP-CIDR6"):
            return None, "IP family mismatch"
        value = str(network)
    if kind == "IP-ASN":
        value = value.upper()
        if not re.fullmatch(r"(AS)?\d+", value):
            return None, "invalid ASN"
        value = value.removeprefix("AS")
    # Loon profile compatibility: CIDR matching must not trigger preliminary
    # DNS resolution. Always add no-resolve for both IP families, regardless
    # of whether an upstream rule supplies the flag. This behavior has been
    # tested by the project maintainer and must not be changed implicitly.
    no_resolve = kind in {"IP-CIDR", "IP-CIDR6"} or bool(flags)
    return kind + "," + value + (",no-resolve" if no_resolve else ""), None


def read_catalog(path=CATALOG):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    sources = [s for s in data["sources"] if s.get("enabled")]
    if len({s["id"] for s in sources}) != len(sources):
        raise ValueError("duplicate source ids")
    group_policies = {}
    for s in sources:
        if s["group"] in group_policies and group_policies[s["group"]] != s["policy"]:
            raise ValueError("conflicting policies within group: " + s["group"])
        group_policies[s["group"]] = s["policy"]
        if s.get("role") == "local":
            path = s.get("path", "")
            if not re.fullmatch(r"rules/custom/[A-Za-z0-9_-]+\.list", path):
                raise ValueError("invalid custom rule file path: " + path)
            if not (ROOT / path).is_file():
                raise ValueError("missing original custom rules: " + path)
        else:
            url = urlparse(s["url"])
            if (url.scheme != "https" or url.netloc != "raw.githubusercontent.com"
                    or not url.path.startswith(SOURCE_URL_PREFIXES)) :
                raise ValueError("unreviewed source URL: " + s["url"])
        if not re.fullmatch(r"[\w\u4e00-\u9fff-]+", s["group"]):
            raise ValueError("unsafe output group: " + s["group"])
        if s["format"] not in {"loon", "domainset", "v2fly", "dnsmasq"}:
            raise ValueError("unknown source format")
    return sources


def fetch_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": "LoonCompositeAudit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        blob = resp.read(MAX_FILE_BYTES + 1)
    if len(blob) > MAX_FILE_BYTES:
        raise ValueError("source exceeds maximum byte limit: " + url)
    return blob.decode("utf-8-sig")


def prune_suffix_redundancy(rules):
    """Prune only a DOMAIN/DOMAIN-SUFFIX covered by a same-group suffix."""
    suffixes = {r[14:] for r in rules if r.startswith("DOMAIN-SUFFIX,")}
    result = set()
    dropped = 0
    for rule in rules:
        kind, _, val = rule.partition(",")
        if kind not in {"DOMAIN", "DOMAIN-SUFFIX"}:
            result.add(rule)
            continue
        labels = val.split(".")
        if kind == "DOMAIN" and val in suffixes:
            dropped += 1
            continue
        if any(".".join(labels[i:]) in suffixes for i in range(1, len(labels))):
            dropped += 1
            continue
        result.add(rule)
    return result, dropped


def own_cross_group_duplicates(by_group):
    """Keep exact matches in only the first ordered policy group."""
    # Tests may use partial toy groups; real catalog is checked independently
    # against the production configuration by test_hybrid_profile.py.
    order = [g for g in PUBLISH_ORDER if g in by_group]
    order += sorted(set(by_group) - set(PUBLISH_ORDER))
    seen = {}
    removed = []
    for group in order:
        for rule in list(by_group[group]):
            if rule in seen:
                removed.append({"rule": rule, "kept_in": seen[rule], "removed_from": group})
                del by_group[group][rule]
            else:
                seen[rule] = group
    return removed


def generate(sources, fetch=fetch_text):
    by_group = defaultdict(dict)
    owners = defaultdict(set)
    source_stats = []
    quarantined = defaultdict(int)
    quarantined_examples = []
    intra_dupes = 0
    protected = protected_domains()
    guarded_direct = []
    for s in sources:
        body = ((ROOT / s["path"]).read_text(encoding="utf-8")
                if s.get("role") == "local" else fetch(s["url"]))
        parsed = 0
        deduped = 0
        source_rules = set()
        for number, raw in enumerate(body.splitlines(), 1):
            rule, reason = normalize(raw, s["format"], source=s)
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
            kind = rule.split(",", 1)[0]
            # Block precise ad/tracker domains, not all IPs sharing a CDN or
            # generic keyword like "analytics." (frequent login failures).
            if s["group"] == "AdBlock" and kind not in ADBLOCK_ALLOWED:
                quarantined["adblock broad matcher omitted: " + kind] += 1
                continue
            if s["policy"] == "DIRECT":
                protected_hit = direct_rule_matches_protected_domain(rule, protected)
                if protected_hit:
                    quarantined["protected diagnostic domain would route DIRECT"] += 1
                    guarded_direct.append({
                        "source": s["id"], "group": s["group"], "line": number,
                        "rule": rule, "protected_domain": protected_hit,
                    })
                    continue
            if s["group"] == "AI":
                reason = excluded_ai_rule(rule)
                if reason:
                    quarantined[reason] += 1
                    continue
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

    # Expected safety exclusions are recorded; unexpected grammar blocks release.
    allowed_quarantine = {
        "URL-REGEX excluded (may require MITM; separate review)",
        "v2fly include not expanded (explicit sources only)",
        "v2fly regexp excluded (manual review)",
        "AI broad ASN omitted",
        "AI shared-provider root omitted",
        "protected diagnostic domain would route DIRECT",
    }
    unexpected = {reason: count for reason, count in quarantined.items()
                  if reason not in allowed_quarantine
                  and not reason.startswith("adblock broad matcher omitted: ")}
    if unexpected:
        raise ValueError("unsupported/invalid upstream rules need manual review: " + str(unexpected))

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

    # If upstream introduces a new coverage form, do not silently publish it.
    # Domain and suffix variants are blocked before grouping; checked again below.
    for group, rules in by_group.items():
        policies = {s["policy"] for s in sources if s["group"] == group}
        if "DIRECT" in policies:
            for rule in rules:
                covered = direct_rule_matches_protected_domain(rule, protected)
                if covered:
                    raise ValueError(f"{group} would direct-route protected {covered}: {rule}")

    # Canonicalize output after gathering full provenance and conflict samples.
    suffix_pruned = {}
    for group, rules in by_group.items():
        clean, count = prune_suffix_redundancy(rules)
        suffix_pruned[group] = count
        by_group[group] = {k: rules[k] for k in clean}
    cross_pruned = own_cross_group_duplicates(by_group)

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
        "status": "STAGED_CANDIDATE",
        "sources": source_stats,
        "group_sizes": {k: len(v) for k, v in sorted(by_group.items())},
        "duplicates_removed_within_group": intra_dupes,
        "same_group_suffix_shadow_pruned": suffix_pruned,
        "cross_group_exact_pruned_count": len(cross_pruned),
        "cross_group_exact_pruned_samples": cross_pruned[:100],
        "cross_group_same_policy_repeated": same_policy_reused,
        "cross_group_different_policy_exact": exact_different_policy_count,
        "cross_group_different_policy_samples": exact_conflicts,
        "domain_suffix_ancestor_conflict_count": ancestor_conflict_count,
        "domain_suffix_ancestor_conflict_samples": ancestor_conflicts,
        "quarantined_by_reason": dict(sorted(quarantined.items())),
        "routing_guardrails": {
            "protected_proxy_domains": list(protected),
            "direct_rules_removed": guarded_direct,
            "active_profile": "NOT_ENABLED_BY_DEFAULT",
        },
        "quarantined_examples": quarantined_examples,
        "notes": [
            "Exact cross-group duplicates retained only in the first published group.",
            "IP-CIDR and IP-CIDR6 always use no-resolve to preserve the project's tested DNS match ordering.",
            "Per-group suffix shadows removed only when same routing policy covers them.",
            "Ad/Privacy uses domain and domain-suffix, excludes keyword/IP/shared-CDN blockers.",
            "Different-policy and ancestor conflicts require a routing priority review.",
            "Local [Rule] in Loon takes precedence over remote lists.",
            "Freshly generated lists are candidates until PR review; approved main snapshots may be active.",
            "Protected diagnostic domains cannot be direct-routed by any generated DIRECT group.",
            "Audit conflict counts are visibility metrics, not proof that all routing conflicts are resolved.",
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
    # Prune obsolete generated groups (e.g. a dedicated per-app rule group
    # folded into a shared domestic DIRECT list). Never touch custom sources.
    for old_list in dest.glob("*.list"):
        if old_list.name not in outputs:
            old_list.unlink()
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
