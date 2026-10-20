# Routing architecture — logical intent vs actual Loon match

## Evidence baseline
Phase 01 `baselines/current/rule-index.json`: 34 remote subscriptions (33 generator groups + ProxyProtect), 66 local rules, 87 enabled generator inputs, 206,505 published matchers. The local terminal rules are `GEOIP,CN,DIRECT,no-resolve` and `FINAL,Final`. Phase 02 final publication has zero exact duplicates but 7,306 cross-policy suffix ancestry candidates, 868 keyword candidates, and 168 IP prefix intersections. These are not proven runtime errors. Source attribution after pruning remains unavailable.

## Five logical layers (NOT a global match order)
1. **Verified mainland DIRECT**: bank/payment/maps/commerce/transit/domestic CDN, China-region Apple/Steam when business and region are evidenced. Evidence-based domain scopes over corporate ownership or raw .cn heuristic.
2. **Special egress overseas**: AI, streaming regional catalogs, TikTok, Telegram and other explicitly selectable applications. Preserve existing policy group names and choices; evaluate whether ordinary non-unlock traffic can use FINAL only after differential tests.
3. **Ads and tracking**: only verified blocking purpose; `AdBlock = select,REJECT,DIRECT`; authentication, purchase, fraud and ambiguous telemetry require MANUAL_DECISION_REQUIRED.
4. **Address and network**: prefer narrow verified IPv4/IPv6 ranges; `IP-ASN`, `GEOIP`, IP families and `no-resolve` are routed through explicit pre-resolution constraints and runtime tests.
5. **FINAL fallback**: `FINAL,Final`, not hard-coded Proxy. `Final` continues supporting Proxy/Auto/Fallback/DIRECT. Domain rules cannot assume all misses are proxied.

## Official matcher model
As documented for Loon 3.0.3+: for a domain destination, Loon evaluates domain-class rules first; if none match, local DNS resolution can precede IP-class matching. Other eligible rules follow configuration order, with source precedence local > plugin > subscription. FINAL applies only if nothing else matches. `DOMAIN` exact; `DOMAIN-SUFFIX` label-boundary suffix; `DOMAIN-KEYWORD` substring. IP-CIDR, IP-CIDR6, IP-ASN and GEOIP are distinct matchers. `no-resolve` restricts an IP-only rule to already-IP destinations and avoids a DNS lookup *by that rule*, but does not globally forbid DNS queries. Official references: https://nsloon.app/en/docs/Rule/ , /domain_rule/ , /ip_rule/ , /final_rule/ .

**Caveat**: Source precedence is not sufficient to infer within-stage precedence of all overlapping DOMAIN, DOMAIN-SUFFIX, DOMAIN-KEYWORD, HTTP and USER-AGENT rules. The effect of multiple overlapping subscriptions, IP-ASN data freshness, node-protocol DNS handoff, and app-DoH/DoT is RUNTIME_VERIFICATION_REQUIRED; not modeled as a proven deterministic ordering.

## Prepublication gates
Normalize → attach immutable upstream SHA + raw line + include ancestry → classify domain/business intent → compile conflict graph across group, type and hierarchy → perform AUTO_RESOLVABLE identical-effective-action dedup only → request explicit human decisions for differing actions or scope → generate candidate output outside `rules/generated` → compare current and candidate matched policy on device by group/region/network/IPv4+6 → human approval → Stage 04+ guarded implementation. A default `PUBLISH_ORDER` tie-break is forbidden for cross-policy ownership. With absent evidence, keep current publication unchanged.

## Boundaries
Prohibit configuration or DNS/TUN rewrites; refuse tests that equate BrowserLeaks display with complete DNS confidentiality. Preserve existing final/AdBlock/overseas selector choices, local terminal rules, historical frozen hashes, original rule order and user credentials. No Stage 03 rules are activated.
