"""Scoped service routing and unified plugin release contracts."""
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import route_diagnostics as diag

class ServiceCoverageReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = (ROOT/"LoonKit.lcf").read_text(encoding="utf-8")
        cls.manifest = json.loads((ROOT/"rules/service_coverage_v6.1.0.json").read_text(encoding="utf-8"))
        cls.router = diag.Router(ROOT)

    def test_curated_sources_and_entire_inserted_block_exact(self):
        scoped = self.profile.split("# Scoped service-owned hosts", 1)[1].split(
            "GEOIP,CN,DIRECT,no-resolve", 1)[0]
        actual = [line for line in scoped.splitlines()
                  if line.startswith("DOMAIN-SUFFIX,")]
        expected = []
        for service, domains in self.manifest["reviewed_services"].items():
            frozen = (ROOT/"rules/inputs"/(service+".list")).read_text(encoding="utf-8")
            sources = set(frozen.splitlines())
            for domain in domains:
                rule = "DOMAIN-SUFFIX,"+domain
                self.assertIn(rule, sources, (service,domain))
                self.assertGreaterEqual(domain.count("."), 1)
                self.assertNotIn(domain, ("cloudfront.net", "akamaized.net",
                                           "fastly.net", "cdn-cf.behance.net"))
                expected.append(rule+","+service)
        self.assertEqual(actual,expected)
        self.assertEqual(self.manifest["domain_rules_count"], 62)
        self.assertEqual(len(actual),len(set(actual)))

    def test_curated_entries_route_through_correct_service(self):
        examples = {
            "Spotify":"www.spotifycdn.com", "Twitch":"static.twitchcdn.net",
            "Abema":"video.abematv.akamaized.net", "BBC":"media.bbci.co.uk",
            "Line":"static.line-cdn.net", "Reddit":"redditstatic.com",
            "Linkedin":"lnkd.in"
        }
        for policy, host in examples.items():
            with self.subTest(service=policy,host=host):
                self.assertEqual(self.router.match(host)["predicted_policy"],policy)

    def test_advertising_auth_payments_and_direct_unchanged(self):
        samples = {
            "analytics.spotify.com":"AdBlock",
            "buttons.reddit.com":"AdBlock",
            "ads.linkedin.com":"AdBlock",
            "spade.twitch.tv":"AdBlock",
            "www.ccb.com":"DIRECT",
            "www.abchina.com":"DIRECT",
            "gemini.google.com":"AI",
            "login.microsoftonline.com":"Microsoft",
            "accounts.spotify.com":"Spotify",
        }
        for host,policy in samples.items():
            with self.subTest(host=host):
                self.assertEqual(self.router.match(host)["predicted_policy"],policy)

    def test_manual_only_service_plugin_is_pinned(self):
        spec = json.loads((ROOT/"build/release_spec.json").read_text(encoding="utf-8"))
        plugin = (ROOT/"release/Network_Diagnostics.plugin").read_text(encoding="utf-8")
        self.assertEqual(spec["stable_release_version"],"v6.3.8")
        self.assertEqual(self.profile.count("/release/Network_Diagnostics.plugin, enabled=true"),1)
        self.assertIn("/"+spec["plugin_assets_commit"]+
                      "/release/Network_Diagnostics.plugin, enabled=true",self.profile)
        self.assertNotIn("/release/Service_Diagnostics.plugin, enabled=true",self.profile)
        self.assertEqual(plugin.count("generic then script("),3)
        self.assertEqual(plugin.count("network-changed then script("),1)
        self.assertNotIn("service = select,",plugin)
        self.assertIn("auto_check = switch,false",plugin)
        self.assertIn("full_scan = switch,false",plugin)
        self.assertIn('tag="解锁检测"',plugin)
        self.assertIn("/"+spec["unified_service_diagnostics_script_commit"]+
                      "/scripts/v20261021r14/media-unlock.js",plugin)
        self.assertNotIn("/main/scripts/",plugin)

    def test_formal_remote_rules_still_original_pinned_set(self):
        old_pin = "9bbac4c9aa0ec33c82ab5fe03648127f3f4754f4"
        lines = diag.profile_sections(self.profile)["Remote Rule"]
        self.assertEqual(len(lines),26)
        for line in lines:
            self.assertIn(old_pin+"/rules/releases/vNext-RC2/",line)

if __name__ == "__main__":
    unittest.main()
