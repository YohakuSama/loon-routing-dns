"""Validate the current portable checksum and immutable historical checksum files."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
HISTORICAL={
    "v6.0.0":None,
    "v6.1.0":"19de1c36ee747ea76512af3bf5b2d62475e77175db09a2568ce8de43a82e480b",
    "v6.2.0":"60af6e40a1fd3794f803724eecd5ed02051af4c58a170113b46f53b6c9dbb534",
}
class ReleaseChecksumTests(unittest.TestCase):
    def test_current_checksum_matches_profile_and_manifest(self):
        spec=json.loads((ROOT/"build/release_spec.json").read_text(encoding="utf-8"))
        manifest=json.loads((ROOT/"build/release_manifest.json").read_text(encoding="utf-8"))
        version=spec["stable_release_version"]
        self.assertEqual(version,"v6.3.3")
        self.assertEqual(version,manifest["label"])
        actual=hashlib.sha256((ROOT/"LoonKit.lcf").read_bytes()).hexdigest()
        self.assertEqual(actual,manifest["profile_sha256"]["LoonKit.lcf"])
        self.assertEqual((ROOT/"release"/("SHA256SUMS."+version)).read_text(encoding="utf-8"),
                         actual+"  LoonKit.lcf\n")
        self.assertIn(actual,(ROOT/"docs"/("RELEASE_CHECKSUM_"+version+".md")).read_text(encoding="utf-8"))

    def test_historical_checksums_are_retained(self):
        for version,expected in HISTORICAL.items():
            with self.subTest(version=version):
                data=(ROOT/"release"/("SHA256SUMS."+version)).read_text(encoding="utf-8")
                self.assertRegex(data,r"^[0-9a-f]{64}  LoonKit\.lcf\n$")
                if expected:self.assertEqual(data,expected+"  LoonKit.lcf\n")

    def test_publisher_writes_portable_checksum(self):
        for version in ("v6.0.0","v6.1.0","v6.2.0","v6.3.0"):
            p={ "v6.0.0":"publish-v6.yml","v6.1.0":"publish-v61.yml",
                "v6.2.0":"publish-v62.yml","v6.3.0":"publish-v63.yml"}[version]
            code=(ROOT/".github/workflows"/p).read_text(encoding="utf-8")
            self.assertIn("(cd release-output && sha256sum LoonKit.lcf > SHA256SUMS)",code)

if __name__=="__main__":
    unittest.main()
