#!/usr/bin/env python3
"""Fail-closed historical license catalog audit; never declares rights cleared."""
import argparse
from collections import Counter
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"build/license_sources.json"
EXPECTED_LICENSE={
 "blackmatrix7":("GPL-2.0-only","https://github.com/blackmatrix7/ios_rule_script/blob/master/LICENSE"),
 "v2fly":("MIT","https://github.com/v2fly/domain-list-community/blob/master/LICENSE"),
 "felixonmars":("WTFPL-2.0","https://github.com/felixonmars/dnsmasq-china-list/blob/master/LICENSE"),
 "self":("INTERNAL_RIGHTS_TO_CONFIRM",None),
}
COPIES={
 "GPL-2.0-only":("rules/LICENSE.GPL-2.0","GNU GENERAL PUBLIC LICENSE"),
 "MIT":("rules/LICENSE.MIT-V2FLY","MIT License"),
 "WTFPL-2.0":("rules/LICENSE.WTFPL-FELIXONMARS","DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE"),
}

def audit(root=ROOT):
    catalog=json.loads((root/"rules/sources.json").read_text(encoding="utf-8"))["sources"]
    ledger=json.loads((root/"build/license_sources.json").read_text(encoding="utf-8"))
    if ledger.get("schema_version")!=1 or ledger.get("release_status")!="LICENSE_NOTICES_DOCUMENTED":
        raise ValueError("upstream license inventory must remain documented without claiming independent certification")
    if ledger.get("record_kind")!="HISTORIC_SOURCE_CATALOG_NOT_PER_RULE_PROVENANCE":
        raise ValueError("historical source list cannot pretend to trace all released matchers")
    if ledger.get("current_release_rule_count")!=197765:
        raise ValueError("release rule count metadata drift")
    if ledger.get("historical_source_count")!=len(catalog) or len(catalog)!=87:
        raise ValueError("historical source catalog coverage incomplete")
    rows=ledger["entries"]
    if len(rows)!=len(catalog) or len({x["source_id"] for x in rows})!=len(catalog):
        raise ValueError("license ledger duplicate/missing source")
    counts=Counter()
    for source,row in zip(catalog,rows):
        url=source.get("url")
        owner="self" if not url else urlsplit(url).path.strip("/").split("/")[0]
        if owner not in EXPECTED_LICENSE:
            raise ValueError("unknown upstream owner: "+owner)
        license_id, evidence=EXPECTED_LICENSE[owner]
        counts[license_id]+=1
        if any((
          row.get("source_id")!=source["id"],row.get("group")!=source.get("group"),
          row.get("role")!=source.get("role"),
          row.get("recorded_url")!=url,
          row.get("recorded_local_path")!=source.get("path"),
          row.get("presumed_license")!=license_id,
          row.get("license_evidence_url")!=evidence,
          row.get("pinned_upstream_commit") is not None,
          row.get("per_rule_origin_verified") is not False,
          row.get("approval_status")!="SOURCE_FAMILY_LICENSE_RECORDED_UNVERIFIED_LINEAGE",
        )):
            raise ValueError("license ledger source rights or provenance misrepresented: "+source["id"])
    for license_id,(filename,marker) in COPIES.items():
        if marker not in (root/filename).read_text(encoding="utf-8"):
            raise ValueError("required historical license notice missing: "+filename)
    if counts!={"GPL-2.0-only":41,"MIT":35,"WTFPL-2.0":1,"INTERNAL_RIGHTS_TO_CONFIRM":10}:
        raise ValueError("historical source-family count changed unexpectedly")
    if (root/"LICENSE").read_bytes()!=(root/"rules/LICENSE.GPL-2.0").read_bytes():
        raise ValueError("project GPL-2.0-only license is missing or altered")
    from license_evidence import check as check_review
    recorded=check_review(root)
    approved=(recorded["independent_clearance"]=="REVIEW_EVIDENCE_PRESENT")
    return {"status":"INDEPENDENT_REVIEW_DOCUMENTED" if approved else "LICENSE_NOTICES_DOCUMENTED",
            "historical_records_checked":len(rows),
            "source_families":dict(sorted(counts.items())),
            "line_level_license_attribution":"NOT_VERIFIED",
            "icon_and_plugin_rights":"HUMAN_REVIEW_DOCUMENTED" if approved else "NOT_VERIFIED",
            "release_clearance_evidence":recorded["independent_clearance"]}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--check",action="store_true",required=True)
    p.parse_args()
    print(json.dumps(audit(),ensure_ascii=False,sort_keys=True))
