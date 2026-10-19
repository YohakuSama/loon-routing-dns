# Pinned current-byte verification

Current commit: `f19421933d2177f95e7537f1208d990b3094f1f4`. Both current `.lcf` profiles have identical ordered `[Remote Rule]` and `[Rule]` sections. They have distinct DNS General sections, and both remain unchanged.

34 verified rule blobs = 33 generated files + one `ProxyProtect.list`. Each has SHA256, original git-blob SHA1, byte count, policy and rule-type counts in `rule-index.json`. All 33 generated counts match `rules/generated/audit.json`. 87 current sources are enabled; 4 entries are candidates. Builder version is represented by pinned Git commit/SHA256, not an invented release number. Live `main` URLs and client caches are not frozen.

These are static integrity results, not on-device DNS leakage tests.


## Existing test and automation inventory at the original main commit

Python tests:
- tests/test_composite_rules.py (generator normalization, guardrails and library behavior)
- tests/test_hybrid_profile.py (configuration and generated-profile invariants)
- tests/test_import_preflight.py
- tests/test_repository_hygiene.py
- tests/test_dns_privacy_profile.py

JavaScript tests:
- tests/test_current_plugin.js
- tests/test_network_diagnostics.js
- tests/test_node_copy.js

Existing automated workflows:
- .github/workflows/loon-ci.yml (main/PR CI, scheduled CI, Python and Node checks)
- .github/workflows/composite-rules.yml (offline regression, staged previews and scheduled source refresh; no automatic production merge)

Other static validations: scripts/validate_repo.py and scripts/build-appstore-icons.py --check-config.

The phase-01 branch adds a separate .github/workflows/baseline-freeze.yml without modifying these existing workflows.

## Existing brittle assertions to review in later phases

- tests/test_composite_rules.py asserts 87 enabled inputs, 10 local inputs, 33 generated sizes, 34 active remote subscriptions and some fixed quarantine/removal counts.
- tests/test_hybrid_profile.py asserts 33 strategy groups, 34 remote subscriptions, 87 inputs and release-specific profile/plugin URL facts.
- These assertions are legitimate release-specific regressions at this pinned commit but must not silently become universal architecture requirements for future refactors.
- This phase does not edit these tests or relax any checks.

## Additional read-only CI observation

On 2026-10-19, the existing scheduled composite-rules run 39218922715 at the pinned main SHA had its offline rule-builder regression job pass, while its separate draft-PR-creation step failed. This is not evidence of failure in generated routing contents or of a DNS leak, and it is not caused by the stage-01 branch.
