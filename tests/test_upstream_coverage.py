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

    def test_known_regex_exclusions_count_as_reviewed_not_translated(self):
        import hashlib
        catalog, report = sample()
        expression = "URL-REGEX,^https?://ads.example.org/.*$"
        evidence = {"line": 42, "expression": expression,
                    "sha256": hashlib.sha256(expression.encode()).hexdigest(),
                    "kind": "URL-REGEX",
                    "reason": "MITM_URL_REGEX_NOT_DOMAIN_RULE"}
        report["sources"][0]["status"] = "PARSED_WITH_DOCUMENTED_EXCLUSIONS"
        report["sources"][0]["excluded_count"] = 1
        report["sources"][0]["excluded_expressions"] = [evidence]
        report["excluded_expressions"] = 1
        report["sources_with_exclusions"] = 1
        result = assess(report, catalog)
        self.assertTrue(result["coverage_complete"])
        self.assertFalse(result["translation_complete"])
        self.assertEqual(result["excluded_expressions"], 1)

        bad = copy.deepcopy(report)
        bad["sources"][0]["excluded_expressions"][0]["sha256"] = "0"*64
        self.assertFalse(assess(bad, catalog)["coverage_complete"])
        bad = copy.deepcopy(report)
        bad["sources"][0]["excluded_expressions"][0]["reason"] = (
            "HOST_REGEX_CANNOT_SAFELY_WIDEN_TO_SUFFIX")
        self.assertFalse(assess(bad, catalog)["coverage_complete"])
        bad = copy.deepcopy(report)
        bad["sources"][0]["excluded_expressions"].clear()
        self.assertFalse(assess(bad, catalog)["coverage_complete"])

    def test_never_confuse_source_review_with_release_permission(self):
        catalog, report = sample()
        report["publication_allowed"] = True
        self.assertFalse(assess(report, catalog)["coverage_complete"])


if __name__ == "__main__":
    unittest.main()
