# AdBlock ownership and collateral-block risk

AdvertisingLite is enabled; Advertising full is a disabled candidate, not a comparable input snapshot.
Privacy/Hijacking may contribute supplemental domains, but per-source published output is untraceable.
The generator only admits DOMAIN/DOMAIN-SUFFIX to AdBlock; keyword/IP exclusions alter coverage.
Platform-first ownership means ad-related exact matches may be removed from AdBlock.
The published anchor check confirms Google owns admob.com, doubleclick.com and
app-measurement.com; Twitter owns ads-twitter.com; ChinaDirect has an exact
app-measurement.com entry. That is a policy-risk candidate, not a proven bypass.
AdBlock is configured as select,REJECT,DIRECT, so runtime selection matters.
Do not infer that every telemetry domain should be blocked.

## Required anchored domain conditions

- `admob.com`: [{"group":"Google","no_resolve":false,"policy":"Google","rule_type":"DOMAIN-SUFFIX","rule_value":"admob.com","source_file":"rules/generated/Google.list","source_line":21}]
- `ads-twitter.com`: [{"group":"Twitter","no_resolve":false,"policy":"Twitter","rule_type":"DOMAIN-SUFFIX","rule_value":"ads-twitter.com","source_file":"rules/generated/Twitter.list","source_line":5}]
- `app-measurement.com`: [{"group":"Google","no_resolve":false,"policy":"Google","rule_type":"DOMAIN-SUFFIX","rule_value":"app-measurement.com","source_file":"rules/generated/Google.list","source_line":42},{"group":"ChinaDirect","no_resolve":false,"policy":"DIRECT","rule_type":"DOMAIN","rule_value":"app-measurement.com","source_file":"rules/generated/ChinaDirect.list","source_line":32}]
- `doubleclick.com`: [{"group":"Google","no_resolve":false,"policy":"Google","rule_type":"DOMAIN-SUFFIX","rule_value":"doubleclick.com","source_file":"rules/generated/Google.list","source_line":204}]

Suggested classification: BLOCK_CANDIDATE, ALLOW_CANDIDATE, CONFLICT, REVIEW_REQUIRED.
