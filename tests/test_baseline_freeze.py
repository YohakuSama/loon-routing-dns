#!/usr/bin/env python3
"""Offline integrity tests for the Phase 01 Git-pinned routing inventory."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_baselines import compare_rule_sets, make_report, parse_rule, render_markdown

JSON_FILES = (
    "baselines/legacy/manifest.json", "baselines/legacy/sources.json",
    "baselines/current/manifest.json", "baselines/current/rule-index.json",
)


def data_file(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def pinned_bytes(commit, path):
    """Do not use mutable main or upstream network URLs for integrity checks."""
    if not re.fullmatch(r"[a-f0-9]{40}", commit) or path.startswith("/") or ".." in Path(path).parts:
        raise ValueError("invalid pinned Git object spec")
    try:
        return subprocess.run(
            ["git", "show", commit + ":" + path], cwd=ROOT, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("missing pinned Git blob " + commit + ":" + path) from exc


def section(contents, heading):
    pattern = re.compile(r"(?m)^\[" + re.escape(heading) + r"\]\s*$")
    match = pattern.search(contents)
    if not match:
        raise ValueError("missing Loon section " + heading)
    rest = contents[match.end():]
    nxt = re.search(r"(?m)^\[[^\]]+\]\s*$", rest)
    rest = rest[:nxt.start()] if nxt else rest
    return [s.strip() for s in rest.splitlines()
            if s.strip() and not s.lstrip().startswith("#")]


def remote_line(line):
    parts = [p.strip() for p in line.split(",")]
    if not parts[0].startswith("https://"):
        raise ValueError("bad remote list URL")
    opts = {}
    for p in parts[1:]:
        if "=" not in p:
            raise ValueError("bad remote option")
        key, value = map(str.strip, p.split("=", 1))
        if key in opts:
            raise ValueError("duplicate remote option")
        opts[key] = value
    return parts[0], opts


class BaselineFreeze(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = data_file(JSON_FILES[0])
        cls.old_sources = data_file(JSON_FILES[1])
        cls.current = data_file(JSON_FILES[2])
        cls.index = data_file(JSON_FILES[3])

    def check_hash(self, record, commit):
        self.assertRegex(record["sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(record["git_blob_sha1"], r"^[0-9a-f]{40}$")
        blob = pinned_bytes(commit, record["path"])
        self.assertEqual(record["bytes"], len(blob), record["path"])
        self.assertEqual(record["sha256"], hashlib.sha256(blob).hexdigest(), record["path"])
        object_payload = b"blob " + str(len(blob)).encode("ascii") + b"\0" + blob
        self.assertEqual(record["git_blob_sha1"], hashlib.sha1(object_payload).hexdigest(), record["path"])
        return blob

    def test_schema_json_and_git_revisions(self):
        for p in JSON_FILES:
            obj = data_file(p)
            self.assertEqual(obj["schema_version"], 1, p)
            self.assertTrue(obj["baseline_name"], p)
            self.assertEqual(obj["source_repository"], "https://github.com/YohakuSama/loonkit")
            self.assertRegex(obj["source_commit"], r"^[a-f0-9]{40}$")
        self.assertEqual(self.old["source_commit"], self.old_sources["source_commit"])
        self.assertEqual(self.current["source_commit"], self.index["source_commit"])
        self.assertNotEqual(self.old["source_commit"], self.current["source_commit"])

    def test_legacy_original_git_config_and_inventory_match(self):
        files = {rec["path"]: rec for rec in self.old["files"]}
        config = self.check_hash(files["Loon_Routing_DNS.lcf"], self.old["source_commit"]).decode("utf-8")
        inv = json.loads(self.check_hash(files["rules/verified-routing-baseline.json"],
                                         self.old["inventory_source_commit"]))
        self.assertEqual(inv["source_commit"], self.old["source_commit"])
        self.assertEqual(inv["remote_rules"], section(config, "Remote Rule"))
        self.assertEqual(inv["local_rules"], section(config, "Rule"))
        self.assertEqual(section(config, "Proxy Group"), self.old_sources["proxy_group_definitions"])
        self.assertEqual(len(inv["remote_rules"]), self.old["remote_subscription_count"])
        self.assertEqual(len(inv["local_rules"]), self.old["local_rule_count"])

    def test_legacy_order_and_terminals(self):
        rr = self.old_sources["remote_rules"]
        lr = self.old_sources["local_rules"]
        self.assertEqual([r["order"] for r in rr], list(range(1, len(rr) + 1)))
        self.assertEqual([r["order"] for r in lr], list(range(1, len(lr) + 1)))
        self.assertEqual(len(rr), self.old["remote_subscription_count"])
        self.assertEqual(len(lr), self.old["local_rule_count"])
        self.assertEqual([r["rule"] for r in lr][-2:],
                         ["GEOIP,CN,DIRECT,no-resolve", "FINAL,Final"])
        self.assertEqual([r["rule"] for r in lr][-2:], self.old_sources["terminal_rules"])
        for r in rr:
            self.assertTrue(r["url"].startswith(
                "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/"))
            self.assertEqual(r["enabled"], "true")
            self.assertTrue(r["policy"] and r["tag"])

    def test_current_pinned_manifest_files(self):
        seen = set()
        for r in self.current["files"]:
            self.assertNotIn(r["path"], seen)
            seen.add(r["path"])
            self.check_hash(r, self.current["source_commit"])
        self.assertIn("LoonKit.lcf", seen)
        self.assertIn("LoonKit.PrivacyDNS.lcf", seen)
        self.assertIn("scripts/build_composite_rules.py", seen)

    def test_subscription_order_and_config_binding(self):
        idx = self.index
        subs = idx["subscriptions"]
        self.assertEqual(idx["subscription_count"], len(subs))
        self.assertEqual(self.current["remote_subscription_count"], len(subs))
        self.assertEqual([r["order"] for r in subs], list(range(1, len(subs) + 1)))
        self.assertEqual(sum(r["group"] != "ProxyProtect" for r in subs),
                         self.current["generated_group_count"])
        self.assertEqual(sum(r["group"] == "ProxyProtect" for r in subs), 1)
        self.assertEqual(len({r["path"] for r in subs}), len(subs))
        self.assertEqual(idx["local_rules"][-2:],
                         ["GEOIP,CN,DIRECT,no-resolve", "FINAL,Final"])
        for path in idx["configuration_files"]:
            conf = pinned_bytes(self.current["source_commit"], path).decode("utf-8")
            self.assertEqual(section(conf, "Rule"), idx["local_rules"])
            self.assertEqual(section(conf, "Proxy Group"), idx["proxy_group_definitions"])
            lines = section(conf, "Remote Rule")
            self.assertEqual(len(lines), len(subs))
            for original, entry in zip(lines, subs):
                url, options = remote_line(original)
                self.assertEqual(url, entry["url"])
                self.assertEqual(url.rsplit("/main/", 1)[-1], entry["path"])
                self.assertEqual(options["policy"], entry["policy"])
                self.assertEqual(options["tag"], entry["tag"])
                self.assertEqual(options["enabled"], str(entry["enabled"]).lower())
        order = json.loads(pinned_bytes(self.current["source_commit"],
                                       "rules/active_profile.json"))["group_order"]
        self.assertEqual(order, [r["group"] for r in subs])

    def test_all_34_rule_blobs_types_policies_and_audit(self):
        audit = json.loads(pinned_bytes(self.current["source_commit"],
                                       "rules/generated/audit.json"))
        for r in self.index["subscriptions"]:
            raw = self.check_hash(r, self.current["source_commit"]).decode("utf-8")
            types = Counter()
            for rule in raw.splitlines():
                rule = rule.strip()
                if not rule or rule.startswith(("#", "//", ";")):
                    continue
                self.assertIn(",", rule, r["path"])
                types[rule.split(",", 1)[0].strip()] += 1
            self.assertEqual(r["rule_count"], sum(types.values()), r["path"])
            self.assertEqual(r["rule_types"], dict(types), r["path"])
            self.assertTrue(r["policy"], r["path"])
            if r["group"] != "ProxyProtect":
                self.assertEqual(audit["group_sizes"][r["group"]], r["rule_count"])

    def test_all_enabled_input_sources(self):
        catalog = json.loads(pinned_bytes(self.current["source_commit"],
                                          "rules/sources.json"))
        enabled = [s for s in catalog["sources"] if s.get("enabled") is True]
        self.assertEqual(self.current["enabled_input_count"], len(enabled))
        self.assertEqual(self.current["candidate_input_count"],
                         len(catalog.get("candidates", [])))
        self.assertEqual(len({s["id"] for s in enabled}), len(enabled))
        reference = [
            {"id": s["id"], "group": s["group"], "policy": s["policy"],
             "role": s["role"], "format": s["format"],
             "source": s.get("url") or s.get("path") or None}
            for s in enabled
        ]
        self.assertEqual(reference, self.index["enabled_sources"])

    def test_no_credentials_in_baseline_artifacts(self):
        secret = re.compile(r"(?i)(password|passwd|api[_-]?key|access[_-]?token)\s*[=:]\s*[^,}\s\"]+")
        for path in JSON_FILES:
            content = (ROOT / path).read_text(encoding="utf-8")
            self.assertNotRegex(content, secret)
            self.assertNotIn("-----BEGIN PRIVATE KEY-----", content)
            object_data = data_file(path)
            for item in object_data.get("remote_rules", []) + object_data.get("subscriptions", []):
                url = urlsplit(item["url"])
                self.assertEqual(url.scheme, "https")
                self.assertEqual(url.hostname, "raw.githubusercontent.com")
                self.assertFalse(url.username or url.password)
                self.assertNotRegex(url.query, r"(?i)(password|token|key)=")
        for row in self.index["enabled_sources"]:
            uri = row["source"]
            if uri and uri.startswith("https://"):
                self.assertFalse(urlsplit(uri).username)

    def test_no_fabricated_historical_content(self):
        self.assertEqual(self.old["historical_upstream_content_status"],
                         "HISTORICAL_CONTENT_UNAVAILABLE")
        self.assertEqual(self.old_sources["historical_upstream_content_status"],
                         "HISTORICAL_CONTENT_UNAVAILABLE")
        for row in self.old_sources["remote_rules"]:
            self.assertEqual(row["historical_content_status"],
                             "HISTORICAL_CONTENT_UNAVAILABLE")
            self.assertNotIn("sha256", row)
        report = make_report(ROOT)
        self.assertEqual(report["remote_rule_diff"]["status"],
                         "HISTORICAL_CONTENT_UNAVAILABLE")
        self.assertIsNone(report["remote_rule_diff"]["added"])
        self.assertIsNone(report["remote_rule_diff"]["removed"])

    def test_missing_bytes_must_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                make_report(tmp)
        with self.assertRaises(RuntimeError):
            pinned_bytes(self.current["source_commit"], "rules/generated/DOES-NOT-EXIST.list")

    def test_deterministic_comparison(self):
        left = make_report(ROOT)
        right = make_report(ROOT)
        self.assertEqual(json.dumps(left, sort_keys=True), json.dumps(right, sort_keys=True))
        self.assertEqual(render_markdown(left), render_markdown(right))
        self.assertEqual(left["counts"]["legacy_remote"], self.old["remote_subscription_count"])
        self.assertEqual(left["counts"]["current_remote"], self.current["remote_subscription_count"])
        self.assertFalse(left["local_rule_diff"]["added"])
        self.assertFalse(left["local_rule_diff"]["removed"])

    def test_matcher_type_policy_and_no_resolve_are_not_conflated(self):
        a = parse_rule("DOMAIN-SUFFIX,Example.com,Proxy")
        b = parse_rule("DOMAIN,example.com,Proxy")
        k = parse_rule("DOMAIN-KEYWORD,example.com,Proxy")
        self.assertEqual(len({(r["kind"], r["value"]) for r in (a, b, k)}), 3)
        self.assertEqual(parse_rule("FINAL,Final")["policy"], "Final")
        old = [parse_rule("IP-CIDR,192.0.2.1/24,Proxy,no-resolve")]
        new = [parse_rule("IP-CIDR,192.0.2.0/24,DIRECT")]
        result = compare_rule_sets(old, new)
        self.assertEqual(len(result["policy_or_no_resolve_conflicts"]), 1)
        self.assertEqual(result["no_resolve_before"], 1)
        self.assertEqual(result["no_resolve_after"], 0)
        self.assertEqual(old[0]["value"], new[0]["value"])
        with self.assertRaises(ValueError):
            parse_rule("IP-CIDR6,192.0.2.0/24,Proxy")


if __name__ == "__main__":
    unittest.main()
