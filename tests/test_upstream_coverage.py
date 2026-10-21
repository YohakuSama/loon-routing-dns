"""Contract tests for truthful weekly-source review status."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_upstream_coverage import assess


def sample():
    source_ids = ["remote-a", "remote-b", "local-c"]
    return (
        {"sources": [{"id": x} for x in source_ids]},
        {"sources": [
            {"id": x, "status": "PARSED_FOR_REVIEW", "invalid_count": 0,
             "minimum_satisfied": True, "sha256": "a" * 64} for x in source_ids
        ], "source_count": 3, "snapshot_count": 3, "incomplete_sources": 0,
         "incomplete_groups": [], "publication_allowed": False},
    )


class UpstreamCoverageTests(unittest.TestCase):
    def test_all_sources_only_counts_when_every_source_parses(self):
        catalog, report = sample()
        self.assertTrue(assess(report, catalog)["coverage_complete"])

    def test_unavailable_source_cannot_greenlight_review(self):
        catalog, report = sample()
        report["sources"][1]["status"] = "UNAVAILABLE_OR_INVALID"
        self.assertFalse(assess(report, catalog)["coverage_complete"])

    def test_unparsed_lines_cannot_be_ignored(self):
        catalog, report = sample()
        report["sources"][1]["invalid_count"] = 2
        self.assertFalse(assess(report, catalog)["coverage_complete"])

    def test_missing_source_or_snapshot_is_failure(self):
        catalog, report = sample()
        report["sources"].pop()
        report["snapshot_count"] = 2
        result = assess(report, catalog)
        self.assertFalse(result["coverage_complete"])
        self.assertTrue(any("Missing source IDs" in msg for msg in result["problems"]))

    def test_incomplete_group_or_wrong_catalog_id_is_failure(self):
        catalog, report = sample()
        report["incomplete_groups"] = ["AdBlock"]
        report["sources"][0]["id"] = "unknown"
        self.assertFalse(assess(report, catalog)["coverage_complete"])

    def test_never_confuse_source_review_with_release_permission(self):
        catalog, report = sample()
        report["publication_allowed"] = True
        self.assertFalse(assess(report, catalog)["coverage_complete"])


if __name__ == "__main__":
    unittest.main()
