# Phase 02 — frozen published snapshot audit

- Frozen source commit: `f19421933d2177f95e7537f1208d990b3094f1f4`
- Input: 34 indexed published .list subscriptions. Local GEOIP and FINAL reviewed separately.
- Published rules parsed: **206,505** across **34** files.
- All 87 enabled inputs inventoried, but exact post-filter source attribution is unavailable.
- Historical remote bodies: `HISTORICAL_CONTENT_UNAVAILABLE`.
- Runtime DNS packet captures: `RUNTIME_VERIFICATION_REQUIRED`.

## Published matcher type totals

- DOMAIN: 23,943
- DOMAIN-KEYWORD: 54
- DOMAIN-SUFFIX: 168,604
- IP-ASN: 7
- IP-CIDR: 9,459
- IP-CIDR6: 4,326
- USER-AGENT: 112

## Risk register

- P0: 0
- P1: 54
- P2: 16
- P3: 0

Full data: `data/normalized_rules.jsonl.gz`, other JSON datasets.
Counts from the historical generator audit are INPUT-STAGE observations, not published errors.
