# Policy overlap audit

- Published cross-policy suffix ancestry pairs: 7306.
- Cross-policy keyword-substring candidate pairs: 868.
- Cross-policy IP prefix overlaps: 168.
- DOMAIN and DOMAIN-SUFFIX are not identical matchers; suffix coverage respects label boundaries.
- IP-ASN to CIDR cannot be mapped without a pinned ASN database.
- Static overlaps do not establish which policy won on-device.
- See data/policy_conflicts.json for every pair and both file locations.
