"""Upstream auto-update risk selector; synthetic inputs are never publication grants."""
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
import beta_upstream_triage as triage


class BetaRiskTriageTests(unittest.TestCase):
    def fixture(self):
        src = {"id":"approved","status":"PARSED_FOR_REVIEW","sha256":"a"*64}
        mani = {"source_count":1,"source_snapshots":[src],"global_source_integrity_complete":True,
                "publication_allowed":False,"branch_push_allowed":False,"version":"v6.5.6-beta.2",
                "groups":{"YouTube":{"baseline_count":5000,"status":"ROUTINE_CANDIDATE_REVIEW"},
                          "ChinaDirect":{"baseline_count":5000,"status":"ROUTINE_CANDIDATE_REVIEW"}}}
        diff = {"YouTube":{"added":["DOMAIN,owned-video-example.test"],"removed":[]},
                "ChinaDirect":{"added":[],"removed":[]}}
        risks = {"YouTube":{"additions":[{
            "rule":"DOMAIN,owned-video-example.test","review_tier":"STANDARD",
            "other_groups":[],"source_ids":["approved"]}]},
                 "ChinaDirect":{"additions":[]}}
        return mani, diff, risks

    def test_safe_exact_addition_only_eligible_for_draft_review(self):
        a,b,c=self.fixture()
        r=triage.evaluate(a,b,c)
        self.assertEqual(r["groups"]["YouTube"]["status"],
                         "LOW_RISK_DRAFT_PR_ELIGIBLE_REVIEW_REQUIRED")
        self.assertEqual(r["draft_eligible_added_rules"],1)
        self.assertFalse(r["publication_allowed"])

    def test_risks_fail_closed(self):
        scenarios=("deletion","direct_owner","broaden","shared","collision",
                   "lost_provenance","source_failure","source_exclusion","volume")
        for scenario in scenarios:
            with self.subTest(case=scenario):
                a,b,c=self.fixture()
                if scenario=="deletion": b["YouTube"]["removed"]=["DOMAIN,old.test"]
                if scenario=="direct_owner":
                    b["ChinaDirect"]["added"]=["DOMAIN,new-cn.example"]
                    c["ChinaDirect"]["additions"]=[{"rule":"DOMAIN,new-cn.example",
                         "review_tier":"STANDARD","other_groups":[],"source_ids":["approved"]}]
                if scenario=="broaden":
                    b["YouTube"]["added"]=["DOMAIN-SUFFIX,example.com"]
                if scenario=="shared":
                    b["YouTube"]["added"]=["DOMAIN,unknown.appspot.com"]
                    c["YouTube"]["additions"][0]["rule"]="DOMAIN,unknown.appspot.com"
                    # appspot isn't in explicit list? catch it in shared roots.
                if scenario=="collision":
                    c["YouTube"]["additions"][0]["other_groups"]=["Google"]
                if scenario=="lost_provenance":
                    c["YouTube"]["additions"][0]["source_ids"]=[]
                if scenario=="source_failure":
                    a["global_source_integrity_complete"]=False
                if scenario=="source_exclusion":
                    a["source_snapshots"][0]["status"]="PARSED_WITH_DOCUMENTED_EXCLUSIONS"
                if scenario=="volume":
                    b["YouTube"]["added"]=["DOMAIN,video-%d.example" % i for i in range(12)]
                    c["YouTube"]["additions"]=[{"rule":r,"review_tier":"STANDARD",
                           "other_groups":[],"source_ids":["approved"]} for r in b["YouTube"]["added"]]
                r=triage.evaluate(a,b,c)
                if scenario=="direct_owner":
                    self.assertEqual(r["groups"]["ChinaDirect"]["status"],"MANUAL_RISK_REVIEW")
                else:
                    self.assertEqual(r["groups"]["YouTube"]["status"],"MANUAL_RISK_REVIEW")
                self.assertEqual(r["draft_eligible_added_rules"],0)

    def test_conflicting_or_partial_audit_group_set_fails(self):
        a,b,c=self.fixture()
        c.pop("ChinaDirect")
        with self.assertRaisesRegex(ValueError,"complete"):
            triage.evaluate(a,b,c)
        a,b,c=self.fixture()
        c["YouTube"]["additions"].append(dict(c["YouTube"]["additions"][0]))
        with self.assertRaisesRegex(ValueError,"duplicated"):
            triage.evaluate(a,b,c)


if __name__=="__main__":
    unittest.main()
