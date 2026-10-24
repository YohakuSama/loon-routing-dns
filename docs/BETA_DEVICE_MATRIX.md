# Beta v6.5.5-beta.1 device acceptance — PENDING, NOT A TEST RESULT

This document is a blank real-device acceptance register. No tests below have been
performed or confirmed by maintainers in this change. Do not substitute offline
routing simulation or a public DNS leak page for packet-path evidence.

## Candidate identity (fill these fields with real observations)
- Observed UTC/local test date, tester and sanitized evidence link: **NOT_RECORDED**
- Profile: `beta/LoonKit.lcf`; beta commit `b071bfd9d569cb40287a49c95882523cc0909991` (initial test candidate; record the **actual imported** beta SHA if branch advances)
- Profile SHA-256: `4abdad9e0542a4f84493b63efe3a18ec91eb61b4c35f9cf26a76d37524d52d75`
- Pinned overlays: `26a24c86b58b133b2d094956f0f615680275a1b0`
- Device/iOS/Loon Build (minimum intended 3.5.1/983): **NOT_RECORDED**
- Wi-Fi/cellular/operator, IPv4/IPv6, node protocol/UDP support and node region: **NOT_RECORDED**
- DNS: AliDNS `https://dns.alidns.com/dns-query` plus ordinary entries 223.5.5.5/223.6.6.6. Loon App encrypted-DNS failure fallback (on/off): **NOT_RECORDED**
- Local AdBlock remote subscriptions on/off, other plugins/filter sources: **NOT_RECORDED**
- Source import and resource-refresh integrity result: **NOT_TESTED**

## Minimum real-device scenario matrix

| Scenario | Expected policy/functional outcome | Status | Sanitized evidence |
| --- | --- | --- | --- |
| First import, 34 remote lists, plugin and icons | No missing resources, no hidden fallback to mutable rules | NOT_TESTED | — |
| Clear cache, cold-start, reconnect and subscription refresh | Deterministic routing after recovery | NOT_TESTED | — |
| Home Wi-Fi vs cellular, IPv4 and IPv6 | No unexpected direct/DNS fallback | NOT_TESTED | — |
| AliDNS DoH reachable on proxy/direct links | Log the actual query resolver/path | NOT_TESTED | — |
| Block DoH, ordinary fallback disabled in Loon UI | Fail closed or explicitly document leaks/failure | NOT_TESTED | — |
| DoH outage with UI fallback enabled (control only) | Identify any unencrypted DNS requests | NOT_TESTED | — |
| Node DNS/bootstrap failure; node outage; UDP unsupported | No silently invented resolver guarantees | NOT_TESTED | — |
| Steam login/store/community and global content | Steam policy, functional playback/download | NOT_TESTED | — |
| Steam exact China CDN candidates and download | Direct only where proven appropriate; successful download | NOT_TESTED | — |
| AI ChatGPT, Gemini, Claude, GitHub Copilot, NotebookLM | Login/API/streaming/attachment flows and service ownership | NOT_TESTED | — |
| Microsoft telemetry and Facebook pixel/analytics | Identify actual first matching rule, app health preserved | NOT_TESTED | — |
| AdBlock on; Spotify analytics and playback | Block selected tracking without breaking auth/playback | NOT_TESTED | — |
| Both `Our-AdBlock` and `Beta-LocalAdBlock` disabled | Previously blocked domains follow original service policy | NOT_TESTED | — |
| Apple push, system update, iCloud, App Store, certificate OCSP | Sign-in, update, push and checks remain functional | NOT_TESTED | — |
| WeChat and international WeChat; mainland payment/map/login | Regions and login/payment redirects correct | NOT_TESTED | — |
| Captchas, 2FA, account validation and payment redirects | No critical feature misclassification | NOT_TESTED | — |
| Media representative playback and social app media upload | Policy works beyond page loading | NOT_TESTED | — |
| Performance baseline A/B using same conditions | Latency/errors/DNS duration/resource/battery measurements | NOT_MEASURED | — |

All test evidence must omit raw HAR URLs, query parameters, credentials, personal
IP addresses, specific node names and DNS private endpoint identifiers. Note
failure rates and timing only if *actually measured*. A checkbox or a "site
loads" screenshot alone cannot establish DNS privacy.

## Loon vs NovaXNS filter isolation

NovaXNS integration is **not enabled in this beta**, at user request. Cloud
toggle and Mask+/ECS tests are therefore **NOT_APPLICABLE** here, not passed.
A future independently reviewed NovaXNS beta may evaluate: Loon-only,
NovaXNS-only, both enabled, both disabled. Do not claim four-way comparison
for this AliDNS candidate.

## Promotion gate

- GitHub Actions: candidate SHA and exact assets must pass all production and beta checks.
- Finish first **7 days of device observation starting at a recorded successful installation**, then verify the complete matrix. Time alone never substitutes for test coverage.
- No unresolved serious DNS bypass, privacy violation, login/payment/system breakage, or high-risk source conflict.
- Record rollback to verified main v6.5.4, then open separate beta → main PR. Re-pin only through a reviewed build.
- Until every requirement holds, status stays **BETA_PENDING_DEVICE_ACCEPTANCE**. No stable promotion or historical cleanup.
