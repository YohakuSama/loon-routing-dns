# PHASE02_CARRYOVER — open blockers

The authoritative **70 individual** Phase 02 risk IDs and their severity, missing evidence, affected Stage 03 decision, release-blocking status and later verification instructions are in `refactor/vnext/unresolved_decisions.json/phase02_carryover`. This document must never mark an item fixed solely because a design/test exists.

| Evidence gap | Impact | Status and next verification |
| --- | --- | --- |
| All 87 lack exact published post-filter source attribution | Unprovable non-replaceable coverage or safe deletion, particularly 9 zero-credit and 52 INVESTIGATE | OPEN — pin upstream object versions and preserve raw source ID/line through normalization, duplicate prune and output; compare reconstructed published snapshot |
| 28 historical upstream remote bodies unavailable | Cannot claim per-rule legacy parity | HISTORICAL_CONTENT_UNAVAILABLE — do not invent; inspect archive only if immutable historical bytes independently obtained |
| AdBlock Google/X anchors and app-measurement DIRECT exact | Cannot approve BLOCK/ALLOW or arbitration | P02-00001…P02-00006 OPEN — business function tests, user REJECT/DIRECT and Loon rule trace |
| 10 broad DIRECT keywords | Unknown unrelated substring capture | P02-00013…P02-00022 OPEN — domain positive/negative fixtures; propose scoped alternatives |
| 47 single-label DIRECT suffixes | Cross-border/TLD and multi-tenant ambiguity | P02-00023…P02-00069 OPEN — IDN/TLD/domain ownership and service function tests |
| 7 IP-ASN no-resolve absences | Possible unnecessary local lookup and incorrect routed IP | P02-00007…P02-00012, P02-00070 OPEN — ASN DB pin, IPv4/6 and packet/device traces |
| 7,306 suffix ancestry / 868 keyword / 168 IP prefix overlaps | Potential cross-strategy misroute, *not* necessarily errors | OPEN — conflict sampling then full matcher join, manually approve differing effects; no arithmetic combination with generator stage |
| BrowserLeaks resolver observation | Cannot attribute specific ASN or establish absence/presence of global DNS leakage | RUNTIME_VERIFICATION_REQUIRED — same DNS settings, Loon logs, packet observations, node protocol variation |

**Decision blocking policy:** every P1 has `blocks_final_design=true`. Source attribution globally blocks removal/merge/FINAL transfers. All 70 are preserved as `status=OPEN_NOT_FIXED`; candidate configurations cannot enter production. Phase 03 upper-bound acceptance is PARTIAL unless these material dependencies are solved with independent evidence; changing criteria cannot improve it.
