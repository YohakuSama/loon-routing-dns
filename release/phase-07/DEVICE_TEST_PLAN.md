# vNext-RC2 真机测试：结构化验收清单

**全部 NOT_EXECUTED**。此前“日常未发现明显问题”不是下述专项测试合格证明。

测试候选：`release/phase-07/LoonKit.vNext-RC2.lcf` / `LoonKit.PrivacyDNS.vNext-RC2.lcf`。通过 `release/phase-07/RC_MANIFEST.json` 核对 SHA256，不可在测试完成后静默替换文件。个人节点与原始 IP 只保留设备本地。

## 执行前基线

- Loon 导入、两份配置分别加载、33 个策略组可选、26 条远程规则全部下载、图标与诊断插件脚本可用。
- 保持**同一设备、网络、Loon 版本、节点、节点协议、IPv4/IPv6 与配置独立的 DNS/TUN 值**，按 HISTORICAL / PRODUCTION / VNEXT 交叉对照，并记录实际命中、策略、节点出口、DNS 解析器、当地/远程解析证据。
- 国内：银行（招行、建行、农行等）、支付（支付宝、微信支付、PayPal）、地图（高德、百度）、出行、电商、国内游戏/下载、Apple 中国大陆业务、SteamCN、CDN。
- 海外：AI 登录和 API、Google/YouTube、Microsoft、Apple、Netflix、Disney、HBO、TikTok、Telegram、WhatsApp、Instagram、Facebook、Steam、PayPal，和 Spotify/Twitch/Abema/BBC/Line/Reddit/Linkedin 的海外出口、附属域名与地区解锁。
- 广告策略依次用 `AdBlock=REJECT` 与 `AdBlock=DIRECT`，检查广告实际命中、认证、风控与支付功能。
- `Final=Proxy/Auto/Fallback/DIRECT` 各档，尤其未分类域名在 DIRECT 下的真实出口。
- DNS/DoH 受控对照：本地查询、远程查询、解析器记录、节点出口、不同 IPv4/IPv6 链路和不预期直连；一个检测网站结果不能证明无泄漏。
- IP-ASN 七项（132203、32934、211157、44907、59930、62014、62041），与高风险父子规则中的代表性域名、登录与支付域名进行真实运行时检查；7331 项不能静态一键认定均合法。

## 证据格式

复用 `validation/phase-05/RESULT_TEMPLATE.json` 和 `scripts/validate_device_results.py`：

```bash
python3 scripts/validate_device_results.py /path/to/redacted-device-results.json
```

校验器验证结构和敏感数据匿名化，不等价于自动通过业务验收。结果至少记录测试编号、配置 Commit SHA、规则版本、时间、设备/网络/节点别名、客户端版本、受控 DNS/TUN 哈希、Loon 实际命中、策略、出口、解析器、IPv4/IPv6 结果和来源证据。相同用例每种配置需一致控制变量。出现故障应保存已匿名化证据和复现步骤，再定位规则归属并更新候选；变更已测试文件后必须重测受影响项。

完整测试尚未获得，不可把 Release Gate 的相关测试状态修改为 PASS。
