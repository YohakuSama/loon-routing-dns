# Advertisement and telemetry decision boundary

`AdBlock = select,REJECT,DIRECT` must retain both user choices. The generator currently admits only DOMAIN and DOMAIN-SUFFIX to AdBlock; keyword and IP exclusions are important to avoid broad collateral blocks. However, treating a rule's position in PUBLISH_ORDER as its business owner can make advertising candidates first-owned by platforms.

Phase 02 published anchors requiring review:
- `admob.com` → Google (published DOMAIN-SUFFIX)
- `doubleclick.com` → Google (published DOMAIN-SUFFIX)
- `app-measurement.com` → Google DOMAIN-SUFFIX; ChinaDirect exact DOMAIN as separate match class
- `ads-twitter.com` → Twitter (published DOMAIN-SUFFIX)

All are `MANUAL_DECISION_REQUIRED`, not automatic REJECT. The authoritative row-by-row locations and policies are in `policy_decisions.json/advertising_anchors`; Phase 02 P02-00001 to P02-00006 cover these overlaps. Function, product breakage and runtime policy winning must be checked before setting any exception.

Review labels: `BLOCK_CANDIDATE` for ad-serving verified hosts only; `ALLOW_CANDIDATE` for authentication/payment/fraud; `CONFLICT` for multiple action candidates; `REVIEW_REQUIRED` when telemetry/tracking is ambiguous. A label is not an active routing decision. A selector set to DIRECT must continue to bypass blocking, including after consolidation.

Required cases: Google ad SDK vs Play Services sign-in/payments, app-measurement telemetry vs app functionality, ads-twitter domain vs X usage, explicit user choice REJECT/DIRECT, wildcard and parent suffix cross-effects. Use owner review of legitimate functions, app test accounts, Loon matching and rollback; do not infer all telemetry safe to block. Do not create new diagnostic site exceptions as a shortcut.
