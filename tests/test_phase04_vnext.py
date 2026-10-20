"""Phase 04 offline candidate acceptance; production baseline tests remain independent."""
import json
import re
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import vnext_rule_engine as ve


class Phase04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = ve.compile_rules()
        cls.summary = json.loads(cls.files["refactor/vnext/reports/diff_summary.json"])
        cls.manifest = ve.load_manifest()
        cls.groups = {}
        for group in cls.manifest["active_groups"]:
            filename = "AnimeCrazy" if group == "動畫瘋" else group
            cls.groups[group] = {
                line for line in cls.files[f"refactor/vnext/generated/{filename}.list"].splitlines()
                if line and not line.startswith("#")
            }

    def test_compiles_identically_twice(self):
        self.assertEqual(self.files, ve.compile_rules())

    def test_no_dependency_on_proxyprotect(self):
        cfg = self.files["refactor/vnext/LoonKit.vNext.Candidate.lcf"]
        self.assertNotIn("ProxyProtect.list", cfg)
        self.assertNotIn("Our-ProxyProtect", cfg)
        self.assertNotIn("vNext-ProxyProtect", cfg)
        self.assertIn("FINAL,Final", cfg)
        self.assertIn("Final = select,Proxy,Auto,Fallback,DIRECT", cfg)

    def test_selector_retained(self):
        cfg = self.files["refactor/vnext/LoonKit.vNext.Candidate.lcf"]
        self.assertIn("AdBlock = select,REJECT,DIRECT", cfg)
        for domain in ve.AD_ANCHORS:
            self.assertIn("DOMAIN-SUFFIX," + domain, self.groups["AdBlock"])
            for group, rules in self.groups.items():
                if group != "AdBlock":
                    self.assertNotIn("DOMAIN-SUFFIX," + domain, rules)


    def test_domain_only_business_regression(self):
        samples = {
            "www.ccb.com": "DIRECT",
            "www.google.com": "Google",
            "gemini.google.com": "AI",
            "www.netflix.com": "Netflix",
            "www.youtube.com": "YouTube",
            "web.telegram.org": "Telegram",
            "www.whatsapp.com": "Whatsapp",
            "copilot.microsoft.com": "AI",
            "login.microsoftonline.com": "Microsoft",
        }
        for host, expected in samples.items():
            result = ve.simulate_domain(host, self.files)
            self.assertEqual(result["policy"], expected, (host, result))
        self.assertEqual(
            ve.simulate_domain("ads-twitter.com", self.files, adblock_choice="REJECT")["effective"], "REJECT")
        self.assertEqual(
            ve.simulate_domain("ads-twitter.com", self.files, adblock_choice="DIRECT")["effective"], "DIRECT")
        unknown = "unknown-5827469.invalid"
        self.assertEqual(ve.simulate_domain(unknown, self.files, final_choice="DIRECT")["effective"], "DIRECT")
        self.assertEqual(ve.simulate_domain(unknown, self.files, final_choice="Proxy")["effective"], "Proxy")

    def test_asn_no_resolve(self):
        for group, asns in (("ChinaDirect", ["132203"]),
                            ("Facebook", ["32934"]),
                            ("Telegram", ["211157", "44907", "59930", "62014", "62041"])):
            for asn in asns:
                self.assertIn("IP-ASN," + asn + ",no-resolve", self.groups[group])
        for rules in self.groups.values():
            for rule in rules:
                if rule.startswith(("IP-CIDR,", "IP-CIDR6,", "IP-ASN,")):
                    self.assertTrue(rule.endswith(",no-resolve"), rule)
                    self.assertEqual(rule.count("no-resolve"), 1)

    def test_direct_isolation(self):
        direct = self.groups["ChinaDirect"]
        self.assertFalse(any(x.startswith("DOMAIN-KEYWORD,") for x in direct))
        self.assertIn("DOMAIN-SUFFIX,tmall.com", direct)
        self.assertIn("DOMAIN-SUFFIX,cn", direct)
        self.assertFalse(any(x.startswith("DOMAIN-SUFFIX,") and "." not in x.split(",")[1]
                             and x != "DOMAIN-SUFFIX,cn" for x in direct))
        guard = json.loads((ROOT / "rules/routing_guardrails.json").read_text())["protected_proxy_domains"]
        for rule in direct:
            for domain in guard:
                self.assertFalse(ve.covers_domain(rule, domain), f"{rule} accidentally directs {domain}")

    def test_cross_policy_exact_collision_is_never_silent(self):
        owners = {}
        for group, rules in self.groups.items():
            for rule in rules:
                self.assertNotIn(rule, owners, f"{rule}: {group} and {owners.get(rule)}")
                owners[rule] = group

    def test_ip_formats(self):
        examples = {
            "IP-CIDR,8.8.8.3/24": "IP-CIDR,8.8.8.0/24,no-resolve",
            "IP-CIDR6,2001:db8::1/64": "IP-CIDR6,2001:db8::/64,no-resolve",
            "IP-ASN,AS32934": "IP-ASN,32934,no-resolve",
            "IP-ASN,32934,no-resolve": "IP-ASN,32934,no-resolve",
        }
        for value, expected in examples.items():
            self.assertEqual(ve.normalize(value), expected)
        for broken in ("IP-ASN,INVALID", "IP-CIDR6,8.8.8.8/24",
                       "DOMAIN,example.com,no-resolve", "IP-CIDR,8.8.8.8,no-resolve,no-resolve"):
            with self.assertRaises(ValueError, msg=broken):
                ve.normalize(broken)

    def test_provenance_and_removed_impact_complete(self):
        provenance = self.files["refactor/vnext/reports/provenance.tsv"]
        self.assertIn("snapshot_line", provenance)
        self.assertIn("possible_upstream_source_ids", provenance)
        self.assertTrue(provenance.count("\n") > 10000)
        removed = self.files["refactor/vnext/reports/removed_or_modified.jsonl"]
        self.assertIn('"origin"', removed)
        self.assertIn('"replacement"', removed)
        self.assertIn('"compatibility"', removed)
        self.assertGreater(len(removed.splitlines()), 100)
        self.assertEqual(self.summary["baseline_upstream_source_count"], 87)

    def test_cross_type_risks_are_audited(self):
        for name, metric in (
            ("domain_parent_child_conflicts", "domain_parent_child_ambiguities"),
            ("domain_keyword_risks", "domain_keyword_review_count"),
            ("ip_network_overlaps", "cross_policy_nested_ip_networks"),
        ):
            lines = self.files["refactor/vnext/reports/" + name + ".jsonl"].splitlines()
            self.assertEqual(len(lines), self.summary[metric])
            if lines:
                record = json.loads(lines[0])
                self.assertEqual(record["status"], "REQUIRES_RUNTIME_TEST")
        self.assertFalse(any(r.startswith("DOMAIN-KEYWORD,") for r in self.groups["ChinaDirect"]))

    def test_all_seventeen_proxyprotect_entries_have_retirement_ledger(self):
        impacts = self.files["refactor/vnext/reports/proxyprotect_impact.jsonl"].splitlines()
        self.assertEqual(len(impacts), 17)
        self.assertEqual(self.summary["legacy_proxyprotect_rule_count"], 17)
        for entry in impacts:
            detail = json.loads(entry)
            self.assertEqual(detail["group"], "ProxyProtect")
            self.assertEqual(detail["replacement"], "service owner or FINAL")
            self.assertTrue(detail["line"] >= 1)
            self.assertIn("FINAL=DIRECT", detail["compatibility"])

    def test_production_general_section_byte_equivalent(self):
        original = (ROOT / "LoonKit.lcf").read_text()
        candidate = self.files["refactor/vnext/LoonKit.vNext.Candidate.lcf"]
        self.assertEqual(original.split("[General]", 1)[1].split("[Proxy]", 1)[0],
                         candidate.split("[General]", 1)[1].split("[Proxy]", 1)[0])

    def test_original_group_names_preserved(self):
        original = (ROOT / "LoonKit.lcf").read_text()
        candidate = self.files["refactor/vnext/LoonKit.vNext.Candidate.lcf"]
        orig = original.split("[Proxy Group]", 1)[1].split("[Remote Rule]", 1)[0]
        new = candidate.split("[Proxy Group]", 1)[1].split("[Remote Rule]", 1)[0]
        self.assertEqual(orig, new)
        for g in self.manifest["inactive_groups"]:
            self.assertNotIn("vNext-" + g + ".list", candidate)

    def test_config_refs_have_generated_files(self):
        candidate = self.files["refactor/vnext/LoonKit.vNext.Candidate.lcf"]
        urls = re.findall(
            r"https://raw.githubusercontent.com/YohakuSama/loonkit/refactor/loonkit-vnext/refactor/vnext/generated/([A-Za-z]+).list", candidate)
        self.assertEqual(len(urls), len(self.groups))
        for filename in urls:
            self.assertIn(f"refactor/vnext/generated/{filename}.list", self.files)
        self.assertNotIn("/main/rules/generated/", candidate)

    def test_baseline_repository_files_are_read_only(self):
        names = self.files.keys()
        self.assertTrue(all(name.startswith("refactor/vnext/") for name in names))
        self.assertFalse(any("/baselines/" in name for name in names))

    def test_explicit_final_handoff_and_no_runtime_claim(self):
        self.assertTrue(self.manifest["inactive_groups"])
        self.assertEqual(self.summary["release"], "NOT_READY_FOR_PRODUCTION")
        self.assertTrue(self.summary["remaining_risks"])
        self.assertLess(self.summary["candidate_rule_count"],
                        self.summary["baseline_count_from_selected_snapshot_groups"])


if __name__ == "__main__":
    unittest.main()
