"""Fail-closed DNS profile preflight; static checks do not claim zero DNS leaks."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "LoonKit.lcf"
PRIVATE = ROOT / "LoonKit.PrivacyDNS.lcf"

OLD_DNS = (
    "dns-server = 223.5.5.5,223.6.6.6",
    "doh-server = https://dns.alidns.com/dns-query",
)
NEW_DNS = (
    "dns-server = 119.29.29.29",
    "doh-server = https://doh.pub/dns-query",
)


def non_comments(source):
    return [line for line in source.splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


class DnsPrivacyProfileTests(unittest.TestCase):
    def test_optional_profile_has_supported_encrypted_dns(self):
        main = BASE.read_text(encoding="utf-8")
        opt = PRIVATE.read_text(encoding="utf-8")
        for old, new in zip(OLD_DNS, NEW_DNS):
            self.assertIn(old, main)
            self.assertIn(new, opt)
            self.assertNotIn(old, opt)
        self.assertIn("hijack-dns = *:53", opt)

    def test_optional_profile_differs_only_by_dns_resolvers(self):
        main = BASE.read_text(encoding="utf-8")
        opt = PRIVATE.read_text(encoding="utf-8")
        original_lines = non_comments(main)
        privacy_lines = non_comments(opt)
        self.assertEqual(len(original_lines), len(privacy_lines))
        for old, new in zip(OLD_DNS, NEW_DNS):
            original_lines = [new if line == old else line for line in original_lines]
        self.assertEqual(original_lines, privacy_lines)
        self.assertEqual(sum("/main/rules/" in line for line in privacy_lines),
                         34)

    def test_no_overseas_dns_in_shipped_profiles(self):
        for profile in (BASE, PRIVATE):
            config = profile.read_text(encoding="utf-8")
            settings = [line.strip() for line in config.splitlines()
                        if line.strip().startswith(("dns-server = ", "doh-server = "))]
            self.assertEqual(len(settings), 2, str(profile))
            self.assertNotIn("cloudflare-dns.com", "\n".join(settings))
            self.assertNotIn("1.1.1.1", "\n".join(settings))
            self.assertNotIn("8.8.8.8", "\n".join(settings))

    def test_docs_explicitly_require_app_toggle(self):
        guide = (ROOT / "docs/DNS_PRIVACY.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for text in (guide, readme):
            self.assertIn("LoonKit.PrivacyDNS.lcf", text)
            self.assertIn("回退", text)
            self.assertTrue("不能" in text or "无法" in text)


if __name__ == "__main__":
    unittest.main()
