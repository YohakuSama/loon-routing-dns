"""Independent deterministic stress and production-invariant audits.

Uses brute-force reference matchers rather than trusting the review indexes.
No networking and no mutation of a published rule, profile, or source lock.
"""
from __future__ import annotations

from collections import defaultdict
import ipaddress
from pathlib import Path
import random
import string
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import rule_engine as engine
import upstream_review as review


def domain_overlap(a: str, b: str) -> bool:
    """Reference set intersection: exact/suffix predicates over DNS hosts."""
    ak, av = engine.fields(a)
    bk, bv = engine.fields(b)
    if ak == "DOMAIN" and bk == "DOMAIN":
        return av == bv
    if ak == "DOMAIN":
        return engine.is_covered(av, bv)
    if bk == "DOMAIN":
        return engine.is_covered(bv, av)
    return engine.is_covered(av, bv) or engine.is_covered(bv, av)


def reference_domain_collisions(rule: str, group: str,
                                groups: dict[str, set[str]]) -> list[str]:
    return sorted({other for other, rules in groups.items() if other != group
                   for existing in rules if domain_overlap(rule, existing)})


def reference_ip_collisions(rule: str, group: str,
                            groups: dict[str, set[str]]) -> list[str]:
    kind, value = engine.fields(rule)
    if kind not in {"IP-CIDR", "IP-CIDR6"}:
        return []
    net = ipaddress.ip_network(value)
    result = set()
    for other, rules in groups.items():
        if group == other:
            continue
        for old in rules:
            k, v = engine.fields(old)
            if k not in {"IP-CIDR", "IP-CIDR6"}:
                continue
            other_net = ipaddress.ip_network(v)
            if net.version == other_net.version and net.overlaps(other_net):
                result.add(other)
    return sorted(result)


class DifferentialIndexTests(unittest.TestCase):
    def test_domain_overlap_index_against_bruteforce(self):
        rng = random.Random(0xC00B42)
        groups = {}
        names = ["a", "b", "api", "auth", "static", "cdn",
                 "example", "parent", "child", "services", "test"]
        domains = []
        for _ in range(150):
            domain = ".".join([rng.choice(names) for _ in range(rng.randint(1, 3))]
                              + [rng.choice(("com", "net", "org"))])
            domains.append(domain)
        for g in range(7):
            group = "grp"+str(g)
            groups[group] = {
                rng.choice(("DOMAIN", "DOMAIN-SUFFIX")) + "," + rng.choice(domains)
                for _ in range(48)
            }
        index, keys = review._overlap_index(groups)
        for number in range(1200):
            host = rng.choice(domains)
            if number % 3 == 0:
                host = rng.choice(names) + "." + host
            rule = rng.choice(("DOMAIN", "DOMAIN-SUFFIX")) + "," + host
            group = "grp"+str(rng.randrange(8))
            with self.subTest(n=number, rule=rule, group=group):
                actual = review._semantic_expansion(rule, group, groups, index, keys)
                expected = reference_domain_collisions(rule, group, groups)
                self.assertEqual(actual, expected)

    def test_ipv4_ipv6_index_against_bruteforce(self):
        rng = random.Random(0x1A11CE)
        groups = defaultdict(set)
        for version in (4, 6):
            bits = 32 if version == 4 else 128
            prefixes = ([8, 12, 16, 24, 28, 32] if version == 4
                        else [16, 24, 32, 48, 64, 96, 128])
            for g in range(7):
                for _ in range(35):
                    net = ipaddress.ip_network((rng.getrandbits(bits),
                                                rng.choice(prefixes)), strict=False)
                    kind = "IP-CIDR" if version == 4 else "IP-CIDR6"
                    groups["grp"+str(g)].add(kind + "," + str(net) + ",no-resolve")
        index = review._ip_overlap_index(groups)
        for number in range(900):
            version = 4 if number % 2 else 6
            bits = 32 if version == 4 else 128
            prefix = rng.choice([8, 12, 16, 24, 28, 32] if version == 4
                                else [16, 24, 32, 48, 64, 96, 128])
            net = ipaddress.ip_network((rng.getrandbits(bits), prefix), strict=False)
            group = "grp"+str(rng.randrange(8))
            kind = "IP-CIDR" if version == 4 else "IP-CIDR6"
            rule = kind + "," + str(net) + ",no-resolve"
            with self.subTest(n=number, rule=rule, group=group):
                self.assertEqual(review._ip_collisions(rule, group, index),
                                 reference_ip_collisions(rule, group, groups))

    def test_same_policy_reduction_preserves_matching_behavior(self):
        rng = random.Random(0xBAD515)
        suffixes = {"DOMAIN-SUFFIX,example.org",
                    "DOMAIN-SUFFIX,service.net",
                    "DOMAIN-SUFFIX,secure.shop"}
        originals = suffixes | {"DOMAIN," + rng.choice(("a", "api", "auth", "ads"))
                                + "." + rng.choice(("example.org", "service.net",
                                                   "unrelated.io"))
                                for _ in range(200)}
        before = {r for r in originals}
        after, removed = review._same_policy_reduce(before)
        self.assertEqual(len(before) - len(after), removed)
        self.assertTrue(after.issubset(before))
        for number in range(600):
            domain = (rng.choice(("a", "api", "auth", "ads", "static")) + "." +
                      rng.choice(("example.org", "service.net", "secure.shop",
                                  "unrelated.io")))
            old = any(engine.covers_domain(rule, domain) for rule in before)
            new = any(engine.covers_domain(rule, domain) for rule in after)
            self.assertEqual(old, new, domain)

    def test_parser_malformed_fuzz_does_not_bypass_or_crash(self):
        rng = random.Random(0x51A1E)
        alphabet = string.ascii_letters + string.digits + " ._-,*/:#\t"
        for number in range(600):
            source = {"format": rng.choice(["loon", "domainset",
                                           "v2fly", "dnsmasq"]), "min_rules": 1}
            payload = "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 85)))
            with self.subTest(n=number, fmt=source["format"]):
                rules, status = review.parse_source(source, payload.encode())
                self.assertLessEqual(len(rules), 1)
                self.assertEqual(status["rules"], len(rules))
                self.assertIn(status["minimum_satisfied"], {True, False})


