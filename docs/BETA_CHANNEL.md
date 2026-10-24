# LoonKit v6.5.5-beta.1 · isolated beta
**Status: pending CI and actual Loon device verification. Do not merge to main yet.**

## Entry and pinned assets
- Stable: https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf (v6.5.4; unchanged)
- Beta after beta branch merges this PR: https://raw.githubusercontent.com/YohakuSama/loonkit/beta/beta/LoonKit.lcf
- The entry follows `beta`; all ten beta overlay resources are pinned to commit `26a24c86b58b133b2d094956f0f615680275a1b0`.
- Existing 24 production rule subscriptions, diagnostics plugin, icons and scripts keep their unchanged immutable refs.
- Exact content hashes and matcher counts: [beta_manifest.json](../build/beta_manifest.json).
- The policy generator is `python3 scripts/beta_assets.py --check`. All ten overlays reproduce from the single [policy_overrides.json](../rules/beta/policy_overrides.json).
- Channel config checksum: `4abdad9e0542a4f84493b63efe3a18ec91eb61b4c35f9cf26a76d37524d52d75`.
- Resource source commit: `26a24c86b58b133b2d094956f0f615680275a1b0`.
- Minimum documented features: Loon 3.2.5 (789) for `hijack-dns`; linked plugin declares 3.5.1 (983). **Use Loon 3.5.1 (983) or newer for beta**, and confirm compatibility on device.

## Changes and decision evidence
- Baseline: main commit `87ba3f50e80ba90212a0eeba7df223949f50e32b`, v6.5.4.
- AliDNS untouched: UDP servers `223.5.5.5,223.6.6.6` and DoH `https://dns.alidns.com/dns-query`.
- The old frozen SteamCN subscription is **replaced only in beta** with 13 conservative CDN/China candidates. Four broad global suffixes (`cm.steampowered.com`, `steamcontent.com`, `steamserver.net`, `steamusercontent.com`) now belong to Steam. The other 13 still require geographic validation.
- 26 previously local AdBlock matchers are migrated to a dedicated `Beta-LocalAdBlock` subscription. Existing frozen `Our-AdBlock` stays first. Removed local Microsoft/Facebook roots are already covered by the frozen remote owner groups; their local priority no longer shadows the earlier remote AdBlock matcher.
- Six supplementary service groups (Spotify, Twitch, BBC, Line, Reddit, Linkedin) migrate from local to pinned remote lists, preserving ownership when ad-block lists are disabled.
- AI/Copilot exact local exceptions remain ahead of remote Microsoft rules. The beta replaces the fixed AI list with a generated scoped copy: removes broad keywords `colab`, `developerprofiles`, `generativelanguage`, adds explicit Colab/developer-profile hosts and keeps the existing `generativelanguage.googleapis.com` suffix.
- Broad `.cn`, WeChat and historical user-agent rules in the giant frozen ChinaDirect source, Apple OTA, have **not** been modified. These remain explicit review work, not silently claimed fixed.
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
