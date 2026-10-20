# 87-source decision review

Machine source of truth: `refactor/vnext/source_decisions.json`, derived from `rules/sources.json`, `audits/phase-02/data/source_inventory.json`, `baselines/legacy/sources.json` and `published_file_inventory.json`. One row for **every exact source ID**, with 16 required dimensions, risk IDs and provenance flags. `sources.candidate.json` embeds the unchanged source object inside an explicitly non-runtime review wrapper.

| Recommendation | Count | Decision strength |
| --- | ---: | --- |
| KEEP_CORE | 4 | AppleOTA, SteamCN, ChinaDirect's two historical URL-backed inputs: provisional retain |
| KEEP_SPECIALIZED | 22 | Existing historical platform/region inputs: provisional retain and preserve selectors |
| CONSOLIDATE | 9 | Stage-02 zero incremental first-owner credit, NOT safe deletion |
| OPTIONAL | 0 | Insufficient positive evidence to reclassify |
| REMOVE_CANDIDATE | 0 | No immutable post-filter attribution/business parity proof |
| DEFER | 52 | Stage-02 INVESTIGATE; keep unresolved rather than manufacture a decision |

**No removal is approved.** The nine consolidation reviews are `local-facebook`, `local-dazn`, `local-hbo`, `local-animecrazy`, `local-microsoft`, `v2-netflix`, `v2-bilibili-cdn`, `v2-linkedin`, `v2-bilibili-game`. Zero first-owner credit before pruning is order-dependent; it cannot establish lossless absence after pruning or runtime behavior.

Per-source `published_rule_contribution.individual` and `irreplaceable_rule_contribution` are **UNKNOWN**, even when a group total and prepruning staged unique credit exist. `associated_risk_ids` are explicitly **group-level exposures, not proven source origin**. Unknown local legacy membership is marked UNVERIFIED. Historical remote bodies are unavailable; a current upstream license reference is not source-item provenance. Removal or transfer to FINAL requires pinned upstream contents, a full lineage graph, verified business requirements, region-specific route fixtures, and maintainer approval.

No numeric target for reducing 87 inputs is imposed. No sources change active state in this phase.
