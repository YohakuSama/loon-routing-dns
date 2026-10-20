# DNS-triggering rule paths — design only

Official documentation: https://nsloon.app/en/docs/Rule/ and https://nsloon.app/en/docs/Rule/ip_rule/ . For a hostname request with no domain-rule hit, Loon can resolve locally to test IP rules. `no-resolve` makes an IP-only rule eligible only where the destination is already an IP; it does **not** force arbitrary third-party DNS, in-app DoH/DoT, proxy transport DNS or every node protocol through the tunnel.

## IP matcher policy
- `IP-CIDR`: validate IPv4 CIDR syntax and trusted owner/region; default candidate no-resolve for IP-literal-only testing, subject to service requirements.
- `IP-CIDR6`: require IPv6-specific fixtures; no assumption that equivalent IPv4 rules cover IPv6.
- `IP-ASN`: pin ASN DB version, verify scope and any shared multi-tenant address ranges; propose no-resolve by default for active domain-avoidance but require device proof.
- `GEOIP,CN,DIRECT,no-resolve`: local terminal rule must **remain unchanged**; assess whether its no-resolve flag affects hostname misses in the observed app version. Default action not guaranteed just by GEOIP.
- `FINAL,Final`: after other matching, user-selected fallback, not DNS privacy guarantee.

## The seven ASN cases (published files not modified)
| Rule | File:line | Stage 04 investigation |
| --- | --- | --- |
| AS211157 | Telegram.list:32 | Proposal: no-resolve; validate Telegram IP-literal reachability |
| AS44907 | Telegram.list:33 | same |
| AS59930 | Telegram.list:34 | same |
| AS62014 | Telegram.list:35 | same |
| AS62041 | Telegram.list:36 | same |
| AS32934 | Facebook.list:471 | same; multi-service impact |
| AS132203 | ChinaDirect.list:110393 | same; potential non-mainland DIRECT |

All seven have Phase 02 risk IDs and `change_approved=false` in `policy_decisions.json/asn_no_resolve_reviews`. They are **not proven** to have caused BrowserLeaks observed resolver changes.

## Stage 04 differential verification
Freeze both `.lcf` DNS sections and TUN/IPv4/IPv6 settings. Run current vs candidate routing in separate on-device test profiles, same DNS provider, same network, same node choice. Capture Loon request detail/selected rule, OS-level DNS packets (UDP/TCP53 and TLS/HTTPS where observable), local DNS cache state, IPv4/IPv6 addresses, DNS through node protocol, app DoH and proxy remote resolution. Test (a) DOMAIN hit, (b) hostname miss, (c) IP literal, (d) same host A/AAAA, (e) AdBlock REJECT vs DIRECT, (f) Final DIRECT vs Proxy. Correlate sample IDs, clock and trace; report inconclusive evidence separately.

## Explicit limits
The protected config values `dns-server`, `doh-server`, `hijack-dns`, `ip-mode`, `ipv6-vif`, `interface-mode`, `skip-proxy`, `bypass-tun`, `real-ip` must not be changed. Rule-only changes cannot guarantee prevention of third-party DNS escape. Diagnostic websites are samples, not global proofs. Broader network policies are out of Stage 03 scope.
