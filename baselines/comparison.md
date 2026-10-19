# Phase 01 initial static comparison

| Property | Legacy | Current |
|---|---:|---:|
| Remote references | 28 | 34 |
| Generated groups | not self-hosted | 33 |
| Independent ProxyProtect list | none | 1 |
| Local rules incl. terminal | 66 | 66 |
| Current enabled inputs | not established | 87 |

Legacy tags, in order: Advertising → AdvertisingDomain → AppleOTA → SteamCN → YouTube → Netflix → Disney → PrimeVideo → Spotify → TikTok → Twitch → AbemaTV → BBC → BiliBili → Telegram → Instagram → Twitter → Discord → Line → LinkedIn → Reddit → Google → AppleDomain → Apple → Steam → PayPal → ChinaDirect → ChinaDomain.

Current groups, in order: ProxyProtect → DomesticCore → AI → AppleOTA → SteamCN → YouTube → Netflix → Disney → PrimeVideo → Spotify → TikTok → Twitch → HBO → Abema → BBC → Bilibili → 動畫瘋 → Dazn → Telegram → Whatsapp → Instagram → Facebook → Twitter → Discord → Line → Reddit → Linkedin → Google → Microsoft → Apple → Steam → Paypal → AdBlock → ChinaDirect.

The entire ordered local rule list is identical: true. Both terminal entries are unchanged (`GEOIP,CN,DIRECT,no-resolve`, `FINAL,Final`).

Current formal rule-type counts, across 206505 list entries: DOMAIN=23943, DOMAIN-KEYWORD=54, DOMAIN-SUFFIX=168604, IP-ASN=7, IP-CIDR=9459, IP-CIDR6=4326, USER-AGENT=112.

**HISTORICAL_CONTENT_UNAVAILABLE** for 28 original downloaded remote rule bodies: do not fabricate historical remote per-rule added/removed entries, kind distribution, no-resolve flags or observed network behavior. Audit flags 159 cross-group exact policy cases; investigate match precedence, broad DIRECT, keywords and IP/no-resolve later, without applying stage 02+ changes now.
