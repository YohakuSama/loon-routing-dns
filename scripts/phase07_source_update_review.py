#!/usr/bin/env python3
"""Offline source-update proposal and rule-level diff. Never publishes or locks.

The old consolidated upstream origins remain unrecoverable. A proposed new
source can ONLY become a future release after licensing, code review, explicit
manifest + lock updates and all release gates, never by invoking this tool.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LOCK=ROOT/"refactor/vnext/sources.lock.json"


def review(source: str, proposed: Path, root: Path=ROOT) -> dict:
    manifest=json.loads((root/"refactor/vnext/sources.lock.json").read_text(encoding="utf-8"))
    sources={entry["path"]:entry for entry in manifest["inputs"]}
    if source not in sources or not source.startswith("rules/snapshots/phase03/generated/"):
        raise ValueError("only frozen composite-source proposals are supported")
    current=root/source
    if not current.is_file() or hashlib.sha256(current.read_bytes()).hexdigest()!=sources[source]["sha256"]:
        raise ValueError("current frozen input failed SHA256 verification")
    if proposed.resolve() == current.resolve():
        raise ValueError("use distinct proposed snapshot; do not rewrite immutable inputs")
    if proposed.resolve().is_relative_to((root/"rules/generated").resolve()) or proposed.resolve().is_relative_to((root/"rules/releases").resolve()):
        raise ValueError("cannot use a production output as upstream source")
    before=current.read_bytes()
    after=proposed.read_bytes()
    if not after or len(after)>50_000_000:
        raise ValueError("empty/oversized proposed input")
    old={x.strip() for x in before.decode("utf-8").splitlines()
         if x.strip() and not x.lstrip().startswith(("#",";","//"))}
    new={x.strip() for x in after.decode("utf-8").splitlines()
         if x.strip() and not x.lstrip().startswith(("#",";","//"))}
    if len(new)<1:
        raise ValueError("proposed input contains no rules")
    allowed={"DOMAIN","DOMAIN-SUFFIX","DOMAIN-KEYWORD","IP-CIDR","IP-CIDR6","IP-ASN","GEOIP"}
    # Historic mixed input contains legacy matcher classes the vNext compiler
    # already filters. Do not reject unchanged historic lines as a new defect;
    # fail closed only on freshly introduced matchers under review.
    add=sorted(new-old)
    remove=sorted(old-new)
    for line in add:
        if line.split(",")[0] not in allowed or len(line.split(",")) not in (2,3):
            raise ValueError("invalid newly proposed Loon matcher: "+line[:120])
    return {
        "schema_version":1, "status":"PENDING_REVIEW_NOT_PUBLISHED",
        "source_path":source, "historical_lineage":"NOT_RECOVERABLE_FROM_MERGED_SNAPSHOT",
        "original_source_sha256":hashlib.sha256(before).hexdigest(),
        "proposed_sha256":hashlib.sha256(after).hexdigest(),
        "added_rule_count":len(add), "removed_rule_count":len(remove),
        "old_distinct_matchers":len(old), "proposed_distinct_matchers":len(new),
        "added_by_kind":dict(sorted(Counter(x.split(",")[0] for x in add).items())),
        "removed_by_kind":dict(sorted(Counter(x.split(",")[0] for x in remove).items())),
        "added_sample":add[:30], "removed_sample":remove[:30],
        "manual_legal_review":"REQUIRED",
        "manifest_and_source_lock_update":"REQUIRED_IN_REVIEWED_PR",
        "new_release_candidate_and_device_retest":"REQUIRED",
        "release_write_performed":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--proposed",type=Path,required=True)
    p.add_argument("--report",type=Path)
    a=p.parse_args()
    content=json.dumps(review(a.source,a.proposed),sort_keys=True,indent=2,ensure_ascii=False)+"\n"
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(content,encoding="utf-8")
    else:
        print(content,end="")


if __name__=="__main__": main()
