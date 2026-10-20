# DNS observations are not traffic-route proof

| ID | Scenario | Required observations | Interpretation |
|---|---|---|---|
| DNS-01 | Ordinary mainland domain on Wi-Fi | Loon DNS query, recursive resolver alias, matched rule, destination exit alias | Compare across all three profiles |
| DNS-02 | Overseas platform via proxy | Local resolver alias, proxy-side resolver if visible, exit alias | Separate remote proxy resolution from local DNS |
| DNS-03 | Application using built-in DoH | App version, Loon DNS logs availability, egress | DoH may bypass UDP/53 hijack, not automatically a device DNS leak |
| DNS-04 | Dual-stack A and AAAA queries | IPv4 and IPv6 resolver observations and transport | Do not generalize from a single address family |
| DNS-05 | Invalid/unmatched domain | FINAL choice and DNS failure mode | Expected behavior depends on user selector and DNS response |
| DNS-06 | Captive portal/local bypass | bypass rule, resolver/egress, network type | Confirm unchanged bypass and TUN profile |
| DNS-07 | DNS check website with multiple resolvers | Full resolver aliases and tested browser path | More resolvers alone is not proof of real-IP leak |
| DNS-08 | Website showing two resolvers | Resolver aliases, other app flows and DNS modes | Two resolvers alone is not proof of complete safety |

All measurements are client/device observations; offline simulations must be labeled STATIC_ONLY. Never modify dns-server, doh-server, hijack-dns, bypass-tun, skip-proxy, ipv6-vif, or ip-mode to make a result pass.
