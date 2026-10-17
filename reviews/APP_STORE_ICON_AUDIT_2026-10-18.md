# App Store 图标候选质量审核（2026-10-18）

> 本报告为自动化素材预检，不是商标授权审查、iPhone 真机或 Loon 渲染实测。
> 仅临时读取 Apple 返回的远程图像，不将品牌图标复制进本仓库。

## 标准与限制

- 当前市场（US/GB/JP/TW/CN）的应用 ID、标题、开发者及图片来源核对。
- 实际图片下载后，验证尺寸不低于 512×512、图片格式及四角 Alpha。
- 对图标上下左右边缘采样，按 WCAG 亮度对比度初步识别可能融入深/浅背景的图片。阈值 1.6 仅用于**触发人工复核**，不是 WCAG 文字合规判定。
- App Store 交付的图标通常是方形原始素材；iOS 圆角是显示裁切效果。Loon 是否额外圆角、是否加边框须真机测试。
- 高分辨率不意味着无锯齿。最终要用 Loon 策略组实际显示尺寸检查锐度。
- Apple iTunes Search API 素材使用条件有限；不能因仓库开源而推断图标允许再分发。

## 24 个候选结果

| 策略组 | 官方 App / 开发者 | 图片像素 | 深色边缘最低对比 | 浅色边缘最低对比 | 状态 |
|---|---|---:|---:|---:|---|
| [YouTube](https://apps.apple.com/us/app/youtube/id544007664?uo=4) | YouTube / Google LLC | 512×512 | 17.24 | 1.05 | CHECK_VISUAL |
| [Netflix](https://apps.apple.com/us/app/netflix/id363590051?uo=4) | Netflix / Netflix, Inc. | 512×512 | 1.14 | 18.67 | CHECK_VISUAL |
| [Disney](https://apps.apple.com/us/app/disney/id1446075923?uo=4) | Disney+ / Disney Electronic Content, Inc. | 512×512 | 1.08 | 2.78 | CHECK_VISUAL |
| [PrimeVideo](https://apps.apple.com/us/app/amazon-prime-video/id545519333?uo=4) | Amazon Prime Video / AMZN Mobile LLC | 512×512 | 4.22 | 3.88 | METADATA_OK |
| [Spotify](https://apps.apple.com/us/app/spotify-music-and-podcasts/id324684580?uo=4) | Spotify: Music and Podcasts / Spotify | 512×512 | 1.22 | 19.92 | CHECK_VISUAL |
| [TikTok](https://apps.apple.com/us/app/tiktok-videos-shop-live/id835599320?uo=4) | TikTok - Videos, Shop & LIVE / TIKTOK PTE. LTD. | 512×512 | 1.22 | 19.92 | CHECK_VISUAL |
| [Twitch](https://apps.apple.com/us/app/twitch-live-streaming/id460177396?uo=4) | Twitch: Live Streaming / Twitch Interactive, Inc. | 512×512 | 3.73 | 4.39 | METADATA_OK |
| [HBO](https://apps.apple.com/us/app/hbo-max-stream-movies-tv/id1666653815?uo=4) | HBO Max: Stream Movies & TV / WarnerMedia Global Digital Services, LLC | 512×512 | 1.02 | 16.68 | CHECK_VISUAL |
| [Abema](https://apps.apple.com/jp/app/abema-%E3%82%A2%E3%83%99%E3%83%9E-%E6%96%B0%E3%81%97%E3%81%84%E6%9C%AA%E6%9D%A5%E3%81%AEtv/id1074866833?uo=4) | ABEMA(アベマ) 新しい未来のTV / ABEMATV, INC. | 512×512 | 1.22 | 19.92 | CHECK_VISUAL |
| [Dazn](https://apps.apple.com/us/app/dazn-stream-live-sports/id1129523589?uo=4) | DAZN: Stream Live Sports / DAZN Limited | 512×512 | 1.12 | 18.39 | CHECK_VISUAL |
| [BBC](https://apps.apple.com/us/app/bbc-world-news-stories/id364147881?uo=4) | BBC: World News & Stories / BBC Studios Distribution Ltd. | 512×512 | 1.22 | 19.92 | CHECK_VISUAL |
| [AnimeCrazy](https://apps.apple.com/tw/app/%E5%B7%B4%E5%93%88%E5%A7%86%E7%89%B9%E5%8B%95%E7%95%AB%E7%98%8B/id1102650114?uo=4) | 巴哈姆特動畫瘋 / ONEUP NETWORK CORPORATION | 512×512 | 17.24 | 1.05 | CHECK_VISUAL |
| [Bilibili](https://apps.apple.com/cn/app/%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9-%E5%BC%B9%E5%B9%95%E7%95%AA%E5%89%A7%E7%9B%B4%E6%92%AD%E9%AB%98%E6%B8%85%E8%A7%86%E9%A2%91/id736536022?uo=4) | 哔哩哔哩-弹幕番剧直播高清视频 / Shanghai Bilibili Animation Co.,Ltd | 512×512 | 1.01 | 2.5 | CHECK_VISUAL |
| [Steam](https://apps.apple.com/gb/app/steam-mobile/id495369748?uo=4) | Steam Mobile / Valve Corporation | 512×512 | 1.02 | 1.05 | CHECK_VISUAL |
| [Paypal](https://apps.apple.com/us/app/paypal-pay-send-save/id283646709?uo=4) | PayPal - Pay, Send, Save / PayPal, Inc. | 512×512 | 1.42 | 11.5 | CHECK_VISUAL |
| [Telegram](https://apps.apple.com/us/app/telegram-messenger/id686449807?uo=4) | Telegram Messenger / Telegram FZ-LLC | 512×512 | 14.6 | 1.03 | CHECK_VISUAL |
| [Whatsapp](https://apps.apple.com/us/app/whatsapp-messenger/id310633997?uo=4) | WhatsApp Messenger / WhatsApp Inc. | 512×512 | 9.29 | 1.51 | CHECK_VISUAL |
| [Instagram](https://apps.apple.com/us/app/instagram/id389801252?uo=4) | Instagram / Instagram, Inc. | 512×512 | 3.45 | 1.38 | CHECK_VISUAL |
| [Facebook](https://apps.apple.com/us/app/facebook/id284882215?uo=4) | Facebook / Meta Platforms, Inc. | 512×512 | 3.53 | 1.05 | CHECK_VISUAL |
| [Twitter](https://apps.apple.com/gb/app/x/id333903271?uo=4) | X / TWITTER INTERNATIONAL UNLIMITED COMPANY | 512×512 | 1.22 | 19.92 | CHECK_VISUAL |
| [Discord](https://apps.apple.com/us/app/discord-talk-play-hang-out/id985746746?uo=4) | Discord - Talk, Play, Hang Out / Discord Inc. | 512×512 | 3.67 | 3.28 | METADATA_OK |
| [Line](https://apps.apple.com/gb/app/line/id443904275?uo=4) | LINE / LY Corporation | 512×512 | 7.64 | 2.14 | METADATA_OK |
| [Reddit](https://apps.apple.com/gb/app/reddit/id1064216828?uo=4) | Reddit / REDDIT, INC. | 512×512 | 5.01 | 3.26 | METADATA_OK |
| [Linkedin](https://apps.apple.com/gb/app/linkedin-community-career/id288429040?uo=4) | LinkedIn: Community & Career / LinkedIn Corporation | 512×512 | 3.04 | 5.38 | METADATA_OK |

## 待人工复核或待处理

共 18/24 个需进一步处理（含无法拉取的情况）。

- **YouTube**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **Netflix**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **Disney**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **Spotify**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **TikTok**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **HBO**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **Abema**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **Dazn**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **BBC**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **AnimeCrazy**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **Bilibili**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **Steam**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **Paypal**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **Telegram**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **Whatsapp**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **Instagram**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **Facebook**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整
- **Twitter**：CHECK_VISUAL — 边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整

## 特别说明

- BBC 的候选是 BBC News，不一定代表 BBC 全部服务；建议确认图标与策略组语义。
- HBO 候选是 HBO Max；如果分流覆盖 Max 与其他 HBO 服务，需要统一名称及应用视觉。
- Netflix、X、Disney、TikTok、Steam 等深色底图标应重点看暗色列表的轮廓；白底图标则看浅色列表。
- 即使全部通过技术预检，也不能自动得出已获权利人商标授权的结论。

原始明细：[JSON](./APP_STORE_ICON_AUDIT_2026-10-18.json)。

