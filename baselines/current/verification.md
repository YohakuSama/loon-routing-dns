# Pinned current-byte verification

Current commit: `f19421933d2177f95e7537f1208d990b3094f1f4`. Both current `.lcf` profiles have identical ordered `[Remote Rule]` and `[Rule]` sections. They have distinct DNS General sections, and both remain unchanged.

34 verified rule blobs = 33 generated files + one `ProxyProtect.list`. Each has SHA256, original git-blob SHA1, byte count, policy and rule-type counts in `rule-index.json`. All 33 generated counts match `rules/generated/audit.json`. 87 current sources are enabled; 4 entries are candidates. Builder version is represented by pinned Git commit/SHA256, not an invented release number. Live `main` URLs and client caches are not frozen.

These are static integrity results, not on-device DNS leakage tests.
