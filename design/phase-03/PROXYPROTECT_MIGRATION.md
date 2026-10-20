# Retirement proposal for standalone ProxyProtect (NOT executed)

The current `rules/ProxyProtect.list` is a first-loaded subscription, policy=Proxy, 17 DOMAIN-SUFFIX entries. This design recommends eventual removal **only after demonstrably equal or safer behavior**; the 17 published rules, order and runtime subscription must not change in Phase 03.

## Four successor responsibilities
1. **Generator source-ownership guard**: before publication, flag an international payment/auth/service hostname unexpectedly covered by a DIRECT domain/keyword/suffix rule. Report rule ID and upstream origin, do not rely on a growing fixed list of IP/DNS check sites.
2. **Regression sample library**: existing 16 diagnostic entries (browserleaks.com, dnscheck.tools, dnsleaktest.com, icanhazip.com, ifconfig.co, ifconfig.me, ip.sb, ipify.org, ipinfo.io, ipleak.net, iplocation.net, myip.com, test-ipv6.com, whatismyip.com, whatismyipaddress.com, whoer.net) can serve as observational fixtures *without enlarging a production whitelist*. BrowserLeaks is a useful observation, not a DNS leak proof.
3. **Business-specific routing**: stripe.com (17th entry) needs an evidence-backed international payments policy decision, not classification as a diagnostics website. Define critical login/checkout tests before any change.
4. **Exception and risk register**: uncertain international service ownership must remain open for human adjudication; a diagnostics success indicator cannot close it.

## Migration gates (all mandatory)
- Preserve effective policy for each of the 17 current hosts, including wildcard subdomains, and record the matched rule and selected node.
- Independently detect incorrect DIRECT from broad keyword, one-label suffix and unmatched-domain IP fallback; test Final=Proxy and Final=DIRECT.
- Compare Loon source precedence on a physical device with the first-loaded subscription present and absent in an **isolated candidate profile**; dual stack, cache cleared, different node protocols and OS versions.
- Validate Stripe sign-in/checkout/auth and unrelated shared payment/CDN flows, and user selectors under the proposed direct/overseas/Final policies.
- Ensure candidate published matcher output supplies explicit audited replacement rules or documented fallback; compare complete route traces rather than simply subtract 17.
- Obtain a maintainer-signed approval with rollback procedure; only Stage 04+ may remove the remote subscription from a formally reviewed config. Existing config remains immutable now.

No new IP/DNS diagnostic domain, whitelist, DNS parameter, published rule or active subscription is added by this plan.
