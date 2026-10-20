#!/usr/bin/env python3
"""Exhaustive and conservative domain parent/child overlap dispositions.

Reports predicate intersection, NOT observed Loon routing. No implicit claims
about precedence, CDN ownership or human-reviewed service classification.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = Path("refactor/vnext/reports/domain_parent_child_conflicts.jsonl")
PROVENANCE = Path("refactor/vnext/reports/provenance.tsv")
DISPOSITIONS = Path("refactor/vnext/reports/conflict_dispositions.jsonl")
SUMMARY = Path("refactor/vnext/reports/conflict_summary.phase05.json")
SHARD_SIZE = 950
DIRECT = {"ChinaDirect", "DomesticCore", "SteamCN", "AppleOTA"}
ADVERTISING = "AdBlock"
SHARED_CDN = ("cloudfront.net", "akamaized.net", "akamaihd.net", "edgesuite.net",
              "fastly.net", "akadns.net")
SHARED_AUTH = ("auth0.com", "microsoftonline.com", "login.live.com", "accounts.google.com")
SHARED_PAYMENT = ("stripe.com", "paypal.com")
SHARED_INFRA = ("windows.net", "appspot.com", "blogspot.com", "azureedge.net")
PRIORITY_PAIRS = {
    frozenset(x.split(":")) for x in (
        "AdBlock:ChinaDirect", "Microsoft:ChinaDirect", "AdBlock:Microsoft",
        "AdBlock:Disney", "Bilibili:ChinaDirect", "AI:Google",
        "Google:YouTube", "Apple:ChinaDirect",
    )
}


def suffix_cover(parent: str, child: str) -> bool:
    return child == parent or child.endswith("." + parent)


def rule_values(p: str, c: str) -> tuple[str, str]:
    kind_p, dom_p = p.split(",", 1)
    kind_c, dom_c = c.split(",", 1)
    if kind_p != "DOMAIN-SUFFIX" or kind_c not in {"DOMAIN", "DOMAIN-SUFFIX"}:
        raise ValueError("non-domain ancestor case in parent-child ledger")
    if not suffix_cover(dom_p, dom_c):
        raise ValueError("incorrect reported ancestor relationship")
    return dom_p, dom_c


def read_origins(root: Path) -> dict[tuple[str, str], tuple[str, int]]:
    origins = {}
    with (root / PROVENANCE).open(encoding="utf-8") as f:
        if f.readline().rstrip("\n") != "group\trule\tsnapshot_file\tsnapshot_line\tpossible_upstream_source_ids":
            raise ValueError("unexpected provenance format")
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) != 5:
                raise ValueError("invalid provenance row")
            origins.setdefault((p[0], p[1]), (p[2], int(p[3])))
    return origins


def classify(row: dict, origins: dict) -> dict:
    pg, cg = row["parent_group"], row["child_group"]
    pr, cr = row["parent_rule"], row["child_rule"]
    root, child = rule_values(pr, cr)
    pid = hashlib.sha256("\x00".join((pg, pr, cg, cr)).encode()).hexdigest()[:24]
    if (pg, pr) not in origins or (cg, cr) not in origins:
        raise ValueError("parent/child not in pinned retained candidate provenance: " + pid)
    pfile, pline = origins[(pg, pr)]
    cfile, cline = origins[(cg, cr)]
    same_effect = pg in DIRECT and cg in DIRECT
    cls = "UNVERIFIED_RUNTIME_PRECEDENCE"
    if same_effect:
        cls = "SAME_EFFECT_REDUNDANCY"
    elif ADVERTISING in (pg, cg):
        cls = "ADBLOCK_OVERLAP"
    elif any(suffix_cover(shared, root) or suffix_cover(shared, child)
             for shared in SHARED_PAYMENT):
        cls = "SHARED_PAYMENT"
    elif any(suffix_cover(shared, root) or suffix_cover(shared, child)
             for shared in SHARED_AUTH):
        cls = "SHARED_AUTH"
    elif any(suffix_cover(shared, root) or suffix_cover(shared, child)
             for shared in SHARED_CDN):
        cls = "SHARED_CDN"
    elif any(suffix_cover(shared, root) or suffix_cover(shared, child)
             for shared in SHARED_INFRA):
        cls = "SHARED_INFRASTRUCTURE"
    elif pg in DIRECT or cg in DIRECT:
        cls = "DIRECT_OVERLAP"
    # All cross-policy ownership claims remain unverified without runtime
    # precedence proof; business-name substrings do NOT make them VERIFIED.
    needs_device = not same_effect
    severe = ((pg == ADVERTISING and cg in DIRECT) or
              (cg == ADVERTISING and pg in DIRECT))
    high_priority = frozenset({pg, cg}) in PRIORITY_PAIRS
    return {
        "conflict_id": "PH05-DOM-" + pid,
        "parent_rule": pr, "parent_policy": "DIRECT" if pg in DIRECT else pg,
        "parent_group": pg, "parent_file": pfile, "parent_line": pline,
        "parent_rule_type": pr.split(",", 1)[0],
        "child_rule": cr, "child_policy": "DIRECT" if cg in DIRECT else cg,
        "child_group": cg, "child_file": cfile, "child_line": cline,
        "child_rule_type": cr.split(",", 1)[0],
        "overlap_condition": "CHILD_DOMAIN_WITHIN_PARENT_SUFFIX",
        "static_matching_example": child,
        "classification": cls,
        "evidence_status": ("EQUIVALENT_DIRECT_POLICY_ONLY" if same_effect
                            else "STATIC_OVERLAP_RUNTIME_PRECEDENCE_NOT_PROVEN"),
        "risk": "HIGH" if severe else "MEDIUM" if needs_device else "LOW",
        "actual_candidate_disposition": "RETAINED_NO_CHANGE",
        "status": "VERIFIED_ACCEPTABLE" if same_effect else "REQUIRES_RUNTIME_TEST",
        "requires_device_validation": needs_device,
        "priority_business_pair": high_priority,
        "notes": ("Static equivalent DIRECT outcome; kept to avoid changing precedence."
                  if same_effect else
                  "No service ownership/precedence proof. Retain candidate pending real Loon test."),
    }


def generate(root: Path = ROOT) -> tuple[dict[str, str], dict]:
    origins = read_origins(root)
    counts, parents, pairs = Counter(), Counter(), Counter()
    seen = set()
    out = []
    with (root / REPORT).open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = classify(json.loads(line), origins)
            if row["conflict_id"] in seen:
                raise ValueError("duplicate conflict pair")
            seen.add(row["conflict_id"])
            out.append(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            counts[row["classification"]] += 1
            parents[row["parent_rule"]] += 1
            pairs[row["parent_group"]+"|"+row["child_group"]] += 1
    if not out:
        raise ValueError("empty legacy conflict ledger")
    summary = {
        "schema_version": 1,
        "input_report": str(REPORT),
        "total_observed": len(out),
        "total_disposed": len(seen),
        "classification_counts": dict(sorted(counts.items())),
        "top_parent_rules": [{"rule": k, "count": v} for k, v in parents.most_common(30)],
        "policy_pairs": dict(sorted(pairs.items())),
        "verified_equivalent_direct_count": counts["SAME_EFFECT_REDUNDANCY"],
        "actual_candidate_modifications": 0,
        "runtime_test_count": len(out)-counts["SAME_EFFECT_REDUNDANCY"],
        "release_claim": "NOT_READY_FOR_PRODUCTION",
        "warning": "Machine-classified observations, not adjudicated Loon routing results.",
    }
    shard_entries = []
    files = {}
    for offset in range(0, len(out), SHARD_SIZE):
        part = offset // SHARD_SIZE + 1
        relative = DISPOSITIONS.with_name(f"conflict_dispositions.part{part:02d}.jsonl")
        block = out[offset:offset + SHARD_SIZE]
        files[str(relative)] = "".join(block)
        shard_entries.append({"path": str(relative), "rows": len(block)})
    summary["shards"] = shard_entries
    summary["shard_size"] = SHARD_SIZE
    files[str(SUMMARY)] = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return files, summary


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--generate", action="store_true")
    p.add_argument("--check", action="store_true")
    p.add_argument("--summary", action="store_true")
    a = p.parse_args()
    if sum((a.generate, a.check, a.summary)) != 1:
        p.error("choose one mode")
    files, summary = generate()
    if a.check:
        for relative, content in files.items():
            if not (ROOT/relative).is_file() or (ROOT/relative).read_text(encoding="utf-8") != content:
                raise ValueError("stale/uncommitted conflict disposition artifact: " + relative)
    if a.generate:
        for relative, content in files.items():
            (ROOT / relative).write_text(content, encoding="utf-8")
        # The single combined ledger is an optional untracked maintainer export;
        # committed and checked source of truth is the complete numbered shard set.
        combined = "".join(files[item["path"]] for item in summary["shards"])
        (ROOT / DISPOSITIONS).write_text(combined, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
