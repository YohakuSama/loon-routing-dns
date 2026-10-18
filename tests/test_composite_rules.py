#!/usr/bin/env python3
"""Offline regression tests for the staged composite rule builder."""
import sys
import json
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_composite_rules import normalize, generate, read_catalog, prune_suffix_redundancy, own_cross_group_duplicates, PUBLISH_ORDER, excluded_ai_rule, protected_domains, direct_rule_matches_protected_domain


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

    def test_guardrail_blocks_real_misclassification_and_broad_suffix(self):
        protected=protected_domains()
        self.assertIn("browserleaks.com",protected)
        self.assertIn("dnsleaktest.com",protected)
        self.assertEqual(direct_rule_matches_protected_domain(
            "DOMAIN-SUFFIX,browserleaks.com"),"browserleaks.com")
        self.assertEqual(direct_rule_matches_protected_domain(
            "DOMAIN,browserleaks.com"),"browserleaks.com")
        self.assertEqual(direct_rule_matches_protected_domain(
            "DOMAIN-SUFFIX,com"),"browserleaks.com")
        self.assertEqual(direct_rule_matches_protected_domain(
            "DOMAIN-KEYWORD,browserleaks"),"browserleaks.com")
        self.assertIsNone(direct_rule_matches_protected_domain(
            "DOMAIN-SUFFIX,alipay.com"))
        self.assertIsNone(direct_rule_matches_protected_domain(
            "DOMAIN-SUFFIX,cn"))

    def test_generator_quarantines_direct_test_domain_and_keeps_ordinary_cn(self):
        source={"id":"test-mainland","group":"ChinaDirect","policy":"DIRECT",
                "url":"https://rules.invalid/cn","format":"loon","min_rules":1}
        fixture=("DOMAIN-SUFFIX,browserleaks.com\\n"
                 "DOMAIN-SUFFIX,alipay.com\\n"
                 "DOMAIN-SUFFIX,cn\\n")
        output,audit=generate([source],lambda _:fixture)
        result=output["ChinaDirect.list"]
        self.assertNotIn("DOMAIN-SUFFIX,browserleaks.com",result)
        self.assertIn("DOMAIN-SUFFIX,alipay.com",result)
        self.assertIn("DOMAIN-SUFFIX,cn",result)
        guarded=audit["routing_guardrails"]["direct_rules_removed"]
        self.assertEqual(len(guarded),1)
        self.assertEqual(guarded[0]["source"],"test-mainland")
        self.assertEqual(guarded[0]["protected_domain"],"browserleaks.com")
        self.assertEqual(audit["status"],"STAGED_CANDIDATE")

    def test_active_rule_library_is_staged_and_published_files_obey_guardrails(self):
        root=Path(__file__).resolve().parents[1]
        audit=json.loads((root/"rules/generated/audit.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["status"],"STAGED_CANDIDATE")
        self.assertEqual(audit["routing_guardrails"]["active_profile"],
                         "NOT_ENABLED_BY_DEFAULT")
        sources=read_catalog()
        direct_groups={s["group"] for s in sources if s["policy"]=="DIRECT"}
        for group in direct_groups:
            filename=group.replace("動畫瘋","AnimeCrazy")+".list"
            lines=(root/"rules/generated"/filename).read_text(encoding="utf-8").splitlines()
            for line in lines:
                if not line or line.startswith("#"):
                    continue
                self.assertIsNone(direct_rule_matches_protected_domain(line),
                                  f"{filename}: {line}")
        self.assertEqual(audit["group_sizes"]["ChinaDirect"],123010)
        self.assertEqual(audit["routing_guardrails"]["direct_rules_removed"][0]
                         ["rule"],"DOMAIN-SUFFIX,browserleaks.com")
        self.assertEqual(
            sum(bool(s.strip()) and not s.startswith("#")
                for s in (root/"rules/generated/ChinaDirect.list").read_text(
                    encoding="utf-8").splitlines()),
            audit["group_sizes"]["ChinaDirect"])

    def test_ai_rule_safety_exclusions_are_repeatable(self):
        self.assertEqual(excluded_ai_rule("IP-ASN,20473"), "AI broad ASN omitted")
        for rule in (
            "DOMAIN-SUFFIX,stripe.com", "DOMAIN-SUFFIX,auth0.com",
            "DOMAIN-SUFFIX,intercom.io", "DOMAIN-SUFFIX,sentry.io",
            "DOMAIN,static.cloudflareinsights.com",
        ):
            self.assertEqual(excluded_ai_rule(rule), "AI shared-provider root omitted")
        self.assertIsNone(excluded_ai_rule("DOMAIN-SUFFIX,openai.com"))
        self.assertIsNone(excluded_ai_rule("DOMAIN,openai-api.arkoselabs.com"))
        self.assertIsNone(excluded_ai_rule("IP-CIDR,24.199.123.28/32,no-resolve"))

    def test_published_ai_list_has_no_shared_roots_or_broad_asn(self):
        profile = (Path(__file__).resolve().parents[1] / "rules/generated/AI.list").read_text(encoding="utf-8")
        for line in profile.splitlines():
            self.assertIsNone(excluded_ai_rule(line), line)

    def test_generator_omits_risky_ai_records_without_losing_first_party(self):
        src={"id":"sample","group":"AI","policy":"AI",
             "url":"https://rules.invalid/sample","format":"loon","min_rules":1}
        body=("DOMAIN-SUFFIX,openai.com\n"
              "DOMAIN-SUFFIX,stripe.com\n"
              "IP-ASN,20473\n")
        output,audit=generate([src], lambda _: body)
        self.assertIn("DOMAIN-SUFFIX,openai.com", output["AI.list"])
        self.assertNotIn("stripe.com", output["AI.list"])
        self.assertNotIn("IP-ASN", output["AI.list"])
        self.assertEqual(audit["quarantined_by_reason"]["AI broad ASN omitted"],1)

    def test_normalizes_domainset_and_lowers_domain(self):
        self.assertEqual(normalize(".EXAMPLE.COM", "domainset")[0],
                         "DOMAIN-SUFFIX,example.com")
        self.assertEqual(normalize("example.com", "domainset")[0],
                         "DOMAIN,example.com")
        self.assertEqual(normalize("DOMAIN-SUFFIX,EXAMPLE.COM")[0],
                         "DOMAIN-SUFFIX,example.com")

    def test_ip_networks_enforce_no_resolve_for_dns_stability(self):
        self.assertEqual(normalize("IP-CIDR,10.0.0.1/24")[0], "IP-CIDR,10.0.0.0/24,no-resolve")
        self.assertEqual(normalize("IP-CIDR,10.0.0.1/24,no-resolve")[0],
                         "IP-CIDR,10.0.0.0/24,no-resolve")
        self.assertEqual(normalize("IP-CIDR6,2001:db8::1/64")[0], "IP-CIDR6,2001:db8::/64,no-resolve")
        self.assertEqual(normalize("IP-CIDR6,2001:db8::1/64,no-resolve")[0],
                         "IP-CIDR6,2001:db8::/64,no-resolve")
        self.assertEqual(normalize("IP-ASN,AS1234,no-resolve")[0], "IP-ASN,1234,no-resolve")
        self.assertEqual(normalize("IP-ASN,AS1234")[0], "IP-ASN,1234")
        self.assertEqual(normalize("DOMAIN-SUFFIX,example.com")[0], "DOMAIN-SUFFIX,example.com")
        self.assertIsNotNone(normalize("IP-CIDR,2001:db8::/64")[1])
        self.assertIsNotNone(normalize("IP-CIDR,10.0.0.1/24,no-resolve,no-resolve")[1])

    def test_composite_publish_order_stays_staged_until_device_validation(self):
        import json
        root = Path(__file__).resolve().parents[1]
        profile = (root / "LoonKit.lcf").read_text(encoding="utf-8")
        baseline = json.loads((root / "rules/verified-routing-baseline.json").read_text(encoding="utf-8"))
        section = profile.split("[Remote Rule]", 1)[1].split("[Rule]", 1)[0]
        active_remote = [row.strip() for row in section.splitlines()
                         if row.strip().startswith("https://")]
        self.assertEqual(active_remote,baseline["remote_rules"])
        self.assertEqual(len(active_remote),28)
        self.assertNotIn("/rules/generated/",section)
        self.assertEqual(len(PUBLISH_ORDER),33)
        for group in PUBLISH_ORDER:
            name = group.replace("動畫瘋","AnimeCrazy")
            self.assertTrue((root / "rules/generated" / (name + ".list")).is_file(),name)

    def test_cidr_flag_variants_canonicalize_to_one_rule(self):
        sources = [
            {"id": "a", "group": "Alpha", "policy": "Proxy",
             "url": "https://rules.invalid/a", "format": "loon", "min_rules": 1},
            {"id": "b", "group": "Alpha", "policy": "Proxy",
             "url": "https://rules.invalid/b", "format": "loon", "min_rules": 1},
        ]
        docs = {"https://rules.invalid/a": "IP-CIDR,10.0.0.1/8\n",
                "https://rules.invalid/b": "IP-CIDR,10.0.0.1/8,no-resolve\n"}
        out, report = generate(sources, lambda url: docs[url])
        self.assertNotIn("IP-CIDR,10.0.0.0/8\n", out["Alpha.list"])
        self.assertEqual(out["Alpha.list"].count("IP-CIDR,10.0.0.0/8,no-resolve\n"), 1)
        self.assertEqual(report["duplicates_removed_within_group"], 1)

    def test_unknown_grammar_fails_candidate_build(self):
        source = {"id": "a", "group": "Alpha", "policy": "Proxy",
                  "url": "https://rules.invalid/a", "format": "loon", "min_rules": 1}
        with self.assertRaisesRegex(ValueError, "unsupported/invalid upstream"):
            generate([source], lambda _: "DOMAIN,example.com\nPROCESS-NAME,example\n")

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
