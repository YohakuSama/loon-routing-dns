#!/usr/bin/env python3
"""Phase 05 immutable provenance, conservative overlap and device evidence tests."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import vnext_source_lock as sl
import vnext_conflict_resolver as cr
import validate_device_results as dr
import vnext_rule_engine as ve


class TestSourceIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock = json.loads((ROOT / "refactor/vnext/sources.lock.json").read_text())

    def test_all_frozen_inputs_sha256(self):
        result = sl.check_lock(ROOT, self.lock)
        self.assertEqual(result["verified_frozen_inputs"], 44)
        self.assertEqual(result["historical_catalog_ids"], 87)
        self.assertEqual(result["verified_raw_inactive_inputs"], 0)

    def test_lock_generation_is_deterministic(self):
        self.assertEqual(sl.build_lock(ROOT), self.lock)

    def test_tampered_sha256_rejected(self):
        tampered = copy.deepcopy(self.lock)
        tampered["inputs"][0]["sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "bytes modified"):
            sl.check_lock(ROOT, tampered)

    def test_missing_source_rejected(self):
        tampered = copy.deepcopy(self.lock)
        tampered["inputs"][0]["path"] = "rules/generated/not_real.list"
        with self.assertRaises(FileNotFoundError):
            sl.check_lock(ROOT, tampered)

    def test_missing_attestation_rejected(self):
        tampered = copy.deepcopy(self.lock)
        tampered["inputs"].pop()
        with self.assertRaisesRegex(ValueError, "does not cover exactly"):
            sl.check_lock(ROOT, tampered)

    def test_duplicate_id_rejected(self):
        tampered = copy.deepcopy(self.lock)
        tampered["inputs"][1]["source_id"] = tampered["inputs"][0]["source_id"]
        with self.assertRaisesRegex(ValueError, "repeated source id"):
            sl.check_lock(ROOT, tampered)

    def test_pinned_version_mismatch_rejected(self):
        tampered = copy.deepcopy(self.lock)
        tampered["snapshot_commit"] = "a"*40
        with self.assertRaisesRegex(ValueError, "version changed"):
            sl.check_lock(ROOT, tampered)

    def test_unlocked_raw_input_cannot_be_activated(self):
        tampered = copy.deepcopy(self.lock)
        raw = copy.deepcopy(tampered["inputs"][0])
        raw["source_id"] = "raw:bad"
        raw["input_kind"] = "PINNED_RAW_UPSTREAM"
        raw["path"] = "rules/ProxyProtect.list"
        raw["active_in_candidate"] = True
        tampered["inputs"].append(raw)
        with self.assertRaisesRegex(ValueError, "repeated source path"):
            sl.check_lock(ROOT, tampered)

    def test_historical_origin_is_not_fabricated(self):
        for item in self.lock["historical_sources"]:
            self.assertIn(item["status"], {
                "HISTORICAL_PROVENANCE_UNRECOVERABLE",
                "LOCAL_SOURCE_CAN_BE_VERIFIED_INDEPENDENTLY",
            })
        for item in self.lock["inputs"]:
            self.assertEqual(item["evidence_level"], "FROZEN_BYTES_VERIFIED_NOT_RAW_UPSTREAM")
            self.assertIsNone(item["original_url"])


class TestOverlapClassification(unittest.TestCase):
    def test_child_within_parent_suffix(self):
        self.assertTrue(cr.suffix_cover("cn", "api.example.cn"))
        self.assertFalse(cr.suffix_cover("cn", "fakecn"))
        self.assertFalse(cr.suffix_cover("apple.com", "notapple.com"))

    def test_direct_same_effect_not_marked_misroute(self):
        row = {"parent_group": "ChinaDirect", "parent_rule": "DOMAIN-SUFFIX,cn",
               "child_group": "DomesticCore", "child_rule": "DOMAIN,foo.cn"}
        locations = {("ChinaDirect", "DOMAIN-SUFFIX,cn"): ("snap", 1),
                     ("DomesticCore", "DOMAIN,foo.cn"): ("snap", 2)}
        result = cr.classify(row, locations)
        self.assertEqual(result["classification"], "SAME_EFFECT_REDUNDANCY")
        self.assertEqual(result["status"], "VERIFIED_ACCEPTABLE")
        self.assertFalse(result["requires_device_validation"])
        self.assertEqual(result["static_matching_example"], "foo.cn")

    def test_adblock_direct_overlap_must_not_be_auto_accepted(self):
        row = {"parent_group": "ChinaDirect", "parent_rule": "DOMAIN-SUFFIX,cn",
               "child_group": "AdBlock", "child_rule": "DOMAIN-SUFFIX,ads.example.cn"}
        locations = {(row["parent_group"], row["parent_rule"]): ("parent.list", 11),
                     (row["child_group"], row["child_rule"]): ("child.list", 5)}
        result = cr.classify(row, locations)
        self.assertEqual(result["classification"], "ADBLOCK_OVERLAP")
        self.assertEqual(result["status"], "REQUIRES_RUNTIME_TEST")
        self.assertEqual(result["risk"], "HIGH")

    def test_invalid_ancestry_is_rejected(self):
        with self.assertRaises(ValueError):
            cr.rule_values("DOMAIN-SUFFIX,apple.com", "DOMAIN-SUFFIX,notapple.com")


class TestCandidateQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated = {p.stem: set(p.read_text().splitlines())
                         for p in (ROOT / "refactor/vnext/generated").glob("*.list")}
        cls.profile = (ROOT / "refactor/vnext/LoonKit.vNext.Candidate.lcf").read_text()

    def test_adblock_selectable_and_known_anchor_roots(self):
        self.assertIn("AdBlock = select,REJECT,DIRECT", self.profile)
        for domain in ve.AD_ANCHORS:
            self.assertIn("DOMAIN-SUFFIX," + domain, self.generated["AdBlock"])

    def test_adblock_does_not_own_shared_payment_or_auth_roots(self):
        for root in ("stripe.com", "paypal.com", "auth0.com",
                     "microsoftonline.com", "accounts.google.com"):
            self.assertNotIn("DOMAIN-SUFFIX," + root, self.generated["AdBlock"])

    def test_china_direct_no_unbounded_keywords(self):
        self.assertFalse(any(x.startswith("DOMAIN-KEYWORD,")
                             for x in self.generated["ChinaDirect"]))
        self.assertIn("DOMAIN-SUFFIX,cn", self.generated["ChinaDirect"])

    def test_seven_retired_groups_remain_distinct_compatibility_issue(self):
        manifest = sl.read_json(ROOT/"refactor/vnext/engine_manifest.json")
        self.assertEqual(set(manifest["inactive_groups"]),
                         {"Spotify", "Twitch", "Abema", "BBC", "Line", "Reddit", "Linkedin"})
        for group in manifest["inactive_groups"]:
            self.assertIn(group + " = select,", self.profile)
            self.assertNotIn("tag=vNext-"+group, self.profile)

    def test_ipv4_ipv6_asn_normalization_idempotent(self):
        rules = ["IP-CIDR,192.0.2.7/24", "IP-CIDR6,2001:db8::1/48",
                 "IP-ASN,AS132203"]
        for r in rules:
            self.assertEqual(ve.normalize(ve.normalize(r)), ve.normalize(r))
            self.assertEqual(ve.normalize(r).count("no-resolve"), 1)

    def test_known_negative_brand_strings_not_global_keywords(self):
        self.assertNotIn("DOMAIN-KEYWORD,taobao", self.generated["ChinaDirect"])
        self.assertNotIn("DOMAIN-KEYWORD,alipay", self.generated["ChinaDirect"])


class TestDeviceValidator(unittest.TestCase):
    def base(self):
        return {"schema_version": 1, "results": [{
            "test_id": "case.ad-001", "configuration": "VNEXT", "config_commit_sha": "UNKNOWN",
            "rule_file_version": "UNKNOWN", "device_alias": "device-A",
            "client_version": "UNKNOWN", "network_alias": "net-A",
            "network_type": "WIFI", "node_alias": "node-A", "node_protocol": "UNKNOWN",
            "dns_config_sha256": "UNKNOWN", "tun_config_sha256": "UNKNOWN",
            "tested_at": "UNKNOWN", "matched_rule": "UNKNOWN",
            "selected_policy": "UNKNOWN", "observed_egress": "UNKNOWN",
            "observed_resolvers": [], "ipv4_result": "UNKNOWN", "ipv6_result": "UNKNOWN",
            "expected_match": "UNKNOWN", "evidence": "UNKNOWN",
            "conclusion": "NOT_EXECUTED",
        }]}

    def test_unknown_is_accepted_but_not_pass(self):
        r = dr.validate(self.base())
        self.assertEqual(r["outcomes"], {"NOT_EXECUTED": 1})

    def test_pass_requires_evidence(self):
        d = self.base()
        d["results"][0]["conclusion"] = "PASS"
        with self.assertRaisesRegex(ValueError, "PASS needs"):
            dr.validate(d)

    def test_public_and_private_ip_must_be_redacted(self):
        for raw in ("8.8.8.8", "192.168.1.1", "2001:db8::1"):
            d = self.base()
            d["results"][0]["evidence"] = raw
            with self.subTest(raw), self.assertRaisesRegex(ValueError, "raw IPv"):
                dr.validate(d)

    def test_private_subscription_keys_are_prohibited(self):
        d = self.base()
        d["results"][0]["subscription_url"] = "PRIVATE"
        with self.assertRaisesRegex(ValueError, "privacy-sensitive"):
            dr.validate(d)

    def test_three_way_comparison_requires_same_conditions(self):
        d = self.base()
        one = d["results"][0]
        two = copy.deepcopy(one)
        two["configuration"] = "PRODUCTION"
        two["network_alias"] = "net-B"
        d["results"].append(two)
        with self.assertRaisesRegex(ValueError, "uncontrolled A/B comparison"):
            dr.validate(d)

    def test_duplicate_device_record_fails(self):
        d = self.base()
        d["results"].append(copy.deepcopy(d["results"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            dr.validate(d)


if __name__ == "__main__":
    unittest.main()
