"""Production-only immutable routing, source, plugin and licensing tests."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import rule_engine as engine
import source_lock as lock
import verify_release as release
import review_source as updates
import license_audit as legal


class ProductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated = engine.compile_rules(ROOT)
        cls.groups = {}
        for path, body in cls.generated.items():
            cls.groups[path.removeprefix("build/generated/").removesuffix(".list")] = {
                line for line in body.splitlines() if line and not line.startswith("#")
            }
        cls.main = (ROOT / "LoonKit.lcf").read_text(encoding="utf-8")
        cls.config = json.loads((ROOT / "build/engine_manifest.json").read_text(encoding="utf-8"))

    @classmethod
    def simulate_domain(cls, host, final_choice="Final", adblock_choice="REJECT"):
        """Limited DOMAIN matcher simulation; not a substitute for real Loon traffic."""
        local = cls.main.split("\n[Rule]\n", 1)[1].split("\n[Plugin]", 1)[0]
        for line in local.splitlines():
            parts = [part.strip() for part in line.split(",")]
            if len(parts) >= 3 and parts[0] in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if engine.covers_domain(",".join(parts[:2]), host):
                    return adblock_choice if parts[2] == "AdBlock" else parts[2]
        for group in cls.config["subscription_order"]:
            filename = "AnimeCrazy" if group == "動畫瘋" else group
            for rule in cls.groups[filename]:
                if engine.covers_domain(rule, host):
                    policy = "DIRECT" if group in {"ChinaDirect", "DomesticCore", "SteamCN", "AppleOTA"} else group
                    return adblock_choice if policy == "AdBlock" else policy
        return final_choice

    def test_locked_inputs_and_determinism(self):
        self.assertEqual(lock.check_lock(ROOT)["verified_frozen_inputs"], 44)
        self.assertEqual(self.generated, engine.compile_rules(ROOT))
        self.assertEqual(len(self.groups), 26)

    def test_all_published_rules_and_dual_profiles(self):
        self.assertEqual(release.verify()["matchers"], 197765)
        self.assertEqual(len(release.section(self.main, "Remote Rule").split("https://"))-1, 26)

    def test_ads_retained_and_user_selectable(self):
        self.assertIn("AdBlock = select,REJECT,DIRECT", self.main)
        for host in engine.AD_ANCHORS:
            rule = "DOMAIN-SUFFIX," + host
            self.assertIn(rule, self.groups["AdBlock"])
            for group, rules in self.groups.items():
                if group != "AdBlock":
                    self.assertNotIn(rule, rules, group)
        self.assertEqual(self.simulate_domain("ads-twitter.com", adblock_choice="REJECT"), "REJECT")
        self.assertEqual(self.simulate_domain("ads-twitter.com", adblock_choice="DIRECT"), "DIRECT")

    def test_domestic_overseas_and_final(self):
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
        for host, policy in samples.items():
            with self.subTest(host=host):
                self.assertEqual(self.simulate_domain(host), policy)
        unknown = "unknown-5827469.invalid"
        self.assertEqual(self.simulate_domain(unknown, final_choice="Proxy"), "Proxy")
        self.assertEqual(self.simulate_domain(unknown, final_choice="DIRECT"), "DIRECT")
        self.assertIn("GEOIP,CN,DIRECT,no-resolve", self.main)
        self.assertIn("FINAL,Final", self.main)

    def test_direct_guardrails_and_cross_policy_conflicts(self):
        direct = self.groups["ChinaDirect"]
        self.assertIn("DOMAIN-SUFFIX,cn", direct)
        self.assertIn("DOMAIN-SUFFIX,tmall.com", direct)
        self.assertFalse(any(line.startswith("DOMAIN-KEYWORD,") for line in direct))
        protected = json.loads((ROOT / "rules/routing_guardrails.json").read_text())["protected_proxy_domains"]
        for rule in direct:
            for domain in protected:
                self.assertFalse(engine.covers_domain(rule, domain), (rule, domain))
        owners = {}
        for group, rules in self.groups.items():
            for rule in rules:
                self.assertNotIn(rule, owners, (rule, group, owners.get(rule)))
                owners[rule] = group

    def test_ip_ipv6_asn_no_resolve(self):
        for group, asns in (
            ("ChinaDirect", ["132203"]),
            ("Facebook", ["32934"]),
            ("Telegram", ["211157", "44907", "59930", "62014", "62041"]),
        ):
            for asn in asns:
                self.assertIn("IP-ASN," + asn + ",no-resolve", self.groups[group])
        for rules in self.groups.values():
            for rule in rules:
                if rule.startswith(("IP-CIDR,", "IP-CIDR6,", "IP-ASN,")):
                    self.assertTrue(rule.endswith(",no-resolve"), rule)
                    self.assertEqual(rule.count("no-resolve"), 1)
        examples = {
            "IP-CIDR,8.8.8.3/24": "IP-CIDR,8.8.8.0/24,no-resolve",
            "IP-CIDR6,2001:db8::1/64": "IP-CIDR6,2001:db8::/64,no-resolve",
            "IP-ASN,AS32934": "IP-ASN,32934,no-resolve",
        }
        for raw, expected in examples.items():
            self.assertEqual(engine.normalize(raw), expected)
        for bad in ("IP-ASN,INVALID", "IP-CIDR6,8.8.8.8/24", "DOMAIN,example.com,no-resolve"):
            with self.assertRaises(ValueError):
                engine.normalize(bad)

    def test_source_review_never_changes_published_files(self):
        source = ROOT / "rules/inputs/Google.list"
        before = source.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            proposed = Path(tmp) / "proposed.list"
            proposed.write_bytes(before + b"\nDOMAIN-SUFFIX,loonkit-ci.invalid\n")
            data = updates.review("rules/inputs/Google.list", proposed)
            self.assertEqual(data["added_rule_count"], 1)
            self.assertFalse(data["release_write_performed"])
        self.assertEqual(before, source.read_bytes())

    def test_license_sources_and_evidence_preserved(self):
        checked = legal.audit()
        self.assertIn(checked["status"], {"BLOCKED_REVIEW", "INDEPENDENT_REVIEW_DOCUMENTED"})
        self.assertEqual(checked["historical_records_checked"], 87)

    def test_production_config_bytes_protected(self):
        hashes = json.loads((ROOT / "build/release_manifest.json").read_text())["profile_sha256"]
        for path, expected in hashes.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()
