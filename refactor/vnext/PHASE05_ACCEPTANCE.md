# LoonKit vNext — Phase 05 engineering acceptance

Date: 2026-10-20. Branch: `refactor/loonkit-vnext`.
Starting remote HEAD: `e8280fa589c8f647f46c092a064627f34e91a1b9`.
Static validation code HEAD: `6b32b48e564ecf9bdc45639d46146b6213476d2b`.
Scope: candidate, source tooling, validation and CI only. No production release or merge.

## Status

| Gate | Result |
|---|---|
| ENGINEERING_STATUS | SUCCESS for delivered offline/static scope |
| STATIC_VALIDATION | PASS |
| DEVICE_VALIDATION | NOT_EXECUTED |
| PRODUCTION_READINESS | NOT_READY |
| Formal production publication | NOT_PERFORMED |

Static engineering passing does not approve main integration or production subscriptions.

## Reproducible commands

```sh
python3 scripts/vnext_source_lock.py --check
python3 scripts/vnext_rule_engine.py --check
python3 scripts/vnext_conflict_resolver.py --check
python3 scripts/vnext_phase05_report.py --check
python3 -m unittest discover -s tests -p test_phase05_validation.py -v
python3 -m unittest discover -s tests -p test_phase04_vnext.py -v
# Stage 04 read-only CI additionally runs all Python, Node and baseline checks.
python3 scripts/validate_device_results.py validation/phase-05/RESULT_TEMPLATE.json
```

Last tested Phase 05 33/33 offline tests: https://github.com/YohakuSama/loonkit/actions/runs/39390242713
Stage 04 full CI: https://github.com/YohakuSama/loonkit/actions/runs/39390029510
Stage 03 previous applicable CI: https://github.com/YohakuSama/loonkit/actions/runs/39390029504

## 1. Source integrity

`scripts/vnext_source_lock.py` checks **44 immutable frozen file attestations** against both Git blob SHA-1 and SHA256. `refactor/vnext/sources.lock.json` separately lists **87 historic source IDs** (including locally retained inputs). There are **zero newly pinned original external raw feeds** currently enabled. Frozen merged snapshots must never be represented as 87 reconstructed original upstreams. Old original upstream source lines remain historically unrecoverable. The stage04 report separately records **65 local source-to-rule mappings**.

New potential raw feeds require pinned 40-character Git commit, original URL, encoding, policy, path, SHA256 and original blob hash. `scripts/vnext_raw_trace.py` implements an **inactive preview** with raw file / original line -> normalize -> modify/isolate -> dedup -> output offset. Its test fixtures prove the lifecycle; **no raw source is activated or published** by the preview. The candidate compiler refuses any unsupported active raw input.

Machine evidence: `reports/source_integrity.json`, `reports/source_provenance.jsonl`, `sources.lock.json`.

## 2. Domain overlap disposition

7,350 of 7,350 original parent-child cross-policy observations are classified and committed to eight numbered JSONL shards, 950 rows each except the last 700. Each contains stable ID, source snapshot file/line, parent/child matching rules and groups, overlap witness, effective policy, risk and status. The original `DOMAIN-SUFFIX,cn` accounts for **3,884** observations.

| Classification | Observations |
|---|---:|
| ADBLOCK_OVERLAP | 6,821 |
| DIRECT_OVERLAP | 447 |
| SAME_EFFECT_REDUNDANCY | 19 |
| SHARED_CDN | 1 |
| SHARED_INFRASTRUCTURE | 2 |
| UNVERIFIED_RUNTIME_PRECEDENCE | 60 |
| **Total** | **7,350** |

19 same-effective-policy DIRECT overlaps are statically acceptable. **7,331 cross-policy observations remain marked REQUIRES_RUNTIME_TEST**; these are *observations*, not automatically 7,331 independent material misroutes. Ownership cannot be inferred from strings alone. No changes were made to these 7,350 remote rule predicates without supporting evidence. Their 8 committed disposition shards and summary are validated byte-for-byte on CI.

