#!/usr/bin/env python3
"""Preview a traceable future PINNED_RAW_UPSTREAM feed; NEVER activate it.

Trace: pinned bytes -> original line -> normalization -> rule decision ->
deduplication -> ownership -> output line. A preview has zero publishing power.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vnext_source_lock import ROOT, LOCK, check_lock, read_json
from vnext_rule_engine import load_manifest, normalize, filter_rule, fields


def trace_bytes(data: bytes, *, source_id: str, origin_path: str,
                group: str, manifest: dict, protected: tuple[str, ...] = ()) -> tuple[list[dict], list[str]]:
    try:
        content = data.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("raw upstream input is not valid UTF-8") from exc
    if not group or group not in manifest["active_groups"]:
        raise ValueError("target policy is not an active candidate group")
    seen = {}
    emitted = []
    records = []
    for line_number, raw in enumerate(content.splitlines(), 1):
        event = {
            "source_id": source_id,
            "original_file": origin_path,
            "original_line": line_number,
            "original_text": raw,
            "policy": group,
            "candidate_activation": "DISABLED_PREVIEW_ONLY",
            "normalization": None,
            "candidate_rule": None,
            "output_line": None,
            "reason": None,
            "action": None,
        }
        try:
            rule = normalize(raw)
        except ValueError as exc:
            event["action"] = "QUARANTINED"
            event["reason"] = "PARSER_REJECTED: " + str(exc)
            records.append(event)
            continue
        if rule is None:
            event["action"] = "IGNORED_COMMENT_OR_EMPTY"
            event["reason"] = "NO_RULE"
            records.append(event)
            continue
        event["normalization"] = rule
        candidate, reason, replacement = filter_rule(
            group, rule, protected, manifest.get("reviewed_keyword_narrowing", {}),
            tuple(manifest.get("reviewed_multi_tenant_suffixes", ())),
            manifest.get("reviewed_multi_tenant_keywords", {}))
        if candidate is None:
            event["action"] = "ISOLATED"
            event["reason"] = reason
            event["replacement"] = replacement
        elif candidate in seen:
            event["action"] = "DEDUPLICATED"
            event["reason"] = "IDENTICAL_NORMALIZED_RULE"
            event["candidate_rule"] = candidate
            event["output_line"] = seen[candidate]
            event["replacement"] = candidate
        else:
            emitted.append(candidate)
            seen[candidate] = len(emitted)
            event["action"] = "MODIFIED" if candidate != rule else "RETAINED"
            event["reason"] = reason or ("NORMALIZATION_ONLY" if raw.strip() != rule else "UNCHANGED")
            event["candidate_rule"] = candidate
            event["output_line"] = len(emitted)
            event["replacement"] = candidate
        records.append(event)
    return records, emitted


def trace_locked_source(root: Path, source_id: str) -> dict:
    integrity = check_lock(root)
    lock = read_json(root / LOCK)
    found = [x for x in lock["inputs"] if x["source_id"] == source_id]
    if len(found) != 1:
        raise ValueError("source ID not in immutable lock")
    src = found[0]
    if src["input_kind"] != "PINNED_RAW_UPSTREAM":
        raise ValueError("merged snapshots cannot masquerade as raw source")
    cfg = load_manifest(root/"refactor/vnext/engine_manifest.json")
    guardrails = read_json(root/"rules/routing_guardrails.json")
    records, emitted = trace_bytes(
        (root / src["path"]).read_bytes(),
        source_id=src["source_id"], origin_path=src["path"],
        group=src["policy"], manifest=cfg,
        protected=tuple(guardrails["protected_proxy_domains"]))
    return {
        "mode": "RAW_UPSTREAM_PREVIEW_NOT_CANDIDATE_ACTIVATION",
        "source_id": source_id,
        "input_sha256": src["sha256"],
        "immutable_ref": src["immutable_ref"],
        "verified_inputs_in_lock": integrity["verified_frozen_inputs"]+integrity["verified_raw_inactive_inputs"],
        "emitted_rules_preview": emitted,
        "trace": records,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source-id", required=True)
    p.add_argument("--output", type=Path, required=True,
                   help="local review JSON output (not a live candidate)")
    a = p.parse_args()
    result = trace_locked_source(ROOT, a.source_id)
    output = a.output.resolve()
    if output.is_relative_to(ROOT.resolve()):
        raise ValueError("write trace preview outside repository for explicit review")
    output.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)+"\n",
                      encoding="utf-8")
    print(f"trace for {result['source_id']} written to {output}")


if __name__ == "__main__":
    main()
