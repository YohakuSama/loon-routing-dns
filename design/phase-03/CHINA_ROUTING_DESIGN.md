# Mainland DIRECT — review standard and migration design

## Evidence
`ChinaDirect.list` has about 123k published rules (group-wide snapshot; exact source-level attribution missing). Phase 02 reports **10** published DIRECT keywords and **47** one-label DOMAIN-SUFFIX rules. Every item retains source path, original published line, associated P02 risk, and an individual provisional recommendation in `refactor/vnext/policy_decisions.json/direct_rule_reviews`. No item is silently dropped or deemed automatically malicious.

## Six business classes
- `CN_CONFIRMED`: independently verified mainland banking, maps, domestic payment/e-commerce, transit and delivery endpoints; suggest scoped DOMAIN or DOMAIN-SUFFIX.
- `CN_CDN_VERIFIED`: only documented CDN hostname/coverage tied to mainland delivery with cross-platform negative tests; avoid shared roots.
- `CN_SERVICE_EXCEPTION`: Chinese Apple OTA, Steam downloads and other function-specific overrides, with service/region definition and rollback.
- `REGION_UNCERTAIN`: ambiguous ownership, publicly registered generic TLD or transnational CDN; **DEFER**, not DIRECT by origin.
- `CROSS_BORDER_EXCLUDE`: multinational payment, international corporate SaaS and cross-border businesses; never inherit DIRECT merely from Chinese registration.
- `RUNTIME_VERIFICATION_REQUIRED`: device routing and pre-resolution are necessary to adjudicate IP/ASN, unknown host or multiple policy matches.

## Two different match classes
`DOMAIN-SUFFIX,cn` is a **label-boundary suffix for names under .cn**; review Chinese-domain exceptions and international operations on .cn. It is not the substring rule `DOMAIN-KEYWORD,alipay`, which can match arbitrary hostnames containing 'alipay', including unrelated brand strings. Do not remove either without real counterexamples. `DOMAIN-SUFFIX,ms`, `wang`, punycode IDN single labels and corporate-name TLDs have their own domain ownership, registry, scope and geopolitical ambiguity; each of 47 is individually listed in machine decisions.

Ten keywords: `.tmall.com` needs consideration as an exact suffix versus literal substring; `alicdn`, `alipay`, `aliyun`, `baidu`, `beplay`, `hnagroup`, `officecdn`, `taobao`, `weibo` each require positive and negative hostname cases before scoped replacement. The published strings and lines remain unchanged.

## Proposed Stage 04 controls
- Rule inventory must preserve IPv4/IPv6 and no-resolve flags, domain label boundaries, raw input SHA and include lineage.
- No silent promotion from country TLD, business headquarters, opaque IP-ASN, broad keyword or shared CDN to verified DIRECT.
- Reject new DIRECT coverage on reviewed international critical services unless a signed exception documents intended mainland routing and tests.
- Compare current/candidate outcomes under Final=Proxy **and** Final=DIRECT; node selection, IP literal and domain request, IPv4/IPv6, regional streaming, payment/auth, update/restore.
- For IP-ASN AS132203 and GEOIP,CN distinguish direct address routing from hostname lookup; a rule-only strategy cannot prevent all app-controlled DNS.
- No BrowserLeaks/whatismyip/other diagnostic-site list additions; diagnostic sites are regression fixtures, not fix strategies.
