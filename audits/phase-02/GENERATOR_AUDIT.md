# Generator review (read-only)

- normalize: CIDR and CIDR6 always gain no-resolve even if upstream did not set it; ASN does not.
- normalize: v2fly plain entries become suffix; dnsmasq records become suffix.
- normalize: URL-REGEX, regexp and selected unsupported entries are omitted or quarantined.
- generate: group dedup retains first owner; later source-origin details are dropped.
- prune_suffix_redundancy: removes descendants only inside one group.
- own_cross_group_duplicates: PUBLISH_ORDER first owner wins, with no business-domain adjudication.
- Published files are lexically sorted; no original source order is maintained.
- Shared-CDN ownership and AdBlock-vs-platform priority are not business-validated.
- The build report stores 100 examples for several conflict categories, not full prepublication records.
