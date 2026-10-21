"""Protect all existing images and verify release automation's critical guards."""
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class OriginalIconIntegrityTests(unittest.TestCase):
    def test_all_original_png_and_svg_bytes_are_unchanged(self):
        report = json.loads((ROOT / "build/icon_integrity.json").read_text(encoding="utf-8"))
        assets = {row["path"]: row["git_blob_sha1"] for row in report["assets"]}
        actual = {
            p.relative_to(ROOT).as_posix()
            for folder, ext in (("icons/v20261021r1", ".png"), ("icons/source", ".svg"))
            for p in (ROOT / folder).glob("*" + ext)
        }
        self.assertEqual(set(assets), actual)
        self.assertEqual(len([x for x in assets if x.endswith(".png")]), 34)
        self.assertEqual(len([x for x in assets if x.endswith(".svg")]), 16)
        for path, expected in assets.items():
            with self.subTest(icon=path):
                data = (ROOT / path).read_bytes()
                blob = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
                self.assertEqual(hashlib.sha1(blob).hexdigest(), expected)

    def test_profile_and_plugin_preserve_existing_icon_addresses(self):
        profile = (ROOT / "LoonKit.lcf").read_text(encoding="utf-8")
        plugin = (ROOT / "release/Network_Diagnostics.plugin").read_text(encoding="utf-8")
        pinned = ("97c48a5d14087597dbba35119d5ee8d43b1ce537/"
                  "icons/v20261021r1/")
        self.assertEqual(profile.count(pinned), 33)
        self.assertEqual(plugin.count(pinned + "Console.png"), 1)
        self.assertNotIn("/icons/v20261021r2/", profile + plugin)
        self.assertFalse((ROOT / "icons/v20261021r2").exists())

class ReleaseWorkflowTests(unittest.TestCase):
    def test_publication_requires_successful_main_push_ci(self):
        code=(ROOT/".github/workflows/publish-v6.yml").read_text(encoding="utf-8")
        for guard in ("workflow_run:", "conclusion == 'success'",
                      "workflow_run.event == 'push'", "head_branch == 'main'",
                      "head_repository.full_name == github.repository",
                      "git rev-parse HEAD", '"$CHECKED_SHA"',
                      "gh release create v6.0.0",
                      "gh release view v6.0.0",
                      "contents: write", "scripts/verify_release.py --check"):
            with self.subTest(guard=guard):
                self.assertIn(guard,code)
        self.assertNotIn("pull_request_target:",code)
        self.assertNotIn("persist-credentials: true",code)

if __name__ == "__main__":
    unittest.main()
