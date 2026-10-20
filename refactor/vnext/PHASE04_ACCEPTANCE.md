# Phase 04 engineering acceptance — 2026-10-20

- ENGINEERING_STATUS: SUCCESS (offline candidate implementation).
- RELEASE_READINESS: READY_FOR_NEXT_STAGE (for stage 05 tests; NOT production-ready).
- Runtime: NOT VERIFIED. No physical device DNS/TUN/ASN, IPv4/IPv6 or node-unlock results are claimed.
- Branch refactor/loonkit-vnext only; main is untouched.
- Starting commit: b982110a189b41b42e8562f7d10226071b0b2432
- Generated candidate commit: 2088025a0b2002ecce60ed29b28a656b6b075575
- Successful complete CI: https://github.com/YohakuSama/loonkit/actions/runs/39378725132

## Inputs and outputs

Build: python3 scripts/vnext_rule_engine.py
Verify: python3 scripts/vnext_rule_engine.py --check

Reads immutable published rules/generated/*.list snapshots, not live upstream feeds.
87 historical upstream source records retained; 26 selected group snapshots active, seven suspended.
This is not proof of 26 recovered original upstream providers. Provenance records snapshot file/line
and only POSSIBLE upstream source IDs. Candidate lists and config live entirely under refactor/vnext/.

Original count: 206,488 group snapshot predicates + 17 ProxyProtect = 206,505.
Candidate: 197,842. Net removal: 8,663 (4.2%).

## Concrete behavior changes

- ChinaDirect 123,008 => 114,889. Nine unsafe keywords quarantined; one narrowed (.tmall.com -> suffix).
  46 ambiguous one-label suffixes excluded; .cn retained. 8,061 overbroad IP ranges isolated.
- AdBlock 77,213 => 76,895. 322 shared service rules isolated. Four advertising root suffixes
  assigned to AdBlock; AdBlock remains selectable REJECT/DIRECT.
- Seven IP-ASN entries amended to include no-resolve.
- Independent ProxyProtect removed. No 17-rule diagnostic proxy whitelist copied.
- Spotify, Twitch, Abema, BBC, Line, Reddit, Linkedin subscriptions removed from candidate
  but their user-facing policy groups remain. Missing routes rely on Final: DIRECT choice may
  direct traffic that was previously matched to a service policy.
- Candidate subscription order starts with AdBlock; prior fixed cross-group exact dedup logic removed.
- Original [General] DNS, DoH, IPv4, IPv6, TUN and proxy group selections byte-equivalent.

## Detailed reports

- reports/provenance.tsv: retained rule and origin snapshot file and line.
- reports/removed_or_modified.jsonl: old rule/group/line, reason, replacement and impact.
- reports/ownership_changes.jsonl: 8,667 changed predicate/group mappings (includes 17 retired ProxyProtect entries).
- reports/direct_changes.jsonl; adblock_changes.jsonl; ip_no_resolve_changes.jsonl.
- reports/proxyprotect_impact.jsonl: each of 17 retired rules has file, line and fallback impact.
- reports/domain_parent_child_conflicts.jsonl: 7,197 cross-policy ancestry cases.
- reports/domain_keyword_risks.jsonl: 39 keywords needing scope review.
- reports/ip_network_overlaps.jsonl: 64 nested IP network cross-group cases.
- reports/added.jsonl; diff_summary.json.
- risk_dispositions.phase04.json: fixed, mitigated, isolated and release-blocking risks.

## Stage 05 blockers

No real DNS, Loon matching, shared CDN, purchase, login or region-unlock testing occurred.
Static simulator supports ONLY domain matches and the defined local/remote ordering approximation;
it does NOT cover resolved IPs, ASN lookup, system bypass, UA, plugins or Loon app runtime.
Large IP exclusions may break domestic IPv4/IPv6 service routes; inspect before publishing.
Historic source attribution is incomplete and must not be represented as upstream-proven.

Release gate remains closed. Do not merge or point main subscriptions to the candidate.
