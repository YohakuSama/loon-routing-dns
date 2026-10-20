#!/usr/bin/env python3
"""Read-only upstream source availability and SHA256 review inventory."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib import request

ROOT=Path(__file__).resolve().parents[1]

def run():
    sources=json.loads((ROOT/"rules/sources.json").read_text())["sources"]
    rows=[]
    for item in sources:
        row={"source_id":item["id"],"group":item["group"],"url":item.get("url")}
        try:
            if item.get("url"):
                req=request.Request(item["url"],headers={"User-Agent":"LoonKit-Upstream/1"})
                with request.urlopen(req,timeout=20) as response:
                    raw=response.read(30_000_001)
                if len(raw)>30_000_000: raise ValueError("upstream too large")
            else:
                raw=(ROOT/item["path"]).read_bytes()
            row.update(status="FETCHED_FOR_REVIEW_ONLY",sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
        except (OSError,ValueError) as e:
            row.update(status="UNAVAILABLE",error_type=type(e).__name__)
        rows.append(row)
    return {"status":"REVIEW_ONLY_NEVER_PUBLISH","sources":rows,
            "unavailable":sum(x["status"]=="UNAVAILABLE" for x in rows)}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(run(),ensure_ascii=False,indent=2,sort_keys=True)+"\n")
