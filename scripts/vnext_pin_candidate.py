#!/usr/bin/env python3
"""Emit an immutable-commit vNext test config WITHOUT touching production."""
from __future__ import annotations
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "refactor/vnext/LoonKit.vNext.Candidate.lcf"
PREFIX = "https://raw.githubusercontent.com/YohakuSama/loonkit/"
MOVING = PREFIX + "refactor/loonkit-vnext/refactor/vnext/generated/"


def pin(commit: str, config: str) -> str:
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("full immutable Git commit SHA required")
    if "https://raw.githubusercontent.com/YohakuSama/loonkit/main/rules/generated/" in config:
        raise ValueError("production rule subscription present in candidate")
    count = config.count(MOVING)
    if count != 26:
        raise ValueError(f"expected 26 candidate resources; found {count}")
    return config.replace(MOVING, PREFIX + commit + "/refactor/vnext/generated/")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--commit", required=True)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    out = a.output.resolve()
    if out.is_relative_to(ROOT.resolve()):
        raise ValueError("immutable test config must be written OUTSIDE the repo")
    cfg = pin(a.commit, SRC.read_text(encoding="utf-8"))
    out.write_text(cfg, encoding="utf-8")
    print(f"wrote private acceptance copy to {out}; source ref {a.commit}")


if __name__ == "__main__":
    main()
