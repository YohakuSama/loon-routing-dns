#!/usr/bin/env python3
"""Fail-closed, exact-artifact beta→main release preflight; NEVER merges branches.

CI success, observed device tests and source policies must be attached as
separate sanitized evidence. A green preflight only permits a human-reviewed
release PR, never an automated formal publication.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import os
from beta_github import GitHub, REPOSITORY

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT/"docs/BETA_ACCEPTANCE_TEMPLATE.json"
MANIFEST = ROOT/"build/beta_manifest.json"
PROFILE = ROOT/"beta/LoonKit.lcf"
HEX40 = re.compile(r"[a-f0-9]{40}\Z")
FORBIDDEN_KEYS = {
    "raw_url", "full_url", "access_token", "token", "password", "private_key",
    "subscriber_id", "device_id", "udid", "imei", "private_dns_url", "raw_har",
    "dns_token", "node_password", "account_id",
}


def load(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("evidence and manifest must be JSON objects")
    return obj


def _date(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("UTC timestamp must end with Z")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _check_private_keys(obj, problems, prefix=""):
    if isinstance(obj, dict):
        for key, item in obj.items():
            if key.lower() in FORBIDDEN_KEYS:
                problems.append("private raw field prohibited: " + prefix + key)
            _check_private_keys(item, problems, prefix + key + ".")
    elif isinstance(obj, list):
        for item in obj:
            _check_private_keys(item, problems, prefix)


def assess(manifest: dict, evidence: dict, profile: bytes,
           expected_cases: dict, expected_risks: dict) -> dict:
    problems = []
    if manifest.get("channel") != "beta" or manifest.get("acceptance", {}).get("promotion") != "BLOCKED":
        problems.append("candidate manifest gate state altered unexpectedly")
    if hashlib.sha256(profile).hexdigest() != manifest.get("configuration_sha256"):
        problems.append("profile checksum differs from versioned manifest")
    if evidence.get("schema_version") != 1 or evidence.get("status") != "VERIFIED_DEVICE_OBSERVATIONS":
        problems.append("evidence remains a template or wrong schema")
    for key in ("version", "configuration_sha256"):
        if evidence.get(key) != manifest.get(key):
            problems.append("candidate " + key + " is not identical to test evidence")
    sha = evidence.get("commit_sha")
    if not isinstance(sha, str) or not HEX40.fullmatch(sha):
        problems.append("missing exact tested beta commit SHA")
    if evidence.get("rollback_commit_sha") != manifest.get("production_baseline"):
        problems.append("rollback pointer differs from published baseline")
    ci = evidence.get("ci")
    if not isinstance(ci, dict) or ci.get("workflow") != "LoonKit Beta CI" or (
        ci.get("commit_sha") != sha or ci.get("conclusion") != "success"
    ):
        problems.append("CI was not passed for the exact tested SHA")
    if not isinstance(ci, dict) or not re.fullmatch(
        r"https://github\.com/YohakuSama/loonkit/actions/runs/[0-9]+",
        str(ci.get("run_url", "")),
    ):
        problems.append("GitHub Actions run URL is missing or not within this repository")
    try:
        begin = _date(evidence.get("observation_started_utc"))
        end = _date(evidence.get("observation_finished_utc"))
        if end <= begin or (end - begin).total_seconds() < 7 * 86400:
            problems.append("first structural beta observation shorter than seven days")
        if end > datetime.now(timezone.utc) or begin > datetime.now(timezone.utc):
            problems.append("future timestamps cannot count as completed device observation")
    except (TypeError, ValueError, OverflowError):
        problems.append("required UTC observation dates missing or malformed")
    results = evidence.get("device_cases", {})
    if not isinstance(results, dict) or set(results) != set(expected_cases):
        problems.append("device matrix lacks exact required case IDs")
    else:
        for case in expected_cases:
            if results[case] != "PASS":
                problems.append("unverified device case: " + case)
    risks = evidence.get("risk_reviews", {})
    if not isinstance(risks, dict) or set(risks) != set(expected_risks):
        problems.append("risk register lacks exact required IDs")
    else:
        for risk in expected_risks:
            if risks[risk] != "RESOLVED_WITH_EVIDENCE":
                problems.append("unresolved source, feature or routing risk: " + risk)
    links = evidence.get("sanitized_evidence_refs", [])
    if not isinstance(links, list) or not links or any(
        not isinstance(s, str) or not s.startswith(("https://github.com/YohakuSama/loonkit/", "docs/"))
        for s in links
    ):
        problems.append("missing sanitized, reviewable evidence references")
    if evidence.get("maintainer_approved") is not True:
        problems.append("maintainer approval missing")
    _check_private_keys(evidence, problems)
    return {
        "candidate_version": manifest.get("version"),
        "configuration_sha256": manifest.get("configuration_sha256"),
        "evaluated_commit": sha if isinstance(sha, str) and HEX40.fullmatch(sha) else None,
        "status": ("PREFLIGHT_READY_REQUIRES_LIVE_GITHUB_APPROVAL_AND_PR"
                   if not problems else "PROMOTION_BLOCKED"),
        "problems": problems,
        "limitations": [
            "This validates supplied evidence fields; it cannot verify that device observations are genuine.",
            "CI run URL and success state require independent live GitHub check for exact SHA.",
            "Promotion itself remains a separately reviewed beta-to-main pull request.",
            "No release branch is updated or merged by this script.",
        ],
    }


def verify_live(result: dict, manifest: dict, evidence: dict, client, promotion_pr: int | None = None) -> dict:
    """Read server state; a forged local CI boolean/URL can never grant release."""
    out = dict(result)
    problems = list(result["problems"])
    if problems:
        out["live_status"] = "NOT_CHECKED_OFFLINE_GATE_BLOCKED"
        return out
    sha = result["evaluated_commit"]
    run_id = evidence["ci"]["run_url"].rsplit("/", 1)[1]
    run = client.get("/actions/runs/" + run_id)
    if not run or any((run.get("head_sha") != sha, run.get("conclusion") != "success",
                       run.get("status") != "completed", run.get("name") != "LoonKit Beta CI",
                       run.get("repository", {}).get("full_name") != REPOSITORY,
                       run.get("head_repository", {}).get("full_name") != REPOSITORY,
                       run.get("path", "").split("@")[0] != ".github/workflows/beta-ci.yml")):
        problems.append("live GitHub run does not prove exact repository, beta workflow and successful tested SHA")
    if run:
        jobs = client.get("/actions/runs/" + run_id + "/jobs?per_page=100") or {}
        if not any(j.get("name") == "beta" and j.get("conclusion") == "success" and j.get("status") == "completed"
                   for j in jobs.get("jobs", [])):
            problems.append("required beta job is absent, skipped or failed")
    head = client.get("/git/ref/heads/beta")
    if not head or head["object"]["sha"] != sha:
        problems.append("beta head moved since the tested commit")
    remote_profile = client.file("beta/LoonKit.lcf", sha)
    remote_manifest = json.loads(client.file("build/beta_manifest.json", sha))
    if hashlib.sha256(remote_profile).hexdigest() != manifest["configuration_sha256"]:
        problems.append("tested GitHub profile bytes differ from local candidate")
    for key in ("version", "configuration_sha256", "overlay_rules", "china_direct", "adblock", "upstream_overlays", "production_baseline"):
        if remote_manifest.get(key) != manifest.get(key):
            problems.append("tested GitHub manifest differs: " + key)
    if promotion_pr is None:
        problems.append("a distinct live beta-to-main promotion PR is required")
    else:
        pr = client.get("/pulls/" + str(promotion_pr))
        if not pr or pr.get("state") != "open" or pr.get("draft") is not False or (
            pr.get("head", {}).get("ref") != "beta" or pr.get("head", {}).get("sha") != sha
            or pr.get("base", {}).get("ref") != "main"
            or pr.get("mergeable_state") != "clean"
        ):
            problems.append("live promotion PR is stale, draft, blocked or not beta-to-main")
    out["problems"] = problems
    out["status"] = "PROMOTION_BLOCKED" if problems else "LIVE_PREFLIGHT_READY_FOR_PROTECTED_MERGE"
    out["live_status"] = "VERIFIED_AGAINST_GITHUB"
    return out


def check(evidence_path: Path):
    manifest = load(MANIFEST)
    template = load(TEMPLATE)
    evidence = load(evidence_path)
    return assess(manifest, evidence, PROFILE.read_bytes(),
                  template["device_cases"], template["risk_reviews"])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", type=Path, default=TEMPLATE)
    p.add_argument("--assert-template-blocked", action="store_true")
    p.add_argument("--live", action="store_true")
    p.add_argument("--promotion-pr", type=int)
    opts = p.parse_args()
    result = check(opts.evidence)
    if opts.live:
        result = verify_live(result, load(MANIFEST), load(opts.evidence),
                             GitHub(os.environ.get("GITHUB_TOKEN", "")), opts.promotion_pr)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if opts.assert_template_blocked:
        if opts.evidence.resolve() != TEMPLATE.resolve() or result["status"] != "PROMOTION_BLOCKED":
            raise SystemExit("current template must remain blocked")
    elif result["status"] not in {"PREFLIGHT_READY_REQUIRES_LIVE_GITHUB_APPROVAL_AND_PR", "LIVE_PREFLIGHT_READY_FOR_PROTECTED_MERGE"}:
        raise SystemExit(1)
