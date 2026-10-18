#!/usr/bin/env python3
"""Offline regression tests for the staged composite rule builder."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_composite_rules import normalize, generate, read_catalog, prune_suffix_redundancy, own_cross_group_duplicates, PUBLISH_ORDER


class CompositeRulesTests(unittest.TestCase):
    def test_reviewed_sources_catalog_is_valid(self):
        sources = read_catalog()
        self.assertEqual(len(sources), 87)
        self.assertEqual(len([s for s in sources if s.get("role") == "local"]), 10)

    def test_v2fly_annotations_and_dnsmasq(self):
        meta = {"policy": "AI", "skip_attrs": ["ads", "!cn"]}
        self.assertEqual(normalize("chatgpt.com", "v2fly", meta)[0],
                         "DOMAIN-SUFFIX,chatgpt.com")
        self.assertEqual(normalize("full:aistudio.google.com", "v2fly", meta)[0],
                         "DOMAIN,aistudio.google.com")
        self.assertIsNone(normalize("api.example.com @ads", "v2fly", meta)[0])
        self.assertIsNone(normalize("bilibili.tv @!cn", "v2fly", meta)[0])
        self.assertIsNone(normalize("xn--bnq297cix3a.cn @cn # 易付通.cn", "v2fly", meta)[0])
        self.assertIsNotNone(normalize("include:google", "v2fly", meta)[1])
        self.assertIsNotNone(normalize("regexp:foo.*", "v2fly", meta)[1])
        self.assertEqual(
            normalize("server=/app-site-association.cdn-apple.com/114.114.114.114",
                      "dnsmasq")[0],
            "DOMAIN-SUFFIX,app-site-association.cdn-apple.com"
        )

    def test_same_group_shadow_removal(self):
        remaining, dropped = prune_suffix_redundancy({
            "DOMAIN-SUFFIX,example.com", "DOMAIN-SUFFIX,a.example.com",
            "DOMAIN,login.example.com", "DOMAIN-SUFFIX,example.net"})
        self.assertEqual(dropped, 2)
        self.assertIn("DOMAIN-SUFFIX,example.com", remaining)
        self.assertNotIn("DOMAIN,login.example.com", remaining)

    def test_exact_cross_group_dedup_is_first_wins(self):
        from collections import defaultdict
        groups = {name: {} for name in PUBLISH_ORDER}
        groups["AI"]["DOMAIN-SUFFIX,example.com"] = "AI"
        groups["AdBlock"]["DOMAIN-SUFFIX,example.com"] = "AdBlock"
        groups["ChinaDirect"]["DOMAIN-SUFFIX,example.com"] = "ChinaDirect"
        report = own_cross_group_duplicates(groups)
        self.assertEqual(len(report), 2)
        self.assertIn("DOMAIN-SUFFIX,example.com", groups["AI"])
        self.assertNotIn("DOMAIN-SUFFIX,example.com", groups["AdBlock"])

    def test_normalizes_domainset_and_lowers_domain(self):
        self.assertEqual(normalize(".EXAMPLE.COM", "domainset")[0],
                         "DOMAIN-SUFFIX,example.com")
        self.assertEqual(normalize("example.com", "domainset")[0],
                         "DOMAIN,example.com")
        self.assertEqual(normalize("DOMAIN-SUFFIX,EXAMPLE.COM")[0],
                         "DOMAIN-SUFFIX,example.com")

    def test_ip_networks_preserve_original_no_resolve_semantics(self):
        self.assertEqual(normalize("IP-CIDR,10.0.0.1/24")[0], "IP-CIDR,10.0.0.0/24")
        self.assertEqual(normalize("IP-CIDR,10.0.0.1/24,no-resolve")[0],
                         "IP-CIDR,10.0.0.0/24,no-resolve")
        self.assertEqual(normalize("IP-CIDR6,2001:db8::1/64")[0], "IP-CIDR6,2001:db8::/64")
        self.assertEqual(normalize("IP-CIDR6,2001:db8::1/64,no-resolve")[0],
                         "IP-CIDR6,2001:db8::/64,no-resolve")
        self.assertEqual(normalize("IP-ASN,AS1234,no-resolve")[0], "IP-ASN,1234,no-resolve")
        self.assertIsNotNone(normalize("IP-CIDR,2001:db8::/64")[1])
        self.assertIsNotNone(normalize("IP-CIDR,10.0.0.1/24,no-resolve,no-resolve")[1])

    def test_publish_order_matches_live_remote_rule_order(self):
        import re
        profile = (Path(__file__).resolve().parents[1] / "Loon_Routing_DNS.lcf").read_text(encoding="utf-8")
        section = profile.split("[Remote Rule]", 1)[1].split("[Rule]", 1)[0]
        actual = [re.search(r"/generated/([^/,]+)\\.list,", line).group(1)
                  for line in section.splitlines() if line.strip().startswith("https://")]
        self.assertEqual([name.replace("動畫瘋", "AnimeCrazy") for name in PUBLISH_ORDER], actual)

    def test_flag_variants_remain_separate(self):
        sources = [
            {"id": "a", "group": "Alpha", "policy": "Proxy",
             "url": "https://rules.invalid/a", "format": "loon", "min_rules": 1},
            {"id": "b", "group": "Alpha", "policy": "Proxy",
             "url": "https://rules.invalid/b", "format": "loon", "min_rules": 1},
        ]
        docs = {"https://rules.invalid/a": "IP-CIDR,10.0.0.1/8\\n",
                "https://rules.invalid/b": "IP-CIDR,10.0.0.1/8,no-resolve\\n"}
        out, report = generate(sources, lambda url: docs[url])
        self.assertIn("IP-CIDR,10.0.0.0/8\\n", out["Alpha.list"])
        self.assertIn("IP-CIDR,10.0.0.0/8,no-resolve\\n", out["Alpha.list"])
        self.assertEqual(report["ip_flag_variant_conflict_count"], 1)

    def test_unknown_grammar_fails_candidate_build(self):
        source = {"id": "a", "group": "Alpha", "policy": "Proxy",
                  "url": "https://rules.invalid/a", "format": "loon", "min_rules": 1}
        with self.assertRaisesRegex(ValueError, "unsupported/invalid upstream"):
            generate([source], lambda _: "DOMAIN,example.com\\nPROCESS-NAME,example\\n")

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
        self.assertEqual(audit["cross_group_exact_pruned_count"], 1)
        self.assertGreaterEqual(audit["domain_suffix_ancestor_conflict_count"], 1)

    def test_refuses_truncated_inputs(self):
        sources = [{"id": "small", "group": "Foo", "policy": "Proxy",
                    "url": "https://rules.invalid/", "format": "loon",
                    "min_rules": 3}]
        with self.assertRaisesRegex(ValueError, "below min_rules"):
            generate(sources, lambda _: "DOMAIN,one.com\n")


if __name__ == "__main__":
    unittest.main()
