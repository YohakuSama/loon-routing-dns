#!/usr/bin/env python3
"""Build the v6.5.5 formal entry from the immutable beta.4 candidate."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
from verify_promoted import active, CANDIDATE_SHA

ROOT = Path(__file__).resolve().parents[1]
HEAD = ("# LoonKit v6.5.5\n"
        "# Maintainer: @YohakuSama\n"
        "# Repository: https://github.com/YohakuSama/loonkit\n"
        "# Community configuration; not affiliated with Loon.\n\n")
SECTION_NOTES = {
    "General": "# Default DNS is AliDNS. DNS fallback depends on Loon settings.",
    "Remote Proxy": "# Add your own proxy nodes or subscriptions in Loon.",
    "Remote Filter": "# All subscribed nodes are eligible by default.",
    "Proxy Group": "# Select routes using these service policies.",
    "Remote Rule": "# Immutable rule snapshots. Disable only Beta-AdBlock-Balanced to restore service routing.",
    "Rule": "# Local exceptions precede remote rules.",
    "Plugin": "# Network diagnostics plugin.",
}


def render(root: Path = ROOT) -> bytes:
    source = (root / "beta/LoonKit.lcf").read_bytes()
    if hashlib.sha256(source).hexdigest() != CANDIDATE_SHA:
        raise ValueError("tested beta profile bytes changed")
    if not source.startswith(b"# LoonKit v6.5.5-beta.4"):
        raise ValueError("candidate version changed")
    out = HEAD
    for line in source.decode("utf-8").split("\n")[1:]:
        if line.strip().startswith("#"):
            continue
        hit = re.fullmatch(r"\[([^\]]+)\]", line)
        if hit:
            out += line + "\n"
            if hit[1] in SECTION_NOTES:
                out += SECTION_NOTES[hit[1]] + "\n"
        else:
            out += line + "\n"
    out = re.sub(r"\n{4,}", "\n\n\n", out).rstrip() + "\n"
    data = out.encode("utf-8")
    if active(data) != active(source):
        raise ValueError("migration modified effective directives")
    return data


def check(root: Path = ROOT) -> dict:
    data = render(root)
    new = json.loads((root / "build/release_spec.json").read_text())["stable_release_version"] == "v6.5.6"
    target = root / ("build/baselines/v6.5.5/LoonKit.lcf" if new else "LoonKit.lcf")
    if data != target.read_bytes():
        raise ValueError("formal candidate is not reproducible")
    release = json.loads((root / ("build/baselines/v6.5.5/release_manifest.json" if new else "build/release_manifest.json")).read_text())
    if hashlib.sha256(data).hexdigest() != release["profile_sha256"]["LoonKit.lcf"]:
        raise ValueError("formal manifest does not match renderer")
    return {"version": "v6.5.5", "sha256": hashlib.sha256(data).hexdigest(),
            "effective_directives_sha256": hashlib.sha256(active(data)).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(check(), sort_keys=True))
