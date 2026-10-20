#!/usr/bin/env python3
"""Bind *manually collected* Loon runtime attestations to exact RC2 profile bytes.

A valid redacted JSON is necessary for a runtime gate PASS but not sufficient:
human review, licensing and maintainer authorization are separate blockers.
No synthetic tests or values are supplied by this tool.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from validate_device_results import validate as validate_redacted

EVIDENCE="validation/phase-07/device-results.redacted.json"
RUNTIME={
 "device_import","domestic_business","overseas_business",
 "adblock","final","dns_egress","ipv4_ipv6",
}
CONFIGS=("LoonKit.lcf","LoonKit.PrivacyDNS.lcf")
SHA=re.compile(r"[a-f0-9]{40}\Z")


def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def inspect(required_scopes:set[str],root:Path=ROOT)->dict:
    if not required_scopes.issubset(RUNTIME):
        raise ValueError("unknown runtime release scope")
    if not required_scopes:
        return {"status":"NOT_EXECUTED","reviewed_rows":0}
    path=root/EVIDENCE
    if not path.is_file():
        raise ValueError("runtime PASS cannot lack structured redacted device evidence: "+EVIDENCE)
    doc=json.loads(path.read_text(encoding="utf-8"))
    verify=validate_redacted(doc)
    if not verify["total_records"]:
        raise ValueError("empty device result file cannot attest any runtime PASS")
    manifest=json.loads((root/"release/phase-07/RC_MANIFEST.json").read_text(encoding="utf-8"))
    expected_sha={p:manifest["profile_sha256"][p] for p in CONFIGS}
    frozen_commit=manifest["source_snapshot_commit"]
    if not SHA.fullmatch(frozen_commit):
        raise ValueError("candidate rule commit is not pinned")

    @lru_cache(maxsize=256)
    def git_profile(commit:str,profile:str)->str:
        if not SHA.fullmatch(commit):
            raise ValueError("test evidence refers to malformed commit")
        try:
            blob=subprocess.run(["git","cat-file","blob",commit+":"+profile],
                 cwd=root,check=True,capture_output=True).stdout
        except (OSError,subprocess.CalledProcessError) as exc:
            raise ValueError("tested config commit not present in Git history") from exc
        return sha(blob)

    covered={scope: {p: [] for p in CONFIGS} for scope in required_scopes}
    for row in doc["results"]:
        scope=row.get("test_scope")
        if scope not in required_scopes:
            continue
        if row["configuration"]!="VNEXT" or row["conclusion"]!="PASS":
            raise ValueError("incomplete/failed scope cannot attest runtime PASS: "+str(scope))
        profile=row.get("profile_file")
        if profile not in CONFIGS:
            raise ValueError("runtime evidence must distinguish BOTH original profile variants")
        if row.get("profile_sha256")!=expected_sha[profile]:
            raise ValueError("device-tested profile bytes differ from pinned RC2 manifest")
        if row["rule_file_version"]!=frozen_commit:
            raise ValueError("device-tested remote rule commit differs from RC2")
        if git_profile(row["config_commit_sha"],profile)!=expected_sha[profile]:
            raise ValueError("device test commit does not contain identical published profile bytes")
        covered[scope][profile].append(row)
    for scope,by_profile in covered.items():
        for profile,rows in by_profile.items():
            if not rows:
                raise ValueError("runtime PASS missing real test for "+scope+"/"+profile)
            if scope=="adblock" and not {"REJECT","DIRECT"}.issubset(
                {row.get("adblock_choice") for row in rows}):
                raise ValueError("AdBlock PASS requires REJECT and DIRECT: "+profile)
            if scope=="final" and not {"Proxy","Auto","Fallback","DIRECT"}.issubset(
                {row.get("final_choice") for row in rows}):
                raise ValueError("Final PASS requires all four user selections: "+profile)
            if scope=="dns_egress" and not all(row["observed_resolvers"] for row in rows):
                raise ValueError("DNS PASS cannot omit observed resolver evidence")
            if scope=="ipv4_ipv6" and not any(
                row["ipv4_result"]!="UNKNOWN" and row["ipv6_result"]!="UNKNOWN"
                for row in rows):
                raise ValueError("IPv4/IPv6 PASS lacks dual-stack observation")
    return {
        "status":"RESULTS_RECEIVED_NOT_AUTOMATICALLY_ATTESTED",
        "reviewed_rows":sum(len(rows) for group in covered.values() for rows in group.values()),
        "covered_scopes":sorted(required_scopes),
        "bound_config_sha256":expected_sha,
        "pinned_rule_commit":frozen_commit,
        "device_truth":"REQUIRES_MAINTAINER_REVIEW",
    }


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--check",action="store_true",required=True)
    p.add_argument("--scope",action="append",choices=sorted(RUNTIME),required=True)
    a=p.parse_args()
    print(json.dumps(inspect(set(a.scope)),indent=2,sort_keys=True))
