# LoonKit v6.5.5-beta.3 · isolated beta
**Status: beta CI verified on latest merged candidate; actual Loon device verification remains pending. Do not merge to main yet.**

## Entry and pinned assets
- Stable: https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf (v6.5.4; unchanged)
- Active beta channel (moving branch): https://raw.githubusercontent.com/YohakuSama/loonkit/beta/beta/LoonKit.lcf
- The entry follows `beta`; all ten beta overlay resources are pinned to commit `26a24c86b58b133b2d094956f0f615680275a1b0`.
- Existing 23 production rule subscriptions, diagnostics plugin, icons and scripts keep their unchanged immutable refs.
- Exact content hashes and matcher counts: [beta_manifest.json](../build/beta_manifest.json).
- The policy generator is `python3 scripts/beta_assets.py --check`. All ten overlays reproduce from the single [policy_overrides.json](../rules/beta/policy_overrides.json).
- Channel config checksum: `9bc445e6fdf0f93d7a2e9dac51a3ac83a23d92461b5c8055f1002f25d098a121`.
- Resource source commit: `26a24c86b58b133b2d094956f0f615680275a1b0`.
- Minimum documented features: Loon 3.2.5 (789) for `hijack-dns`; linked plugin declares 3.5.1 (983). **Use Loon 3.5.1 (983) or newer for beta**, and confirm compatibility on device.

## Changes and decision evidence
- Baseline: main commit `87ba3f50e80ba90212a0eeba7df223949f50e32b`, v6.5.4.
- AliDNS untouched: UDP servers `223.5.5.5,223.6.6.6` and DoH `https://dns.alidns.com/dns-query`.
- The old frozen SteamCN subscription is **replaced only in beta** with 13 conservative CDN/China candidates. Four broad global suffixes (`cm.steampowered.com`, `steamcontent.com`, `steamserver.net`, `steamusercontent.com`) now belong to Steam. The other 13 still require geographic validation.
- 26 previously local AdBlock matchers are migrated to a dedicated `Beta-LocalAdBlock` subscription. Existing frozen `Our-AdBlock` stays first. Removed local Microsoft/Facebook roots are already covered by the frozen remote owner groups; their local priority no longer shadows the earlier remote AdBlock matcher.
- Six supplementary service groups (Spotify, Twitch, BBC, Line, Reddit, Linkedin) migrate from local to pinned remote lists, preserving ownership when ad-block lists are disabled.
- AI/Copilot exact local exceptions remain ahead of remote Microsoft rules. The beta replaces the fixed AI list with a generated scoped copy: removes broad keywords `colab`, `developerprofiles`, `generativelanguage`, adds explicit Colab/developer-profile hosts and keeps the existing `generativelanguage.googleapis.com` suffix.
- Beta.3 removes the global `.cn` suffix and all 59 USER-AGENT direct matchers, retaining the other 114,777 ChinaDirect lines. Broad WeChat parents, some historical owner overlap and AppleOTA still require review.
- The published app-level `AdBlock = select,REJECT,DIRECT` choice remains for compatibility. **DIRECT is not a disable switch**: it forces direct connection and can leak routing intentions. To stop Loon ad filtering while retaining service routing, turn **off both** `Our-AdBlock` and `Beta-LocalAdBlock` in Remote Rule. This is a manual two-toggle mechanism; it must be confirmed on device. The diagnostics plugin contains no Loon REJECT rules; third-party user plugins must be audited separately. NovaXNS filtering is independent.
- `GEOIP,CN,DIRECT,no-resolve` and `FINAL,Final` remain; no assumption that unrecognized domestic domains are always direct.

## DNS privacy acceptance
- Official Loon docs: when both encrypted and ordinary DNS are present, encrypted is preferred; fallback to UDP is enabled by default. **In Loon App → DNS Servers, disable encrypted-DNS failure fallback to ordinary DNS** for a fail-closed test, then check actual packet/log paths. Config cannot prove that switch state.
- Test Loon DNS, proxy-node bootstrap vs target resolution, Wi-Fi/cellular and IPv4/IPv6, DoH outage and node outage. `hijack-dns = *:53` does not intercept all DoT, private DoH and TCP DNS. Do not claim zero leaks from a web leak-test alone.
- NovaXNS endpoint/tokens, cloud filtering, ECS and Mask+ settings are not used or committed. User requested AliDNS for now.

## Pending gates
1. Beta CI, manifest hashes and immutable GitHub Raw URLs green against the exact test commit.
2. Loon import plus traffic analysis: telemetry.microsoft.com, events.data.microsoft.com, pixel.facebook.com, analytics.spotify.com, copilot.microsoft.com; Apple update, login, cert checks; Steam global vs CDN; payments, login, push, captcha.
3. Four blocking combinations: Loon-only, NovaXNS-only, both on, both off **only if** NovaXNS is later configured. Currently AliDNS, so NovaXNS comparison is not applicable.
4. Document iOS, device, Loon Build, network, node protocol, DNS switches, failures and sanitized evidence. Minimum first observation window **7 days** after usable device test entry.
5. No beta→main promotion, release publication or cleanup before evidence and review.

## Recover
- Return to stable channel `https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf` and select your prior node/subscription.
- The previous main commit `87ba3f50e80ba90212a0eeba7df223949f50e32b` remains immutable.
- Do not change old pinned rule blobs. Open beta PRs must be reviewed; no forced history rewrite.

## Safe beta upstream proposals (2026-10-24)
The original `.github/workflows/rules-update.yml` remains the weekly default-branch read-only audit. Its `candidate/` directory is deliberately unchanged. It is **not** an upstream beta update and must not be described as such.

