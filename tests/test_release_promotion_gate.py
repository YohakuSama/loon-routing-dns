"""Fail-closed release gate checks: tests never constitute real device evidence."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import release_promotion_gate as gate


class ReleaseGateTests(unittest.TestCase):
    def test_unfilled_device_template_blocks_real_release(self):
        outcome=gate.offline()
        self.assertEqual(outcome["status"],"RELEASE_PROMOTION_BLOCKED")
        self.assertIn("seven days"," ".join(outcome["problems"]))
        self.assertIs(outcome["publication_is_authorized"],False)

    def fixture(self):
        ev=json.loads(gate.TEMPLATE.read_text())
        ev.update(status="VERIFIED_DEVICE_OBSERVATIONS",commit_sha=gate.SOURCE,maintainer_approved=True)
        ev["ci"]={"workflow":"LoonKit Beta CI","commit_sha":gate.SOURCE,
                  "run_url":"https://github.com/YohakuSama/loonkit/actions/runs/123","conclusion":"success"}
        dt=datetime(2026,10,1,tzinfo=timezone.utc)
        ev["observation_started_utc"]=dt.isoformat().replace("+00:00","Z")
        ev["observation_finished_utc"]=(dt+timedelta(days=8)).isoformat().replace("+00:00","Z")
        ev["risk_reviews"]={k:"RESOLVED_WITH_EVIDENCE" for k in ev["risk_reviews"]}
        ev["device_cases"]={k:"PASS" for k in ev["device_cases"]}
        ev["sanitized_evidence_refs"]=["docs/BETA_DEVICE_MATRIX.md"]
        return ev

    def test_wrong_commit_or_unverified_scenarios_still_block(self):
        src=self.fixture()
        for field,value in (("commit_sha","0"*40),("observation_finished_utc","2026-10-02T00:00:00Z"),
                            ("maintainer_approved",False)):
            with self.subTest(field=field):
                ev=copy.deepcopy(src)
                ev[field]=value
                from beta_promotion_gate import assess
                template=json.loads(gate.TEMPLATE.read_text())
                beta=json.loads((ROOT/"build/beta_manifest.json").read_text())
                a=assess(beta,ev,(ROOT/"beta/LoonKit.lcf").read_bytes(),
                         template["device_cases"],template["risk_reviews"])
                self.assertEqual(a["status"],"PROMOTION_BLOCKED")

    def test_no_release_pr_or_failed_device_gate_never_calls_network(self):
        class Client:
            def get(self,p): raise AssertionError("network must not be called")
        outcome=gate.offline()
        r=gate.check_live(outcome,{}, {},Client(),119)
        self.assertEqual(r["status"],"RELEASE_PROMOTION_BLOCKED")
        self.assertEqual(r["live_status"],"NOT_RUN_DEVICE_GATE_BLOCKED")


if __name__=="__main__":
    unittest.main()
