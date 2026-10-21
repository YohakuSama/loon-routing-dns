"""Repository-level, non-network contract checks for metadata and docs.

The production rule compiler is tested separately. These tests catch stale
maintenance references and unsafe release workflow inputs that rule CI misses.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
RAW = re.compile(r"https://raw[.]githubusercontent[.]com/YohakuSama/loonkit/[a-f0-9]{40}/([^,\\s\"')]+)")
MARKDOWN_LINK = re.compile(r"\]\((\.{1,2}/[^)#?]+)(?:#[^)]*)?\)")


class RepositoryConsistency(unittest.TestCase):
    def test_maintained_docs_use_current_asset_paths(self):
        profile = (ROOT / "LoonKit.lcf").read_text(encoding="utf-8")
        plugin = (ROOT / "release/Network_Diagnostics.plugin").read_text(encoding="utf-8")
        dep = (ROOT / "docs/DEPENDENCIES.md").read_text(encoding="utf-8")
        for text in (profile, plugin):
            for path in RAW.findall(text):
                self.assertTrue((ROOT / path).is_file(), "missing active resource " + path)
                self.assertIn(path, dep, "undocumented current dependency " + path)
        self.assertIn("scripts/v20261021r2/network-diagnostics.js", dep)
        self.assertIn("release/Network_Diagnostics.plugin", dep)
        self.assertIn("icons/v20261021r1/", dep)
        for stale in ("release/phase-07/", "release/phase-08/",
                      "icons/v20261018r2/", "icons/v20261018r3/",
                      "scripts/v20261020r1/", "scripts/v20261020r2/"):
            self.assertNotIn(stale, dep)

    def test_markdown_relative_links_refer_to_existing_files_or_directories(self):
        files = [ROOT/"README.md", ROOT/"rules/README.md",
                 ROOT/"icons/README.md", *sorted((ROOT/"docs").glob("*.md"))]
        checked = 0
        for doc in files:
            text = doc.read_text(encoding="utf-8")
            for rel in MARKDOWN_LINK.findall(text):
                with self.subTest(document=str(doc.relative_to(ROOT)), target=rel):
                    dest = (doc.parent / rel).resolve()
                    self.assertTrue(dest.is_relative_to(ROOT))
                    self.assertTrue(dest.exists(), "broken local link " + rel)
                    checked += 1
        self.assertGreaterEqual(checked, 50)

    def test_user_version_is_shell_quoted_environment_input(self):
        release = (ROOT / ".github/workflows/release.yml").read_text()
        self.assertIn("RELEASE_VERSION: ${{ inputs.version }}", release)
        self.assertIn('python3 scripts/prepare_release.py --version "$RELEASE_VERSION"', release)
        for line in release.splitlines():
            if line.lstrip().startswith("run:"):
                self.assertNotIn("${{ inputs.version }}", line)
        self.assertIn("contents: read", release)

    def test_live_upstream_audit_watches_actual_parser_and_tests(self):
        live = (ROOT / ".github/workflows/upstream-live-audit.yml").read_text()
        for path in (
            "scripts/upstream_review.py",
            "scripts/verify_upstream_coverage.py",
            "tests/test_upstream_review.py",
            "tests/test_upstream_coverage.py",
            "tests/test_rule_stress.py",
            "rules/sources.json",
        ):
            self.assertIn(path, live)
            self.assertTrue((ROOT / path).is_file())
        self.assertNotIn("tests/test_upstream_live.py", live)
        self.assertIn("workflow_dispatch:", live)


if __name__ == "__main__":
    unittest.main()
