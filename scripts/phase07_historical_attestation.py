#!/usr/bin/env python3
"""Attest locked vNext snapshots against actual phase03 Git history objects.

The frozen Git commit contains *pre-migration* rules/generated/*, not the new
rules/snapshots/phase03/generated/* paths. The path mapping below is
intentional and auditable. This does NOT reconstruct line-level upstream origin.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
NEW_ROOT = "rules/snapshots/phase03/generated/"
OLD_ROOT = "rules/generated/"
COMMIT = re.compile(r"[0-9a-f]{40}\Z")


def historical_path(relative: str) -> str:
    if relative.startswith(NEW_ROOT) and relative.endswith(".list"):
        return OLD_ROOT + relative[len(NEW_ROOT):]
    if relative.startswith("rules/custom/") and relative.endswith(".list"):
        return relative
    if relative == "rules/ProxyProtect.list":
        return relative
    raise ValueError("unexpected non-historical frozen source path: " + relative)


def check(root: Path = ROOT) -> dict:
    manifest = json.loads((root / "refactor/vnext/engine_manifest.json").read_text(encoding="utf-8"))
    lock = json.loads((root / "refactor/vnext/sources.lock.json").read_text(encoding="utf-8"))
    commit = manifest.get("frozen_head")
    if not isinstance(commit, str) or not COMMIT.fullmatch(commit):
        raise ValueError("missing historical frozen 40-hex commit")
    frozen = manifest.get("frozen_git_blob_sha1")
    if not isinstance(frozen, dict) or len(frozen) != 44:
        raise ValueError("incomplete frozen input object inventory")
    items = {x["path"]: x for x in lock.get("inputs", [])}
    if set(items) != set(frozen) or lock.get("snapshot_commit") != commit:
        raise ValueError("historical manifest and SHA256 lock disagree")
    restored = 0
    for relative, objid in sorted(frozen.items()):
        old = historical_path(relative)
        if not COMMIT.fullmatch(objid):
            raise ValueError("invalid locked Git object identifier")
        path = root / relative
        data = path.read_bytes()
        locked = items[relative]
        if locked["immutable_ref"] != commit:
            raise ValueError("snapshot does not link to historical commit: " + relative)
        if hashlib.sha256(data).hexdigest() != locked["sha256"]:
            raise ValueError("snapshot local SHA256 failed: " + relative)
        if hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest() != objid:
            raise ValueError("snapshot local Git blob failed: " + relative)
        obj = commit + ":" + old
        try:
            historical = subprocess.run(["git", "cat-file", "blob", obj],
                       cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ValueError("cannot locate historical git object: " + obj) from exc
        if historical != data:
            raise ValueError("historical Git bytes differ from locked input: " + relative)
        restored += 1
    return {"status": "PINNED_HISTORICAL_BLOBS_VERIFIED",
            "source_commit": commit,
            "verified_bytes": restored,
            "moved_generated_snapshots": sum(p.startswith(NEW_ROOT) for p in frozen),
            "original_upstream_lineage": "NOT_RECOVERABLE_FROM_MERGED_SNAPSHOT",
            "production_output_dependency": False}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", required=True)
    ap.parse_args()
    print(json.dumps(check(), sort_keys=True))
