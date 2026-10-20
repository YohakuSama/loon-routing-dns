"""Regression tests for the independent Phase 02 immutable published-rule audit."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("phase02_audit", ROOT / "scripts" / "audit_rule_conflicts.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class Phase02AuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.index = audit.validate_snapshot()
        cls.rules, cls.files = audit.scan_published(cls.index)

    def rec(self, rule, policy="Proxy", group="Test", line=1):
        return audit.parse_rule(rule, policy, "rules/generated/Test.list", line, group)

    def test_01_87_enabled_sources_in_index(self):
        self.assertEqual(len(self.index["enabled_sources"]), 87)
        self.assertEqual(len(audit.read_json("rules/sources.json")["sources"]), 87)

    def test_02_34_immutable_published_files(self):
        self.assertEqual(len(self.files), 34)
        self.assertEqual({i["source_file"] for i in self.files},
                         {s["path"] for s in self.index["subscriptions"]})

    def test_03_rule_total_matches_frozen_stage01(self):
        self.assertEqual(len(self.rules),
                         sum(e["rule_count"] for e in self.index["subscriptions"]))
        self.assertEqual(len(self.rules), 206505)

    def test_04_type_statistics_reproduce_index(self):
        reported = Counter()
        for e in self.index["subscriptions"]:
            reported.update(e["rule_types"])
        self.assertEqual(Counter(r["rule_type"] for r in self.rules), reported)

    def test_05_exact_duplicate(self):
        d = audit.overlap_analysis([self.rec("DOMAIN,example.org"),
                                    self.rec("DOMAIN,example.org", line=2)])
        self.assertEqual(len(d["published_exact_duplicates"]), 1)

    def test_06_exact_cross_policy_duplicate(self):
        d = audit.overlap_analysis([self.rec("DOMAIN,example.org"),
                                    self.rec("DOMAIN,example.org", "DIRECT", "ChinaDirect", 2)])
        self.assertEqual(len(d["published_cross_policy_exact"]), 1)

    def test_07_domain_vs_suffix_are_distinct(self):
        d = audit.overlap_analysis([self.rec("DOMAIN,example.org"),
                                    self.rec("DOMAIN-SUFFIX,example.org", "DIRECT", "CN")])
        self.assertFalse(d["published_exact_duplicates"])
        self.assertTrue(d["domain_suffix_cross_policy_coverage"])

    def test_08_keyword_matches_substring_not_label_prefix(self):
        d = audit.overlap_analysis([self.rec("DOMAIN-KEYWORD,shop", "DIRECT", "CN"),
                                    self.rec("DOMAIN,myshop-example.net", "Proxy", "Intl")])
        self.assertEqual(len(d["keyword_cross_policy_possible"]), 1)
        self.assertFalse(d["domain_suffix_cross_policy_coverage"])

    def test_09_ipv4_overlapping_networks(self):
        d = audit.overlap_analysis([self.rec("IP-CIDR,198.51.100.0/24,no-resolve"),
                                    self.rec("IP-CIDR,198.51.100.32/27,no-resolve",
                                             "DIRECT", "CN")])
        self.assertEqual(len(d["ip_cross_policy_overlap"]), 1)

    def test_10_ipv6_overlapping_networks(self):
        d = audit.overlap_analysis([self.rec("IP-CIDR6,2001:db8::/32,no-resolve"),
                                    self.rec("IP-CIDR6,2001:db8:1::/48,no-resolve",
                                             "DIRECT", "CN")])
        self.assertEqual(len(d["ip_cross_policy_overlap"]), 1)

    def test_11_no_resolve_preservation(self):
        self.assertFalse(self.rec("IP-ASN,AS132203")["no_resolve"])
        self.assertTrue(self.rec("IP-CIDR,203.0.113.0/24,no-resolve")["no_resolve"])
        self.assertFalse(self.rec("IP-CIDR6,2001:db8::/32")["no_resolve"])

    def test_12_stable_source_file_line(self):
        self.assertTrue(all(r["source_file"].startswith("rules/") and
                            r["source_line"] > 0 for r in self.rules))
        r = self.rec("DOMAIN-SUFFIX,example.org", "DIRECT", "CN", 123)
        self.assertEqual(audit.locator(r)["source_line"], 123)

    def test_13_no_invented_historical_snapshot(self):
        legacy = audit.read_json("baselines/legacy/sources.json")
        self.assertTrue(all(e["historical_content_status"] == "HISTORICAL_CONTENT_UNAVAILABLE"
                            for e in legacy["remote_rules"]))
        self.assertEqual(len(legacy["remote_rules"]), 28)

    def test_14_read_only_stability(self):
        before = {e["path"]: hashlib.sha256((ROOT / e["path"]).read_bytes()).hexdigest()
                  for e in self.manifest["files"]}
        with tempfile.TemporaryDirectory() as tmp:
            stats = audit.build(Path(tmp))
            self.assertEqual(stats["published_rules"], len(self.rules))
        after = {e["path"]: hashlib.sha256((ROOT / e["path"]).read_bytes()).hexdigest()
                 for e in self.manifest["files"]}
        self.assertEqual(before, after)

    def test_15_deterministic_gzip_and_report(self):
        import gzip
        v = b'{"type":"DOMAIN"}\n' * 4
        self.assertEqual(gzip.compress(v, compresslevel=9, mtime=0),
                         gzip.compress(v, compresslevel=9, mtime=0))
        with tempfile.TemporaryDirectory() as one, tempfile.TemporaryDirectory() as two:
            audit.build(Path(one))
            audit.build(Path(two))
            a = {str(p.relative_to(one)): p.read_bytes()
                 for p in Path(one).rglob("*") if p.is_file()}
            b = {str(p.relative_to(two)): p.read_bytes()
                 for p in Path(two).rglob("*") if p.is_file()}
            self.assertEqual(a, b)

    def test_16_no_uncontrolled_quadratic_scaling(self):
        # 20k exact/suffix rules, no all-pairs comparison.
        many = [self.rec(f"DOMAIN,d{i}.sub.example.org", line=i+1) for i in range(20000)]
        t0 = time.monotonic()
        result = audit.overlap_analysis(many)
        elapsed = time.monotonic() - t0
        self.assertFalse(result["published_cross_policy_exact"])
        self.assertLess(elapsed, 12, f"synthetic audit took {elapsed:.1f}s")

    def test_17_ip_asn_no_false_exact_mapping(self):
        d = audit.overlap_analysis([self.rec("IP-ASN,AS64500"),
                                    self.rec("IP-CIDR,198.51.100.0/24", "DIRECT", "CN")])
        self.assertEqual(d["asn_to_prefix_status"], "ASN_PREFIX_SNAPSHOT_UNAVAILABLE")
        self.assertFalse(d["ip_cross_policy_overlap"])

    def test_18_rule_flags_do_not_collapse(self):
        d = audit.overlap_analysis([self.rec("IP-ASN,AS64500"),
                                    self.rec("IP-ASN,64500,no-resolve", "DIRECT", "CN")])
        self.assertFalse(d["published_exact_duplicates"])
        self.assertEqual(len(d["same_match_different_flags"]), 1)


    def test_21_stage_ingestion_credits_are_distinct_from_published_attribution(self):
        inventory = audit.source_inventory(self.index, self.rules)
        self.assertEqual(len(inventory["sources"]), 87)
        self.assertEqual(len(inventory["staged_zero_incremental_sources"]),
                         inventory["source_recommendation_counts"].get("MERGE", 0))
        self.assertEqual(sum(s["reported_intra_group_duplicates"] for s in inventory["sources"]),
                         inventory["prepublication"]["duplicates_removed_within_group"])
        for row in inventory["sources"]:
            self.assertEqual(row["stage_unique_added_before_pruning"],
                             row["input_count_reported"] - row["reported_intra_group_duplicates"])
            self.assertIsNone(row["published_individual_contribution"])
            if row["stage_unique_added_before_pruning"] == 0:
                self.assertEqual(row["recommendation"], "MERGE")


    def test_22_local_source_line_level_match_is_nonexclusive(self):
        local = audit.local_source_matches(self.rules)
        self.assertEqual(local["exclusive_attribution"], "UNKNOWN")
        self.assertGreaterEqual(len(local["sources"]), 8)
        for source in local["sources"]:
            self.assertEqual(source["normalized_local_input_count"], len(source["per_rule"]))
            self.assertEqual(source["normalized_local_input_count"],
                             source["published_condition_matches"] + source["unmatched_conditions"])
            self.assertEqual(source["unmatched_conditions"],
                             source["same_group_suffix_covered"] + source["unexplained_conditions"])
            self.assertTrue(all(e["source_line"] > 0 for e in source["per_rule"]))

    def test_19_geoip_final_local_rule_handling(self):
        local = audit.scan_local_rules(self.index)
        self.assertTrue(any(r["rule_type"] == "GEOIP" and r["no_resolve"]
                            for r in local))
        self.assertTrue(any(r["rule_type"] == "FINAL" and r["policy"] == "Final"
                            for r in local))
        self.assertTrue(all(r["source_line"] > 0 for r in local))

    def test_20_adblock_published_cross_ownership(self):
        target = [r for r in self.rules if r["rule_value"] == "admob.com"]
        self.assertTrue(any(r["group"] == "Google" for r in target))
        obj, risks = audit.candidates(self.rules, audit.overlap_analysis(
            [r for r in self.rules if r["rule_value"] in audit.KNOWN_AD]), {})
        self.assertTrue(any(r["category"] == "ADBLOCK_PLATFORM_OWNERSHIP"
                            for r in risks))


if __name__ == "__main__":
    unittest.main()
