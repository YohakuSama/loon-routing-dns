# Conflict classification, not uniform priority

**Never use publish position as business truth**. Stage 02 shows zero exact repeated *published* rules, 7,306 suffix ancestry pairs, 868 keyword candidate pairs and 168 overlapping prefixes. The historical generator reports separate input-stage cross-policy pruning statistics that are not additive.

## Decision matrix
| Conflict | Decision gate | Proposed outcome |
| --- | --- | --- |
| AdBlock vs Google/Twitter | Function: pure ad vs auth/measurement/payment? user REJECT/DIRECT? | MANUAL_DECISION_REQUIRED |
| AI vs Microsoft / Google | Dedicated Copilot or Gemini endpoint, or shared auth/CDN? | MANUAL_DECISION_REQUIRED |
| Disney vs HBO / streaming | Shared AWS/CDN or service-owned host? | MANUAL_DECISION_REQUIRED |
| Facebook vs WhatsApp / Instagram | Common Meta infrastructure vs specialized exit? | MANUAL_DECISION_REQUIRED |
| DIRECT vs international payment | Is mainland direct actually intended? | MANUAL_DECISION_REQUIRED |
| Apple vs DIRECT | Is this an Apple mainland region-specific service? | MANUAL_DECISION_REQUIRED |
| Parent vs child suffix or DOMAIN | Different effective policies, domain stage and label semantics | MANUAL_DECISION_REQUIRED or RUNTIME_VERIFICATION_REQUIRED |
| Keyword vs branded domain | Substring overmatch, counterexample host | MANUAL_DECISION_REQUIRED |
| IP-CIDR / CIDR6 intersection | Network containment/intersection and action | MANUAL_DECISION_REQUIRED if different |
| ASN vs CIDR | Pin ASN database and validate intersecting addresses | RUNTIME_VERIFICATION_REQUIRED |
| Same-condition, same-action duplicate | Exact matcher, options, same effective outcome proven, merge provenance | AUTO_RESOLVABLE |
| Equal condition, distinct policy choice | Both selectors could differ even if currently pointing to same node | MANUAL_DECISION_REQUIRED |

## Resolution contract
For each conflict capture `conflict_id, match_class, canonical_condition, left/right policies, upstream_sha, source_id/raw_line, normalized_line, published_path/line, overlap_witness, selector_state, locale, runtime_version, requested_action, rationale, reviewer, tests, expiry`. Domain parent-child overlap is not exact match; no cross-policy dropping without reviewed exception. Where effect is identical with static proof, dedup may union provenance (not silently discard second source).

Policy results: `AUTO_RESOLVABLE` only for proven equivalence; `MANUAL_DECISION_REQUIRED` for ownership or tradeoff; `RUNTIME_VERIFICATION_REQUIRED` for unresolved client/parser/ASN behavior. No decision or insufficient evidence ⇒ current published state unchanged, open risk record and fail any candidate release gate.

## Runtime uncertainty
Loon >=3.0.3 domain stage first and local > plugin > subscription from official docs. Do not infer that text order alone resolves all match classes. A candidate route graph is advisory until Loon device logs identify the actual selected policy for overlapping matchers.
