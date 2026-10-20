#!/usr/bin/env python3
"""Privacy-first validator of manually collected Loon device results.

Does not run Loon, does not infer DNS leaks, and NEVER auto-assigns PASS.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import ipaddress
import json
import re
from pathlib import Path

VARIANTS = {"HISTORICAL", "PRODUCTION", "VNEXT"}
OUTCOMES = {"PASS", "FAIL", "UNKNOWN", "NOT_EXECUTED", "BLOCKED"}
NETWORK = {"WIFI", "CELLULAR", "ETHERNET", "UNKNOWN"}
IP_RESULT = {"IPv4_OK", "IPv6_OK", "NO_ROUTE", "FAILED", "NOT_AVAILABLE", "UNKNOWN"}
CONTEXT_FIELDS = ("device_alias", "client_version", "network_alias", "network_type",
                  "node_alias", "node_protocol", "dns_config_sha256", "tun_config_sha256")
REQUIRED = {"test_id", "configuration", "config_commit_sha", "rule_file_version",
            "device_alias", "client_version", "network_alias", "network_type",
            "node_alias", "node_protocol", "dns_config_sha256", "tun_config_sha256",
            "tested_at", "matched_rule", "selected_policy", "observed_egress",
            "observed_resolvers", "ipv4_result", "ipv6_result", "expected_match",
            "evidence", "conclusion"}
FORBIDDEN_KEYS = re.compile(r"(?i)(password|passwd|api.?key|bearer|secret|token|cookie|subscription.?url|private.?key)")
IPV4 = re.compile(r"(?<![a-zA-Z0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![a-zA-Z0-9])")
# Deliberately strict about submitted strings: public/private raw IPs are both
# prohibited in records committed to GitHub; use stable salted aliases instead.
IPV6 = re.compile(r"(?<![A-Za-z0-9:])(?:[0-9a-fA-F]{0,4}:){2,}[0-9a-fA-F:.]*(?![A-Za-z0-9:])")


def reject_private_data(value, path: str = ""):
    if isinstance(value, dict):
        for key, val in value.items():
            if FORBIDDEN_KEYS.search(key):
                raise ValueError("privacy-sensitive field prohibited: " + path + "/" + key)
            reject_private_data(val, path+"/"+key)
    elif isinstance(value, list):
        for i, val in enumerate(value):
            reject_private_data(val, path+"/"+str(i))
    elif isinstance(value, str):
        for hit in IPV4.findall(value):
            try:
                ipaddress.ip_address(hit)
            except ValueError:
                continue
            raise ValueError("raw IPv4 address must be redacted: " + path)
        if IPV6.search(value):
            raise ValueError("raw IPv6 address must be redacted: " + path)
        if re.search(r"(?i)(https?://\S*[?&](?:key|token|auth)=|bearer\s+\S+)", value):
            raise ValueError("credential-like evidence must be redacted: " + path)


def validate(doc: dict) -> dict:
    if doc.get("schema_version") != 1 or not isinstance(doc.get("results"), list):
        raise ValueError("missing result schema_version/results")
    rows = doc["results"]
    reject_private_data(doc)
    seen, contexts = set(), defaultdict(list)
    counts = Counter()
    for row in rows:
        missing = REQUIRED - row.keys()
        if missing:
            raise ValueError("missing mandatory result fields: " + ", ".join(sorted(missing)))
        test_id = row["test_id"]
        conf = row["configuration"]
        if not isinstance(test_id, str) or not re.fullmatch(r"[a-zA-Z0-9_.-]{3,100}", test_id):
            raise ValueError("invalid test id")
        if conf not in VARIANTS:
            raise ValueError("unknown configuration variant")
        if (test_id, conf) in seen:
            raise ValueError("duplicate test/configuration record")
        seen.add((test_id, conf))
        sha = row["config_commit_sha"]
        if sha != "UNKNOWN" and not re.fullmatch("[0-9a-f]{40}", sha):
            raise ValueError("configuration commit must be full SHA or UNKNOWN")
        if row["network_type"] not in NETWORK:
            raise ValueError("unsupported network type")
        if row["conclusion"] not in OUTCOMES:
            raise ValueError("invalid conclusion")
        if row["ipv4_result"] not in IP_RESULT or row["ipv6_result"] not in IP_RESULT:
            raise ValueError("invalid IPv4/IPv6 observation")
        if not isinstance(row["observed_resolvers"], list):
            raise ValueError("resolver list must be present (possibly empty)")
        if row["expected_match"] not in (True, False, "UNKNOWN"):
            raise ValueError("expected_match is true/false/UNKNOWN")
        stamp = row["tested_at"]
        if stamp != "UNKNOWN":
            dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                raise ValueError("test time must include zone")
        if row["conclusion"] == "PASS":
            if row["expected_match"] is not True or row["config_commit_sha"] == "UNKNOWN":
                raise ValueError("PASS needs explicit positive observation and pinned commit")
            if any(row[k] == "UNKNOWN" for k in ("matched_rule", "selected_policy",
                                                 "observed_egress", "tested_at", "evidence")):
                raise ValueError("PASS cannot have unknown core evidence")
        if row["conclusion"] == "FAIL" and row["expected_match"] is True:
            raise ValueError("FAIL contradicts explicit expected_match=true")
        if row["conclusion"] in {"NOT_EXECUTED", "UNKNOWN"} and row["expected_match"] is True:
            raise ValueError("cannot attest match without testing")
        contexts[test_id].append(row)
        counts[row["conclusion"]] += 1
    for test_id, members in contexts.items():
        if len(members) <= 1:
            continue
        for key in CONTEXT_FIELDS:
            values = {json.dumps(m[key], sort_keys=True) for m in members}
            if len(values) > 1:
                raise ValueError("uncontrolled A/B comparison change: " + test_id + "/" + key)
    return {"total_records": len(rows), "outcomes": dict(sorted(counts.items())),
            "three_way_comparisons": sum(len(x)==3 for x in contexts.values()),
            "partially_observed_cases": sum(len(x)!=3 for x in contexts.values()),
            "device_validation": "NOT_EXECUTED" if not rows else "RESULTS_RECEIVED_NOT_AUTOMATICALLY_ATTESTED"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("results_json", type=Path)
    a = p.parse_args()
    print(json.dumps(validate(json.loads(a.results_json.read_text(encoding="utf-8"))),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
