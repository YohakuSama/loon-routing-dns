"""Independent naive reference against beta remote-domain index and conflict samples."""
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import beta_effective_audit as audit


class BetaEffectiveAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta, cls.local, cls.remotes = audit.build()

    def test_real_enabled_profile_has_expected_static_routes(self):
        info = audit.report()
        self.assertEqual(info["candidate"], "v6.5.5-beta.3")
        self.assertEqual(len(info["verified_synthetic_routes"]), 15)
        self.assertEqual(info["remote_subscriptions"], 34)
        for host in ("pixel.facebook.com", "telemetry.microsoft.com",
                     "analytics.spotify.com", "events.data.microsoft.com"):
            self.assertEqual(info["verified_synthetic_routes"][host]
                             ["adblock_on"]["policy"], "AdBlock")
        self.assertEqual(info["verified_synthetic_routes"]
                         ["copilot.microsoft.com"]["adblock_on"]["policy"], "AI")
        self.assertEqual(info["verified_synthetic_routes"]
                         ["ocsp.apple.com"]["adblock_on"]["policy"], "DIRECT")

    def test_domain_index_matches_naive_independent_membership(self):
        samples = [
            "pixel.facebook.com", "events.data.microsoft.com",
            "foo.wechat.com", "foo.wechatapp.com",
            "unknown-unlisted-tld-proof.cn", "youtube.com", "google.com",
            "t.example.steamcontent.com", "example.invalid", "tenant-unknown.apis.google.com"
        ]
        for item in self.remotes:
            for host in samples:
                indexed = item["index"].match(host) is not None
                naive = any(audit.naive_domain_match(host, rule) for rule in item["lines"])
                self.assertEqual(indexed, naive, (host, item["tag"]))

    def test_apple_identity_and_shared_infrastructure_are_not_autoblocked(self):
        for host in ("ocsp.apple.com", "mesu.apple.com", "login.microsoftonline.com"):
            self.assertNotEqual(audit.trace(host, self.local, self.remotes)["policy"],
                                "AdBlock", host)
        pending = audit.report()["open_scope_review"]
        self.assertEqual(pending["tenant-unknown.apis.google.com"].get("risk"),
                         "SHARED_INFRASTRUCTURE_OWNER_REVIEW")
        self.assertEqual(pending["wechat.com"]["device_verification"], "NOT_TESTED")

    def test_traffic_logs_and_private_dns_not_required_or_uploaded(self):
        import inspect
        src = inspect.getsource(audit)
        for bad in ("requests.get(", "urllib.request", "HTTP_PROXY", "shutil.rmtree",
                    "subprocess.run(", "os.environ["):
            self.assertNotIn(bad, src)
        self.assertNotIn("NovaXNS", audit.report()["configuration_sha256"])

    def test_no_broad_tld_and_restored_known_policy(self):
        self.assertEqual(audit.trace("unknown-unlisted-tld-proof.cn",
                                    self.local, self.remotes)["policy"], "Final")
        self.assertEqual(audit.trace("analytics.spotify.com",
                                    self.local, self.remotes, True)["policy"], "Spotify")
        self.assertEqual(audit.trace("pixel.facebook.com",
                                    self.local, self.remotes, True)["policy"], "Facebook")


if __name__ == "__main__":
    unittest.main()
