"""Beta isolation, content-addressed asset, source-priority and routing regressions."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "LoonKit.lcf"
BETA = ROOT / "beta/LoonKit.lcf"
META = ROOT / "build/beta_manifest.json"
SOURCE = ROOT / "rules/beta/policy_overrides.json"


def section(data: str, label: str) -> str:
    return data.split("[" + label + "]", 1)[1].split("\n[", 1)[0]


def match(host: str, text: str) -> bool:
    parts = text.split(",")
    if len(parts) < 2:
        return False
    kind, value = parts[:2]
    return (
        (kind == "DOMAIN" and host == value) or
        (kind == "DOMAIN-SUFFIX" and (host == value or host.endswith("." + value))) or
        (kind == "DOMAIN-KEYWORD" and value in host)
    )


class BetaChannelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = BASE.read_text(encoding="utf-8")
        cls.beta = BETA.read_text(encoding="utf-8")
        cls.manifest = json.loads(META.read_text())
        cls.policy = json.loads(SOURCE.read_text())
        cls.local = [line for line in section(cls.beta, "Rule").splitlines()
                     if line.startswith(("DOMAIN,", "DOMAIN-SUFFIX,", "DOMAIN-KEYWORD,"))]
        cls.remotes = []
        for entry in section(cls.beta, "Remote Rule").splitlines():
            if not entry.startswith("https://"):
                continue
            uri, *args = entry.split(",")
            props = {k.strip(): v.strip() for a in args if "=" in a
                     for k, v in [a.strip().split("=", 1)]}
            if "/rules/beta/" in uri:
                path = ROOT / uri.split("/loonkit/" + cls.manifest["immutable_overlay_commit"] + "/", 1)[1]
            else:
                path = ROOT / uri.split("/loonkit/" + cls.manifest["production_release_commit"] + "/", 1)[1]
            cls.remotes.append((props, path))

    def effective(self, host: str, *, without_adblock: bool = False) -> str:
        host = host.lower()
        for line in self.local:
            if match(host, line):
                return line.split(",", 2)[2]
        for props, path in self.remotes:
            if without_adblock and props["policy"] == "AdBlock":
                continue
            # Loon local-first, remote rules in listed order; no plugin block rules.
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith(("DOMAIN,", "DOMAIN-SUFFIX,", "DOMAIN-KEYWORD,")) and match(host, line):
                    return props["policy"]
        return "Final"  # Tests only domain inputs; GEOIP/no-resolve requires device/IP path.

    def test_manifest_and_frozen_rule_integrity(self):
        self.assertEqual(hashlib.sha256(self.beta.encode()).hexdigest(),
                         self.manifest["configuration_sha256"])
        self.assertEqual(hashlib.sha256(self.main.encode()).hexdigest(),
                         self.manifest["original_production_config_sha256"])
        self.assertEqual(self.beta.splitlines()[0], "# LoonKit v6.5.5-beta.1 · BETA TEST ONLY")
        self.assertEqual(len(self.manifest["overlay_rules"]), 10)
        for item in self.manifest["overlay_rules"].values():
            path = ROOT / item["uri"].split("/loonkit/" + self.manifest["immutable_overlay_commit"] + "/", 1)[1]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])
        self.assertEqual(len(self.remotes), 34)

    def test_dns_equal_to_production_and_no_private_dns(self):
        for key in ("dns-server", "doh-server", "hijack-dns", "ip-mode", "ipv6-vif",
                    "interface-mode", "skip-proxy", "bypass-tun", "real-ip"):
            pat = r"(?m)^" + re.escape(key) + r"\s*=.*$"
            self.assertEqual(re.search(pat, section(self.main, "General")).group(),
                             re.search(pat, section(self.beta, "General")).group())
        self.assertIn("https://dns.alidns.com/dns-query", self.beta)
        self.assertNotIn("novaxns", self.beta.lower())
        self.assertIn("GEOIP,CN,DIRECT,no-resolve", section(self.beta, "Rule"))
        self.assertIn("FINAL,Final", section(self.beta, "Rule"))

    def test_adblock_resources_are_reversible(self):
        self.assertFalse(any(x.endswith(",AdBlock") for x in self.local))
        self.assertEqual({p["tag"] for p, _ in self.remotes if p["policy"] == "AdBlock"},
                         {"Our-AdBlock", "Beta-LocalAdBlock"})
        self.assertEqual(self.effective("analytics.spotify.com"), "AdBlock")
        self.assertEqual(self.effective("analytics.spotify.com", without_adblock=True), "Spotify")
        self.assertEqual(self.effective("pixel.facebook.com", without_adblock=True), "Facebook")
        self.assertEqual(self.effective("copilot.microsoft.com", without_adblock=True), "AI")
        # No broad local ownership can shadow an earlier remote tracking rule.
        for host in ("telemetry.microsoft.com", "events.data.microsoft.com", "pixel.facebook.com"):
            self.assertFalse(any(match(host, x) for x in self.local))

    def test_steam_split_and_unknown_fallback(self):
        for host in ("cm.steampowered.com", "a.steamcontent.com",
                     "a.steamserver.net", "a.steamusercontent.com",
                     "store.steampowered.com"):
            self.assertEqual(self.effective(host), "Steam", host)
        for host in ("dl.steam.ksyna.com", "dl.steam.clngaa.com", "steamchina.com"):
            self.assertEqual(self.effective(host), "DIRECT", host)
        self.assertEqual(self.effective("unregistered-service.example"), "Final")
        self.assertEqual(self.effective("notcolab-specific-example.invalid"), "Final")
        self.assertIn("DOMAIN,copilot.microsoft.com,AI", self.local)

    def test_no_lie_about_selector_direct(self):
        self.assertIn("AdBlock = select,REJECT,DIRECT", section(self.beta, "Proxy Group"))
        self.assertIn("DIRECT in AdBlock is NOT bypass/continue matching", self.beta)
        self.assertNotIn("policy=PASS", self.beta)


if __name__ == "__main__":
    unittest.main()
