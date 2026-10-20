# IP matching and DNS investigation

- IP rules lacking no-resolve: 7.
- The generator *adds* no-resolve to IP-CIDR/CIDR6, but preserves optional IP-ASN flags.
- On a domain miss, IP-rule matching may involve local lookup; exact runtime execution is unverified.
- Distinguish Loon DNS, app DoH, proxy remote DNS, local pre-resolution and reported recursive egress.
- GEOIP,CN,DIRECT,no-resolve and FINAL in local [Rule] must be assessed against remote ordering.
- These static findings neither demonstrate DNS leakage nor prove exposure of a device address.

## Missing flags (complete)
- `rules/generated/Telegram.list:32` `IP-ASN,211157` → `Telegram`
- `rules/generated/Telegram.list:33` `IP-ASN,44907` → `Telegram`
- `rules/generated/Telegram.list:34` `IP-ASN,59930` → `Telegram`
- `rules/generated/Telegram.list:35` `IP-ASN,62014` → `Telegram`
- `rules/generated/Telegram.list:36` `IP-ASN,62041` → `Telegram`
- `rules/generated/Facebook.list:471` `IP-ASN,32934` → `Facebook`
- `rules/generated/ChinaDirect.list:110393` `IP-ASN,132203` → `DIRECT`

RUNTIME_VERIFICATION_REQUIRED
