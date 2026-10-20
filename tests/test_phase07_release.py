"""Phase07: immutable input/output separation, deterministic RC2, separate DNS."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import phase07_release as pr
import phase07_gate as gate
import phase07_source_update_review as updates
import phase07_license_audit as license_audit
import vnext_rule_engine as ve


class ReleaseBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = pr.generate()
        cls.spec = pr.read_spec()

    def test_source_and_output_are_disjoint_and_locked(self):
        m = ve.load_manifest()
        lock = json.loads((ROOT/"refactor/vnext/sources.lock.json").read_text())
        self.assertEqual(len(m["frozen_git_blob_sha1"]), 44)
        self.assertEqual(set(m["frozen_git_blob_sha1"]),
                         {x["path"] for x in lock["inputs"]})
        self.assertTrue(all(not p.startswith("rules/generated/")
                            for p in m["frozen_git_blob_sha1"]))
        self.assertTrue(all(not p.startswith("rules/releases/")
                            for p in m["frozen_git_blob_sha1"]))
        self.assertFalse(set(m["frozen_git_blob_sha1"]) &
                         set(x["path"] for x in json.loads(self.outputs["release/phase-07/RC_MANIFEST.json"])["rules"].values()))
        ve.verify_immutable_sources(ROOT, m)

    def test_two_profiles_same_rules_separate_original_general(self):
        main = self.outputs["LoonKit.lcf"]
        alt = self.outputs["LoonKit.PrivacyDNS.lcf"]
        self.assertEqual(pr.section(main, "Rule"), pr.section(alt, "Rule"))
        self.assertEqual(pr.section(main, "Remote Rule"), pr.section(alt, "Remote Rule"))
        self.assertEqual(pr.section(main, "Proxy Group"), pr.section(alt, "Proxy Group"))
        self.assertNotEqual(pr.section(main, "General"), pr.section(alt, "General"))
        for p, baseline in ((main,"LoonKit.legacy-seed.lcf"),
                            (alt,"LoonKit.PrivacyDNS.legacy-seed.lcf")):
            b=(ROOT/"refactor/vnext/templates"/baseline).read_text()
            self.assertEqual(pr.section(p,"General"), pr.section(b,"General"))
            self.assertNotIn("ProxyProtect", pr.section(p,"Remote Rule"))
            self.assertNotIn("/main/", pr.section(p,"Remote Rule"))
            self.assertNotIn("/main/", pr.section(p,"Plugin"))
            self.assertEqual(len([x for x in pr.section(p,"Remote Rule").splitlines()
                                  if x.startswith("https://")]),26)
            self.assertEqual(len([x for x in pr.section(p,"Rule").splitlines()
                                  if x.startswith(("DOMAIN,","DOMAIN-SUFFIX,","IP-ASN,",
                                                  "GEOIP,","FINAL,"))]),106)
            self.assertIn("FINAL,Final",p)
            self.assertIn("GEOIP,CN,DIRECT,no-resolve",p)

    def test_double_build_same_bytes(self):
        self.assertEqual(self.outputs, pr.generate())

    def test_legacy_formal_output_mutation_and_deletion_cannot_poison_input(self):
        # All necessary independent inputs are copied into a throwaway checkout.
        # Explicitly tamper with/remove the prior production output path.
        m=ve.load_manifest()
        with tempfile.TemporaryDirectory(prefix="loonkit-p7-") as temp:
            scratch=Path(temp)
            needed = set(m["frozen_git_blob_sha1"])
            needed.update(["refactor/vnext/engine_manifest.json",
                           "refactor/vnext/sources.lock.json",
                           "rules/sources.json", "rules/routing_guardrails.json",
                           "refactor/vnext/templates/LoonKit.legacy-seed.lcf",
                           "refactor/vnext/templates/LoonKit.PrivacyDNS.legacy-seed.lcf"])
            for rel in sorted(needed):
                dest=scratch/rel
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/rel,dest)
            expected=ve.compile_rules(scratch)
            output=scratch/"rules/generated/Google.list"
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_text("MALFORMED NEW OUTPUT\n")
            self.assertEqual(expected,ve.compile_rules(scratch))
            output.unlink()
            self.assertEqual(expected,ve.compile_rules(scratch))
            (scratch/"rules/generated").rmdir()

    def test_gate_prevents_unauthorized_merge(self):
        evidence=gate.check()
        self.assertEqual(evidence["release_status"], "BLOCKED_PENDING_MAINTAINER_TEST")
        self.assertIn("maintainer_approval", evidence["open_blockers"])
        with self.assertRaisesRegex(ValueError, "release BLOCKED"):
            gate.check(require_ready=True)

    def test_proposed_source_update_produces_review_only_diff(self):
        source="rules/snapshots/phase03/generated/Google.list"
        original=(ROOT/source).read_bytes()
        with tempfile.TemporaryDirectory() as td:
            proposed=Path(td)/"Google.proposed.list"
            proposed.write_bytes(original+b"\nDOMAIN-SUFFIX,example-phase07.invalid\n")
            report=updates.review(source,proposed)
            self.assertEqual(report["status"],"PENDING_REVIEW_NOT_PUBLISHED")
            self.assertEqual(report["added_rule_count"],1)
            self.assertFalse(report["release_write_performed"])
            self.assertEqual((ROOT/source).read_bytes(),original)

    def test_license_catalog_87_historical_records_is_explicitly_blocked(self):
        result=license_audit.audit()
        self.assertEqual(result["status"],"BLOCKED_REVIEW")
        self.assertEqual(result["historical_records_checked"],87)
        self.assertEqual(result["line_level_license_attribution"],"NOT_VERIFIED")

    def test_invalid_new_source_rule_rejected_without_touching_snapshot(self):
        src="rules/snapshots/phase03/generated/Google.list"
        original=(ROOT/src).read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            proposed=Path(tmp)/"Google.proposed.list"
            proposed.write_bytes(original+b"\nIP-ASN,NONNUMERIC\n")
            with self.assertRaisesRegex(ValueError,"invalid newly proposed Loon matcher"):
                updates.review(src,proposed)
            self.assertEqual((ROOT/src).read_bytes(),original)

    def test_release_gate_remains_explicitly_blocked(self):
        gate=json.loads((ROOT/"release/phase-07/RELEASE_GATE.json").read_text())
        self.assertEqual(gate["release_status"],"BLOCKED_PENDING_MAINTAINER_TEST")
        for key in ("licenses","device_import","domestic_business","overseas_business",
                    "adblock","final","dns_egress","ipv4_ipv6","maintainer_approval"):
            self.assertTrue(gate["checks"][key]["blocks_release"])
            self.assertNotEqual(gate["checks"][key]["status"],"PASS")


if __name__ == "__main__":
    unittest.main()
