# IPv4 / IPv6 / ASN / no-resolve device matrix

| ID | Literal / scenario | Offline check | On-device requirement |
|---|---|---|---|
| IP-01 | 17.81.100.1 | Apple vs former ChinaDirect nested IP | Loon matched IP-CIDR and exit |
| IP-02 | 74.125.16.70 | Google vs former ChinaDirect overlap | Match rule/selector |
| IP-03 | 34.228.4.220 | Former WhatsApp broad AWS collision | Verify Netflix/FINAL outcome |
| IP-04 | 149.154.160.1 | Telegram IPv4 | Compare literal IP vs hostname path |
| IP-05 | 2a0a:f280::1 | Telegram IPv6 | IPv6 support, selected rule, exit alias |
| IP-06 | 2001:db8::1 | IPv6 documentation-range boundary | Expected synthetic only; not routable service |
| IP-07 | AS132203, AS32934 | IP-ASN no-resolve | Verify literal and hostname paths |
| IP-08 | AS211157, AS44907, AS59930, AS62014, AS62041 | IP-ASN no-resolve | Confirm Loon syntax and matching |
| IP-09 | GEOIP,CN and FINAL | No preceding domain hit | Resolution path and final fallback |
| IP-10 | IPv4 /24 first and last addresses | Network boundaries | Loon match vs Python offline IP model |
| IP-11 | IPv6 /48 first and last addresses | Network boundaries | Loon match vs Python offline IP model |
| IP-12 | Unmatched host A/AAAA | No DNS pre-resolve presumption | Loon resolver logs and actual selected policy |

Pin client version and keep the original ip-mode, ipv6-vif, real-ip, bypass-tun, DNS and DoH settings unchanged. A static no-resolve string check proves neither timing of resolution nor true Loon ASN precedence.
