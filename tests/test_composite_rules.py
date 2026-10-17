#!/usr/bin/env python3
"""Offline regression tests for the staged composite rule builder."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_composite_rules import normalize, generate, read_catalog


class CompositeRulesTests(unittest.TestCase):
    def test_reviewed_sources_catalog_is_valid(self):
        sources = read_catalog()
        self.assertEqual(len(sources), 46)
        self.assertEqual(len([s for s in sources if s.get("role") == "local"]), 8)

    def test_normalizes_domainset_and_lowers_domain(self):
        self.assertEqual(normalize(".EXAMPLE.COM", "domainset")[0],
                         "DOMAIN-SUFFIX,example.com")
        self.assertEqual(normalize("example.com", "domainset")[0],
                         "DOMAIN,example.com")
        self.assertEqual(normalize("DOMAIN-SUFFIX,EXAMPLE.COM")[0],
                         "DOMAIN-SUFFIX,example.com")

    def test_ip_networks_preserve_no_resolve_and_normalize(self):
        self.assertEqual(normalize("IP-CIDR,10.0.0.1/24")[0],
                         "IP-CIDR,10.0.0.0/24")
        self.assertEqual(normalize("IP-CIDR,10.0.0.1/24,no-resolve")[0],
                         "IP-CIDR,10.0.0.0/24,no-resolve")
        self.assertEqual(normalize("IP-CIDR6,2001:db8::1/64")[0],
                         "IP-CIDR6,2001:db8::/64")
        self.assertEqual(normalize("IP-CIDR6,2001:db8::1/64,no-resolve")[0],
                         "IP-CIDR6,2001:db8::/64,no-resolve")
        self.assertEqual(normalize("IP-ASN,AS1234,no-resolve")[0],
                         "IP-ASN,1234,no-resolve")
        self.assertIsNotNone(normalize("IP-CIDR,2001:db8::/64")[1])
        self.assertIsNotNone(normalize("IP-CIDR,10.0.0.1/24,what")[1])

    def test_unsupported_rules_are_quarantined(self):
        self.assertIn("URL-REGEX", normalize("URL-REGEX,^https://ad\\.site")[1])
        self.assertIn("unsupported", normalize("PROCESS-NAME,broken")[1])

    def test_same_group_dedupe_and_cross_group_conflicts(self):
        docs = {
            "https://rules.invalid/a": (
                "# updated yesterday\n"
                "DOMAIN-SUFFIX,example.com\n"
                "DOMAIN-SUFFIX,EXAMPLE.com\n"
                "DOMAIN-SUFFIX,example.org\n"
            ),
            "https://rules.invalid/b": (
                "DOMAIN-SUFFIX,example.com\nDOMAIN,www.example.com\n"
            ),
            "https://rules.invalid/c": "DOMAIN-SUFFIX,example.com\n",
        }
        sources = [
            {"id": "a", "group": "Alpha", "policy": "Proxy",
             "url": "https://rules.invalid/a", "format": "loon", "min_rules": 1},
            {"id": "b", "group": "Alpha", "policy": "Proxy",
             "url": "https://rules.invalid/b", "format": "loon", "min_rules": 1},
            {"id": "c", "group": "Beta", "policy": "DIRECT",
             "url": "https://rules.invalid/c", "format": "loon", "min_rules": 1},
        ]
        out, audit = generate(sources, lambda url: docs[url])
        self.assertEqual(out["Alpha.list"].count("DOMAIN-SUFFIX,example.com"), 1)
        self.assertEqual(audit["duplicates_removed_within_group"], 2)
        self.assertEqual(audit["cross_group_different_policy_exact"], 1)
        self.assertGreaterEqual(audit["domain_suffix_ancestor_conflict_count"], 1)

    def test_flag_variants_are_not_silently_merged(self):
        sources = [
            {"id": "a", "group": "Alpha", "policy": "Proxy",
             "url": "https://rules.invalid/a", "format": "loon", "min_rules": 1},
            {"id": "b", "group": "Alpha", "policy": "Proxy",
             "url": "https://rules.invalid/b", "format": "loon", "min_rules": 1},
        ]
        docs = {"https://rules.invalid/a": "IP-CIDR,10.0.0.0/8\n",
                "https://rules.invalid/b": "IP-CIDR,10.0.0.0/8,no-resolve\n"}
        out, audit = generate(sources, lambda u: docs[u])
        self.assertIn("IP-CIDR,10.0.0.0/8\n", out["Alpha.list"])
        self.assertIn("IP-CIDR,10.0.0.0/8,no-resolve\n", out["Alpha.list"])
        self.assertEqual(audit["ip_flag_variant_conflict_count"], 1)
        self.assertEqual(audit["duplicates_removed_within_group"], 0)

    def test_refuses_unknown_upstream_syntax(self):
        source = {"id": "a", "group": "Alpha", "policy": "Proxy",
                  "url": "https://rules.invalid/a", "format": "loon",
                  "min_rules": 1}
        with self.assertRaisesRegex(ValueError, "unsupported/invalid"):
            generate([source], lambda _: "DOMAIN,example.com\nPROCESS-NAME,app\n")

    def test_drops_known_url_regex_but_records_quarantine(self):
        source = {"id": "a", "group": "Alpha", "policy": "Proxy",
                  "url": "https://rules.invalid/a", "format": "loon",
                  "min_rules": 1}
        _, audit = generate([source],
                            lambda _: "DOMAIN,example.com\nURL-REGEX,^https://ads\n")
        self.assertEqual(sum(audit["quarantined_by_reason"].values()), 1)

    def test_refuses_truncated_inputs(self):
        sources = [{"id": "small", "group": "Foo", "policy": "Proxy",
                    "url": "https://rules.invalid/", "format": "loon",
                    "min_rules": 3}]
        with self.assertRaisesRegex(ValueError, "below min_rules"):
            generate(sources, lambda _: "DOMAIN,one.com\n")


if __name__ == "__main__":
    unittest.main()
