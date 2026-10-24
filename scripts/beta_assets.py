#!/usr/bin/env python3
"""Deterministically compile the beta-only overlays from one reviewed policy input.

Does not edit production snapshots. Use --check before publishing any candidate.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFINITION = ROOT / "rules/beta/policy_overrides.json"


def render(root: Path = ROOT) -> dict[str, bytes]:
    spec = json.loads((root / "rules/beta/policy_overrides.json").read_text(encoding="utf-8"))
    if spec.get("schema_version") != 1:
        raise ValueError("unreviewed beta policy schema")
    prefix = "rules/beta/" + spec["version"] + "/"
    rules = {"RoutingAdBlock": spec["adblock_local_rules"],
             "SteamCN": spec["steamcn_mainland_candidates"],
             "SteamGlobal": spec["steam_global_rules"],
             "AIScoped": spec["ai_scoped_rules"]}
    for group, entries in spec["service_groups"].items():
        rules["Service-" + group] = entries
    paths = {}
    for group, entries in sorted(rules.items()):
        if not entries or len(entries) != len(set(entries)):
            raise ValueError("empty or duplicate beta rules: " + group)
        if any(not rule.startswith(("DOMAIN,", "DOMAIN-SUFFIX,")) or rule.count(",") != 1
               for rule in entries):
            raise ValueError("unsupported beta overlay matcher: " + group)
        paths[prefix + group + ".list"] = (
            "# LoonKit " + spec["version"] + " immutable beta overlay; generated from rules/beta/policy_overrides.json\n"
            + "\n".join(entries) + "\n").encode("utf-8")
    return paths


def check(root: Path = ROOT) -> None:
    files = render(root)
    for path, data in files.items():
        if not (root / path).is_file() or (root / path).read_bytes() != data:
            raise ValueError("beta overlay not reproducible: " + path)
    directory = root / "rules/beta" / json.loads(DEFINITION.read_text())["version"]
    actual = {p.relative_to(root).as_posix() for p in directory.glob("*.list")}
    if actual != set(files):
        raise ValueError("unexpected or missing beta overlay files")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true", required=True)
    p.parse_args()
    check()
    print("beta overlays reproduce from reviewed input")