class PublishedPolicyAudits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contents = engine.compile_rules(ROOT)
        cls.groups = {}
        for p, body in cls.contents.items():
            key = p.removeprefix("build/generated/").removesuffix(".list")
            cls.groups[key] = {x.strip() for x in body.splitlines()
                               if x.strip() and not x.startswith("#")}

    def test_locked_production_has_no_duplicate_exact_matchers(self):
        owners = {}
        for group, rules in self.groups.items():
            for rule in rules:
                self.assertNotIn(rule, owners,
                                 f"{rule}: {owners.get(rule)} versus {group}")
                owners[rule] = group
        self.assertEqual(len(self.groups), 26)
        self.assertGreater(len(owners), 190000)

    def test_all_domestic_direct_groups_respect_protected_hosts(self):
        import json
        guards = json.loads((ROOT/"rules/routing_guardrails.json").read_text())
        hosts = guards["protected_proxy_domains"]
        for group in ("DomesticCore", "AppleOTA", "SteamCN", "ChinaDirect"):
            for rule in self.groups[group]:
                kind, _ = engine.fields(rule)
                if kind not in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                    continue
                for host in hosts:
                    self.assertFalse(engine.covers_domain(rule, host),
                                     f"{group} unexpectedly DIRECT {host} via {rule}")

    def test_adblock_critical_auth_payment_domain_protection(self):
        for rule in self.groups["AdBlock"]:
            kind, _ = engine.fields(rule)
            if kind not in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                continue
            for host in engine.AD_SAFETY_ROOTS:
                self.assertFalse(engine.covers_domain(rule, host),
                                 f"AdBlock could block critical host {host}: {rule}")

    def test_published_groups_have_expected_adblock_user_control(self):
        content = (ROOT/"LoonKit.lcf").read_text()
        self.assertIn("AdBlock = select,REJECT,DIRECT", content)
        for host in engine.AD_ANCHORS:
            ad = "DOMAIN-SUFFIX," + host
            self.assertIn(ad, self.groups["AdBlock"])
            self.assertFalse(any(ad in rules for group, rules in self.groups.items()
                                 if group != "AdBlock"))


if __name__ == "__main__":
    unittest.main()
