#!/usr/bin/env python3
"""Offline regression tests for the staged composite rule builder."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_composite_rules import normalize, generate


class CompositeRulesTests(unittest.TestCase):
    def test_normalizes_domainset_and_lowers_domain(self):
        self.assertEqual(normalize(".EXAMPLE.COM", "domainset")[0],
                         "DOMAIN-SUFFIX,example.com")
        self.assertEqual(normalize("example.com", "domainset")[0],
                         "DOMAIN,example.com")
        self.assertEqual(normalize("DOMAIN-SUFFIX,EXAMPLE.COM")[0],
                         "DOMAIN-SUFFIX,example.com")

    def test_ip_networks_are_canonical_and_no_resolve(self):
        self.assertEqual(normalize("IP-CIDR,10.0.0.1/24")[0],
                         "IP-CIDR,10.0.0.0/24,no-resolve")
        self.assertEqual(normalize("IP-CIDR6,2001:db8::1/64")[0],
                         "IP-CIDR6,2001:db8::/64,no-resolve")
        self.assertIsNotNone(normalize("IP-CIDR,2001:db8::/64")[1])

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

    def test_refuses_truncated_inputs(self):
        sources = [{"id": "small", "group": "Foo", "policy": "Proxy",
                    "url": "https://rules.invalid/", "format": "loon",
                    "min_rules": 3}]
        with self.assertRaisesRegex(ValueError, "below min_rules"):
            generate(sources, lambda _: "DOMAIN,one.com\n")


if __name__ == "__main__":
    unittest.main()
