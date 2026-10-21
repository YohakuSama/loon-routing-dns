"""Check the checksum that users download alongside the v6 configuration."""
import hashlib
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ReleaseChecksumTests(unittest.TestCase):
    def test_portable_hash_matches_profile(self):
        expected=hashlib.sha256((ROOT/"LoonKit.lcf").read_bytes()).hexdigest()
        actual=(ROOT/"release/SHA256SUMS.v6.0.0").read_text(encoding="utf-8")
        self.assertEqual(actual,expected+"  LoonKit.lcf\n")

    def test_future_publish_writes_simple_basename(self):
        code=(ROOT/".github/workflows/publish-v6.yml").read_text()
        self.assertIn("(cd release-output && sha256sum LoonKit.lcf > SHA256SUMS)", code)

if __name__=="__main__":
    unittest.main()
