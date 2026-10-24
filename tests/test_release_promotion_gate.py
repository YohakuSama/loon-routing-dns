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
        self.assertTrue(any("observation dates" in p or "seven days" in p for p in outcome["problems"]))
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

    def test_live_release_gate_rejects_stale_head_and_wrong_ci(self):
        # Complete synthetic evidence is not real user approval; inspect the live model only.
        stable=json.loads((ROOT/"build/release_manifest.json").read_text())
        release_bytes=(ROOT/"LoonKit.lcf").read_bytes()
        beta_bytes=(ROOT/"beta/LoonKit.lcf").read_bytes()
        sha="a"*40
        class Fake:
            stale=False
            wrong_ci=False
            def get(self,path):
                if path=="/pulls/119":
                    return {"state":"open","draft":False,"mergeable_state":"clean",
                        "head":{"ref":gate.HEAD_BRANCH,"sha":sha,"repo":{"full_name":"YohakuSama/loonkit"}},
                        "base":{"ref":"main","sha":gate.BASE,"repo":{"full_name":"YohakuSama/loonkit"}}}
                if path=="/git/ref/heads/main": return {"object":{"sha":gate.BASE}}
                if path=="/git/ref/heads/beta": return {"object":{"sha":gate.SOURCE}}
                if path=="/git/ref/heads/"+gate.HEAD_BRANCH:
                    return {"object":{"sha":"b"*40 if self.stale else sha}}
                if path=="/actions/runs/123":
                    return {"head_sha":gate.SOURCE,"conclusion":"success","status":"completed","name":"LoonKit Beta CI",
                            "repository":{"full_name":"YohakuSama/loonkit"}}
                if path=="/actions/runs/123/jobs?per_page=100":
                    return {"jobs":[{"name":"beta","conclusion":"success"}]}
                if path.startswith("/actions/runs?head_sha="):
                    return {"workflow_runs":[{"id":444,"name":"LoonKit Production CI","head_sha":sha,
                        "status":"completed","conclusion":"failure" if self.wrong_ci else "success",
                        "repository":{"full_name":"YohakuSama/loonkit"}}]}
                if path=="/actions/runs/444/jobs?per_page=100":
                    return {"jobs":[{"name":"production","conclusion":"success","head_sha":sha}]}
                raise AssertionError("unexpected fake API route "+path)
            def file(self,path,ref):
                if (path,ref)==("beta/LoonKit.lcf",gate.SOURCE): return beta_bytes
                if (path,ref)==("LoonKit.lcf",sha): return release_bytes
                if (path,ref)==("build/release_manifest.json",sha): return json.dumps(stable).encode()
                raise AssertionError("unexpected fake file "+path)
        evidence={"ci":{"run_url":"https://github.com/YohakuSama/loonkit/actions/runs/123"}}
        ready={"status":"READY_FOR_LIVE_RELEASE_PR_CHECK","problems":[]}
        api=Fake()
        r=gate.check_live(ready,evidence,stable,api,119)
        self.assertEqual(r["status"],"LIVE_READY_FOR_PROTECTED_REVIEW")
        self.assertIs(r["publication_is_authorized"],False)
        api.stale=True
        self.assertEqual(gate.check_live(ready,evidence,stable,api,119)["status"],"RELEASE_PROMOTION_BLOCKED")
        api.stale=False
        api.wrong_ci=True
        self.assertEqual(gate.check_live(ready,evidence,stable,api,119)["status"],"RELEASE_PROMOTION_BLOCKED")


if __name__=="__main__":
    unittest.main()
