#!/usr/bin/env python3
"""Plan historical beta-tree cleanup; apply only after exact stable promotion.

Never rewrites Git history or deletes original release/input snapshots. Old
commit-pinned clients remain supported by their immutable archival Git objects.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.request
from beta_channel import ROOT, URI, resource_records


def inventory(root: Path = ROOT) -> dict:
    meta = json.loads((root / "build/beta_manifest.json").read_text())
    release = json.loads((root / "build/release_manifest.json").read_text())
    history = json.loads((root / "build/beta_history.json").read_text())
    current = {URI.fullmatch(uri)["path"] for uri in resource_records(meta)}
    archival = {}
    for revision in history["revisions"]:
        for row in revision["resources"]:
            archival[URI.fullmatch(row["uri"])["path"]] = row
    # Keep explicit source-code/docs dependencies in the working tree.
    referenced = set()
    for directory in ("scripts", "tests", "docs", ".github"):
        for path in (root / directory).rglob("*"):
            if path.is_file() and path.suffix in {".py", ".md", ".json", ".yml"}:
                referenced.update(re.findall(r"rules/beta/v[0-9A-Za-z.-]+/[A-Za-z0-9_-]+\.list", path.read_text()))
    orphan = []
    for path in sorted((root / "rules/beta").glob("v*/*.list")):
        if path.is_symlink():
            raise ValueError("symlink is not a cleanup inventory resource")
        relative = path.relative_to(root).as_posix()
        if relative not in current and relative not in referenced:
            orphan.append({"path":relative, "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                           "archival_reference":archival.get(relative)})
    publication = release.get("publication", {})
    stable = (publication.get("status") == "VERIFIED_ON_MAIN"
              and re.fullmatch(r"[a-f0-9]{40}", str(publication.get("published_main_commit_sha", ""))) is not None
              and release.get("label") == meta["version"].split("-beta.")[0]
              and release.get("promoted_beta_config_sha256") == meta["configuration_sha256"]
              and release.get("profile_sha256", {}).get("LoonKit.lcf") == hashlib.sha256((root / "LoonKit.lcf").read_bytes()).hexdigest())
    return {"status":"READY_FOR_ARCHIVAL_VERIFICATION" if stable else "BLOCKED_UNTIL_EXACT_STABLE_PROMOTION",
            "beta_version":meta["version"], "stable_version":release.get("label"),
            "current_resources_protected":len(current), "candidates":orphan,
            "rules":"Only historical beta working-tree copies; all original inputs, stable rules and Git objects retained."}


def apply(root: Path = ROOT):
    plan = inventory(root)
    if plan["status"] != "READY_FOR_ARCHIVAL_VERIFICATION":
        raise ValueError("stable promotion has not happened; no cleanup permitted")
    # Verify ALL references first. Any missing archive aborts before any deletion.
    for row in plan["candidates"]:
        archive = row["archival_reference"]
        if not archive or archive["sha256"] != row["sha256"] or not URI.fullmatch(archive["uri"]):
            raise ValueError("historical resource lacks a verified immutable rollback reference")
        path = root / row["path"]
        if path.is_symlink() or not path.resolve().is_relative_to((root / "rules/beta").resolve()):
            raise ValueError("unsafe cleanup target")
        with urllib.request.urlopen(archive["uri"], timeout=30) as response:
            if not URI.fullmatch(response.geturl()):
                raise ValueError("historical resource redirect invalid")
            data = response.read(8 * 1024 * 1024 + 1)
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("historical client resource unavailable or changed")
    for row in plan["candidates"]:
        (root / row["path"]).unlink()
    return {"removed":[row["path"] for row in plan["candidates"]], "git_history_rewritten":False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(apply() if args.apply else inventory(), ensure_ascii=False, indent=2))
