#!/usr/bin/env python3
"""Read-only live checks for the precise beta.4 -> release branch -> main model.

A one-time version-scoped owner decision may replace the observation gate.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from beta_github import GitHub, REPOSITORY
from beta_promotion_gate import assess, load

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "adc567168eed8e21dc8d80aebc40b85f35fc1a1b"
SOURCE_HASH = "fd1a01c6f8363a5dffaa1db9dbf044014c711fa48ea46e34a7c107180acbe0b7"
BASE = "62dcaa273ebff92176b510186f7b73ea994e72b6"
HEAD_BRANCH = "release/v6.5.5-beta4-reviewed-20261024"
TEMPLATE = ROOT/"docs/BETA_ACCEPTANCE_TEMPLATE.json"
HEX = re.compile(r"[a-f0-9]{40}\Z")


def one_time_approval(root: Path = ROOT) -> bool:
    """Verify the exact owner-authorized release; never permit future versions."""
    doc = root / "docs/RELEASE_OWNER_DECISION_v6.5.5.json"
    if not doc.is_file():
        return False
    d = load(doc)
    s = d.get("scope", {})
    return (d.get("schema_version") == 1
            and d.get("decision") == "OWNER_APPROVED_ONE_TIME_RELEASE"
            and d.get("owner_decision_received") == "2026-10-24"
            and d.get("observed_seven_days") == "NOT_PROVIDED"
            and d.get("device_case_matrix") == "NOT_PROVIDED"
            and d.get("apply_to_future_versions") is False
            and d.get("require_green_actual_pr_head_ci") is True
            and d.get("require_real_merge_and_postmerge_verification") is True
            and s == {
                "release_version": "v6.5.5",
                "release_profile_sha256": "d97984a42e313e5b4fc81c26ce760fd4d1163275ad7278e3930cbce69dcf9f03",
                "beta_version": "v6.5.5-beta.4",
                "beta_commit": SOURCE,
                "beta_profile_sha256": SOURCE_HASH,
                "resource_commit": "1b54e079486a06a5cfff5c5f03016628a52a7701",
                "rollback_main_commit": BASE,
                "promotion_pr": 119,
                "base_branch": "main",
                "beta_ci_run": "https://github.com/YohakuSama/loonkit/actions/runs/40093753299",
            })


def offline(evidence_path: Path = TEMPLATE, root: Path = ROOT, *, owner_override: bool = False) -> dict:
    evidence = load(evidence_path)
    template = load(root/"docs/BETA_ACCEPTANCE_TEMPLATE.json")
    beta = load(root/"build/beta_manifest.json")
    stable = load(root/"build/release_manifest.json")
    spec = load(root/"build/release_spec.json")
    result = assess(beta, evidence, (root/"beta/LoonKit.lcf").read_bytes(),
                    template["device_cases"], template["risk_reviews"])
    problems = list(result["problems"])
    identity_bad = any((beta.get("configuration_sha256") != SOURCE_HASH,
            beta.get("candidate_source_commit") != "1b54e079486a06a5cfff5c5f03016628a52a7701",
            stable.get("promoted_beta_config_sha256") != SOURCE_HASH,
            stable.get("promoted_beta_commit_sha") != SOURCE,
            stable.get("publication", {}).get("rollback_main_commit_sha") != BASE,
            stable.get("label") != "v6.5.5",
            spec.get("promoted_candidate_commit") != SOURCE,
            hashlib.sha256((root/"LoonKit.lcf").read_bytes()).hexdigest() !=
                stable.get("profile_sha256", {}).get("LoonKit.lcf")))
    if identity_bad:
        problems.append("formal release identity, rollback or source hash differs from tested beta")
    if evidence.get("commit_sha") != SOURCE:
        problems.append("device evidence does not identify the exact tested beta commit")
    if owner_override:
        if not identity_bad and one_time_approval(root):
            problems = []
            result["evidence_mode"] = "SCOPED_OWNER_DECISION_NOT_DEVICE_ATTESTATION"
        else:
            problems.append("owner decision or exact candidate identity invalid")
    result["problems"] = problems
    result["status"] = "RELEASE_PROMOTION_BLOCKED" if problems else "READY_FOR_LIVE_RELEASE_PR_CHECK"
    result["publication_is_authorized"] = False
    return result


def check_live(result: dict, evidence: dict, stable: dict, client, pr_number: int | None) -> dict:
    """Reject stale PRs, wrong target, wrong commits, and CI from another head."""
    result = dict(result)
    problems = list(result["problems"])
    if problems:
        result.update(status="RELEASE_PROMOTION_BLOCKED", live_status="NOT_RUN_DEVICE_GATE_BLOCKED")
        return result
    if pr_number is None:
        problems.append("independent reviewable release PR required")
    pr = client.get("/pulls/" + str(pr_number)) if pr_number is not None else None
    h = (pr or {}).get("head", {})
    b = (pr or {}).get("base", {})
    sha = h.get("sha")
    if not pr or any((pr.get("state") != "open",pr.get("draft") is not False,
                       h.get("ref") != HEAD_BRANCH, h.get("repo", {}).get("full_name") != REPOSITORY,
                       b.get("ref") != "main",b.get("sha") != BASE,
                       b.get("repo", {}).get("full_name") != REPOSITORY,
                       pr.get("mergeable_state") != "clean",
                       not isinstance(sha, str) or not HEX.fullmatch(sha))):
        problems.append("release PR must be an undrafted clean approved head from the exact release branch into unchanged main")
    base_ref = client.get("/git/ref/heads/main")
    branch_ref = client.get("/git/ref/heads/" + HEAD_BRANCH)
    beta_ref = client.get("/git/ref/heads/beta")
    if not base_ref or base_ref.get("object", {}).get("sha") != BASE:
        problems.append("main has moved since reviewed rollback baseline")
    if not branch_ref or branch_ref.get("object", {}).get("sha") != sha:
        problems.append("release head moved since PR inspection")
    if not beta_ref or beta_ref.get("object", {}).get("sha") != SOURCE:
        problems.append("reviewed candidate no longer equals beta HEAD: freeze and reassess")
    run_id = evidence.get("ci", {}).get("run_url", "").rsplit("/", 1)[-1]
    beta_run = client.get("/actions/runs/" + run_id)
    if not beta_run or any((beta_run.get("head_sha") != SOURCE,
                           beta_run.get("conclusion") != "success",
                           beta_run.get("status") != "completed",
                           beta_run.get("name") != "LoonKit Beta CI",
                           beta_run.get("repository", {}).get("full_name") != REPOSITORY)):
        problems.append("reviewed beta CI is not proven on exact source commit")
    beta_jobs = client.get("/actions/runs/" + run_id + "/jobs?per_page=100") if beta_run else None
    if not beta_jobs or not any(j.get("name") == "beta" and j.get("conclusion") == "success" for j in beta_jobs.get("jobs", [])):
        problems.append("beta run has no successful actual beta job")
    if isinstance(sha, str) and HEX.fullmatch(sha):
        try:
            remote_candidate = client.file("beta/LoonKit.lcf", SOURCE)
            remote_release = client.file("LoonKit.lcf", sha)
            remote_manifest = json.loads(client.file("build/release_manifest.json", sha))
            if hashlib.sha256(remote_candidate).hexdigest() != SOURCE_HASH:
                problems.append("live tested beta bytes differ")
            if any((hashlib.sha256(remote_release).hexdigest() != stable["profile_sha256"]["LoonKit.lcf"],
                    remote_manifest["promoted_beta_config_sha256"] != SOURCE_HASH,
                    remote_manifest["promoted_beta_commit_sha"] != SOURCE,
                    remote_manifest["runtime_resources"] != stable["runtime_resources"])):
                problems.append("release PR profile/manifest differs from reviewed pinned candidate")
        except (ValueError, KeyError, TypeError):
            problems.append("release PR files unavailable or malformed")
    # Explicitly check successful production job at the current PR head,
    # never a green check from a previous commit or another branch.
    runs = client.get("/actions/runs?head_sha=" + str(sha) + "&event=pull_request&per_page=100") or {}
    candidates = [r for r in runs.get("workflow_runs", [])
                  if r.get("name") == "LoonKit Production CI" and r.get("head_sha") == sha
                  and r.get("status") == "completed" and r.get("conclusion") == "success"
                  and r.get("repository", {}).get("full_name") == REPOSITORY]
    verified = False
    for run in candidates:
        jobs = client.get("/actions/runs/" + str(run["id"]) + "/jobs?per_page=100") or {}
        verified = verified or any(j.get("name") == "production" and j.get("conclusion") == "success"
                                    and j.get("head_sha") == sha for j in jobs.get("jobs", []))
    if not verified:
        problems.append("no passing production job for the exact current release PR head")
    result.update(problems=problems, live_status="VERIFIED_AGAINST_GITHUB",
                  status="RELEASE_PROMOTION_BLOCKED" if problems else "LIVE_READY_FOR_PROTECTED_REVIEW",
                  publication_is_authorized=False)
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", type=Path, default=TEMPLATE)
    p.add_argument("--assert-template-blocked", action="store_true")
    p.add_argument("--live", action="store_true")
    p.add_argument("--promotion-pr", type=int)
    p.add_argument("--owner-override", action="store_true")
    args = p.parse_args()
    result = offline(args.evidence, owner_override=args.owner_override)
    evidence = load(args.evidence)
    if args.owner_override and one_time_approval():
        evidence["ci"] = {"run_url": "https://github.com/YohakuSama/loonkit/actions/runs/40093753299"}
    if args.live:
        result = check_live(result, evidence, load(ROOT/"build/release_manifest.json"),
                            GitHub(os.environ.get("GITHUB_TOKEN", "")), args.promotion_pr)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    if args.assert_template_blocked:
        if args.evidence.resolve() != TEMPLATE.resolve() or result["status"] != "RELEASE_PROMOTION_BLOCKED":
            raise SystemExit("blank acceptance template must never satisfy publication gate")
    elif result["status"] != ("LIVE_READY_FOR_PROTECTED_REVIEW" if args.live else "READY_FOR_LIVE_RELEASE_PR_CHECK"):
        raise SystemExit(1)
