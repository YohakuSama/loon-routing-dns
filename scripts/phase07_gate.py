#!/usr/bin/env python3
"""Fail-closed release gate; static CI PASS does not imply release approval."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQUIRED={"code_review","rule_generation","source_integrity","config_integrity","dns_tun_unchanged","dual_profile_parity","plugin_icons","licenses","ci","merge_rehearsal","rollback_rehearsal","device_import","domestic_business","overseas_business","adblock","final","dns_egress","ipv4_ipv6","maintainer_approval"}
SHA=re.compile(r"[0-9a-f]{40}\Z")
STAMP=re.compile(r"\d{4}-\d{2}-\d{2}T.+(?:Z|[+-]\d{2}:\d{2})\Z")

def check(require_ready=False):
    d=json.loads((ROOT/"release/phase-07/RELEASE_GATE.json").read_text(encoding="utf-8"))
    if d.get("schema_version")!=1 or set(d.get("checks",{}))!=REQUIRED:
        raise ValueError("missing required gate check")
    if d.get("release_status") not in {"BLOCKED_PENDING_MAINTAINER_TEST","READY_FOR_MAINTAINER_APPROVAL","APPROVED","PUBLISHED_WITH_OPEN_REVIEWS"}:
        raise ValueError("invalid overall release status")
    blockers=[]
    for name,row in d["checks"].items():
        if row.get("status") not in {"PASS","FAIL","BLOCKED","NOT_EXECUTED"}:
            raise ValueError("unsupported status "+name)
        if not isinstance(row.get("blocks_release"),bool) or not row.get("owner"):
            raise ValueError("missing gate owner or blocking flag "+name)
        if row["status"]=="PASS":
            if not row.get("evidence") or not SHA.fullmatch(row.get("commit") or "") or not STAMP.fullmatch(row.get("test_time") or ""):
                raise ValueError("PASS lacks immutable evidence "+name)
        if row["blocks_release"] and row["status"]!="PASS":
            blockers.append(name)
    # Runtime PASS is invalid unless the redacted record proves both tested
    # profiles and frozen rule Git blobs match the exact reviewed RC2 bytes.
    runtime={"device_import","domestic_business","overseas_business",
             "adblock","final","dns_egress","ipv4_ipv6"}
    passed={name for name in runtime if d["checks"][name]["status"]=="PASS"}
    if passed:
        from phase07_device_attestation import inspect as check_device
        check_device(passed,ROOT)
    # A manually typed PASS on licensing is not proof of redistribution rights.
    # Verify actual preserved texts and substantive independent rights review.
    if d["checks"]["licenses"]["status"]=="PASS":
        from phase07_license_evidence import check as check_legal
        report=check_legal(ROOT)
        if report["independent_clearance"]!="REVIEW_EVIDENCE_PRESENT":
            raise ValueError("license PASS requires independent candidate-specific clearance evidence")
    if d["release_status"]=="APPROVED" and blockers:
        raise ValueError("APPROVED contradicts open blockers")
    if require_ready and (blockers or d["release_status"]!="APPROVED"):
        raise ValueError("release BLOCKED: "+",".join(blockers or ["approval_status"]))
    return {"release_status":d["release_status"],"open_blockers":sorted(blockers),"required_checks":len(REQUIRED)}

def main():
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--lint",action="store_true")
    group.add_argument("--require-ready",action="store_true")
    a=p.parse_args()
    print(json.dumps(check(require_ready=a.require_ready),sort_keys=True))

if __name__=="__main__": main()
