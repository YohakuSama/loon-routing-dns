"""Keep current public assets while rejecting obsolete generated previews."""
from __future__ import annotations
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryHygiene(unittest.TestCase):
    def test_stale_unversioned_icon_tools_removed(self):
        for item in (
            ".github/workflows/console-icon.yml",
            "scripts/generate-console-icon.mjs",
            "scripts/generate-policy-icons.mjs",
        ):
            with self.subTest(item=item):
                self.assertFalse((ROOT / item).exists())

    def test_local_caches_ignored_not_release_assets(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        for entry in ("__pycache__/", "*.pyc", ".pytest_cache/", "node_modules/",
                      ".DS_Store", "icons/*.png", "*.log"):
            with self.subTest(entry=entry):
                self.assertIn(entry, ignore)
        self.assertNotIn("icons/v20261018r2/", ignore)
        self.assertNotIn("rules/generated/", ignore)

    def test_public_icons_and_rollback_remain(self):
        active = (ROOT / "Loon_Routing_DNS.lcf").read_text(encoding="utf-8")
        urls = re.findall(r"img-url\s*=\s*(https://\S+?\.png)", active)
        self.assertEqual(len(urls), 33)
        for url in urls:
            rel = url.split("/main/", 1)[1]
            with self.subTest(path=rel):
                self.assertTrue((ROOT / rel).is_file())
        self.assertTrue((ROOT / "icons/v20261018r2/Console.png").is_file())
        self.assertTrue((ROOT / "reviews/Loon_Routing_DNS_Hybrid_Review.lcf").is_file())

    def test_current_plugin_sources_are_available(self):
        data = (ROOT / "plugins/Network_Diagnostics.plugin").read_text(encoding="utf-8")
        self.assertEqual(data, (ROOT / "plugins/v20261018r10/Network_Diagnostics.plugin").read_text(encoding="utf-8"))
        for source in ("scripts/v20261018r10/node-intelligence.js",
                       "scripts/v20261018r4/network-diagnostics.js"):
            with self.subTest(source=source):
                self.assertIn("/main/" + source, data)
                self.assertTrue((ROOT / source).is_file())

    def test_legacy_plugins_and_release_archives_are_gone(self):
        for source in (
            "plugins/v20261018r2/Network_Diagnostics.plugin",
            "plugins/v20261018r4/Network_Diagnostics.plugin",
            "plugins/v20261018r5/Network_Diagnostics.plugin",
            "plugins/v20261018r9/Network_Diagnostics.plugin",
            "scripts/console.js",
            "scripts/network-diagnostics.js",
            "scripts/node-intelligence.js",
            "scripts/v20261018r4/node-intelligence.js",
            "scripts/v20261018r5/node-intelligence.js",
            "releases/v4.4.8/Loon_Routing_DNS.lcf",
            "releases/v5.1.0/CHANGELOG.md",
        ):
            with self.subTest(source=source):
                self.assertFalse((ROOT / source).exists())

    def test_no_obsolete_generator_references_in_icon_guide(self):
        guide = (ROOT / "icons/README.md").read_text(encoding="utf-8")
        self.assertNotIn("scripts/generate-console-icon.mjs", guide)
        self.assertNotIn("scripts/generate-policy-icons.mjs", guide)
        self.assertIn("scripts/build-appstore-icons.py --check-config", guide)


if __name__ == "__main__":
    unittest.main()
