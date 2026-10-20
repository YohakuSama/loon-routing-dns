# Loon matcher semantics — independent documentation review (2026-10-20)

This file records statements supported by the vendor documentation. It is NOT a statement that the current candidate has been tested in Loon on a device.

## Primary documentation

- https://nsloon.app/docs/Rule/
- https://nsloon.app/docs/Rule/domain_rule/
- https://nsloon.app/docs/Rule/ip_rule/
- https://nsloon.app/en/docs/General/

The Loon manual says (for version 3.0.3 and later):
1. When the destination is a hostname, hostname rules are considered before IP rules.
2. If no domain rule matches, Loon may resolve DNS locally and then evaluate IP predicates.
3. Other rules are evaluated in configured order; rule origin priority is local > plugin > subscription.
4. Without a matching rule, FINAL applies.
5. DOMAIN-SUFFIX uses DNS-label suffix boundaries: apple.com matches www.apple.com but not app-apple.com.
6. IP-CIDR (IPv4), IP-CIDR6 (IPv6) and IP-ASN are documented types. IP-ASN syntax uses the integer ASN.
7. With no-resolve, an IP predicate only matches requests whose destination is already an IP and does not trigger DNS resolution for domain input.

## Consequences for the stage 05 candidate

- The 14 candidate-only inline domain suffixes for restored overseas selectors are LOCAL rules, so they can override remote predicates; inspect AdBlock and shared-domain overlap rather than assuming remote AdBlock always wins.
- The 7,350 cross-policy parent/child pairs include remote subscription predicates. The vendor docs do **not** independently prove the service owner and observed outcome of each specific case.
- A suffix within cn is not automatically a misroute: the candidate puts AdBlock early and ChinaDirect late, but real Loon group precedence and current service egress still require device logs where policies differ.
- Candidate IP-ASN no-resolve formatting is consistent with the vendor's documented syntax. Actual ASN databases, literal targets and resolution behavior require device evidence.
- DNS/TUN/IPv4/IPv6 settings are frozen and must never be changed merely to make the rules appear to pass.

## Acceptance evidence

Maintain configured selector states, actual matching rule, Loon version, policy, selected node alias, anonymized egress and anonymized resolver aliases. Distinguish DOMAIN-only offline simulation from true Loon match logs. Do not mark undocumented differences VERIFIED_ACCEPTABLE.
