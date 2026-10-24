# Beta v6.5.5-beta.3 decision and conflict ledger

Last edited 2026-10-24. This records repository facts and predicted routes, NOT device results.

## Effective rule precedence

Loon's documented sources are **local rules → plugin rules → remote rule
subscriptions**. Rules within subscriptions are evaluated according to Loon's
rule priority/ordering; do not infer a "continue matching" action that Loon
does not support. In this candidate, local AI exact exceptions remain local;
AdBlock rules moved out of local into explicit remote subscription resources.
The active diagnostic plugin has no REJECT/filter rules (check again if user
installs additional plugins). The GeoIP and Final terms remain at the end
of [Rule]. The offline matcher tests model supported domain types only,
not actual DNS/IP-triggered matching or Fake IP behavior.

| Domain / route | Baseline conflict | Candidate prediction | Evidence category |
| --- | --- | --- | --- |
| `analytics.spotify.com` | local AdBlock may be assigned REJECT/DIRECT before Spotify | AdBlock on; Spotify when both filter resources disabled | CI offline; device pending |
| `pixel.facebook.com` | local `facebook.com` root shadowed remote advertiser rule | Not locally shadowed; exact remote result needs individual source inspection | Static rule-order check; device pending |
| `telemetry.microsoft.com` | local `microsoft.com` root shadowed remote matcher | Not locally shadowed; eventual remote rule must be examined | Static conflict check; device pending |
| `events.data.microsoft.com` | local Microsoft root | Local root removed, remote rules retain ownership | Static conflict check; device pending |
| `copilot.microsoft.com` | AI exact before Microsoft owner | Local `DOMAIN` → AI preserved | CI offline |
| `store.steampowered.com` | Remote Steam | Steam | CI offline |
| `cm.steampowered.com` | Frozen broad SteamCN DIRECT | Steam overlay before frozen Steam | CI offline |
| `example.steamcontent.com` | Frozen broad SteamCN DIRECT | Steam overlay | CI offline |
| `dl.steam.ksyna.com` | SteamCN direct candidate | Beta SteamCN DIRECT candidate remains; actual CDN geography unverified | CI offline, device pending |
| unknown foreign domain | Final selector | Final selector (by domain matching only) | CI offline |
| IP literal with geolocation | GEOIP CN no-resolve, then Final | Unchanged, subject to Loon runtime matching | Official semantics + device pending |

## Key scope decisions

1. **Advertising**: 26 previously local rules moved into `Beta-LocalAdBlock`, with existing `Our-AdBlock` first. Selecting **DIRECT** inside AdBlock does not skip filtering and would override service selection. Turn off *both remote* AdBlock subscriptions in Loon instead (two manual switches). A user's other installed plugins, DNS host mappings and NovaXNS cloud filter may remain effective independently.
2. **Microsoft/Facebook**: remove broad local roots on beta only; original immutable remote Microsoft/Facebook lists are still present. Never indiscriminately REJECT shared login/OCSP/identity hosts. `pixel.facebook.com` and `telemetry.microsoft.com` require effective-rule logging before concluding they are blocked.
3. **Steam**: four global families leave SteamCN direct and are now Steam policy; 13 SteamCN exact/owned China candidates remain for device review. Original frozen source still contains many overlapping Steam entries: use effective-match tests, not raw deduplication, before removing any other rule.
4. **AI**: remove keyword `colab`, `developerprofiles`, `generativelanguage` from beta AI subscription. Retain the known `generativelanguage.googleapis.com` suffix and exact `copilot.microsoft.com`; add exact Colab / developer profile hosts. Shared public Cloud APIs and LiveKit are not categorically AI-owned.
5. **Domestic**: frozen ChinaDirect is intentionally untouched pending specific audits of `.cn`, `wechat.com`, UA, wide CIDR and unknown IP ownership; `GEOIP,CN,DIRECT,no-resolve` never promises all unknown mainland hostnames are direct. No evidence for default-disabling IPv6/UDP.
6. **Apple**: OTA, certificate and push exceptions are unchanged pending real-device evidence. The `real-ip` setting changes resolution behavior, not route `DIRECT`.
7. **DNS**: AliDNS is unchanged, per user. Encrypted transport does not establish resolver anonymity, and Loon UI settings may enable UDP fallback under DoH failure. Verify actual packet path. Node bootstrap vs business target DNS are different.

## Source-update state

The weekly read-only upstream review on main remains operational. On beta,
`beta-upstream-candidate.yml` can run after code changes or manually. It
produces actual 26-group proposed changes plus full source evidence and checks
upstream integrity. A green candidate job **does not write beta PRs or update
runtime rules**. Low-risk automatic beta PR and release promotion remain
pending explicit trusted workflow design and mandatory gates. No fake success
status should be assigned here.

## Promotion and rollback

- Stable: `main/LoonKit.lcf` at verified prior commit `87ba3f50e80ba90212a0eeba7df223949f50e32b`.
- Beta: `beta/LoonKit.lcf` through branch `beta`. For exact reproduction use the beta commit and manifest, not a moving link.
- Roll back Loon by reimporting existing verified stable entry, checking node
  and app-specific settings. Do not force-push or remove pinned historical resources.

## v6.5.5-beta.2 SNI/IP target experiment

- Added only `sni-sniffing = true` to the beta's `[General]` based on the Loon-maintained 2026-09-11 syntax. Main remains unchanged.
- Intended benefit: for TLS connections addressed to a literal IP, available SNI can provide the hostname needed to select a service rule rather than falling directly to IP/Final.
- Conditions: visible SNI, supported TLS type and Loon's runtime interpretation. No claim for ECH, QUIC, UDP, or generic TLS with hidden names; does not change the AliDNS resolver or `no-resolve` semantics.
- New risk: IP-targeted traffic with SNI may match a new rule, including REJECT; log effective match and compare with earlier beta on-device. Roll back to previous beta.1 commit if critical false-positives appear.

## v6.5.5-beta.3 audited ChinaDirect delta

- Excluded `DOMAIN-SUFFIX,cn` and 59 USER-AGENT items from the pinned ChinaDirect only in beta; all other 114,777 entries are retained in the previous order. This removes two **classes of unproven geographic inference**, not a statement about app origin.
- `api.weixin.qq.com` remains explicitly domestic through `qq.com`. Broader `wechat.com`, `wechatapp.com` still demand real dependency/location evidence; no blanket overseas WeChat rewrite is claimed.
- The complete explicit diff can be reconstructed from [domestic decisions](../rules/beta/domestic_decisions.json), the old pinned release and new [ChinaDirect beta rule](../rules/beta/v6.5.5-beta.3/ChinaDirect.list). SHA: `bdeafed6ce861f1f72e1f891c798257687123a8f29867ae4e7a89b007001b68a`.
- AppleOTA system check and update routes unchanged; no claim of narrower Apple region routing without field results.
