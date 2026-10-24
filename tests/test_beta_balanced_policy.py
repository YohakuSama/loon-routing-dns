"""Balanced filtering positive/negative behavior and deterministic channel generation."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import beta_assets
import beta_channel
import beta_policy_review
import beta_profile
import beta_effective_audit as audit
import beta_upstream_candidate as candidate


class BalancedPolicyTests(unittest.TestCase):
    def test_frozen_beta4_filter_rebuilds_from_original_reviewed_inputs(self):
        spec=json.loads((ROOT/'rules/beta/balanced_decisions.json').read_text())
        owners=json.loads((ROOT/'rules/beta/policy_overrides.json').read_text())
        original=set(beta_policy_review.rules((ROOT/spec['baseline_path']).read_bytes()))
        path,data=beta_policy_review.render()
        expected=original-{r['rule'] for r in spec['excluded_rules']}
        expected.update(owners['adblock_local_rules'])
        expected.update(r['rule'] for r in spec['privacy_additions'])
        self.assertEqual(set(beta_policy_review.rules(data)),expected)
        self.assertEqual(path.read_bytes(),data)
        for host in spec['critical_function_hosts']:
            self.assertFalse(any(beta_policy_review.matches(rule,host) for rule in expected),host)

    def test_rendered_profile_is_reproducible_and_no_service_root_duplicates_remain_local(self):
        meta=json.loads((ROOT/'build/beta_manifest.json').read_text())
        profile,generated=beta_profile.render(meta['immutable_overlay_commit'])
        self.assertEqual(profile,(ROOT/'beta/LoonKit.lcf').read_bytes())
        self.assertEqual(generated,meta)
        _,local,remote=audit.build()
        self.assertEqual(len(local),4)
        for host,(_,off) in audit.EXPECTED.items():
            self.assertEqual(audit.trace(host,local,remote,True)['policy'],off)

    def test_corrupted_active_balanced_asset_fails_closed(self):
        manifest=json.loads((ROOT/'build/beta_manifest.json').read_text())
        selected=ROOT/beta_channel.URI.fullmatch(manifest['adblock']['uri'])['path']
        original=Path.read_bytes
        def read(path):
            data=original(path)
            return data+b'DOMAIN,critical.example\n' if path==selected else data
        with patch.object(Path,'read_bytes',read):
            with self.assertRaises(ValueError):
                beta_channel.validate()

    def test_beta_update_baseline_uses_all_33_runtime_groups_and_preserves_scoping(self):
        observed={}
        def report(**kwargs):
            observed.update(kwargs['baseline_rules'])
            raise RuntimeError('stop before network in this regression')
        with patch.object(candidate.upstream_review,'build_report',side_effect=report):
            with self.assertRaisesRegex(RuntimeError,'stop before network'):
                candidate.run('v6.5.5-beta.5',Path('/unused-synthetic-output'))
        self.assertEqual(len(observed),33)
        self.assertIn('DOMAIN-SUFFIX,spotify.com',observed['Spotify'])
        self.assertNotIn('DOMAIN-SUFFIX,cn',observed['ChinaDirect'])
        self.assertNotIn('DOMAIN-SUFFIX,wechat.com',observed['ChinaDirect'])
        self.assertNotIn('DOMAIN-SUFFIX,crl.microsoft.com',observed['AdBlock'])
        self.assertNotIn('DOMAIN-SUFFIX,apis.google.com',observed['AI'])


if __name__=='__main__':
    unittest.main()
