# Routing regression / selector matrix

| ID | Destination | Case | Expected static policy | Required device check |
|---|---|---|---|---|
| ROUTE-01 | www.ccb.com | Mainland bank | DIRECT | Login/static assets and cross-border auth separately |
| ROUTE-02 | www.alipay.com | Mainland payment | DIRECT | No accidental blocking or auth redirect |
| ROUTE-03 | fake-taobao-global.invalid | False substring owner | Final | Must not match broad ChinaDirect keyword |
| ROUTE-04 | www.google.com | Google | Google | Matching precedence and chosen egress |
| ROUTE-05 | gemini.google.com | AI vs Google | AI | Which rule actually wins |
| ROUTE-06 | www.youtube.com | YouTube vs Google | YouTube | Dedicated node is honored |
| ROUTE-07 | www.apple.com | Apple vs shared infrastructure | Apple | Separate Apple mainland and global behavior |
| ROUTE-08 | login.microsoftonline.com | Microsoft shared auth | Microsoft | Auth endpoint unblocked |
| ROUTE-09 | www.spotify.com | Disabled-list compatibility repaired inline | Spotify | All four FINAL choices |
| ROUTE-10 | www.twitch.tv | Region-specific overseas selector | Twitch | All four FINAL choices |
| ROUTE-11 | www.abema.tv | Region-specific overseas selector | Abema | Dedicated node and geo-unlock |
| ROUTE-12 | www.bbc.co.uk | Region-specific overseas selector | BBC | Dedicated node and geo-unlock |
| ROUTE-13 | www.line.me | Specialized overseas selector | Line | Login/media endpoints |
| ROUTE-14 | www.reddit.com | Specialized overseas selector | Reddit | Login/media endpoints |
| ROUTE-15 | www.linkedin.com | Specialized overseas selector | Linkedin | Login/media endpoints |
| ROUTE-16 | unknown-5827469.invalid | No exact domain match | Final | Proxy, Auto, Fallback, DIRECT each |
| ROUTE-17 | random.company.cn | Parent .cn vs child specialization | REVIEW_REQUIRED | Check actual Loon precedence; no assumed DIRECT |
| ROUTE-18 | www.bilibili.com | Dedicated vs ChinaDirect | Bilibili | Match owner and user selector |
| ROUTE-19 | stripe.com | Payment/shared | Final static model | No adverse payment or anti-fraud impact |
| ROUTE-20 | www.paypal.com | Intl payment | Paypal | Check payment and authentication |

For routes restored inline, this validates only selected first-party service suffixes, **not** every historic auxiliary CDN/auth endpoint. Cases require historic/production/candidate comparisons and logs of matched predicates.
