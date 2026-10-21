"""Offline service coverage, routing and redacted log summary regressions."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import route_diagnostics as diag


class ParserAndPrivacy(unittest.TestCase):
    def test_matcher_semantics(self):
        self.assertEqual(diag.matcher("DOMAIN-SUFFIX,CN"), ("DOMAIN-SUFFIX", "cn"))
        self.assertEqual(diag.matcher("DOMAIN-SUFFIX,spotify.com"), ("DOMAIN-SUFFIX", "spotify.com"))
        self.assertEqual(diag.matcher("IP-CIDR,8.8.8.8/24"), ("IP-CIDR", "8.8.8.0/24"))
        self.assertEqual(diag.matcher("IP-CIDR6,2001:db8::1/64"), ("IP-CIDR6", "2001:db8::/64"))
        self.assertIsNone(diag.matcher("IP-CIDR6,8.8.8.0/24"))
        self.assertIsNone(diag.matcher("DOMAIN,http://foo.example"))
        self.assertIsNone(diag.matcher("URL-REGEX,example.com"))

    def test_log_redaction_har(self):
        raw = json.dumps({"log":{"entries":[
            {"request":{"url":"https://open.spotify.com/private?token=SECRET987",
                        "headers":[{"name":"Cookie","value":"PRIVATECOOKIE"}]},
             "response":{"status":403},
             "_policy":"SuperSecretNodeTokyo"},
            {"request":{"url":"https://api.linkedin.com/oauth?secret=PRIVATE"},
             "response":{"status":200}, "_policy":"Linkedin"},
            {"request":{"url":"https://203.0.113.2/private?token=SECRET"},
             "response":{"status":500}}
        ]}}).encode()
        output = diag.sanitized_log_summary(raw, diag.known_services())
        result = json.dumps(output, ensure_ascii=False)
        self.assertEqual(output["processed_requests"],2)
        self.assertIn('"service": "Spotify"',result)
        self.assertIn('"service": "Linkedin"',result)
        self.assertIn('"policy": "未知"',result)
        for secret in ("SECRET987","PRIVATECOOKIE","SuperSecretNodeTokyo","/oauth",
                       "open.spotify.com","api.linkedin.com"):
            self.assertNotIn(secret,result)
        self.assertNotIn("203.0.113.2",result)

    def test_log_redaction_text_and_limits(self):
        raw = b"2026-10-21 https://reddit.com/login?token=SECRET321 HTTP 401\n" \
              b"https://other.org/path?password=HIDDEN HTTP 503\n"
        out = diag.sanitized_log_summary(raw, diag.known_services(),text_mode=True)
        self.assertEqual(out["processed_requests"],2)
        self.assertIn("Reddit",str(out))
        for private in ("SECRET321","HIDDEN","reddit.com","other.org"):
            self.assertNotIn(private,str(out))
        with self.assertRaises(ValueError):
            diag.sanitized_log_summary(b"x"*(diag.MAX_LOG_SIZE+1),diag.known_services())
        with self.assertRaises(ValueError):
            diag.sanitized_log_summary(b"{}",diag.known_services())

    def test_private_triage_never_exposes_sensitive_fields(self):
        raw = json.dumps({"log": {"entries": [
            {"request": {"url": "https://open.spotify.com/secret?token=SENSITIVE_X11",
                          "headers": [{"name": "Cookie", "value": "COOKIE_X11"}]},
             "response": {"status": 403}, "_policy": "PersonalSecretNodeX11"},
            {"request": {"url": "https://log.spotify.com/trace?token=SENSITIVE_X12"},
             "response": {"status": 0}, "_policy": "AdBlock"},
            {"request": {"url": "https://www.reddit.com/private?token=SENSITIVE_X13"},
             "response": {"status": 503}, "_policy": "Reddit"},
            {"request": {"url": "https://other.example/file?secret=SENSITIVE_X14"},
             "response": {"status": 200}, "_policy": "other_unknown_node"},
        ]}}).encode()
        router = diag.Router(ROOT)
        result = diag.private_triage(raw, diag.known_services(), router)
        output = json.dumps(result, ensure_ascii=False)
        self.assertEqual(result["processed_requests"], 4)
        self.assertTrue(any("AdBlock" in x["finding"] for x in result["findings"]))
        self.assertTrue(any("5xx" in x["finding"] for x in result["findings"]))
        self.assertTrue(any("4xx" in x["finding"] for x in result["findings"]))
        for forbidden in (
            "SENSITIVE_X11", "SENSITIVE_X12", "SENSITIVE_X13", "SENSITIVE_X14",
            "COOKIE_X11", "PersonalSecretNodeX11", "other_unknown_node",
            "open.spotify.com", "log.spotify.com", "www.reddit.com",
            "other.example", "/secret", "/private"):
            self.assertNotIn(forbidden, output)

    def test_private_triage_text_mode_is_privacy_safe(self):
        raw = b"https://open.spotify.com/path?token=SENSITIVE_TXT HTTP 401\\n"
        result = diag.private_triage(raw, diag.known_services(), diag.Router(ROOT),
                                    text_mode=True)
        self.assertEqual(result["processed_requests"], 1)
        self.assertEqual(result["findings"][0]["recorded_policy"], "未知")
        self.assertNotIn("SENSITIVE_TXT", json.dumps(result))

    def test_missing_log_path_does_not_expose_private_filename(self):
        marker = "PRIVATE_SECRET_LOCAL_PATH_4519"
        result = subprocess.run([sys.executable, str(ROOT/"scripts/route_diagnostics.py"),
                                 "logs", "/tmp/"+marker+".har"],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(marker, result.stdout + result.stderr)

    def test_host_never_accepts_urls_as_rule_query(self):
        self.assertIsNone(diag._host("file:///private/secret"))
        self.assertIsNone(diag._host("https://127.0.0.1/secret"))
        self.assertIsNone(diag._host("https://my.example/path"*1000))


class SyntheticRouting(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = self.root = Path(self.temporary.name)
        path = root/"rules/releases/vNext-RC2"
        path.mkdir(parents=True)
        (path/"Spotify.list").write_text("DOMAIN-SUFFIX,spotify.com\n",encoding="utf-8")
        (root/"LoonKit.lcf").write_text(
            "[Rule]\nDOMAIN-SUFFIX,tracker.spotify.com,AdBlock\n"
            "DOMAIN-SUFFIX,cn,DIRECT\n"
            "[Remote Rule]\nhttps://raw.githubusercontent.com/YohakuSama/loonkit/"
            + "a"*40 + "/rules/releases/vNext-RC2/Spotify.list, policy=Spotify, tag=Example, enabled=true\n",
            encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def test_local_first_and_suffix_and_unmatched(self):
        router = diag.Router(self.root)
        self.assertEqual(router.match("tracker.spotify.com")["predicted_policy"],"AdBlock")
        self.assertEqual(router.match("open.spotify.com")["predicted_policy"],"Spotify")
        self.assertEqual(router.match("a.example.cn")["predicted_policy"],"DIRECT")
        self.assertTrue(router.match("unlisted.example")["predicted_policy"].startswith("Final"))
        self.assertEqual(router.match("tracker.spotify.com")["other_policies"],["Spotify"])
        with self.assertRaises(ValueError):
            router.match("https://spotify.com/auth?token=PRIVATE")

    def test_untrusted_remote_fails_closed(self):
        profile=self.root/"LoonKit.lcf"
        profile.write_text(profile.read_text().replace("a"*40,"main"),encoding="utf-8")
        with self.assertRaises(ValueError):
            diag.Router(self.root)


class ProductionCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.router = diag.Router(ROOT)

    def test_current_main_26_subscriptions(self):
        self.assertEqual(len(self.router.subscriptions),26)
        self.assertGreater(self.router.count,190000)

    def test_seven_registered_roots_correctly_routed(self):
        result = diag.coverage(self.router)
        self.assertTrue(result["all_reviewed_roots_match"],result)
        self.assertEqual({x["service"] for x in result["services"]},set(diag.SERVICE_GROUPS))
        self.assertEqual(len(result["services"]),7)

    def test_staged_service_rules_audit_is_review_only(self):
        result = diag.candidate_coverage_audit(self.router)
        self.assertFalse(result["publication_allowed"])
        self.assertEqual(len(result["services"]), 7)
        for item in result["services"]:
            self.assertGreater(item["candidate_domain_rules"], 0)
            self.assertEqual(
                item["candidate_domain_rules"],
                sum(item["counts"].get(k, 0) for k in (
                    "covered_by_service", "adblock_review",
                    "not_explicitly_routed", "routed_to_other_policy")))

    def test_known_safeguards(self):
        self.assertEqual(self.router.match("analytics.spotify.com")["predicted_policy"],"AdBlock")
        self.assertEqual(self.router.match("www.spotify.com")["predicted_policy"],"Spotify")
        self.assertEqual(self.router.match("gemini.google.com")["predicted_policy"],"AI")
        self.assertEqual(self.router.match("www.ccb.com")["predicted_policy"],"DIRECT")


if __name__ == "__main__":
    unittest.main()
