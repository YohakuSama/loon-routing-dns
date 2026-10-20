# Phase 04 implementation specification (engineering handoff; no Stage 03 generator changes)

## 0. Release boundary / prerequisites
Refactor branch must retain bytewise `LoonKit.lcf`, `LoonKit.PrivacyDNS.lcf`, `rules/generated/*.list`, `rules/ProxyProtect.list`, `rules/sources.json`, `rules/active_profile.json`, and `scripts/build_composite_rules.py` until separately approved Stage 04. Phase 02 SOURCE_PROVENANCE_INCOMPLETE and RUNTIME_VERIFICATION_REQUIRED gates stay open. Do not edit DNS provider, DNS/TUN config or Final choices. Do not interpret the candidate JSON as a publishable source.

## 1. Candidate source schema
Consume `refactor/vnext/sources.candidate.json` (schema_version=3, `candidate_only=true`, `non_runtime=true`, `activation_allowed=false`) *only in a new isolated preview tool*. Each `sources[]` entry has `source_id`, `current_production_source` (unaltered original), `design_decision`, `original_group`, `group_target`, `enabled_in_production`, `candidate_activation`, `legacy_compatibility`, `replacement_policy`, `regression_cases`, `linked_risk_ids`. References must resolve 1:1 to `rules/sources.json`; never silently skip a source. Unrecognized schema versions fail closed.

## 2. Candidate profile schema
`refactor/vnext/active_profile.candidate.json` has `existing_order_immutable`, `proposed_order_for_review`, `groups[]`, `final`, `local_terminal_rules`, and `runtime_questions`. Each group needs `name`, `current_policy`, `business_definition`, `logical_layer`, `logical_priority`, `current_subscription_order`, `candidate_subscription_order`, `order_change_approved`, `shared_dependencies_allowed`, `conflict_resolution`, `legacy_compatibility`. Only an approved future activation may add groups/change order. Final must remain `FINAL,Final` with the current 4 choices.

## 3. Proposed isolated module API
Create **new** (not mutate existing until separate review) `scripts/vnext_rule_engine.py`:
```python
def load_candidate(path, production_path) -> CandidateCatalog: ...
def normalize_rule(raw: str, source_id: str, revision_sha: str, line_no: int,
                   source_format: str, include_chain: tuple[str, ...]) -> NormalizedRule | Quarantine: ...
def collect_conflicts(rules: list[NormalizedRule], asn_db_version: str | None) -> list[Conflict]: ...
def decide_conflict(conflict: Conflict, signed_decisions: dict[str, "Decision"]) -> Decision | Unresolved: ...
def preview_emit(rules: list[NormalizedRule], decisions: list["Decision"], out_dir: Path) -> Manifest: ...
def compare_routes(old_index: Path, preview_index: Path, fixtures: list["Fixture"]) -> DiffReport: ...
```
No network fetch without pinned immutable upstream revision and byte hash; no preview output beneath `rules/generated`. Store snapshot SHA-256, parser version, actor and source license metadata.

## 4. Normalization & provenance
Represent `rule_type, rule_value, normalized_options, policy, policy_group, source_id, source_url, upstream_commit, raw_sha256, raw_line, normalized_line, include_chain, transformation_steps, resulting_output_path/line`. Preserve original case-sensitive raw line but canonicalize match keys (lowercase IDNA host with label boundaries and trailing-dot normalization, CIDR canonical via ipaddress; validate IPv4 vs IPv6, ASN numerics and legal options). Never conflate `DOMAIN`, `DOMAIN-SUFFIX`, `DOMAIN-KEYWORD`. Reject/quarantine unknown Loon syntax, unsupported URL-REGEX and unproven new rule types with a reason; do not publish them by accident. Include chains must be cycle-checked and source-licensed.

## 5. Duplicate and policy conflict logic
Same exact canonical matcher and **provably same effective policy**: `AUTO_RESOLVABLE`, union source lineages, stable sorted output. Same syntax but different selectable policy group is NOT the same effect merely because groups temporarily resolve to one node. Different policy or matcher → `MANUAL_DECISION_REQUIRED`; uncertain Loon runtime matching or ASN database → `RUNTIME_VERIFICATION_REQUIRED`. Conflicts are immutable objects with ID=SHA256(canonical conflict tuple), original paths/lines, app/region expectations, supported witness and open risk ID. Default unknown conflict action `BLOCK_PREVIEW_ACTIVATION`; never arbitrate cross-policy matches by PUBLISH_ORDER.

## 6. Domain hierarchy and keywords
For DOMAIN and DOMAIN-SUFFIX use label-boundary matching; distinguish `example.com`, `api.example.com` and nonmatch `notexample.com`. For cross-group parent/child, keep both and request an annotated winner/selector scenario; do not prune. For DOMAIN-KEYWORD use literal substring witness with **negative counterexamples** outside intended business; new DIRECT keyword proposals fail preview promotion unless approved by evidence. Review the exact 10 keywords and 47 single-label suffixes in `policy_decisions.json/direct_rule_reviews`, preserving published file line provenance. `DOMAIN-SUFFIX,cn` must never be treated as a keyword or automatic whole-world China routing proof.

