# AdBlock: selector-controlled, not unconditional REJECT

| ID | Domain/use | AdBlock choice | Static intent | Evidence needed |
|---|---|---|---|---|
| ADS-01 | admob.com | REJECT | AdBlock | Loon rule/policy, DNS and connection result |
| ADS-02 | doubleclick.com | REJECT | AdBlock | Verify actual reject mode, not just matching |
| ADS-03 | app-measurement.com | REJECT | AdBlock | Log actual request |
| ADS-04 | ads-twitter.com | REJECT | AdBlock | Log actual request |
| ADS-05 | each of ADS-01..04 | DIRECT | AdBlock→DIRECT | Ensure no independent rule forces REJECT |
| ADS-06 | stripe.com | both | Do not blindly REJECT | Payment/anti-fraud transaction safeguards |
| ADS-07 | login.microsoftonline.com | both | Microsoft auth | Confirm platform precedence and sign-in |
| ADS-08 | auth0.com | both | Shared authentication | Do not classify by name substring |
| ADS-09 | accounts.google.com | both | Google authentication | No Google/AdBlock misroute |
| ADS-10 | cloudfront.net service tenant | both | Shared infrastructure | Different tenants may have different owners |
| ADS-11 | 322 isolated risky blockers | both | ISOLATED_FROM_CANDIDATE | Confirm relevant business owner before any reintroduction |

Do not convert AdBlock to unconditional REJECT. For third-party sites, avoid live purchases and retain only masked logs with service-specific permission. Static simulation is not a Loon runtime result.
