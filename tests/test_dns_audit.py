#!/usr/bin/env python3
"""Offline unit tests for DNS configuration risk warnings."""
import unittest
from scripts.audit_dns_config import inspect


def config(general):
    return "[General]\n" + general + "\n[Rule]\nFINAL,Final\n"


class DnsAuditTests(unittest.TestCase):
    def test_normal_configuration(self):
        warnings = inspect(config(
            "doh-server = https://dns.alidns.com/dns-query\n"
            "hijack-dns = *:53\n"))
        self.assertEqual(warnings, [])

    def test_missing_encryption_and_hijack(self):
        warnings = inspect(config("dns-server = 223.5.5.5"))
        self.assertTrue(any("No DoH" in x for x in warnings))
        self.assertTrue(any("Plain DNS" in x for x in warnings))
        self.assertTrue(any("No DNS hijack" in x for x in warnings))

    def test_insecure_doh_and_default_tun_bypass(self):
        warnings = inspect(config(
            "doh-server = http://example.com/dns-query\n"
            "hijack-dns = 192.168.1.1:53\n"
            "bypass-tun = 0.0.0.0/0\n"))
        self.assertTrue(any("non-HTTPS" in x for x in warnings))
        self.assertTrue(any("not global" in x for x in warnings))
        self.assertTrue(any("Default route" in x for x in warnings))


if __name__ == "__main__":
    unittest.main()
