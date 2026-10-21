"""Neutral visual asset reproducibility and production reference checks."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
import build_neutral_icons as icons

class IconAssetTests(unittest.TestCase):
    def test_all_icon_assets_reproducible_from_original_source(self):
        published = ROOT/"icons/v20261021r2"
        actual = {p.name for p in published.glob("*.png")}
        expected = {n+".png" for n in icons.ASSETS}
        self.assertEqual(actual, expected)
        self.assertEqual(len(expected),34)
        with tempfile.TemporaryDirectory() as td:
            output = Path(td)
            icons.render(output)
            for name in expected:
                with self.subTest(name=name):
                    a=(output/name).read_bytes()
                    b=(published/name).read_bytes()
                    self.assertTrue(a.startswith(b"\\x89PNG\\r\\n\\x1a\\n".decode("unicode_escape").encode("latin1")))
                    self.assertEqual(a,b, "published icon diverged from reproducible original icon")

    def test_active_profile_uses_only_new_versioned_tiles(self):
        profile=(ROOT/"LoonKit.lcf").read_text(encoding="utf-8")
        plugin=(ROOT/"release/Network_Diagnostics.plugin").read_text(encoding="utf-8")
        self.assertEqual(profile.count("/icons/v20261021r2/"),33)
        self.assertEqual(plugin.count("/icons/v20261021r2/"),1)
        self.assertNotIn("/icons/v20261021r1/", profile+plugin)
        self.assertFalse((ROOT/"icons/v20261021r1").exists())
        self.assertFalse((ROOT/"icons/source").exists())

if __name__=="__main__":
    unittest.main()