## 7. IP rules, ASN and no-resolve
Use Python `ipaddress` for IP-CIDR and IP-CIDR6 family-safe prefix normalization and overlap witnesses. Store no-resolve explicitly as boolean/flag and roundtrip it in candidate parser. IP-ASN requires pinned DB version and exact provenance; absent DB means no automatic ASN/CIDR ownership. Default proposal for IP-only candidates is no-resolve, but changing output requires target-specific hostname-miss and literal-IP runtime tests. Seven known ASN rules (AS132203, AS32934, AS211157, AS44907, AS59930, AS62014, AS62041) are only `change_approved=false` proposals. Preserve local GEOIP,CN,DIRECT,no-resolve and FINAL untouched.

## 8. AdBlock review interface
For `AdBlock` vs Google/X/AI/etc require `{conflict_id, action: BLOCK|ALLOW|SPECIAL_POLICY|DEFER, matched_business, app_context, region, expected_user_AdBlock_REJECT, expected_user_AdBlock_DIRECT, reviewer, evidence_links, test_ids, signed_at, expires_at}`. Block release if reviewer missing or REJECT/DIRECT functionality untested. Explicitly review admob.com, doubleclick.com, app-measurement.com, ads-twitter.com; never auto-REJECT telemetry, auth, attribution or payment.

## 9. DIRECT safe owner contract
Candidate DIRECT assignment requires `{hostname_or_cidr, business_owner, mainland_service_evidence, jurisdiction_restrictions, shared_infra_negative_tests, expected_proxy_default, review_id}`. If ambiguous, `DEFER` (and keep current publishing behavior during design). Prevent accidental direct inheritance through corporate identity, .cn suffix alone, shared IP-ASN or generic CDN. Export reasoned risk findings instead of growing diagnostic URL allowlists.

## 10. Human decision input (new `refactor/vnext/reviews/approved_decisions.json`, future only)
```json
{
  "schema_version": 1,
  "decisions": [{
    "conflict_id": "sha256-canonical-id",
    "resolution": "MANUAL_DECISION_REQUIRED",
    "selected_policy": null,
    "reason": "business owner not yet verified",
    "affected_source_line_ids": [],
    "witnesses": [],
    "user_policy_states": ["AdBlock=REJECT", "AdBlock=DIRECT", "Final=Proxy", "Final=DIRECT"],
    "test_case_ids": [],
    "reviewer": null,
    "approved_at": null,
    "immutable_evidence_sha256": null,
    "status": "OPEN"
  }]
}
```
No null/OPEN review can be treated as authorization. A future approved resolution must include non-null selected_policy, signed reviewer, immutable evidence reference and passing fixtures; engine never invents one.

## 11. Determinism and output manifest
Sort inputs by stable source_id + raw line location and normalized matcher (not fetch timing); fix locale, encoding UTF-8, LF newline, JSON sorted keys, no timestamps in content hash and no network-dependent default data. Emit preview into `build/vnext-preview/<sha>/` (gitignored in Stage 04), including per-rule ancestry and dropped-item reasons, source-count reconciliation, conflict decision table, SHA256 per output, stale-input errors. Two identical input snapshots must produce byte-identical candidate manifest; end-to-end previous published SHA must remain frozen until human review.

## 12. Compatibility / diff fixtures
Before any activation, compare current vs candidate effective policy for each platform, bank/payment/auth, CN Apple/Steam, AI Gemini/Copilot, country-specific streaming, Facebook/WhatsApp, shared CDN, IP IPv4/6 literals, hostname misses, AdBlock REJECT/DIRECT and Final Proxy/DIRECT/Auto/Fallback. If a service group changes exit choice, record its explicit compatibility impact and signed acceptance. Use real-device packet and Loon-match logs for ambiguous protocol/DNS semantics, and test rollback by restoring baseline.

## 13. Required automated suites
(1) normalized syntax/property cases; (2) idempotent canonicalization; (3) 87-source inventory + exact catalog bijection; (4) per-source provenance through all transforms; (5) same-policy dedup and cross-policy non-dedup; (6) prefix/suffix/keyword witnesses; (7) IPv4/6 and pinned ASN DB; (8) no-resolve flags; (9) selected AdBlock/Final semantics; (10) fixed risk register ID linkage; (11) deterministic preview hashes; (12) candidate isolation and protected-file SHA freeze; (13) legacy selectors and policy names; (14) shared CDN/payment/auth negative cases; (15) runtime questionnaire and owner signoff; (16) 17 ProxyProtect replacement parity fixtures.

## 14. CI and forbidden side effects
Separate Stage 04 preview workflow with contents:read, artifact upload only, no push, no write token, no PR auto-merge. Never consume candidate filenames from current `scripts/build_composite_rules.py` or active `.lcf` and do not rewrite existing production workflows in Phase 03. Freeze baseline SHA and branch HEAD to detect races. Publish changes **only** after explicit maintainer authorization in a subsequent phase; Stage 03 does not permit release.

## 15. Acceptance blockers / unresolved questions
Source-wise exact post-filter contribution for 87 inputs; 52 INVESTIGATE ownership; nine order-dependent zero contributors; absent historical upstream bodies; rule-stage behavior for mixed classes; IP-ASN/CIDR DB overlap; true node-protocol DNS path; seven ASN flags; 70 P02 risks; all 17 ProxyProtect migrations, especially Stripe. Stage 04 must not silently waive these.
