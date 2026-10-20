#!/usr/bin/env python3
"""Stage the NEXT reviewed Loon rule candidate without changing RC2, main, or legacy URLs.

Inputs are locked and compiled by vnext_rule_engine. This writes only to an
explicit directory OUTSIDE the checkout, never downloads, pushes or publishes.
An independent reviewed PR must freeze the resulting blobs at a Git commit,
then construct and test the final configs against that exact immutable commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import rule_engine as engine

BASE_RELEASE = "rules/releases/vNext-RC2"
PREFIX = "build/generated/"
VERSION = re.compile(r"(?:vNext-RC[3-9][0-9]*|v[0-9]+\.[0-9]+\.[0-9]+(?:-rc[0-9]+)?)\Z")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_rules(data: bytes) -> set[str]:
    lines = data.decode("utf-8").splitlines()
    return {x.strip() for x in lines if x.strip() and not x.lstrip().startswith(("#", ";", "//"))}


def render(version: str, root: Path = ROOT) -> dict[str, bytes]:
    if not VERSION.fullmatch(version):
        raise ValueError("explicit candidate version required (vNext-RC3+ or vX.Y.Z); never infer a stable version")
    if (root / "rules/releases" / version).exists():
        raise ValueError("candidate version already exists; released snapshots are immutable")
    compiled = engine.compile_rules(root)
    rules = {k[len(PREFIX):]:v.encode("utf-8") for k,v in compiled.items()
             if k.startswith(PREFIX) and k.endswith(".list")}
    if len(rules) != 26 or len(set(rules)) != len(rules):
        raise ValueError("vNext compiler did not return exactly 26 reviewed policy outputs")
    locked = json.loads((root / "build/sources.lock.json").read_text(encoding="utf-8"))
    if locked.get("input_lock_policy") != "FAIL_CLOSED":
        raise ValueError("unsafe source lock")
    locked_sha=sha((root / "build/sources.lock.json").read_bytes())
    files: dict[str, bytes] = {}
    manifest_rules: dict[str, dict] = {}
    diffs = {}
    total = 0
    for filename, content in sorted(rules.items()):
        out = f"rules/releases/{version}/{filename}"
        old_file=root / BASE_RELEASE / filename
        if not old_file.is_file():
            raise ValueError("cannot locate immutable baseline release: " + filename)
        previous=old_file.read_bytes()
        before=normalized_rules(previous)
        after=normalized_rules(content)
        if len(after)!=sum(bool(x.strip()) and not x.lstrip().startswith(("#",";","//"))
                           for x in content.decode("utf-8").splitlines()):
            raise ValueError("new compiled output contains duplicate matchers: "+filename)
        added=sorted(after-before)
        removed=sorted(before-after)
        manifest_rules[filename[:-5]]={
            "path":out,"sha256":sha(content),
            "rule_count":len(after),"base_sha256":sha(previous),
        }
        total+=len(after)
        files[out]=content
        diffs[filename[:-5]]={
            "added":added,"removed":removed,
            "added_count":len(added),"removed_count":len(removed),
        }
    diffs_blob=json.dumps(diffs,sort_keys=True,ensure_ascii=False,indent=2).encode("utf-8")+b"\n"
    review={
        "schema_version":1,"version":version,
        "status":"CANDIDATE_REVIEW_ONLY_NOT_PUBLISHED",
        "license_review":"BLOCKED_PENDING_REVIEW",
        "runtime_device_test":"NOT_EXECUTED",
        "maintainer_approval":"NOT_EXECUTED",
        "requires_new_pinned_git_commit":True,
        "compiler_inputs":"INDEPENDENT_LOCKED_SNAPSHOTS_NOT_FORMAL_OUTPUTS",
        "source_lock_sha256":locked_sha,
        "reference_release":BASE_RELEASE,
        "remote_rule_files":len(rules),
        "remote_matchers":total,
        "rules":manifest_rules,
        "diff_sha256":sha(diffs_blob),
        "diff_path":"NEXT_RELEASE_DIFF.json",
    }
    files["NEXT_RELEASE_DIFF.json"]=diffs_blob
    files["NEXT_RELEASE_MANIFEST.json"]=json.dumps(
        review,sort_keys=True,ensure_ascii=False,indent=2).encode("utf-8")+b"\n"
    return files


def run(version: str, output: Path, check: bool = False, root: Path=ROOT) -> dict:
    out=output.resolve()
    repo=root.resolve()
    if out==repo or out.is_relative_to(repo) or repo.is_relative_to(out):
        raise ValueError("review preview must be in a separate directory outside the checkout")
    if out.is_symlink():
        raise ValueError("review output symlinks prohibited")
    contents=render(version,root)
    if check:
        missing=[p for p,b in contents.items()
                 if not (out/p).is_file() or (out/p).read_bytes()!=b]
        unexpected=sorted(p.relative_to(out).as_posix() for p in out.rglob("*")
                          if p.is_file() and p.relative_to(out).as_posix() not in contents)
        if missing or unexpected:
            raise ValueError("staged candidate differs from deterministic build: "+
                             repr({"missing_or_modified":missing,"unexpected":unexpected}))
    else:
        if out.exists() and any(out.iterdir()):
            raise ValueError("staging destination must be initially empty, never overwrite a prior candidate")
        out.mkdir(parents=True,exist_ok=True)
        for p,b in sorted(contents.items()):
            dest=out/p
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(b)
    return {
        "status":"CANDIDATE_REVIEW_ONLY_NOT_PUBLISHED",
        "version":version,
        "output_file_count":len(contents),
        "rule_file_count":len(contents)-2,
        "formal_user_paths_modified":False,
    }


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version",required=True)
    parser.add_argument("--output",type=Path,required=True)
    op=parser.add_mutually_exclusive_group(required=True)
    op.add_argument("--build",action="store_true")
    op.add_argument("--check",action="store_true")
    args=parser.parse_args()
    print(json.dumps(run(args.version,args.output,check=args.check),sort_keys=True))
