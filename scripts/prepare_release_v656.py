#!/usr/bin/env python3
"""Rebuild the v6.5.6 profile from the verified v6.5.5 release."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from verify_promoted import active

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA256 = "d97984a42e313e5b4fc81c26ce760fd4d1163275ad7278e3930cbce69dcf9f03"
EXPECTED_SHA256 = "d75c37a9dc0dcb8a109c1cdaa0cae647a95b7f70dcf22ec94a5e1ac179528b11"
EXPECTED_DIRECTIVES_SHA256 = "e19dc446bddf93fea2d3c31367325ede139b725fdb4b08b7c82f11d40c60fb12"
OLD = b"\ndns-reject-mode = NOANSWER\n"
NEW = b"\ndns-reject-mode = LOOPBACKIP\n"


def render(root: Path = ROOT) -> bytes:
    frozen = (root / "build/baselines/v6.5.5/LoonKit.lcf").read_bytes()
    if hashlib.sha256(frozen).hexdigest() != BASE_SHA256:
        raise ValueError("v6.5.5 historical profile was modified")
    if not frozen.startswith(b"# LoonKit v6.5.5\n") or frozen.count(OLD) != 1:
        raise ValueError("unexpected v6.5.5 source")
    output = frozen.replace(b"# LoonKit v6.5.5\n", b"# LoonKit v6.5.6\n", 1).replace(OLD, NEW, 1)
    if hashlib.sha256(output).hexdigest() != EXPECTED_SHA256:
        raise ValueError("unapproved current profile bytes")
    if hashlib.sha256(active(output)).hexdigest() != EXPECTED_DIRECTIVES_SHA256:
        raise ValueError("unapproved active directive bytes")
    return output


def check(root: Path = ROOT) -> dict:
    output = render(root)
    historical = json.loads((root / "build/release_spec.json").read_text())["stable_release_version"] != "v6.5.6"
    prefix = "build/baselines/v6.5.6/" if historical else ""
    if output != (root / (prefix + "LoonKit.lcf")).read_bytes():
        raise ValueError("current v6.5.6 profile does not reproduce")
    release = json.loads((root / (prefix + "release_manifest.json" if historical else "build/release_manifest.json")).read_text())
    if release["label"] != "v6.5.6" or release["profile_sha256"] != {"LoonKit.lcf": EXPECTED_SHA256}:
        raise ValueError("release manifest version/hash mismatch")
    return {"version": "v6.5.6", "sha256": EXPECTED_SHA256}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(check(), sort_keys=True))
