"""Synthetic preflight fixtures; NEVER misrepresent fixture PASS as device evidence."""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import beta_promotion_gate as gate


class BetaPromotionPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT/"build/beta_manifest.json").read_text())
        cls.template = json.loads((ROOT/"docs/BETA_ACCEPTANCE_TEMPLATE.json").read_text())
        cls.profile = (ROOT/"beta/LoonKit.lcf").read_bytes()

    def assess(self, ev):
        return gate.assess(self.manifest, ev, self.profile,
                           self.template["device_cases"], self.template["risk_reviews"])

    def synthetic_complete_fixture(self):
        # Test-only fabricated evidence. Never publish or use for approval.
        ev = copy.deepcopy(self.template)
        ev["status"] = "VERIFIED_DEVICE_OBSERVATIONS"
        ev["commit_sha"] = "b" * 40
        ev["ci"] = {"workflow":"LoonKit Beta CI","commit_sha":"b"*40,
                    "conclusion":"success",
                    "run_url":"https://github.com/YohakuSama/loonkit/actions/runs/123"}
        day = datetime(2026, 10, 1, tzinfo=timezone.utc)
        ev["observation_started_utc"] = day.isoformat().replace("+00:00","Z")
        ev["observation_finished_utc"] = (day + timedelta(days=8)).isoformat().replace("+00:00","Z")
        ev["device_cases"] = {key:"PASS" for key in ev["device_cases"]}
        ev["risk_reviews"] = {key:"RESOLVED_WITH_EVIDENCE" for key in ev["risk_reviews"]}
        ev["sanitized_evidence_refs"] = ["docs/BETA_DEVICE_MATRIX.md"]
        ev["maintainer_approved"] = True
        return ev

    def test_actual_template_cannot_pass_gate(self):
        outcome = self.assess(self.template)
        self.assertEqual(outcome["status"], "PROMOTION_BLOCKED")
        self.assertTrue(any("seven days" in p or "UTC observation" in p
                            for p in outcome["problems"]))
        self.assertTrue(any("unverified device" in p for p in outcome["problems"]))

    def test_positive_synthetic_fixture_exercises_conditions_only(self):
        outcome = self.assess(self.synthetic_complete_fixture())
        self.assertEqual(outcome["status"], "PREFLIGHT_READY_REQUIRES_LIVE_GITHUB_APPROVAL_AND_PR")
        self.assertTrue(any("cannot verify" in p for p in outcome["limitations"]))

    def test_exact_commit_ci_and_checksum_required(self):
        for mutation in ("candidate_version", "ci_sha", "hash", "wrong_ref"):
            with self.subTest(mutation=mutation):
                ev = self.synthetic_complete_fixture()
                m = copy.deepcopy(self.manifest)
                if mutation == "candidate_version": ev["version"] = "v0.0.0"
                if mutation == "ci_sha": ev["ci"]["commit_sha"] = "c"*40
                if mutation == "hash": ev["configuration_sha256"] = "0"*64
                if mutation == "wrong_ref": ev["rollback_commit_sha"] = "0"*40
                self.assertEqual(self.assess(ev)["status"], "PROMOTION_BLOCKED")

    def test_fail_closed_for_day_six_failures_and_unresolved_risk(self):
        for mutation in ("six_days","future_days","failed_case","open_risk","missing_case",
                         "no_review","raw_secret","invalid_ci_link"):
            with self.subTest(mutation=mutation):
                ev = self.synthetic_complete_fixture()
                if mutation == "six_days":
                    ev["observation_finished_utc"] = "2026-10-07T00:00:00Z"
                if mutation == "future_days":
                    ev["observation_started_utc"] = "2099-01-01T00:00:00Z"
                    ev["observation_finished_utc"] = "2099-01-09T00:00:00Z"
                if mutation == "failed_case":
                    ev["device_cases"]["mainland_payment_login_map"] = "FAIL"
                if mutation == "open_risk":
                    ev["risk_reviews"]["shared_ai_google_apis"] = "OPEN"
                if mutation == "missing_case":
                    ev["device_cases"].pop("dns_doh_failed_without_plain_fallback")
                if mutation == "no_review": ev["maintainer_approved"] = False
                if mutation == "raw_secret": ev["private_dns_url"] = "https://hidden.invalid/secret"
                if mutation == "invalid_ci_link":
                    ev["ci"]["run_url"] = "https://not-github.example/jobs/1"
                self.assertEqual(self.assess(ev)["status"], "PROMOTION_BLOCKED")

    def test_live_ci_and_protected_pr_cannot_be_replaced_by_local_booleans(self):
        ev=self.synthetic_complete_fixture()
        manifest=self.manifest
        profile=self.profile
        class API:
            failed=False
            def get(self,path):
                if path.startswith('/actions/runs/') and path.endswith('/jobs?per_page=100'):
                    return {'jobs':[{'name':'beta','status':'completed','conclusion':'success'}]}
                if path.startswith('/actions/runs/'):
                    return {'head_sha':ev['commit_sha'],'conclusion':'failure' if self.failed else 'success','status':'completed',
                        'name':'LoonKit Beta CI','path':'.github/workflows/beta-ci.yml',
                        'repository':{'full_name':'YohakuSama/loonkit'},'head_repository':{'full_name':'YohakuSama/loonkit'}}
                if path=='/git/ref/heads/beta': return {'object':{'sha':ev['commit_sha']}}
                if path=='/pulls/999': return {'state':'open','draft':False,'head':{'ref':'beta','sha':ev['commit_sha']},
                    'base':{'ref':'main'},'mergeable_state':'clean'}
                raise AssertionError(path)
            def file(self,path,ref):
                return profile if path=='beta/LoonKit.lcf' else json.dumps(manifest).encode()
        api=API()
        passed=gate.verify_live(self.assess(ev),manifest,ev,api,999)
        self.assertEqual(passed['status'],'LIVE_PREFLIGHT_READY_FOR_PROTECTED_MERGE')
        api.failed=True
        self.assertEqual(gate.verify_live(self.assess(ev),manifest,ev,api,999)['status'],'PROMOTION_BLOCKED')


if __name__ == "__main__":
    unittest.main()
