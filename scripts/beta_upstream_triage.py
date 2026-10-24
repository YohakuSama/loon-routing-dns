#!/usr/bin/env python3
"""Strict upstream delta risk triage. No automatic deployment or token usage.

Consumes the *actual* beta_upstream_candidate review artifact (87 registered
sources, complete snapshots, full delta and per-rule source provenance) and
emits low-risk DRAFT-PR ELIGIBILITY or elevated human-review decisions.
Eligibility never approves a rule, updates beta, or authorizes main release.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

DIRECT = {"ChinaDirect", "DomesticCore", "SteamCN", "AppleOTA"}
RESTRICTED = DIRECT | {"AdBlock", "AI", "Apple", "Microsoft", "Paypal"}
LOW_RISK_OWNERS = {"YouTube", "Netflix", "Disney", "PrimeVideo", "TikTok",
                   "Bilibili", "Telegram", "Whatsapp", "Instagram", "Facebook",
                   "Twitter", "Discord", "Google", "Steam", "HBO", "Dazn", "動畫瘋"}
DOMAIN = re.compile(r"DOMAIN,([a-z0-9-]+\.)+[a-z0-9-]+\Z")
SHA = re.compile(r"[a-f0-9]{64}\Z")
SHARED = (
    "googleapis.com", "apis.google.com", "appspot.com", "cloudfront.net", "akamaihd.net",
    "akamaized.net", "fastly.net", "windows.net", "blob.core.windows.net",
    "amazonaws.com", "github.io", "pages.dev", "workers.dev", "vercel.app",
    "stripe.com", "auth0.com", "microsoftonline.com", "icloud.com",
    "apple.com", "paypal.com", "recaptcha.net", "gstatic.com",
    "livekit.cloud", "twilio.com", "githubusercontent.com",
)
MAX_GROUP_ADD = 10
MAX_TOTAL_ADD = 30


def _covered(host, parent):
    return host == parent or host.endswith("." + parent)


def evaluate(manifest: dict, diff: dict, risk: dict) -> dict:
    source_rows = manifest.get("source_snapshots", [])
    valid_sources = isinstance(source_rows, list) and all(
        isinstance(s, dict) and isinstance(s.get("id"), str)
        for s in source_rows
    )
    source_by_id = {s["id"]: s for s in source_rows} if valid_sources else {}
    complete = (bool(manifest.get("global_source_integrity_complete"))
                and manifest.get("publication_allowed") is False
                and manifest.get("branch_push_allowed") is False
                and valid_sources
                and len(source_rows) == manifest.get("source_count") == len(source_by_id)
                and all(s.get("status") == "PARSED_FOR_REVIEW"
                        and isinstance(s.get("sha256"), str)
                        and SHA.fullmatch(s["sha256"]) for s in source_rows))
    groups = manifest.get("groups", {})
    if not isinstance(groups, dict) or not groups or set(groups) != set(diff) or set(groups) != set(risk):
        raise ValueError("complete candidate manifest/diff/risk groups required")
    output = {}
    eligible_total = 0
    for group, info in sorted(groups.items()):
        adds = diff[group].get("added", [])
        removes = diff[group].get("removed", [])
        entries = risk[group].get("additions", [])
        mapped = {entry["rule"]: entry for entry in entries}
        if (not isinstance(adds, list) or not isinstance(removes, list)
                or not isinstance(entries, list)
                or len(mapped) != len(entries) or len(set(adds)) != len(adds)):
            raise ValueError("bad or duplicated full risk delta for " + group)
        reasons = set()
        if not complete:
            reasons.add("SOURCE_INCOMPLETE_OR_EXCLUSIONS")
        if group not in LOW_RISK_OWNERS or group in RESTRICTED:
            reasons.add("SENSITIVE_OR_DIRECT_OWNER_REVIEW")
        if info.get("status") not in {"UNCHANGED", "ROUTINE_CANDIDATE_REVIEW"}:
            reasons.add("CANDIDATE_FLAGGED_HIGH_RISK_OR_INCOMPLETE")
        if removes:
            reasons.add("REMOVALS_NEVER_AUTOMATED")
        if not adds and not removes:
            output[group] = {"status": "UNCHANGED" if complete else "SOURCE_BLOCKED",
                             "added": 0, "removed": 0, "reasons": sorted(reasons)}
            continue
        before = info.get("baseline_count", 0)
        limit = min(MAX_GROUP_ADD, max(1, int(before * 0.01)))
        if len(adds) > limit:
            reasons.add("ADDITIONS_TOO_LARGE_FOR_ROUTINE_REVIEW")
        for value in adds:
            row = mapped.get(value)
            if not DOMAIN.fullmatch(value):
                reasons.add("NON_EXACT_DOMAIN_MATCHER")
                continue
            host = value.split(",", 1)[1]
            if any(_covered(host, s) for s in SHARED):
                reasons.add("SHARED_MULTI_TENANT_OR_CRITICAL_ROOT")
            if row is None:
                reasons.add("RISK_OR_PROVENANCE_MISSING")
                continue
            if row.get("review_tier") != "STANDARD" or row.get("other_groups"):
                reasons.add("ELEVATED_OR_CROSS_POLICY_COLLISION")
            provenance = row.get("source_ids", [])
            if not provenance or any(s not in source_by_id for s in provenance):
                reasons.add("UNKNOWN_SOURCE_PROVENANCE")
        if eligible_total + len(adds) > MAX_TOTAL_ADD:
            reasons.add("TOTAL_CHANGED_RULE_LIMIT")
        if not reasons:
            eligible_total += len(adds)
        output[group] = {
            "status": "LOW_RISK_DRAFT_PR_ELIGIBLE_REVIEW_REQUIRED" if not reasons else "MANUAL_RISK_REVIEW",
            "added": len(adds), "removed": len(removes),
            "routine_cap": limit, "reasons": sorted(reasons),
        }
    return {
        "schema_version": 1, "source_integrity_complete": complete,
        "candidate_version": manifest.get("version"),
        "status": "REVIEW_ONLY_NEVER_AUTO_MERGE",
        "draft_eligible_added_rules": eligible_total,
        "groups": output,
        "publication_allowed": False,
        "requires_immutable_asset_commit_and_exact_beta_profile": True,
        "requires_human_merge_and_license_review": True,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    base = args.candidate.resolve()
    if args.output.resolve().is_relative_to(Path(__file__).resolve().parents[1]):
        raise ValueError("risk reports must be outside repository")
    manifest = json.loads((base/"BETA_UPSTREAM_MANIFEST.json").read_text(encoding="utf-8"))
    diff = json.loads((base/"evidence/FULL_DIFF.json").read_text(encoding="utf-8"))
    risk = json.loads((base/"evidence/FULL_RISK_AUDIT.json").read_text(encoding="utf-8"))
    result = evaluate(manifest, diff, risk)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2,
                                      sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "source_integrity_complete": result["source_integrity_complete"],
        "draft_eligible_added_rules": result["draft_eligible_added_rules"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
