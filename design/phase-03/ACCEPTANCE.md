# Phase 03 acceptance and integrity contract

## Precondition
Entry branch HEAD `d1fa4082582bb8c1d659f820e56b05511aaafce2` was inspected. Stage 02 still PARTIAL: 87 cataloged, post-filter origin incomplete, 52 INVESTIGATE, nine MERGE not removal proof, 70 OPEN Phase 02 risk records. Terminal Stage 03 acceptance **PARTIAL**, regardless of CI, while core ownership/routing issues remain.

## Produced artifacts
- 13 design documents (this directory).
- Five review-only machine-readable JSON files (`refactor/vnext`) with 87 source decisions, 34 current subscription groups, 70 carryovers, 57 DIRECT rule reviews, seven ASN reviews, four AdBlock anchors.
- Standalone `tests/test_phase03_architecture.py` and branch-only independent `.github/workflows/phase-03-architecture.yml`.

## Executable acceptance
```sh
python3 -m unittest discover -s tests -p 'test_baseline_freeze.py' -v
python3 scripts/compare_baselines.py --markdown-out /tmp/phase03-baseline.md --json-out /tmp/phase03-baseline.json
python3 -m unittest discover -s tests -p 'test_phase02_audit.py' -v
python3 scripts/audit_rule_conflicts.py --output audits/phase-02 --check
python3 -m unittest discover -s tests -p 'test_phase03_architecture.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_repo.py
python3 scripts/build-appstore-icons.py --check-config
node tests/test_node_copy.js
node tests/test_network_diagnostics.js
node tests/test_current_plugin.js
```

All frozen SHA256 in `baselines/current/manifest.json`, `baselines/current/rule-index.json` and git blob identities must stay equal. The new workflow runs the same offline Python/JS regressions without mutating existing CI/publish behavior. Full project remote-resource validation is subject to independent reachability; report unknown instead of claiming PASS.

## Release decision
**PARTIAL**, not SUCCESS. NO source deletion, rule change, config change, DNS/TUN change, Final option change, ProxyProtect retirement, main update or automatic merge. Blocked: per-source final attribution, business-specific right-to-remove, domain/IP match decisions requiring real Loon tests, AdBlock correctness, full ProxyProtect parity. Stage 04 is *not started*. Maintaining a review design despite these blockers is not an admission that the production implementation has changed.
