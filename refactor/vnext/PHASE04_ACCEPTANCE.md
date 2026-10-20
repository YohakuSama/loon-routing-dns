# Phase 04 vNext candidate: engineering acceptance (2026-10-20)

## Final status

- ENGINEERING_STATUS: SUCCESS for static candidate engineering, generator, tests, and committed rule outputs.
- RELEASE_READINESS: READY_FOR_NEXT_STAGE. PRODUCTION_READINESS: NOT_READY.
- Neither real Loon DNS/TUN/ASN routing nor iPhone node / unlock behavior is claimed to have passed.
- Only refactor/loonkit-vnext changed. No main merge, public subscription activation, DNS or TUN change.
- Start commit: b982110a189b41b42e8562f7d10226071b0b2432
- Final generated artifact commit: 252ae73d99704f6040d375bd68fc4f039116ac3b
- Full green stage 04 CI: https://github.com/YohakuSama/loonkit/actions/runs/39382796854

## Rule counts and differences (verified generated report)

| Metric | Before | Candidate |
|---|---:|---:|
| Total publishable rule predicates, including separate ProxyProtect | 206,505 | 197,765 |
| ChinaDirect | 123,008 | 114,837 |
| AdBlock | 77,213 | 76,895 |
| Independent ProxyProtect rules | 17 | 0 |
| Original upstream source IDs | 87 | 87 documented |
| Group snapshots selected as immutable candidate inputs | 33 | 26 |
| Additional dedicated FINAL-fallback groups | 0 | 7 |

Net predicate reduction: 8,740 (4.23%). Added predicate/group pairs: 8; removed: 8,748;
changed ownership mappings: 8,752. These are static predicate counts, not semantic equivalence.

## Substantive follow-up repairs

- Frozen input integrity: all 33 published group list files, all 10 custom local files, and
  ProxyProtect are checked against 44 frozen Git blob SHA-1 attestations before generation.
- 87 historical source entries each have an explicit evidence status. Of those, 63 reference
  active merged snapshots but are not individually attributable, 14 belong to disabled candidate
  groups, and 10 are verifiable maintained-local sources; 65 retained local source-to-rule line
  mappings are independently proven and emitted as verified_local_provenance.tsv.
- The engine does not imply that a frozen merged snapshot equals a recovered original feed.
- The initial 64 nested IP network collisions were resolved statically: 56 suspect ChinaDirect
  IP ranges nested within Apple/Google policy nets were isolated; two overly broad Whatsapp
  shared-AWS net ranges overlapping Netflix were isolated. Resulting nested conflicts: 0.
- 20 high-risk global substring brand matches are now narrower validated domain suffixes.
  Of these, five restore precise ChinaDirect support for baidu.com, taobao.com, weibo.com,
  alipay.com, and aliyun.com; one previous `.tmall.com` keyword also remains suffix-scoped.
- Four other unproven ChinaDirect keywords stay excluded. Generic shared-hosting keywords
  `appspot` and `blogspot` are isolated, not reintroduced as whole-provider Google suffixes.
- Six generic multitenant hosting / CDN suffixes cannot force a vendor-specific policy.
- Seven IP-ASN predicates have exactly one no-resolve flag.
- AdBlock remains select,REJECT,DIRECT, with four explicit advertising roots assigned to
  AdBlock, while 322 risk-bearing shared-service blockers remain isolated.
- 17 retired ProxyProtect entries each have file, line, replacement, and FINAL=DIRECT risk.
- Seven disabled specialized overseas rule subscriptions fall back to the user's FINAL
  selector without deleting any corresponding user-visible policy group names.

## Independent test coverage and evidence

- Run: `python3 scripts/vnext_rule_engine.py`
- Determinism check: `python3 scripts/vnext_rule_engine.py --check`
- Test command: `python3 -m unittest discover -s tests -p 'test_phase04_vnext.py' -v`
- Full Python, Node, stages 01-03 baseline tests and repository validation passed in stage 04 CI.
- 34 representative domain-only business scenarios and AdBlock REJECT/DIRECT plus all FINAL
  selector states have static fixtures in business_regression_cases.json.
- Six explicit IP-literal scenarios are stage 05 validation fixtures, NOT device-tested results.
- `reports/domain_parent_child_conflicts.jsonl`: 7,350 potential parent/child overrides.
- `reports/domain_keyword_risks.jsonl`: 22 remaining substring matchers.
- `reports/ip_network_overlaps.jsonl`: zero remaining cross-policy nested IP networks.
- `reports/provenance.tsv`: immutable published snapshot path/line, upstream candidates clearly
  marked non-proven; `reports/verified_local_provenance.tsv`: proven local input path/line.
- `reports/sources.vnext.candidate.json`: full 87-entry candidate-origin and attribution ledger.
- `reports/removed_or_modified.jsonl`, `ownership_changes.jsonl`, `direct_changes.jsonl`,
  `adblock_changes.jsonl`, `ip_no_resolve_changes.jsonl`, `proxyprotect_impact.jsonl`,
  `diff_summary.json`: exhaustive machine-readable static change ledgers.

## Unresolved release gates

- 7,350 domain parent-child overlap observations are not automatically 7,350 real misroutes.
  Domain rule classes, local vs remote precedence and same-stage collision behavior still
  require verified Loon device semantics and service-specific acceptance.
- Of the 87 historic upstream feeds, complete original upstream byte/line provenance cannot
  be retroactively reconstructed from old merged lists. Verified evidence is kept separate.
- Domestic/overseas Apple, Netflix unlock, payments, anti-fraud, AdBlock, true DNS leak
  behavior, ASN and IPv4/IPv6 routing need device and live-service tests.
- A user's FINAL=DIRECT selection can direct previously filtered unknown foreign services.
- No automatic candidate publication, main merge or change to either Loon DNS/TUN section.
