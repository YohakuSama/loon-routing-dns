# Historical evidence

Git commit `6b1e091ee66bc601b5e166987b3a01e5b3a39329` exists; `Loon_Routing_DNS.lcf` Git blob `a5a3b3dbdbf3d3e6e2ae14ad812e301ae1cb2058`, SHA256 `0b583fe15bb1fe9d8c6f39471d3ef47141c906550fb9d350deadb87033179b29`.

The actual old `.lcf` contains 28 remote references, 66 ordered local rules and 33 policy-group definitions; both rule sections **match exactly** `rules/verified-routing-baseline.json` at `f19421933d2177f95e7537f1208d990b3094f1f4`. Its last two rules are `GEOIP,CN,DIRECT,no-resolve` and `FINAL,Final`.

**HISTORICAL_CONTENT_UNAVAILABLE** for byte-exact then-downloaded upstream files referenced through mutable `master` URLs. Do not replace old rules with modern upstream bytes. The old config contains settings, but does not certify old DNS behavior or guarantee correct historical DIRECT rules.