Beta now has `scripts/beta_upstream_candidate.py`, reusing `upstream_review.build_report()` rather than implementing an alternative parser. Execute:

```sh
python3 scripts/beta_upstream_candidate.py --version v6.5.6-beta.1 --output /tmp/loonkit-beta-upstream
```

Its `proposed-assets/` files contain actual newly fetched, normalized proposals instead of copies of the current 26 published lists. The artifact includes snapshots, v2fly includes, full diffs, provenance and risk review. Any invalid/empty/partial source results in retention of last valid baseline rules and a blocked publication status. Changed direct/IP/keyword/large-risk rules and removals require explicit review; the manifest **always** marks `publication_allowed=false` until a separate gated publication step exists.

The read-only beta workflow uploads a review artifact on relevant beta pushes. GitHub scheduled workflows run from the default branch, so **this workflow is not a working independent weekly beta scheduler** while the default branch is main. The existing Monday weekly read-only audit continues unchanged. Automatic creation of a beta PR after low-risk acceptance remains **not implemented**: a reviewed policy decision, immutable asset commit and verified beta config repinning must be added first, then the default-branch scheduler updated through the formal release gate. A green artifact job is not permission to publish any rules.

Never install the `proposed-assets/` outputs directly; they are review-only raw proposals, without pinned configuration URLs. Never delete pinned last-known-good or historical resources to make the artifact pass.

## Device test and decision evidence

- [Beta device acceptance matrix](BETA_DEVICE_MATRIX.md): all real-device checks still marked NOT_TESTED; contains required device metadata, DNS failures and 7-day observation.
- [Routing, AdBlock and source conflict ledger](BETA_DECISION_REGISTER.md): baseline vs beta ownership decisions, offline-test boundaries and unverified domains.

## Official Loon syntax reference (2026-09-11)

The [2026 syntax audit](SYNTAX_BASELINE_2026-09-11.md) compares the current Loon-maintained example and online manual with beta. It deliberately does not copy optional example settings or adjust AliDNS, the DNS privacy tradeoff or immutable resource URLs. CI includes a narrow syntax-baseline regression contract; **actual Loon Build and device behavior remain unverified**.

## v6.5.5-beta.3: optional 2026 capability under test

This profile now sets `sni-sniffing = true`. Loon's 2026 example documents this switch as a way to use available TLS SNI for domain-rule decisions on connections whose target is an IP. It is not an ad-block bypass, not a new resolver, and not a general ECH/QUIC name detector. It may affect IP-literal routing; compare real request routing against beta.1 for IP-literal HTTPS, encrypted/ECH and non-TLS/UDP control cases. If SNI is unavailable, normal IP/no-resolve/Final behavior should remain; **verify on device rather than claiming this as a test result**. The switch can be disabled in a personal local copy by deleting that line; a public rollback must use a reviewed candidate PR. All ten beta.1 rules remain pinned to the same immutable commit; this is a config-only beta.2 release. No changes to AliDNS, REJECT/UDP fallback, real-ip, or system routing.

## v6.5.5-beta.3 domestic scope reduction (frozen in 2f4980593843dbe28d4b983c309de6713913b8c9)

- Beta replaces only `Our-ChinaDirect` with a new 114,777-line generated, **content-addressed** `Beta-ChinaDirect-Scoped`. Exactly 60 from the historical 114,837 matchers are excluded: `DOMAIN-SUFFIX,cn` and 59 `USER-AGENT` rules. These rules can match a client name instead of the actual server, so they lack proof of mainland geography. The other 114,777 lines (including 4,443 IP/ASN rules) are preserved byte-for-byte in their original relative order.
- Other known mainland service suffixes remain direct; `api.weixin.qq.com` remains covered by `qq.com`. Unknown `.cn` domains can now be Final/Proxy if no more-specific route. This is deliberate; do not claim every mainland website will direct.
- Broad WeChat-related suffixes and some other service-owned historical ChinaDirect suffixes are **still quarantined for review, not silently removed**. The AppleOTA whitelist remains unchanged. This change needs import, route and payment/WeChat tests before stable promotion.
- Regeneration: `python3 scripts/beta_domestic_rules.py --check`; exact matcher decisions: [domestic_decisions.json](../rules/beta/domestic_decisions.json). The old immutable ChinaDirect and formal release remain intact.

## Effective source priority audit

The [offline trace documentation](BETA_EFFECTIVE_AUDIT.md) and `scripts/beta_effective_audit.py` test current local/remote/plugin sources with on/off advertising comparisons. The CI artifact is **synthetic**, not a real iOS/Loon capture; unresolved shared-Google infrastructure and WeChat root domains remain flagged.

## Promotion preflight gate

The [fail-closed beta promotion preflight](BETA_PROMOTION_GATE.md) and `scripts/beta_promotion_gate.py` reject missing/mismatched CI, a missing full device matrix, unresolved risk register and less than seven days of observation. CI tests only **synthetic fixtures** and proves the real device template is still blocked; it does not approve formal promotion.

## Upstream risk triage (review only)

The read-only [beta updater workflow](../.github/workflows/beta-upstream-candidate.yml) now runs [beta_upstream_triage.py](../scripts/beta_upstream_triage.py) after staged actual proposed rule snapshots. It archives an additional `RISK_TRIAGE.json` assigning source-failure, removals, broad IP/suffix, direct, advertising, shared infra and cross-policy changes to manual review. Only tightly bounded exact domain additions under approved routine service groups can be marked **draft PR eligible**. This classification does not create a PR, write rules, relax the source lock, authorize automated publication, or bypass seven-day/device gates. Full unattended beta PR creation remains unfinished and intentionally must not be represented as live.
