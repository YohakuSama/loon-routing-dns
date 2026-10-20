# LoonKit immutable routing baselines — Phase 01

Schema v1; all sources pinned to full Git commit IDs. No DNS/TUN settings, main branch, active config, rule files, plugin or proxy account was modified. Legacy `.lcf` fully restored from Git while upstream historical remote content is **HISTORICAL_CONTENT_UNAVAILABLE**.

- `legacy/manifest.json`: verified historical config commit and SHA256.
- `legacy/sources.json`: 28 ordered historical subscription references, 66 local rules, policy groups.
- `current/manifest.json`: current commit, SHA256 of config, catalogs, generator and CI.
- `current/rule-index.json`: 34 ordered rule files with SHA256, type distribution, policies and 87 enabled sources.
- `comparison.md`: initial static difference analysis.
- `ROLLBACK.md`: safe restoration.

Run `python3 -m unittest discover -s tests -p test_baseline_freeze.py -v` and `python3 scripts/compare_baselines.py` in a complete checkout. Git blob SHA-1 and SHA256 are distinct checksums. Published subscription `main` URLs are mutable even though these Git objects are fixed.
