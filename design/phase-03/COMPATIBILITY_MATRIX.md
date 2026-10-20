# Compatibility / regression matrix

| Area | Frozen current behavior | Stage 03 design constraint | Gate before activation |
| --- | --- | --- | --- |
| Local Rules | 66 ordered local rules, ending GEOIP,CN,DIRECT,no-resolve and FINAL,Final | Preserve byte-for-byte | Compare frozen index and on-device local match |
| Remote Rules | 34 URLs incl. ProxyProtect; 33 generated group lists | Keep order and count in candidate profile; future changes reviewed | Domain/IP precedence and effective-route differential |
| Inputs | 87 enabled `rules/sources.json` | Candidate wraps same 87, not generator input | Source SHA, raw line, lineage and license |
| Existing selectors | All named groups and Final with selectable Proxy/Auto/Fallback/DIRECT | No rename, deletion or selector option loss | Compare group choices and installed device preferences |
| AdBlock | select,REJECT,DIRECT | Keep both choices | App sign-in, analytics, purchase, reject/direct A/B |
| Apple/Microsoft | Existing DIRECT options | Preserve both | Mainland vs international login/update/CDN |
| Streaming/AI | Per-platform selectable exit | Preserve custom region/node intent | Regional unlock per platform; shared-CDN negative |
| Domestic | ChinaDirect, DomesticCore, AppleOTA, SteamCN + GEOIP | No automatic international DIRECT expansion | Domestic bank/maps/commerce and foreign payment fixtures |
| IP / no-resolve | 7 ASN published without flag; GEOIP local no-resolve | Design-only proposals | Dual-stack Loon device DNS traces |
| ProxyProtect | 17 entries, first subscription | Decommission *plan* only | 17 parity fixtures and Stripe checkout |
| DNS/TUN | Frozen main and PrivacyDNS sections | Zero config or provider changes | Frozen SHA256 and packet captures in identical environment |
| Main publication | main subscribable URLs mutable, snapshots Git-pinned | No merge/publish/active rewrite | Signed review and staged candidate only |

Regression dimensions: iOS/Loon version, device/node protocol, selected strategy-group option, country, app/network, DNS cache state, IPv4 vs IPv6, hostname vs IP literal, prefetch and direct/reject behavior. Unknown remains `RUNTIME_VERIFICATION_REQUIRED`.
