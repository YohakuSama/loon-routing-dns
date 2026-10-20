#!/usr/bin/env python3
"""Phase 03 read-only architecture gates. No upstream downloads or rule emission."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "refactor" / "vnext"

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def sha256(path):
    # This phase tests hashes of historical version-frozen publication inputs,
    # not those of RC2 production entry points.
    archived = {"LoonKit.lcf": "refactor/vnext/templates/LoonKit.legacy-seed.lcf",
                "LoonKit.PrivacyDNS.lcf": "refactor/vnext/templates/LoonKit.PrivacyDNS.legacy-seed.lcf"}
    return hashlib.sha256((ROOT / archived.get(path, path)).read_bytes()).hexdigest()

def decisions_valid(entries):
    ids = [x.get("source_id") for x in entries]
    if len(ids) != len(set(ids)):
        return False
    for s in entries:
        required = ("source_id", "current_group", "current_policy", "legacy_remote_presence",
                    "original_business_purpose", "published_rule_contribution",
                    "irreplaceable_rule_contribution", "cross_source_overlap",
                    "potential_misroute_risk", "special_region_exit_necessary",
                    "can_fall_through_final", "suitable_for_consolidation",
                    "removal_business_loss", "evidence_sources", "recommendation",
                    "confidence", "associated_risk_ids", "reason", "phase04_condition")
        if any(k not in s or s[k] is None for k in required):
            return False
        if s.get("is_removal_approved"):
            return False
        if s["recommendation"] == "REMOVE_CANDIDATE":
            # Even a proposal requires evidence, fallback and regression proofs.
            if not all(s.get(k) for k in ("removal_evidence", "replacement_policy",
                                          "regression_test_ids", "device_validation_plan")):
                return False
    return True

class Phase03ArchitectureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load("rules/sources.json")
        cls.inventory = load("audits/phase-02/data/source_inventory.json")
        cls.source = load("refactor/vnext/source_decisions.json")
        cls.candidate = load("refactor/vnext/sources.candidate.json")
        cls.profile = load("refactor/vnext/active_profile.candidate.json")
        cls.current_profile = load("rules/active_profile.json")
        cls.policy = load("refactor/vnext/policy_decisions.json")
        cls.unresolved = load("refactor/vnext/unresolved_decisions.json")
        cls.risks = load("audits/phase-02/data/risk_register.json")
        cls.dns = load("audits/phase-02/data/dns_risk_candidates.json")
        cls.manifest = load("baselines/current/manifest.json")
        cls.index = load("baselines/current/rule-index.json")

    def test_01_all_87_source_ids_bijective(self):
        ids = [x["id"] for x in self.catalog["sources"]]
        self.assertEqual(len(ids), 87)
        self.assertEqual(len(self.inventory["sources"]), 87)
        self.assertEqual(set(ids), {x["source_id"] for x in self.source["sources"]})
        self.assertEqual(set(ids), {x["source_id"] for x in self.candidate["sources"]})
        self.assertEqual(len(self.source["sources"]), len({x["source_id"] for x in self.source["sources"]}))

    def test_02_review_decisions_and_counts_match(self):
        counts = Counter(s["recommendation"] for s in self.source["sources"])
        self.assertEqual(dict(self.source["summary"]), {
            "KEEP_CORE": 4, "KEEP_SPECIALIZED": 22, "CONSOLIDATE": 9,
            "OPTIONAL": 0, "REMOVE_CANDIDATE": 0, "DEFER": 52})
        self.assertEqual(sum(counts.values()), 87)
        self.assertEqual({k: counts[k] for k in self.source["summary"]}, self.source["summary"])
        original = {x["id"]: x for x in self.inventory["sources"]}
        for s in self.source["sources"]:
            o = original[s["source_id"]]
            if o["recommendation"] == "MERGE":
                self.assertEqual(s["recommendation"], "CONSOLIDATE")
            if o["recommendation"] == "INVESTIGATE":
                self.assertEqual(s["recommendation"], "DEFER")

    def test_03_no_unauthorized_removal(self):
        self.assertTrue(decisions_valid(self.source["sources"]))
        self.assertTrue(all(not s["is_removal_approved"] for s in self.source["sources"]))
        self.assertFalse(self.candidate["removal_approved"])
        self.assertFalse(self.candidate["activation_allowed"])
        synthetic = dict(self.source["sources"][0], recommendation="REMOVE_CANDIDATE")
        self.assertFalse(decisions_valid([synthetic]))

    def test_04_production_catalog_isolated(self):
        self.assertTrue(self.candidate["candidate_only"])
        self.assertTrue(self.candidate["non_runtime"])
        self.assertEqual(self.candidate["source_of_truth"], "rules/sources.json")
        originals = {s["id"]: s for s in self.catalog["sources"]}
        for item in self.candidate["sources"]:
            self.assertEqual(item["current_production_source"], originals[item["source_id"]])
            self.assertEqual(item["candidate_activation"], "PRESERVE_PRODUCTION_UNCHANGED")
        for path in ("LoonKit.lcf", "LoonKit.PrivacyDNS.lcf",
                     "scripts/build_composite_rules.py", "rules/active_profile.json"):
            data = (ROOT / path).read_text(encoding="utf-8")
            self.assertNotIn("refactor/vnext/", data)
            self.assertNotIn("sources.candidate.json", data)
            self.assertNotIn("active_profile.candidate.json", data)

    def test_05_all_34_groups_have_business_purpose(self):
        names = self.current_profile["group_order"]
        self.assertEqual(len(names), 34)
        self.assertEqual(self.profile["existing_order_immutable"], names)
        self.assertEqual(self.profile["proposed_order_for_review"], names)
        self.assertEqual([g["name"] for g in self.profile["groups"]], names)
        for g in self.profile["groups"]:
            self.assertGreater(len(g["business_definition"]), 12)
            self.assertTrue(g["logical_layer"])
            self.assertTrue(g["conflict_resolution"])
            self.assertFalse(g["order_change_approved"])

    def test_06_every_source_has_group_and_policy(self):
        groups = {g["name"] for g in self.profile["groups"]}
        orig = {s["id"]: s for s in self.catalog["sources"]}
        decisions = {s["source_id"]: s for s in self.source["sources"]}
        for item in self.candidate["sources"]:
            self.assertIn(item["group_target"], groups)
            self.assertEqual(item["original_group"], orig[item["source_id"]]["group"])
            self.assertEqual(item["design_decision"], decisions[item["source_id"]]["recommendation"])
            self.assertEqual(item["enabled_in_production"], bool(orig[item["source_id"]]["enabled"]))

    def test_07_consolidation_not_equated_to_safe_deletion(self):
        merges = [x for x in self.source["sources"] if x["recommendation"] == "CONSOLIDATE"]
        self.assertEqual(len(merges), 9)
        for x in merges:
            self.assertIn("ZERO_STAGE_CREDIT", x["suitable_for_consolidation"])
            self.assertEqual(x["published_rule_contribution"]["individual"], "UNKNOWN_SOURCE_PROVENANCE_INCOMPLETE")
            self.assertEqual(x["can_fall_through_final"], "NOT_APPROVED_REQUIRES_POLICY_EQUIVALENCE_AND_USER_CHOICE_TEST")

    def test_08_adblock_anchors_always_manual(self):
        expected = {"admob.com", "doubleclick.com", "app-measurement.com", "ads-twitter.com"}
        anchors = self.policy["advertising_anchors"]
        self.assertEqual({x["domain"] for x in anchors}, expected)
        for x in anchors:
            self.assertEqual(x["status"], "MANUAL_DECISION_REQUIRED")
            self.assertEqual(x["effect"], "NO_AUTOMATIC_REJECT_OR_ALLOW")
            self.assertIn("REJECT_AND_DIRECT_SELECTOR", x["test_plan"])

    def test_09_direct_keywords_and_single_label_suffixes_full_coverage(self):
        reviews = self.policy["direct_rule_reviews"]
        self.assertEqual(len(reviews), 57)
        actual = {(x["source_file"], x["source_line"], x["rule_type"], x["rule_value"])
                  for x in reviews}
        frozen = {(x["source_file"], x["source_line"], x["rule_type"], x["rule_value"])
                  for x in self.dns["direct_keywords"] + self.dns["direct_top_level_suffixes"]}
        self.assertEqual(actual, frozen)
        self.assertEqual(sum(x["rule_type"] == "DOMAIN-KEYWORD" for x in reviews), 10)
        self.assertEqual(sum(x["rule_type"] == "DOMAIN-SUFFIX" for x in reviews), 47)
        self.assertTrue(all(x["risk_id"] and not x["release_change_approved"] for x in reviews))
        cn = [x for x in reviews if x["rule_type"] == "DOMAIN-SUFFIX" and x["rule_value"] == "cn"]
        self.assertEqual(len(cn), 1)
        self.assertIn("PUBLIC_SUFFIX", cn[0]["proposal"])

    def test_10_seven_asn_flags_not_declared_fixed(self):
        reviews = self.policy["asn_no_resolve_reviews"]
        frozen = self.dns["missing_no_resolve"]
        self.assertEqual(len(reviews), len(frozen))
        self.assertEqual({int(x["rule_value"]) for x in reviews},
                         {132203, 32934, 211157, 44907, 59930, 62014, 62041})
        for x in reviews:
            self.assertTrue(x["require_runtime_verification"])
            self.assertFalse(x["change_approved"])
            self.assertEqual(x["proposed_flag"], "no-resolve")
            self.assertTrue(x["risk_id"])

    def test_11_final_selectable_semantics_retained(self):
        final = self.profile["final"]
        self.assertEqual(final["rule"], "FINAL,Final")
        self.assertEqual(final["choices"], ["Proxy", "Auto", "Fallback", "DIRECT"])
        self.assertTrue(final["preserve_user_selection"])
        self.assertTrue(final["default_proxy_assumption_forbidden"])
        self.assertEqual(self.profile["local_terminal_rules"], self.index["local_rules"][-2:])

    def test_12_proxyprotect_retirement_not_live_or_whitelist_expansion(self):
        self.assertEqual(self.profile["groups"][0]["name"], "ProxyProtect")
        self.assertEqual(self.profile["groups"][0]["current_subscription_order"], 1)
        self.assertEqual(self.profile["proposed_order_for_review"][0], "ProxyProtect")
        content = (ROOT / "design/phase-03/PROXYPROTECT_MIGRATION.md").read_text(encoding="utf-8")
        self.assertIn("NOT executed", content)
        self.assertIn("Stripe", content)
        self.assertIn("No new IP/DNS diagnostic domain", content)

    def test_13_production_and_frozen_manifest_sha256(self):
        for entry in self.manifest["files"]:
            self.assertEqual(sha256(entry["path"]), entry["sha256"], entry["path"])
        for entry in self.index["subscriptions"]:
            self.assertEqual(sha256(entry["path"]), entry["sha256"], entry["path"])
        self.assertEqual(self.manifest["source_commit"],
                         "f19421933d2177f95e7537f1208d990b3094f1f4")
        self.assertEqual(self.manifest["remote_subscription_count"], 34)

    def test_14_reproducible_architecture_report(self):
        def report():
            payload = {
                "source_decisions": self.source,
                "candidate_sources": self.candidate,
                "candidate_profile": self.profile,
                "policy": self.policy,
                "unresolved": self.unresolved,
            }
            raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            return hashlib.sha256(raw.encode("utf-8")).hexdigest()
        self.assertEqual(report(), report())
        self.assertEqual(report(), report())

    def test_15_every_phase02_risk_remains_open(self):
        items = self.unresolved["phase02_carryover"]
        self.assertEqual(len(items), 70)
        self.assertEqual({r["risk_id"] for r in items}, {r["risk_id"] for r in self.risks})
        self.assertEqual(Counter(r["severity"] for r in items), Counter({"P1": 54, "P2": 16}))
        self.assertTrue(all(r["status"] == "OPEN_NOT_FIXED" and r["evidence_missing"]
                            and r["phase03_affected_decision"] and r["verification"]
                            and not r["publication_change_approved"] for r in items))
        self.assertTrue(all(r["blocks_final_design"] for r in items if r["severity"] == "P1"))
        self.assertEqual(self.unresolved["status"], "PARTIAL")

    def test_16_all_policies_have_resolution_routing(self):
        category_ids = {x["id"] for x in self.policy["categories"]}
        for expected in ("DIRECT_VS_PROXY", "ADBLOCK_VS_PLATFORM", "OVERSEAS_VS_OVERSEAS",
                         "PARENT_VS_CHILD", "SHARED_CDN", "AUTH_AND_PAYMENT",
                         "SAME_POLICY_DUPLICATE", "IP_PREFIX_OVERLAP", "ASN_VS_CIDR",
                         "AI_VS_MICROSOFT", "AI_VS_GOOGLE", "DISNEY_VS_HBO",
                         "FACEBOOK_VS_WHATSAPP", "APPLE_VS_DIRECT", "DIRECT_VS_PAYMENT"):
            self.assertIn(expected, category_ids)
        self.assertTrue(self.policy["allow_automatic_only_for_semantically_identical_effect"])
        self.assertTrue(all(x["required_evidence"] for x in self.policy["categories"]))

    def test_17_no_unapproved_SOURCE_PROVENANCE_claims(self):
        unresolved_ids = set(self.unresolved["source_provenance_blocker"]["affected_sources"])
        ids = {s["source_id"] for s in self.source["sources"]
               if s["recommendation"] in {"CONSOLIDATE", "DEFER"}}
        self.assertEqual(unresolved_ids, ids)
        self.assertEqual(len(unresolved_ids), 61)
        self.assertTrue(self.unresolved["source_provenance_blocker"]["releasing_removals_forbidden"])
        self.assertTrue(all(s["risk_association_scope"] == "GROUP_LEVEL_NOT_PROOF_OF_ORIGIN"
                            for s in self.source["sources"]))

if __name__ == "__main__":
    unittest.main()
