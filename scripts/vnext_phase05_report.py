#!/usr/bin/env python3
"""Stage 05 deterministic, OFFLINE evidence/diff reports, no release actions.

The comparison baseline is stage04 static candidate expectations, not observed
production Loon behavior; runtime data must be supplied separately.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vnext_rule_engine as ve
from vnext_source_lock import check_lock, read_json, ROOT

OUT = ROOT/"refactor/vnext/reports"


def encoded(value) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def make_reports(root: Path = ROOT) -> dict[str, str]:
    integrity = check_lock(root)
    files = ve.compile_rules(root)
    ve.write_outputs(files, root, check=True)
    manifest = read_json(root/"refactor/vnext/engine_manifest.json")
    locked = read_json(root/"refactor/vnext/sources.lock.json")
    previous = read_json(root/"refactor/vnext/business_regression_cases.phase04.snapshot.json")
    fixtures = read_json(root/"refactor/vnext/business_regression_cases.json")
    stage04 = read_json(root/"refactor/vnext/reports/diff_summary.json")
    conflict = read_json(root/"refactor/vnext/reports/conflict_summary.phase05.json")
    old_cases = {x["case_id"]: x for x in previous["cases"]}
    results, successes = [], Counter()
    for case in fixtures["cases"]:
        c = {}
        for ad in ("REJECT", "DIRECT"):
            for final in ("Proxy", "Auto", "Fallback", "DIRECT"):
                route = ve.simulate_domain(case["host"], files, adblock_choice=ad,
                                           final_choice=final)
                if route["policy"] != case["expected_policy"]:
                    raise ValueError("candidate static routing differs from approved fixture: "
                                     + case["case_id"] + ": " + repr(route))
                c[f"AdBlock={ad};Final={final}"] = route
                successes[case["expected_policy"]] += 1
        prev = old_cases.get(case["case_id"])
        results.append({
            "case_id": case["case_id"], "host": case["host"],
            "stage04_expected_static_policy": prev["expected_policy"] if prev else "NOT_TESTED",
            "stage05_expected_static_policy": case["expected_policy"],
            "candidate_static_selectors": c,
            "stage04_to_stage05_expected_change": (prev is not None and
                prev["expected_policy"] != case["expected_policy"]),
            "risk_id": case.get("risk_id", "PH05-REGRESSION-"+case["case_id"]),
            "comparison_kind": "STAGE04_FIXTURE_EXPECTATION_VS_STAGE05_DOMAIN_ONLY_SIMULATION",
            "production_measured_policy": "UNKNOWN",
            "device_verification": "NOT_EXECUTED",
        })
    inputs = []
    for input in locked["inputs"]:
        inputs.append({
            "source_id": input["source_id"],
            "kind": input["input_kind"],
            "path": input["path"],
            "sha256": input["sha256"],
            "git_blob_sha1": input["git_blob_sha1"],
            "original_upstream_provenance": "UNRECOVERABLE",
        })
    provenance = [
        {"record_type": "LOCKED_FROZEN_INPUT", **row} for row in inputs
    ] + [
        {"record_type": "HISTORIC_SOURCE_CATALOG_ONLY", **row}
        for row in locked["historical_sources"]
    ]
    source_integrity = {
        "schema_version": 1,
        "evidence": "IMMUTABLE_FROZEN_BYTES_CHECKED_NOT_RAW_UPSTREAM",
        **integrity,
        "verified_input_count": len(inputs),
        "source_records": inputs,
        "original_raw_lineage_verified_count": 0,
        "separate_stage04_verified_local_line_mappings": stage04["verified_local_source_line_mappings"],
    }
    generated = {}
    remote_rule_count = 0
    for group in manifest["active_groups"]:
        fn = "AnimeCrazy" if group == "動畫瘋" else group
        path = f"refactor/vnext/generated/{fn}.list"
        raw = files[path]
        count = sum(1 for x in raw.splitlines() if x and not x.startswith("#"))
        generated[group] = {"rule_count": count, "sha256": hashlib.sha256(raw.encode()).hexdigest()}
        remote_rule_count += count
    profile = files["refactor/vnext/LoonKit.vNext.Candidate.lcf"]
    new_overseas = [x for x in profile.splitlines() if x.startswith("DOMAIN-SUFFIX,")
                   and x.rsplit(",",1)[-1] in manifest["inactive_groups"]]
    local_ad_overrides = [x for x in profile.splitlines()
                          if x.startswith(("DOMAIN-SUFFIX,", "DOMAIN,"))
                          and x.endswith(",AdBlock")]
    previous_total = stage04["candidate_rule_count"]
    if remote_rule_count != previous_total:
        raise ValueError("unexpected stage04 rule list count change")
    if len(new_overseas) != 14 or len(local_ad_overrides) != 26:
        raise ValueError("overseas AdBlock/local routing safeguards regressed")
    phase_diff = {
        "schema_version": 1,
        "comparison": "STAGE04_OFFLINE_CANDIDATE_TO_STAGE05_OFFLINE_CANDIDATE",
        "candidate_only": True,
        "candidate_profile_sha256": hashlib.sha256(profile.encode()).hexdigest(),
        "stage04_remote_predicate_group_count": previous_total,
        "stage05_remote_predicate_group_count": remote_rule_count,
        "stage05_new_local_overseas_routes": new_overseas,
        "stage05_new_local_adblock_precedence_guards": local_ad_overrides,
        "net_new_inline_predicate_entries": len(new_overseas)+len(local_ad_overrides),
        "remote_groups": generated,
        "china_direct_stage04": stage04["after_groups"]["ChinaDirect"],
        "china_direct_stage05": generated["ChinaDirect"]["rule_count"],
        "adblock_stage04": stage04["after_groups"]["AdBlock"],
        "adblock_stage05": generated["AdBlock"]["rule_count"],
        "cross_policy_parent_child_total": conflict["total_disposed"],
        "conflict_classification_counts": conflict["classification_counts"],
        "unverified_overlap_count": conflict["runtime_test_count"],
        "input_kinds": integrity,
        "regression_case_count": len(results),
        "stage04_regression_case_count": len(previous["cases"]),
        "stage05_static_routing_selector_scenarios": sum(len(x["candidate_static_selectors"])
                                                      for x in results),
        "device_validation": "NOT_EXECUTED",
        "production_readiness": "NOT_READY",
        "warning": "Local AdBlock and overseas overrides are static Loon syntax only, not device results.",
    }
    routing = {
        "schema_version": 1,
        "mode": "DOMAIN_ONLY_SIMULATOR_NOT_LOON",
        "stage04_source_commit": previous["source_commit"],
        "stage04_fixture_count": len(old_cases),
        "stage05_case_count": len(results),
        "selector_scenarios": sum(len(x["candidate_static_selectors"]) for x in results),
        "static_regression_results": "PASS",
        "runtime_validation": "NOT_EXECUTED",
        "cases": results,
    }
    return {
        "refactor/vnext/reports/source_integrity.json": encoded(source_integrity),
        "refactor/vnext/reports/source_provenance.jsonl": "".join(
            json.dumps(x, sort_keys=True, ensure_ascii=False)+"\n" for x in provenance),
        "refactor/vnext/reports/phase05_diff.json": encoded(phase_diff),
        "refactor/vnext/reports/routing_regression.json": encoded(routing),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    x = p.add_mutually_exclusive_group(required=True)
    x.add_argument("--generate", action="store_true")
    x.add_argument("--check", action="store_true")
    x.add_argument("--print", action="store_true")
    args = p.parse_args()
    files = make_reports()
    if args.check:
        for key, value in files.items():
            path = ROOT/key
            if not path.is_file() or path.read_text(encoding="utf-8") != value:
                raise ValueError("missing/stale stage05 evidence report: " + key)
    elif args.generate:
        for key, value in files.items():
            path = ROOT/key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value, encoding="utf-8")
    else:
        for key, value in files.items():
            print("LOONKIT_REPORT_START " + key)
            print(value, end="")
            print("LOONKIT_REPORT_END " + key)
    print("PHASE05_REPORTS_VALIDATED=" + str(len(files)))


if __name__ == "__main__":
    main()
