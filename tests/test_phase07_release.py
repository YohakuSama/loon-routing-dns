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
import phase07_next_release as next_release
import phase07_device_attestation as device_attestation
import phase07_license_audit as license_audit
import phase07_historical_attestation as historical_attestation
import vnext_rule_engine as ve


class ReleaseBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = pr.generate()
        cls.spec = pr.read_spec()

    def test_all_44_frozen_inputs_have_original_git_object_bytes(self):
        result=historical_attestation.check()
        self.assertEqual(result["status"],"PINNED_HISTORICAL_BLOBS_VERIFIED")
        self.assertEqual(result["verified_bytes"],44)
        self.assertEqual(result["moved_generated_snapshots"],33)

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

    def test_all_live_actions_have_read_only_permissions_and_no_auto_write(self):
        workflows=sorted((ROOT/".github/workflows").glob("*.yml"))
        self.assertGreaterEqual(len(workflows),9)
        for workflow in workflows:
            body=workflow.read_text(encoding="utf-8")
            for disallowed in ("contents: write", "pull-requests: write", "git push ",
                               "git commit ", "peter-evans/create-pull-request",
                               "persist-credentials: true"):
                self.assertNotIn(disallowed,body,(workflow.name,disallowed))
        archived=(ROOT/"refactor/vnext/templates/phase01-composite-rules.yml").read_bytes()
        baseline=json.loads((ROOT/"baselines/current/manifest.json").read_text())
        expected=next(row["sha256"] for row in baseline["files"]
                      if row["path"]==".github/workflows/composite-rules.yml")
        import hashlib
        self.assertEqual(hashlib.sha256(archived).hexdigest(),expected)

    def test_gate_prevents_unauthorized_merge(self):
        evidence=gate.check()
        if evidence["release_status"]=="APPROVED":
            self.assertEqual(evidence["open_blockers"],[])
            self.assertEqual(gate.check(require_ready=True)["release_status"],"APPROVED")
        else:
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
            self.assertEqual(report["full_change_set"]["added"],
                             ["DOMAIN-SUFFIX,example-phase07.invalid"])
            self.assertEqual(report["full_change_set"]["removed"],[])
            self.assertEqual(len(report["change_set_sha256"]),64)
            self.assertEqual(report["high_risk_matcher_changes"],0)
            self.assertFalse(report["release_write_performed"])
            self.assertEqual((ROOT/source).read_bytes(),original)

    def test_license_catalog_87_historical_records_is_explicitly_blocked(self):
        result=license_audit.audit()
        self.assertEqual(result["status"],"BLOCKED_REVIEW")
        self.assertEqual(result["historical_records_checked"],87)
        self.assertEqual(result["line_level_license_attribution"],"NOT_VERIFIED")

    def test_runtime_gate_cannot_pass_without_real_bound_device_records(self):
        with self.assertRaisesRegex(ValueError,"cannot lack structured"):
            device_attestation.inspect({"device_import"},ROOT)

    def test_future_release_stages_independently_and_rebuilds_exact_bytes(self):
        with tempfile.TemporaryDirectory(prefix="loonkit-next-release-") as temp:
            stage=Path(temp)/"candidate"
            result=next_release.run("vNext-RC3",stage)
            self.assertEqual(result["rule_file_count"],26)
            self.assertFalse(result["formal_user_paths_modified"])
            manifest=json.loads((stage/"NEXT_RELEASE_MANIFEST.json").read_text())
            self.assertEqual(manifest["status"],"CANDIDATE_REVIEW_ONLY_NOT_PUBLISHED")
            self.assertEqual(manifest["runtime_device_test"],"NOT_EXECUTED")
            self.assertEqual(len(manifest["rules"]),26)
            self.assertEqual(manifest["remote_matchers"],197765)
            import hashlib
            self.assertEqual(
                hashlib.sha256((stage/"NEXT_RELEASE_DIFF.json").read_bytes()).hexdigest(),
                manifest["diff_sha256"])
            self.assertEqual(next_release.run("vNext-RC3",stage,check=True)["rule_file_count"],26)
            with self.assertRaisesRegex(ValueError,"initially empty"):
                next_release.run("vNext-RC3",stage,check=False)
            with self.assertRaisesRegex(ValueError,"staged candidate differs"):
                (stage/"rules/releases/vNext-RC3/AI.list").write_text("MALFORMED\\n")
                next_release.run("vNext-RC3",stage,check=True)
            for forbidden in ("vNext-RC2","../../main","main","v1"):
                with self.assertRaises(ValueError):
                    next_release.render(forbidden)

    def test_complete_source_diff_is_untruncated_and_flags_risky_matchers(self):
        source="rules/snapshots/phase03/generated/Google.list"
        original=(ROOT/source).read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            proposed=Path(temp)/"review.list"
            additions="".join("DOMAIN-SUFFIX,phase07-%d.invalid\n" % n
                              for n in range(45))
            proposed.write_bytes(original+b"\n"+additions.encode()+
                                 b"DOMAIN-KEYWORD,phase07risk\n")
            report=updates.review(source,proposed)
            self.assertEqual(report["added_rule_count"],46)
            self.assertEqual(len(report["full_change_set"]["added"]),46)
            self.assertEqual(len(report["added_sample"]),30)
            self.assertEqual(report["high_risk_matcher_changes"],1)
            self.assertEqual(report["risk_sample"],["DOMAIN-KEYWORD,phase07risk"])

    def test_invalid_new_source_rule_rejected_without_touching_snapshot(self):
        src="rules/snapshots/phase03/generated/Google.list"
        original=(ROOT/src).read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            proposed=Path(tmp)/"Google.proposed.list"
            proposed.write_bytes(original+b"\nIP-ASN,NONNUMERIC\n")
            with self.assertRaisesRegex(ValueError,"invalid newly proposed Loon matcher"):
                updates.review(src,proposed)
            self.assertEqual((ROOT/src).read_bytes(),original)

    def test_critical_gate_rows_always_block_without_real_evidence(self):
        doc=json.loads((ROOT/"release/phase-07/RELEASE_GATE.json").read_text())
        evidence=gate.check()
        for key in ("licenses","device_import","domestic_business","overseas_business",
                    "adblock","final","dns_egress","ipv4_ipv6","maintainer_approval"):
            self.assertTrue(doc["checks"][key]["blocks_release"])
            if doc["checks"][key]["status"]!="PASS":
                self.assertIn(key,evidence["open_blockers"])
            else:
                self.assertTrue(doc["checks"][key]["evidence"])
                self.assertEqual(len(doc["checks"][key]["commit"]),40)


if __name__ == "__main__":
    unittest.main()
