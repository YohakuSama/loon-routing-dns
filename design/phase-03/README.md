# Phase 03 — vNext routing architecture (REVIEW ONLY)

Status: **PARTIAL**. Phase 02 remains **PARTIAL**; no SOURCE_PROVENANCE_INCOMPLETE items are approved for deletion. Frozen input: `f19421933d2177f95e7537f1208d990b3094f1f4`; working branch at entry `d1fa4082582bb8c1d659f820e56b05511aaafce2`. This directory describes intended Stage 04 engineering, not active Loon behavior.

## Scope and deliverables
- All 87 catalog inputs are enumerated in `refactor/vnext/source_decisions.json`: KEEP_CORE **4**, KEEP_SPECIALIZED **22**, CONSOLIDATE **9**, OPTIONAL **0**, REMOVE_CANDIDATE **0**, DEFER **52**. All remain active in published configuration; even CONSOLIDATE is **unapproved**.
- 34 subscriptions/33 generated groups and one ProxyProtect are preserved in the candidate profile with unchanged order; `FINAL,Final` and selectable `Final = select,Proxy,Auto,Fallback,DIRECT` are retained.
- All 70 Phase 02 risks are OPEN in `refactor/vnext/unresolved_decisions.json` (54 P1, 16 P2), plus global upstream and runtime evidence gaps.
- The ten DIRECT keyword and 47 one-label suffix rules, seven ASN flags and four AdBlock anchors each have machine-readable review records in `policy_decisions.json`.
- `sources.candidate.json` and `active_profile.candidate.json` are **not inputs** to any released generator, config, publication workflow, or subscription.

## Reading order
ARCHITECTURE → SOURCE_DECISIONS → CHINA_ROUTING_DESIGN / INTERNATIONAL_ROUTING_DESIGN / ADBLOCK_DESIGN → POLICY_PRIORITY → DNS_ROUTING_DESIGN → PROXYPROTECT_MIGRATION → COMPATIBILITY_MATRIX → PHASE02_CARRYOVER → PHASE04_IMPLEMENTATION_SPEC → ACCEPTANCE.

Official Loon semantics consulted: https://nsloon.app/en/docs/Rule/ ; https://nsloon.app/en/docs/Rule/domain_rule/ ; https://nsloon.app/en/docs/Rule/ip_rule/ ; https://nsloon.app/en/docs/Rule/final_rule/ . The 3.0.3+ rule-source ordering supersedes outdated statements that subscriptions always outrank plugins. Observations not covered by docs are RUNTIME_VERIFICATION_REQUIRED.

No `.lcf`, published rule, DNS/TUN setting, baseline, official source catalog or generator was modified in Stage 03.
