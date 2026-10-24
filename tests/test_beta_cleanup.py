"""Cleanup is blocked before promotion and validates all archives before deleting."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import beta_cleanup


class BetaCleanupTests(unittest.TestCase):
    def test_current_real_checkout_is_blocked_without_network_or_deletion(self):
        plan=beta_cleanup.inventory()
        self.assertEqual(plan['status'],'BLOCKED_UNTIL_EXACT_STABLE_PROMOTION')
        with patch.object(beta_cleanup.urllib.request,'urlopen') as network:
            with self.assertRaisesRegex(ValueError,'stable promotion'):
                beta_cleanup.apply()
            network.assert_not_called()

    def fixture(self,root):
        (root/'build').mkdir()
        (root/'LoonKit.lcf').write_bytes(b'synthetic promoted profile')
        raw=b'# synthetic old overlay\nDOMAIN,old.example.test\n'
        path=root/'rules/beta/v0.0.0-beta.1/Old.list';path.parent.mkdir(parents=True);path.write_bytes(raw)
        active='https://raw.githubusercontent.com/YohakuSama/loonkit/'+'a'*40+'/rules/beta/v1.0.0-beta.1/Active.list'
        meta={'version':'v1.0.0-beta.1','configuration_sha256':'b'*64,'overlay_rules':{},
              'china_direct':{'uri':active},'adblock':{'uri':active.replace('Active.list','Filter.list')}}
        archive={'uri':'https://raw.githubusercontent.com/YohakuSama/loonkit/'+'c'*40+'/rules/beta/v0.0.0-beta.1/Old.list','sha256':hashlib.sha256(raw).hexdigest()}
        (root/'build/beta_manifest.json').write_text(json.dumps(meta))
        (root/'build/beta_history.json').write_text(json.dumps({'revisions':[{'resources':[archive]}]}))
        (root/'build/release_manifest.json').write_text(json.dumps({'label':'v1.0.0','promoted_beta_config_sha256':'b'*64,
            'profile_sha256':{'LoonKit.lcf':hashlib.sha256((root/'LoonKit.lcf').read_bytes()).hexdigest()},
            'publication':{'status':'VERIFIED_ON_MAIN','published_main_commit_sha':'d'*40}}))
        return path,raw,archive

    def test_failed_archive_verification_retains_all_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path,raw,archive=self.fixture(root)
            class Response:
                def __enter__(self): return self
                def __exit__(self,*args): pass
                def geturl(self): return archive['uri']
                def read(self,n): return b'corrupted archive'
            with patch.object(beta_cleanup.urllib.request,'urlopen',return_value=Response()):
                with self.assertRaisesRegex(ValueError,'unavailable or changed'):
                    beta_cleanup.apply(root)
            self.assertEqual(path.read_bytes(),raw)

    def test_exact_promoted_fixture_removes_only_verified_historical_working_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path,raw,archive=self.fixture(root)
            class Response:
                def __enter__(self): return self
                def __exit__(self,*args): pass
                def geturl(self): return archive['uri']
                def read(self,n): return raw
            with patch.object(beta_cleanup.urllib.request,'urlopen',return_value=Response()):
                result=beta_cleanup.apply(root)
            self.assertFalse(path.exists())
            self.assertFalse(result['git_history_rewritten'])
            self.assertTrue((root/'LoonKit.lcf').is_file())


if __name__=='__main__': unittest.main()
