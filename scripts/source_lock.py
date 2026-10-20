#!/usr/bin/env python3
"""Offline immutable input lock for LoonKit vNext; no network downloads.

Frozen merged snapshots are not raw upstreams. Never infer historic upstream
line origins from these bytes. --init is an explicit maintainer operation;
CI must use --check, and must never rewrite the lock.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "build/engine_manifest.json"
LOCK = "build/sources.lock.json"
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
SHA1 = re.compile(r"[a-f0-9]{40}\Z")
SAFE_RAW_ROOT = "build/upstream/"
KINDS = {"FROZEN_MERGED_SNAPSHOT", "PINNED_RAW_UPSTREAM"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_path(root: Path, relative: str) -> Path:
    p = Path(relative)
    if p.is_absolute() or ".." in p.parts or p.as_posix() != relative:
        raise ValueError("unsafe source path: " + relative)
    path = (root / p).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("source escapes checkout")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def source_metadata(root: Path, relative: str, blob: str, commit: str) -> dict:
    data = safe_path(root, relative).read_bytes()
    if git_blob_sha(data) != blob:
        raise ValueError("frozen Git blob mismatch: " + relative)
    return {
        "source_id": "frozen:" + relative,
        "input_kind": "FROZEN_MERGED_SNAPSHOT",
        "original_url": None,
        "immutable_ref": commit,
        "git_blob_sha1": blob,
        "sha256": hashlib.sha256(data).hexdigest(),
        "path": relative,
        "encoding": "utf-8",
        "rule_format": "loon",
        "policy": (relative.rsplit("/", 1)[-1].removesuffix(".list")
                   if relative.startswith("rules/inputs/") else "maintained_local_or_legacy"),
        "license": "UNKNOWN_MERGED_PROVENANCE",
        "evidence_level": "FROZEN_BYTES_VERIFIED_NOT_RAW_UPSTREAM",
        "original_line_provenance": "HISTORICAL_PROVENANCE_UNRECOVERABLE",
    }


def build_lock(root: Path = ROOT) -> dict:
    manifest = read_json(root / MANIFEST)
    sources = [source_metadata(root, path, blob, manifest["frozen_head"])
               for path, blob in sorted(manifest["frozen_git_blob_sha1"].items())]
    catalog = read_json(root / "rules/sources.json")["sources"]
    historical = [{
        "source_id": s["id"],
        "original_url": s.get("url"),
        "original_path": s.get("path"),
        "status": "HISTORICAL_PROVENANCE_UNRECOVERABLE"
        if s.get("role") != "local" else "LOCAL_SOURCE_CAN_BE_VERIFIED_INDEPENDENTLY",
    } for s in catalog]
    return {
        "schema_version": 1,
        "input_lock_policy": "FAIL_CLOSED",
        "snapshot_commit": manifest["frozen_head"],
        "inputs": sources,
        "historical_sources": historical,
        "warning": "Historical source IDs are not attestations of original rule lines.",
    }


def check_lock(root: Path = ROOT, lock: dict | None = None) -> dict:
    lock = read_json(root / LOCK) if lock is None else lock
    manifest = read_json(root / MANIFEST)
    if lock.get("schema_version") != 1 or lock.get("input_lock_policy") != "FAIL_CLOSED":
        raise ValueError("unknown source-lock schema or policy")
    if lock.get("snapshot_commit") != manifest["frozen_head"]:
        raise ValueError("frozen upstream version changed")
    inputs = lock.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        raise ValueError("source lock has no inputs")
    ids, paths = set(), set()
    frozen = {}
    for item in inputs:
        sid = item.get("source_id")
        relative = item.get("path")
        if not isinstance(sid, str) or not sid or sid in ids:
            raise ValueError("missing or repeated source id")
        ids.add(sid)
        if not isinstance(relative, str) or relative in paths:
            raise ValueError("missing or repeated source path")
        paths.add(relative)
        kind = item.get("input_kind")
        if kind not in KINDS:
            raise ValueError("unlocked or unknown source kind")
        if item.get("encoding") != "utf-8" or not item.get("rule_format") or not item.get("policy"):
            raise ValueError("incomplete format, encoding or policy")
        if not item.get("license") or not item.get("evidence_level"):
            raise ValueError("source license/evidence missing")
        sha = item.get("sha256")
        if not isinstance(sha, str) or not SHA256.fullmatch(sha):
            raise ValueError("missing/invalid SHA256: " + sid)
        if not isinstance(item.get("git_blob_sha1"), str) or not SHA1.fullmatch(item["git_blob_sha1"]):
            raise ValueError("missing/invalid Git blob SHA: " + sid)
        data = safe_path(root, relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != sha or git_blob_sha(data) != item["git_blob_sha1"]:
            raise ValueError("source bytes modified: " + relative)
        try:
            data.decode(item["encoding"])
        except UnicodeError as e:
            raise ValueError("source encoding changed") from e
        if kind == "FROZEN_MERGED_SNAPSHOT":
            if item.get("original_url") is not None or item.get("immutable_ref") != manifest["frozen_head"]:
                raise ValueError("frozen snapshot cannot claim a raw original URL")
            if item.get("evidence_level") != "FROZEN_BYTES_VERIFIED_NOT_RAW_UPSTREAM":
                raise ValueError("snapshot evidence misrepresented")
            frozen[relative] = item["git_blob_sha1"]
        else:
            if not relative.startswith(SAFE_RAW_ROOT):
                raise ValueError("raw source must be under candidate-only upstream directory")
            if not item.get("original_url") or not re.fullmatch(r"[0-9a-f]{40}", item.get("immutable_ref", "")):
                raise ValueError("raw source needs immutable URL and 40-hex commit pin")
            if item.get("evidence_level") != "PINNED_RAW_UPSTREAM_VERIFIED":
                raise ValueError("raw source has unproven provenance")
            # Raw files are locked but cannot silently enter the candidate. Any
            # active raw source requires a separate, trace-aware engine change.
            if item.get("active_in_candidate", False):
                raise ValueError("active raw source not wired to trace-aware compiler")
    if frozen != manifest["frozen_git_blob_sha1"]:
        raise ValueError("source lock does not cover exactly the manifest's frozen input set")
    historical = lock.get("historical_sources", [])
    catalog = read_json(root / "rules/sources.json")["sources"]
    if len(historical) != len(catalog) or {x["source_id"] for x in historical} != {x["id"] for x in catalog}:
        raise ValueError("historical source ledger incomplete")
    if len({x["source_id"] for x in historical}) != len(historical):
        raise ValueError("duplicate historical source ID")
    return {"verified_frozen_inputs": len(frozen), "verified_raw_inactive_inputs": len(inputs)-len(frozen),
            "historical_catalog_ids": len(historical),
            "original_upstream_lineage": "NOT_RECOVERABLE_FROM_MERGED_SNAPSHOT"}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--init", action="store_true", help="maintainer only: make lock in checkout")
    p.add_argument("--print-init-json", action="store_true", help="print candidate lock for review")
    p.add_argument("--check", action="store_true", help="CI: validate committed lock")
    a = p.parse_args()
    if sum((a.init, a.print_init_json, a.check)) != 1:
        p.error("choose exactly one operation")
    if a.init or a.print_init_json:
        content = json.dumps(build_lock(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if a.init:
            (ROOT / LOCK).write_text(content, encoding="utf-8")
        else:
            print("LOONKIT_LOCK_JSON_START")
            print(content)
            print("LOONKIT_LOCK_JSON_END")
    else:
        print(json.dumps(check_lock(), sort_keys=True))


if __name__ == "__main__":
    main()
