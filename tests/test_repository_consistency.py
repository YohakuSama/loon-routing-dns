"""Repository-level, non-network contract checks for metadata and docs.

The production rule compiler is tested separately. These tests catch stale
maintenance references and unsafe release workflow inputs that rule CI misses.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
RAW = re.compile(r"https://raw[.]githubusercontent[.]com/YohakuSama/loonkit/[a-f0-9]{40}/([^,\s\"')]+)")
MARKDOWN_LINK = re.compile(r"\]\((\.{1,2}/[^)#?]+)(?:#[^)]*)?\)")


class RepositoryConsistency(unittest.TestCase):
    def test_maintained_docs_use_current_asset_paths(self):
        profile = (ROOT / "LoonKit.lcf").read_text(encoding="utf-8")
        plugin = (ROOT / "release/Network_Diagnostics.plugin").read_text(encoding="utf-8")
        dep = (ROOT / "docs/DEPENDENCIES.md").read_text(encoding="utf-8")
        for text in (profile, plugin):
            for path in RAW.findall(text):
                self.assertTrue((ROOT / path).is_file(), "missing active resource " + path)
                documented = (path if path.startswith("scripts/") or path.startswith("release/")
                              else "icons/v20261021r1/" if path.startswith("icons/")
                              else "rules/releases/vNext-RC2/" if path.startswith("rules/")
                              else path)
                self.assertIn(documented, dep, "undocumented current dependency " + path)
        self.assertIn("scripts/v20261021r3/network-diagnostics.js", dep)
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

    def test_current_assistant_is_single_and_legacy_assets_are_not_active(self):
        from json import loads
        spec=loads((ROOT/"build/release_spec.json").read_text(encoding="utf-8"))
        plugin=(ROOT/"release/Network_Diagnostics.plugin").read_text(encoding="utf-8")
        profile=(ROOT/"LoonKit.lcf").read_text(encoding="utf-8")
        deps=(ROOT/"docs/DEPENDENCIES.md").read_text(encoding="utf-8")
        self.assertEqual(spec["stable_release_version"],"v6.3.7")
        self.assertEqual(profile.count(".plugin, enabled=true"),1)
        self.assertIn(spec["plugin_assets_commit"]+"/release/Network_Diagnostics.plugin",profile)
        for path,key in (
            ("scripts/v20261021r3/node-intelligence.js","node_script_commit"),
            ("scripts/v20261021r3/network-diagnostics.js","diagnostics_script_commit"),
            ("scripts/v20261021r13/media-unlock.js","unified_service_diagnostics_script_commit"),
        ):
            self.assertTrue((ROOT/path).is_file())
            self.assertIn(spec[key]+"/"+path,plugin)
            self.assertIn(path,deps)
        for retired in (
            "release/Service_Diagnostics.plugin",
            "scripts/v20261021r1/node-intelligence.js",
            "scripts/v20261021r2/network-diagnostics.js",
            "scripts/v20261021r3/service-diagnostics.js",
            "scripts/v20261021r4/service-diagnostics.js",
            "scripts/v20261021r5/service-diagnostics.js",
            "scripts/v20261021r6/service-diagnostics.js",
        ):
            self.assertFalse((ROOT/retired).exists(),retired)
        self.assertNotIn("service = select,",plugin)
        self.assertIn('tag="解锁检测"',plugin)
        self.assertEqual(plugin.count("generic then script("),3)
        self.assertIn('auto_check = switch,false',plugin)

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
