"""Formal v6 compiler, locking, routing selectors and rights regression."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import rule_engine as engine
import source_lock as lock
import verify_release as release
import review_source as updates
import license_audit as legal

class ProductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated=engine.compile_rules(ROOT)

    def test_source_lock(self):
        self.assertEqual(lock.check_lock(ROOT)["verified_frozen_inputs"],44)

    def test_rule_rebuild_exact(self):
        self.assertEqual(len([p for p in self.generated if p.endswith(".list")]),26)
        self.assertEqual(release.verify()["matchers"],197765)

    def test_routing_adblock_domestic_overseas_final_ip(self):
        a=(ROOT/"LoonKit.lcf").read_text()
        for marker in ("AdBlock = select,REJECT,DIRECT","GEOIP,CN,DIRECT,no-resolve","FINAL,Final",
                       "policy=AI","policy=Google","policy=DIRECT"):
            self.assertIn(marker,a)
        for name in ("AdBlock","ChinaDirect","AI","Google"):
            self.assertIn("DOMAIN-SUFFIX,",self.generated["build/generated/"+name+".list"])

    def test_source_review_readonly(self):
        orig=ROOT/"rules/inputs/Google.list"
        data=orig.read_bytes()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"new.list"
            p.write_bytes(data+b"\nDOMAIN-SUFFIX,ci-test.invalid\n")
            result=updates.review("rules/inputs/Google.list",p)
        self.assertEqual(result["added_rule_count"],1)
        self.assertFalse(result["release_write_performed"])
        self.assertEqual(orig.read_bytes(),data)

    def test_licenses(self):
        out=legal.audit()
        self.assertIn(out["status"],{"BLOCKED_REVIEW","INDEPENDENT_REVIEW_DOCUMENTED"})
        self.assertEqual(out["historical_records_checked"],87)

    def test_profile_frozen_hashes(self):
        expected=json.loads((ROOT/"build/release_manifest.json").read_text())["profile_sha256"]
        for path,digest in expected.items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__=="__main__":
    unittest.main()
