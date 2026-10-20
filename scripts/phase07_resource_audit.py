#!/usr/bin/env python3
"""Phase07 resource audit: URL lock, real immutable Git blobs, and signed SHA256.

Never alters resources or downloads third-party code during normal --check.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib import request

ROOT=Path(__file__).resolve().parents[1]
HOST="https://raw.githubusercontent.com/YohakuSama/loonkit/"
EXTRACT=re.compile(r"https://raw\.githubusercontent\.com/YohakuSama/loonkit/([^/,\s'\"\)]+)/([^,\s'\"\)]+)")
SHA=re.compile(r"[a-f0-9]{40}\Z")
SECRET=re.compile(r"(?i)(?:token|api_key|password|passwd|access_token)=([^,\s&]+)")


def get_blob(revision: str, path: str) -> bytes:
    if not SHA.fullmatch(revision) or not path or ".." in Path(path).parts:
        raise ValueError("non-pinned or unsafe immutable resource ref")
    try:
        return subprocess.check_output(["git", "cat-file", "blob", revision+":"+path],cwd=ROOT,stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise ValueError("missing pinned Git blob: "+revision+":"+path) from e


def check_remote(url: str) -> None:
    query=request.Request(url,method="HEAD",headers={"User-Agent":"LoonKit-ReleaseGate/1.0"})
    with request.urlopen(query,timeout=20) as req:
        if req.status != 200:
            raise ValueError("pinned resource not reachable: "+url+" HTTP "+str(req.status))


def run(network: bool=False) -> dict:
    spec=json.loads((ROOT/"release/phase-07/release_spec.json").read_text())
    manifest=json.loads((ROOT/"release/phase-07/RC_MANIFEST.json").read_text())
    profiles=[(ROOT/x).read_text(encoding="utf-8")
              for x in ("LoonKit.lcf","LoonKit.PrivacyDNS.lcf")]
    plugin=(ROOT/"release/phase-07/assets/Network_Diagnostics.plugin").read_text()
    artifacts=profiles+[plugin]
    if SECRET.search("\n".join(artifacts)):
        raise ValueError("possible private credential or token in public candidate")
    refs=[]
    for i,body in enumerate(artifacts):
        if "https://raw.githubusercontent.com/YohakuSama/loonkit/main/" in body:
            raise ValueError("dynamic main Git URL in runtime RC2 asset "+str(i))
        refs.extend(EXTRACT.findall(body))
    for ref,path in refs:
        if not SHA.fullmatch(ref) or ref not in {spec["release_assets_commit"],spec["reviewed_auxiliary_commit"]}:
            raise ValueError("unexpected moving or unreviewed immutable ref "+ref)
        if not path.startswith(("rules/releases/vNext-RC2/","icons/v20261018r","release/phase-07/assets/","scripts/v20261018r11/")):
            raise ValueError("unexpected asset path "+path)
    counts=Counter(path.split("/")[0] for _,path in refs)
    if len(refs)!=26*2+33*2+1*2+4:  # both profiles: 26 rules + 33 icons + plugin; plugin: 3 script refs + 1 icon
        raise ValueError("wrong number of pinned runtime references: "+str(len(refs)))
    for name,row in manifest["rules"].items():
        if (spec["release_assets_commit"],row["path"]) not in refs:
            raise ValueError("missing published rule reference "+name)
        value=get_blob(spec["release_assets_commit"],row["path"])
        if hashlib.sha256(value).hexdigest()!=row["sha256"]:
            raise ValueError("pinned Git object hash mismatch "+name)
    for ref,path in set(refs):
        blob=get_blob(ref,path)
        if (ROOT/path).is_file() and ref==spec["release_assets_commit"]:
            if (ROOT/path).read_bytes()!=blob:
                raise ValueError("candidate bytes differ from pinned reviewed resource "+path)
    if network:
        for ref,path in sorted(set(refs)):
            check_remote(HOST+ref+"/"+path)
    return {"status":"STATIC_PINNED_GIT_BLOBS_PASS",
            "pinned_runtime_url_count":len(refs),
            "distinct_resources":len(set(refs)),
            "locked_rule_count":len(manifest["rules"]),
            "remote_https": "CHECKED" if network else "NOT_EXECUTED",
            "device_network": "NOT_EXECUTED"}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check",action="store_true",required=True)
    ap.add_argument("--remote",action="store_true")
    args=ap.parse_args()
    print(json.dumps(run(network=args.remote),sort_keys=True))


if __name__=="__main__": main()
