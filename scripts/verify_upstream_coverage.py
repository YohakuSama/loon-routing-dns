#!/usr/bin/env python3
"""Evaluate completeness of the read-only upstream review, not release approval."""
import argparse
import json
import os
from pathlib import Path


def assess(report: dict, source_catalog: dict) -> dict:
    entries = source_catalog["sources"]
    expected_ids = [entry["id"] for entry in entries]
    seen = report.get("sources", [])
    observed_ids = [entry.get("id") for entry in seen]
    problems = []
    if len(expected_ids) != len(set(expected_ids)):
        problems.append("Duplicate source IDs in source catalog")
    if len(observed_ids) != len(set(observed_ids)):
        problems.append("Duplicate source IDs in review result")
    missing = sorted(set(expected_ids) - set(observed_ids))
    unexpected = sorted(set(observed_ids) - set(expected_ids))
    if missing:
        problems.append("Missing source IDs: " + ", ".join(missing))
    if unexpected:
        problems.append("Unexpected source IDs: " + ", ".join(unexpected))
    count = len(expected_ids)
    if report.get("source_count") != count:
        problems.append(f"Catalog count mismatch: {report.get('source_count')} vs {count}")
    if report.get("snapshot_count") != count:
        problems.append(f"Raw snapshots incomplete: {report.get('snapshot_count')} vs {count}")
    for entry in seen:
        sid = entry.get("id", "<missing>")
        if entry.get("status") != "PARSED_FOR_REVIEW":
            problems.append(f"{sid}: {entry.get('status', 'missing status')}")
        if entry.get("invalid_count", 0) != 0:
            problems.append(f"{sid}: {entry.get('invalid_count')} unparsed lines")
        if entry.get("minimum_satisfied") is not True:
            problems.append(f"{sid}: minimum source size not met or unchecked")
        if not entry.get("sha256"):
            problems.append(f"{sid}: missing content hash")
    if report.get("incomplete_sources") != 0:
        problems.append(f"Declared incomplete source count: {report.get('incomplete_sources')}")
    if report.get("incomplete_groups"):
        problems.append("Incomplete groups: " + ", ".join(report["incomplete_groups"]))
    if report.get("publication_allowed") is not False:
        problems.append("Unapproved rule publication guard missing")
    return {"coverage_complete": not problems, "checked": len(seen),
            "expected": count, "snapshot_count": report.get("snapshot_count"),
            "problems": problems}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--catalog", type=Path, default=Path("rules/sources.json"))
    args = p.parse_args()
    if not args.report.is_file():
        print("INCOMPLETE: no upstream review report generated.")
        return 1
    result = assess(json.loads(args.report.read_text(encoding="utf-8")),
                    json.loads(args.catalog.read_text(encoding="utf-8")))
    summary = ("## Upstream source coverage (not release approval)\n"
               f"- Reviewed: {result['checked']}/{result['expected']}\n"
               f"- Raw snapshots: {result['snapshot_count']}/{result['expected']}\n"
               f"- Full coverage: {'YES' if result['coverage_complete'] else 'NO'}\n"
               "- Published rules unchanged.\n")
    for item in result["problems"]:
        summary += f"- Issue: {item}\n"
    print(summary)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fd:
            fd.write(summary)
    return 0 if result["coverage_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
