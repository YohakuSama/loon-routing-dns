# Controlled A/B/C testing: historic, production and candidate

Use one physical device and the same Loon client build. Collect three configuration variants for each test ID: `HISTORICAL`, `PRODUCTION`, `VNEXT`. Pin candidate remote URLs to one full 40-hex Git commit; the historic version may contain changed mutable sources, so document that it is not a precise historical snapshot.

Environment controls: device alias, Loon version, network type/name, time, identical proxy node alias and protocol, node options, DNS/DoH/TUN fingerprint, IPv4/IPv6 state, client rules order, identical service account and region. Different contexts invalidate direct A/B claims.

Before each case: clear only the service-local state required by the test, reset Loon connection/log capture, record policy selections and rule-update time. Do not change frozen DNS/TUN settings.

Record request target domain, rule hit shown by Loon, actual policy group, selected node class, measured egress *alias*, DNS resolver *aliases*, IPv4/IPv6 observations, expected vs actual, and masked logs. A website's visible recursive resolver is not necessarily its traffic egress and alone proves neither DNS leak nor safety.

Apply FINAL=Proxy, Auto, Fallback, DIRECT independently; apply AdBlock=REJECT and DIRECT independently; vary a dedicated overseas selector where supported. Evaluate original and candidate with the same other selector settings.

Never call an unexecuted case PASS. Unknown observations must remain UNKNOWN. Stop a test if payment, login or account security is at risk; record BLOCKED.
