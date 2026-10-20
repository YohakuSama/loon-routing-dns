# Overseas services and user-controlled Final

| Group | Separate exit/business condition | Stage 03 disposition |
| --- | --- | --- |
| AI | Stable dedicated node, geo-eligibility, Copilot/Gemini boundaries | Preserve selector; narrow only verified model endpoints |
| Netflix / Disney / PrimeVideo / HBO | Regional catalog, license and playback/CDN | Preserve dedicated optional regions; shared cloud/manual review |
| YouTube / Spotify / TikTok | Geolocation, account and media transport | Preserve region selectors when used; test ordinary content fallback |
| Telegram | Distinct transport paths and ASN overlaps | Preserve until routing and ASN device tests |
| Google / Microsoft / Apple | Diverse auth, regional updates, hosted clouds and direct choice | Preserve existing selectors, especially DIRECT options for Microsoft/Apple |
| Facebook / Whatsapp / Instagram / Twitter / Discord / Reddit / Line / Linkedin | Distinct app preferences; Meta shared-host conflicts | Preserve manual choices; grouped consolidation is only proposal |
| Steam / Paypal | Mainland SteamCN separation; international payment and account trust | Preserve separate from DIRECT and Final until cross-region regression |
| Twitch / Abema / BBC / Bilibili / 動畫瘋 / Dazn | Live/video region specificity | Preserve legacy or currently available user choices |

For every group compare: separate exit selected?, geographic unlock?, user selection saved?, rules wholly redundant?, shared auth/CDN/payment?, ordinary traffic behavior when Final=Proxy/Auto/Fallback/DIRECT?, historic group-selector compatibility?, can it be optional without changing past users? Answers remain provisional until real user needs, immutable input attribution and device tests.

**Ordinary overseas traffic** may match `FINAL,Final` when no dedicated requirement exists. No blanket rule that foreign traffic is always PROXY: the Final policy is user-selected and can be DIRECT. A shift from any dedicated service rule to Final is a behavior change when node choices differ; no such shift is approved.

**Shared dependencies**: `akadns.net`, `execute-api.us-east-1.amazonaws.com`, shared AWS/Cloudflare/CDN, login and payment must be reviewed by hostname + functional context. A provider domain used by Disney/HBO, Facebook/WhatsApp, AI/Microsoft or AI/Google cannot be permanently assigned solely to whichever platform appears first in publish order. Record policy and exact matched rule fixture rather than global hostname ownership.