Machine evidence: `reports/conflict_dispositions.part01.jsonl` ... `part08.jsonl`, `reports/conflict_summary.phase05.json`. Do not report 7,350 repaired or zero residual risks.

## 3. Actual policy quality and candidate modifications

Stage04 and stage05 remote generated predicate-group totals are both **197,765**; ChinaDirect stays **114,837**, AdBlock **76,895**. Existing candidate filtering already removed broad ChinaDirect keyword matches, questionable wide IP ranges and specified shared AdBlock services; this stage does not claim additional ChinaDirect list deletions.

Seven previously disconnected overseas groups gained **14 scoped first-party local rules** to restore actual user selector reachability for Spotify, Twitch, Abema, BBC, Line, Reddit and Linkedin. These do not rebuild the full historic subscription, and missing auxiliary endpoints and geo-unlock must be tested.

During testing, a newly introduced local-vs-subscription precedence regression was identified: local overseas roots would shadow **26 preexisting precise AdBlock rules** (examples: `pixel.reddit.com`, `ads.linkedin.com`, `analytics.spotify.com`). The candidate now places **26 explicitly scoped AdBlock rules before those 14 overseas service roots**. The strategy remains `AdBlock = select,REJECT,DIRECT`; the static simulator and tests cover both selectable effects. This is a **candidate-only actual repair**, not merely a risk record.

Remote group count is unchanged; there are **40 additional inline candidate predicates** compared with stage04 (14 service + 26 AdBlock protection). No user-facing strategy group was removed.

Machine evidence: `reports/phase05_diff.json`, `reports/routing_regression.json`, generated candidate `.lcf`.

## 4. Automated quality gates and device acceptance

41 non-random business fixtures (stage04: 34) are exercised in **328 AdBlock×Final static state scenarios**, each explicitly labeled `DOMAIN_ONLY_SIMULATOR_NOT_LOON`. Original stage04 fixture assertions are frozen separately in `business_regression_cases.phase04.snapshot.json`, not mislabeled as historic true Loon traces. Phase05 has **33 independent passing Python tests** for source lock, raw line trace, domain suffix conflicts, selector compatibility, false positive brand matching, AdBlock priority, IPv4/IPv6 boundary tests, ASN normalization, GEOIP/FINAL, and privacy/evidence gates.

Device package: `validation/phase-05` README, test plan, DNS/routing/AdBlock/IPv6 matrices, redaction requirements, NOT_EXECUTED template. `scripts/validate_device_results.py` validates observation evidence, rejects common IP and secret leaks, demands consistent comparison conditions and never automatically records PASS. `scripts/vnext_pin_candidate.py` creates immutable-commit rule URLs **in a separate private test config**, without modifying live subscriptions.

GitHub Actions Phase04 was changed from auto git add/commit/push (`contents:write`) to readonly candidate `--check` (`contents:read`), with checkout credentials disabled. Phase05 CI likewise checks source lock, committed overlap shards, generated source integrity and regression reports, candidate generator deterministic equality and clean Git working tree. Neither workflow changes main, pushes, merges or releases.

## 5. Remaining release gates

- Historical upstream feed-by-feed original line ancestry cannot be fully restored from merged snapshots. This limitation is documented rather than concealed.
- 7,331 non-equivalent domain overlaps require representative real-client precedence/service tests; remaining unclear shared CDN/authentication/payment ownership cannot be accepted automatically.
- LIVE payment/authentication, DNS local vs proxy remote resolver, real egress, client IPv4/IPv6, ASN, GEOIP, FINAL and no-resolve behavior remain NOT_EXECUTED.
- Seven restored overseas selectors have minimum domain coverage, **not full auxiliary CDN or region-unlock certification**.
- Final=Proxy, Auto, Fallback, DIRECT and AdBlock=REJECT, DIRECT real-device states must be tested before production approval.
- The privacy scrubber is defense-in-depth only. Maintainer must manually inspect raw/redacted evidence before publication.
- No production user impact or fully safe DNS behavior is claimed based on offline checks.

Do not initiate stage06, publish or merge as part of this report.
