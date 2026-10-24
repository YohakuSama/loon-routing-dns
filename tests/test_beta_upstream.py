"""Independent fail-closed beta upstream staging tests, without live network."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import beta_upstream_candidate


class BetaUpdaterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.output = Path(self.temp.name) / "output"
        self.report = {
            "source_count": 2, "snapshot_count": 2,
            "incomplete_sources": 0, "incomplete_groups": [],
            "full_delta_sha256": "a" * 64,
            "sources": [
                {"id": "one", "url": "https://example.org/a", "sha256": "1" * 64,
                 "status": "PARSED_FOR_REVIEW", "bytes": 6},
                {"id": "two", "url": "https://example.org/b", "sha256": "2" * 64,
                 "status": "PARSED_FOR_REVIEW", "bytes": 6}],
            "groups": {
                "AdBlock": {"risk_categories": {}, "volume_change_percent": 15},
                "SteamCN": {"risk_categories": {}, "volume_change_percent": 5}},
        }
        self.snapshots = {"one": b"test-a", "two": b"test-b"}
        self.review = {
            "rules": {
                "AdBlock": {"DOMAIN,old.example", "DOMAIN,kept.example"},
                "SteamCN": {"DOMAIN,cn-download.example"}},
            "unapproved_proposals": {
                "AdBlock": {"DOMAIN,new.example", "DOMAIN,kept.example"},
                "SteamCN": {"DOMAIN,cn-download.example"}},
            "full_risk_audit": {
                "AdBlock": {"additions": [{"review_tier": "STANDARD"}]},
                "SteamCN": {"additions": []}},
            "source_ids_by_rule": {},
        }

    def stage(self):
        return beta_upstream_candidate.stage(self.report, self.snapshots, self.review,
                                             self.output, "v6.5.6-beta.1", self.root)

    def test_actual_proposal_is_not_pinned_preview(self):
        result = self.stage()
        p = self.output / result["groups"]["AdBlock"]["path"]
        text = p.read_text()
        self.assertIn("DOMAIN,new.example", text)
        self.assertNotIn("DOMAIN,old.example", text)
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),
                         result["groups"]["AdBlock"]["sha256"])
        self.assertFalse(result["publication_allowed"])
        self.assertFalse(result["branch_push_allowed"])
        self.assertEqual(result["groups"]["AdBlock"]["status"], "HIGH_RISK_HUMAN_REVIEW")
        self.assertTrue((self.output / "evidence/FULL_DIFF.json").exists())
        self.assertFalse((self.root / "rules").exists())

    def test_incomplete_source_restores_last_valid_rules(self):
        self.report["incomplete_sources"] = 1
        self.report["sources"][1]["status"] = "UNAVAILABLE_OR_INVALID"
        result = self.stage()
        p = self.output / result["groups"]["AdBlock"]["path"]
        self.assertIn("DOMAIN,old.example", p.read_text())
        self.assertNotIn("DOMAIN,new.example", p.read_text())
        self.assertEqual(result["groups"]["AdBlock"]["status"],
                         "RETAINED_LAST_GOOD_ON_INCOMPLETE_SOURCE")
        self.assertFalse(result["global_source_integrity_complete"])

    def test_missing_and_empty_proposals_are_rejected_or_quarantined(self):
        self.review["unapproved_proposals"]["AdBlock"] = set()
        result = self.stage()
        self.assertEqual(result["groups"]["AdBlock"]["status"],
                         "RETAINED_LAST_GOOD_ON_INCOMPLETE_SOURCE")
        self.assertEqual(result["groups"]["AdBlock"]["staged_count"], 2)

    def test_missing_group_or_repeat_output_fails(self):
        self.review["unapproved_proposals"].pop("SteamCN")
        with self.assertRaisesRegex(ValueError, "missing"):
            self.stage()
        self.review["unapproved_proposals"]["SteamCN"] = {"DOMAIN,cn-download.example"}
        self.stage()
        with self.assertRaisesRegex(ValueError, "empty"):
            self.stage()

    def test_invalid_version_or_repository_target_blocked(self):
        with self.assertRaisesRegex(ValueError, "version"):
            beta_upstream_candidate.stage(self.report, self.snapshots, self.review,
                self.output, "v6.5.6", self.root)
        with self.assertRaisesRegex(ValueError, "checkout"):
            beta_upstream_candidate.stage(self.report, self.snapshots, self.review,
                self.root / "inside", "v6.5.6-beta.1", self.root)


if __name__ == "__main__":
    unittest.main()
