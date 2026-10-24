#!/usr/bin/env python3
"""Version-specific v6.5.6 release verification, including old pinned assets."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from prepare_release_v656 import check as check_build, BASE_SHA256, EXPECTED_SHA256, EXPECTED_DIRECTIVES_SHA256
from verify_promoted import verify as verify_frozen_v655, active
from verify_release import check_public_checksums

ROOT = Path(__file__).resolve().parents[1]


def verify(remote: bool = False, root: Path = ROOT) -> dict:
    current_spec = json.loads((root / "build/release_spec.json").read_text())
    archived = current_spec["stable_release_version"] != "v6.5.6"
    spec = json.loads((root / "build/baselines/v6.5.6/release_spec.json").read_text()) if archived else current_spec
    latest = json.loads((root / ("build/baselines/v6.5.6/release_manifest.json" if archived else "build/release_manifest.json")).read_text())
    frozen = json.loads((root / "build/baselines/v6.5.5/release_manifest.json").read_text())
    if spec["stable_release_version"] != "v6.5.6" or latest["label"] != "v6.5.6":
        raise ValueError("unexpected new release version")
    if any((
        spec.get("previous_formal_profile_sha256") != BASE_SHA256,
        spec.get("approved_runtime_directives_sha256") != "16c7ae59c51dc46ed92af8cb38d9aa2635062a0b1bbb5aa5ab21659600f539a9",
        spec.get("current_runtime_directives_sha256") != EXPECTED_DIRECTIVES_SHA256,
        latest.get("previous_release", {}).get("profile_sha256") != BASE_SHA256,
        latest.get("profile_sha256") != {"LoonKit.lcf": EXPECTED_SHA256},
        latest.get("runtime_change", {}).get("changed_options") != {
            "dns-reject-mode": {"before": "NOANSWER", "after": "LOOPBACKIP"}},
    )):
        raise ValueError("changed release identity or unapproved runtime delta")
    previous = frozen.copy()
    new = latest.copy()
    for key in ("label", "profile_sha256", "publication", "maintainer_approval", "device_test"):
        previous.pop(key, None)
        new.pop(key, None)
    for key in ("previous_release", "runtime_change"):
        new.pop(key, None)
    if new != previous:
        raise ValueError("immutable manifest fields changed")
    check_public_checksums(root, json.loads((root / "build/release_manifest.json").read_text()), current_spec)
    check_build(root)
    profile = (root / ("build/baselines/v6.5.6/LoonKit.lcf" if archived else "LoonKit.lcf")).read_bytes()
    if (hashlib.sha256(active(profile)).hexdigest() != EXPECTED_DIRECTIVES_SHA256 or
            b"\ndomain-reject-mode = DNS\n" not in profile or
            b"\ndns-reject-mode = LOOPBACKIP\n" not in profile or
            b"[Mitm]" in profile or b"skip-server-cert-verify = true" in profile):
        raise ValueError("unapproved global network or TLS change")
    old = verify_frozen_v655(remote=remote, root=root, historical_v655=True)
    return {"release":"v6.5.6", "remote_checked":remote,
            "resources":old["runtime_resources"], "matchers":old["runtime_matchers"],
            "previous_release":"v6.5.5", "sha256":EXPECTED_SHA256}
