"""Protect LoonKit's fixed group layout and balanced multi-subscription selection."""
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "LoonKit.lcf"
EXPECTED_GROUPS = (
    "Proxy", "Auto", "Fallback", "AdBlock", "Final", "AI", "Google",
    "Microsoft", "Apple", "YouTube", "Netflix", "Disney", "PrimeVideo",
    "Spotify", "TikTok", "Twitch", "HBO", "Abema", "動畫瘋", "Dazn",
    "BBC", "Bilibili", "Telegram", "Whatsapp", "Instagram", "Facebook",
    "Twitter", "Discord", "Line", "Reddit", "Linkedin", "Steam", "Paypal",
)


def get_section(profile, heading):
    match = re.search(r"(?m)^\[" + re.escape(heading) + r"\]$", profile)
    if not match:
        raise AssertionError("Missing Loon section " + heading)
    rest = profile[match.end():]
    next_section = re.search(r"(?m)^\[[^\]]+\]$", rest)
    return rest[:next_section.start()] if next_section else rest


def settings(section):
    return {key.strip(): value.strip()
            for line in section.splitlines() if line.strip() and not line.lstrip().startswith("#")
            for key, sep, value in [line.partition("=")] if sep}


class PolicySelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = PROFILE.read_text(encoding="utf-8")
        cls.groups = settings(get_section(cls.profile, "Proxy Group"))
        cls.filters = settings(get_section(cls.profile, "Remote Filter"))
        cls.general = settings(get_section(cls.profile, "General"))

    def test_no_new_or_removed_strategy_groups(self):
        self.assertEqual(tuple(self.groups), EXPECTED_GROUPS)
        self.assertEqual(len(self.groups), 33)

    def test_filters_isolate_manual_and_automatic_candidates(self):
        for name in ("ALL_Filter", "Auto_Filter", "Fallback_Filter"):
            self.assertEqual(self.filters[name], 'NameRegex, FilterKey = ".*"')
        self.assertTrue(self.groups["Proxy"].startswith("select,Auto,Fallback,ALL_Filter,"))
        self.assertTrue(self.groups["Auto"].startswith("url-test,Auto_Filter,"))
        self.assertTrue(self.groups["Fallback"].startswith("fallback,Fallback_Filter,"))
        # All existing service selectors retain manual/auto/fallback access.
        for name in EXPECTED_GROUPS:
            if name in ("Proxy", "Auto", "Fallback", "AdBlock", "Final"):
                continue
            self.assertIn("ALL_Filter", self.groups[name], name)

    def test_native_probe_address_is_consistent(self):
        probe = "http://cp.cloudflare.com/generate_204"
        self.assertEqual(self.general["proxy-test-url"], probe)
        for name in ("Auto", "Fallback"):
            self.assertIn("url = " + probe, self.groups[name])
            self.assertNotIn("http://bing.com/", self.groups[name])
        self.assertEqual(self.general["internet-test-url"],
                         "http://wifi.vivo.com.cn/generate_204")
        self.assertEqual(self.general["test-timeout"], "5")

    def test_balanced_intervals_and_failover_threshold(self):
        self.assertIn("interval = 900", self.groups["Auto"])
        self.assertIn("tolerance = 80", self.groups["Auto"])
        self.assertIn("interval = 900", self.groups["Fallback"])
        self.assertIn("max-timeout = 1800", self.groups["Fallback"])

    def test_dns_routes_and_plugin_are_unchanged_in_scope(self):
        rules = get_section(self.profile, "Rule")
        self.assertIn("GEOIP,CN,DIRECT,no-resolve", rules)
        self.assertIn("FINAL,Final", rules)
        self.assertEqual(len([x for x in get_section(self.profile, "Plugin").splitlines()
                              if x.startswith("https://") and ".plugin" in x]), 1)


if __name__ == "__main__":
    unittest.main()
