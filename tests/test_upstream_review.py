"""Regressions for read-only upstream review. Purely synthetic, no HTTP."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
import upstream_review as review


class SourceSyntax(unittest.TestCase):
    def parse(self, fmt, data, **kw):
        return review.parse_source({"format": fmt, "min_rules": 1, **kw},
                                   data.encode("utf-8"))

    def test_supported_source_conversions_and_no_unsafe_guessing(self):
        rules, info = self.parse("loon", "# comment\nDOMAIN-SUFFIX,example.org\nIP-CIDR,8.8.8.8/24")
        self.assertEqual(rules, {"DOMAIN-SUFFIX,example.org", "IP-CIDR,8.8.8.0/24,no-resolve"})
        self.assertEqual(info["invalid_count"], 0)
        rules, info = self.parse("domainset", ".example.org\nexample.net\n.example.org")
        self.assertEqual(rules, {"DOMAIN-SUFFIX,example.org", "DOMAIN,example.net"})
        self.assertEqual(info["source_duplicates"], 1)
        rules, info = self.parse("dnsmasq", "server=/cdn.example.org/114.114.114.114\n")
        self.assertEqual(rules, {"DOMAIN-SUFFIX,cdn.example.org"})
        self.assertEqual(info["invalid_count"], 0)
        rules, info = self.parse("v2fly",
            "openai.com\nfull:api.openai.com\nfull:ads.openai.com @ads\nregexp:^*.invalid\ninclude:cloud",
            skip_attrs=["ads"])
        self.assertEqual(rules, {"DOMAIN-SUFFIX,openai.com", "DOMAIN,api.openai.com"})
        self.assertEqual(info["invalid_count"], 2)
        self.assertFalse(info["invalid_count"] == 0)

    def test_domainset_exact_vs_suffix_is_not_widened(self):
        rules, info = self.parse("domainset",
            "api.example.org\n.example.org\n+.service.example.net\n")
        self.assertEqual(info["invalid_count"], 0)
        self.assertEqual(rules, {"DOMAIN,api.example.org",
                                 "DOMAIN-SUFFIX,example.org",
                                 "DOMAIN-SUFFIX,service.example.net"})
        self.assertNotIn("DOMAIN-SUFFIX,api.example.org", rules)

    def test_v2fly_inline_comment_is_not_an_invalid_domain(self):
        rules, info = self.parse("v2fly",
            "antspace.dev # source: provider\nfull:cdn.example.com # exact\n")
        self.assertEqual(info["invalid_count"], 0)
        self.assertEqual(rules, {"DOMAIN-SUFFIX,antspace.dev",
                                 "DOMAIN,cdn.example.com"})

    def test_same_policy_dedup_does_not_change_other_groups(self):
        kept, removed = review._same_policy_reduce({
            "DOMAIN-SUFFIX,example.org", "DOMAIN,sub.example.org",
            "IP-CIDR,8.8.8.0/24,no-resolve", "DOMAIN-KEYWORD,example"
        })
        self.assertNotIn("DOMAIN,sub.example.org", kept)
        self.assertEqual(removed, 1)
        self.assertIn("IP-CIDR,8.8.8.0/24,no-resolve", kept)
        self.assertIn("DOMAIN-KEYWORD,example", kept)

    def test_other_policy_semantic_coverage_is_flagged(self):
        base = {"AI": {"DOMAIN,api.example.org"},
                "ChinaDirect": {"DOMAIN-SUFFIX,cn"}}
        idx, domains = review._overlap_index(base)
        self.assertEqual(review._semantic_expansion("DOMAIN-SUFFIX,example.org",
            "ChinaDirect", base, idx, domains), ["AI"])
        self.assertEqual(review._semantic_expansion("DOMAIN,api.example.org",
            "ChinaDirect", base, idx, domains), ["AI"])



class HardeningTests(unittest.TestCase):
    def test_malformed_inputs_rejected_but_valid_broad_matchers_triaged(self):
        malformed = [
            ("domainset", "*.example.org"),
            ("domainset", "..example.org"),
            ("loon", "DOMAIN-KEYWORD,foo*"),
            ("loon", "DOMAIN-SUFFIX,foo..bar.com"),
            ("loon", "DOMAIN-SUFFIX,-example.org"),
        ]
        for fmt, raw in malformed:
            with self.subTest(category="invalid", fmt=fmt, raw=raw):
                rules, report = review.parse_source(
                    {"format": fmt, "min_rules": 1}, raw.encode())
                self.assertEqual(rules, set())
                self.assertEqual(report["invalid_count"], 1)
                self.assertEqual(report["quality_review_count"], 0)

        valid_but_risky = [
            ("domainset", "com", "SINGLE_LABEL_OR_TLD_SCOPE_REVIEW"),
            ("domainset", ".co.uk", "PUBLIC_SUFFIX_LIKE_SCOPE_REVIEW"),
            ("domainset", ".github.io", "MULTITENANT_ROOT_SCOPE_REVIEW"),
            ("domainset", ".cloudfront.net", "MULTITENANT_ROOT_SCOPE_REVIEW"),
            ("loon", "DOMAIN-KEYWORD,api", "SHORT_KEYWORD_SCOPE_REVIEW"),
            ("loon", "DOMAIN-KEYWORD,cdn", "GENERIC_KEYWORD_SCOPE_REVIEW"),
            ("loon", "IP-CIDR,0.0.0.0/0", "WIDE_IP_SCOPE_REVIEW"),
            ("loon", "IP-CIDR6,::/0", "WIDE_IP_SCOPE_REVIEW"),
            ("loon", "DOMAIN-SUFFIX,localhost", "PRIVATE_OR_RESERVED_DOMAIN_REVIEW"),
        ]
        for fmt, raw, expected_flag in valid_but_risky:
            with self.subTest(category="needs_review", fmt=fmt, raw=raw):
                rules, report = review.parse_source(
                    {"format": fmt, "min_rules": 1}, raw.encode())
                self.assertEqual(len(rules), 1)
                self.assertEqual(report["invalid_count"], 0)
                self.assertEqual(report["quality_review_count"], 1)
                self.assertIn(expected_flag,
                              report["quality_review_samples"][0]["reasons"])
                self.assertTrue(report["minimum_satisfied"])

    def test_standard_matchers_not_overflagged(self):
        standard = [
            ("domainset", ".api.example.org"),
            ("loon", "DOMAIN,api.example.org"),
            ("loon", "DOMAIN-SUFFIX,example.org"),
            ("loon", "IP-CIDR,203.0.113.0/24"),
        ]
        for fmt, raw in standard:
            with self.subTest(fmt=fmt, raw=raw):
                rules, report = review.parse_source(
                    {"format": fmt, "min_rules": 1}, raw.encode())
                self.assertEqual(len(rules), 1)
                self.assertEqual(report["invalid_count"], 0)
                self.assertNotIn("WIDE_IP_SCOPE_REVIEW",
                                 report["quality_review_samples"][0]["reasons"]
                                 if report["quality_review_samples"] else [])

    def test_mixed_risk_source_remains_parse_complete(self):
        source = {"format": "loon", "min_rules": 2}
        rules, report = review.parse_source(
            source, b"DOMAIN,api.example.org\nDOMAIN-KEYWORD,api\n")
        self.assertEqual(len(rules), 2)
        self.assertEqual(report["invalid_count"], 0)
        self.assertEqual(report["quality_review_count"], 1)
        self.assertTrue(report["minimum_satisfied"])

    def test_ipv4_and_ipv6_cross_policy_overlap_both_directions(self):
        baseline = {
            "AI": {"IP-CIDR,10.20.0.0/16,no-resolve",
                   "IP-CIDR6,2001:db8:abcd::/48,no-resolve"},
            "ChinaDirect": {"IP-CIDR,192.168.8.0/24,no-resolve"}
        }
        ix = review._ip_overlap_index(baseline)
        self.assertEqual(review._ip_collisions(
            "IP-CIDR,10.20.1.0/24,no-resolve", "ChinaDirect", ix), ["AI"])
        self.assertEqual(review._ip_collisions(
            "IP-CIDR,10.20.0.0/15,no-resolve", "ChinaDirect", ix), ["AI"])
        self.assertEqual(review._ip_collisions(
            "IP-CIDR6,2001:db8::/32,no-resolve", "ChinaDirect", ix), ["AI"])
        self.assertEqual(review._ip_collisions(
            "IP-CIDR,10.20.1.0/24,no-resolve", "AI", ix), [])
        self.assertEqual(review._ip_collisions(
            "DOMAIN-SUFFIX,example.org", "AI", ix), [])

    def test_exact_parent_does_not_falsely_match_subdomain(self):
        existing = {
            "AI": {"DOMAIN,example.org"},
            "Google": {"DOMAIN-SUFFIX,google.org"}
        }
        idx, domains = review._overlap_index(existing)
        self.assertEqual(review._semantic_expansion(
            "DOMAIN,sub.example.org", "ChinaDirect", existing, idx, domains), [])
        self.assertEqual(review._semantic_expansion(
            "DOMAIN,sub.google.org", "ChinaDirect", existing, idx, domains), ["Google"])

    def test_new_adblock_matchers_cannot_auto_block_critical_services(self):
        protected = tuple(["browserleaks.com"])
        for raw in ("DOMAIN-SUFFIX,stripe.com", "DOMAIN,accounts.google.com",
                    "DOMAIN-SUFFIX,cloudfront.net"):
            tags = review._domain_risk(raw, "AdBlock", protected)
            self.assertIn("ADBLOCK_NEW_RULE_REQUIRES_EVIDENCE", tags)
            self.assertTrue("ADBLOCK_CRITICAL_SERVICE_OVERLAP" in tags or
                            "ADBLOCK_SHARED_HOSTING_OVERLAP" in tags)
        self.assertIn("ADBLOCK_UNSAFE_MATCHER", review._domain_risk(
            "DOMAIN-KEYWORD,track", "AdBlock", protected))
        self.assertIn("DIRECT_PROTECTED_DOMAIN", review._domain_risk(
            "DOMAIN-SUFFIX,browserleaks.com", "ChinaDirect", protected))

class IncludeResolutionTests(unittest.TestCase):
    def test_expand_multiple_safe_includes_and_keep_original_evidence(self):
        src = {"format": "v2fly"}
        raw = b"include:abc\ninclude:hotstar # Disney child\nexample.org\n"
        corpus = {
            "abc": b"abc.com\nfull:api.abc.com\n",
            "hotstar": b"hotstar.com\nfull:cdn.hotstar.com\n",
        }
        actual, files = review.expand_v2fly_includes(src, raw, corpus.__getitem__)
        self.assertEqual(set(files), {"abc", "hotstar"})
        self.assertEqual(files["abc"], corpus["abc"])
        rules, info = review.parse_source(src, actual)
        self.assertEqual(info["invalid_count"], 0)
        self.assertEqual(rules, {
            "DOMAIN-SUFFIX,abc.com", "DOMAIN,api.abc.com",
            "DOMAIN-SUFFIX,hotstar.com", "DOMAIN,cdn.hotstar.com",
            "DOMAIN-SUFFIX,example.org",
        })

    def test_include_cycles_and_bad_paths_are_fail_closed(self):
        src = {"format": "v2fly"}
        with self.assertRaisesRegex(ValueError, "cyclic"):
            review.expand_v2fly_includes(src, b"include:a\n", lambda _: b"include:a\n")
        for text in (b"include:../evil\n", b"include:https://evil.test\n",
                     b"include:abc/def\n", b"include:\n"):
            with self.subTest(raw=text):
                with self.assertRaises(ValueError):
                    review.expand_v2fly_includes(src, text, lambda _: b"foo.com\n")

    def test_unresolved_regexp_in_nested_source_stays_incomplete(self):
        src = {"format": "v2fly", "min_rules": 1}
        actual, captured = review.expand_v2fly_includes(
            src, b"include:hotstar\n",
            lambda _: b"example.org\nregexp:^sub[1-5]\\.example\\.org$\n")
        self.assertIn("hotstar", captured)
        rules, status = review.parse_source(src, actual)
        self.assertEqual(rules, {"DOMAIN-SUFFIX,example.org"})
        self.assertEqual(status["invalid_count"], 1)


class CandidateWorkflow(unittest.TestCase):
    @staticmethod
    def fixture(root: Path):
        groups = ["AI", "ChinaDirect"] + ["Group"+str(i) for i in range(24)]
        (root/"rules/releases/vNext-RC2").mkdir(parents=True)
        (root/"build").mkdir()
        for group in groups:
            (root/"rules/releases/vNext-RC2"/(group+".list")).write_text(
                "DOMAIN-SUFFIX,"+group.lower()+".org\n", encoding="utf-8")
        (root/"build/engine_manifest.json").write_text(
            json.dumps({"active_groups": groups}), encoding="utf-8")
        (root/"rules/routing_guardrails.json").write_text(
            json.dumps({"protected_proxy_domains": ["private.example.org"]}), encoding="utf-8")
        # 87 synthetic sources, no network; 2 sources target the SAME policy.
        catalog = []
        for i in range(87):
            group = "AI" if i == 0 else ("ChinaDirect" if i == 1 else groups[i % 26])
            catalog.append({"id": f"fixture-{i}", "group": group, "format": "loon",
                            "enabled": True, "url": "https://example.invalid/fixture",
                            "min_rules": 1})
        (root/"rules/sources.json").write_text(json.dumps({"sources": catalog}),
                                                encoding="utf-8")
        return catalog

    def test_review_full_diff_and_provenance_never_publishes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)/"repo"
            catalog = self.fixture(root)
            data = {s["id"]: "DOMAIN-SUFFIX,"+s["group"].lower()+".org\n"
                    for s in catalog}
            data["fixture-0"] = ("DOMAIN-SUFFIX,example.org\n"
                "DOMAIN,api.example.org\nDOMAIN-KEYWORD,tracker\n")
            data["fixture-1"] = "DOMAIN-SUFFIX,private.example.org\n"
            # Deliberately remove AI's baseline entry to exercise removal review.
            for i in (26, 52, 78):
                data[f"fixture-{i}"] = "DOMAIN-SUFFIX,updated.ai.org\n"
            result, snapshots, review_data = review.build_report(
                root, fetcher=lambda s: data[s["id"]].encode())
            self.assertEqual(result["status"], "REVIEW_ONLY_NEVER_PUBLISH")
            self.assertEqual(result["source_count"], 87)
            self.assertEqual(result["snapshot_count"], 87)
            self.assertEqual(result["incomplete_sources"], 0)
            self.assertEqual(result["groups"]["AI"]["risk_categories"]
                             ["BROAD_KEYWORD_OR_IP_REVIEW"], 1)
            self.assertGreaterEqual(result["groups"]["ChinaDirect"]["risk_categories"]
                                    ["DIRECT_PROTECTED_DOMAIN"], 1)
            self.assertGreaterEqual(result["groups"]["AI"]["risk_categories"]
                                    ["NEW_SUFFIX_SCOPE_REVIEW"], 1)
            self.assertGreaterEqual(result["groups"]["AI"]["removed"], 1)
            before = (root/"rules/releases/vNext-RC2/AI.list").read_bytes()
            output = Path(td)/"candidate-output"
            review.write_review(output, result, snapshots, review_data, root)
            self.assertTrue((output/"UPSTREAM_REVIEW.json").exists())
            self.assertTrue((output/"FULL_DIFF.json").exists())
            self.assertTrue((output/"FULL_RISK_AUDIT.json").exists())
            self.assertFalse(result["publication_allowed"])
            self.assertTrue(result["preview_sha256_unchanged"])
            self.assertEqual(review_data["rules"]["AI"],
                             {"DOMAIN-SUFFIX,ai.org"})
            self.assertIn("DOMAIN-SUFFIX,example.org",
                          review_data["unapproved_proposals"]["AI"])
            pinned_preview = (output/"candidate/AI.list").read_text()
            self.assertIn("DOMAIN-SUFFIX,ai.org", pinned_preview)
            self.assertNotIn("DOMAIN-SUFFIX,example.org", pinned_preview)
            details = json.loads((output/"FULL_RISK_AUDIT.json").read_text())
            self.assertGreater(len(details["AI"]["additions"]), 0)
            self.assertTrue(all("reasons" in row for row
                                in details["AI"]["additions"]))
            self.assertTrue(all("source_ids" in row for row
                                in details["AI"]["additions"]))
            tiers = {entry["rule"]: entry["review_tier"]
                     for entry in details["AI"]["additions"]}
            self.assertEqual(tiers["DOMAIN-KEYWORD,tracker"], "ELEVATED")
            self.assertEqual(tiers["DOMAIN-SUFFIX,updated.ai.org"], "STANDARD")
            self.assertTrue(details["AI"]["removals"])
            for group in result["groups"]:
                name = "AnimeCrazy" if group == "動畫瘋" else group
                preview = (output/"candidate"/(name+".list")).read_text()
                self.assertNotIn("DOMAIN-KEYWORD,tracker", preview)
                self.assertEqual(result["groups"][group]["publication_gate"],
                                 "BLOCKED_UNTIL_EXPLICIT_APPROVAL")
            self.assertTrue((output/"snapshots/fixture-0.txt").exists())
            self.assertEqual((root/"rules/releases/vNext-RC2/AI.list").read_bytes(), before)
            with self.assertRaises(ValueError):
                review.write_review(root/"inside", result, snapshots, review_data, root)

    def test_bad_source_never_becomes_complete(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)/"repo"
            catalog = self.fixture(root)
            data = {s["id"]: ("DOMAIN-SUFFIX,"+s["group"].lower()+".org\n").encode()
                    for s in catalog}
            data["fixture-0"] = b"URL-REGEX,https://.*\n"
            result, snapshots, review_data = review.build_report(
                root, fetcher=lambda s: data[s["id"]])
            self.assertEqual(result["incomplete_sources"], 1)
            self.assertIn("AI", result["incomplete_groups"])
            self.assertEqual(result["groups"]["AI"]["status"], "INCOMPLETE_SOURCE_DATA")
            self.assertTrue(snapshots)
            self.assertEqual(review_data["rules"]["AI"],
                             {"DOMAIN-SUFFIX,ai.org"})


if __name__ == "__main__":
    unittest.main()
