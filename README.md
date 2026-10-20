# LoonKit

**Loon 分流规则与策略配置 · v6.0.0**

LoonKit 提供国内外网络分流、常用服务的独立策略组和广告拦截规则，适用于 [Loon](https://nsloon.app/)。

项目提供完整配置和规则，**代理节点需要自行添加**。

## 配置订阅

| 版本 | DNS 解析服务 | 订阅地址 |
| --- | --- | --- |
| 标准版 | 阿里 AliDNS（DoH） | [LoonKit.lcf](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf) |
| DNSPod 版 | 腾讯 DNSPod（DoH） | [LoonKit.PrivacyDNS.lcf](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.PrivacyDNS.lcf) |

两个版本使用相同的分流规则、策略组和插件，仅 DNS 服务器与 DoH 地址不同。按自己的网络环境选择即可。

## 快速开始

1. 在 Loon 中备份现有配置与节点订阅。
2. 复制上方任一订阅地址，在 Loon 中通过 URL 导入完整配置。
3. 添加或恢复自己的代理节点订阅，更新远程规则与插件。
4. 在策略组中选择可用节点，并根据需要调整各项分流策略。

从 v5.10.0 升级时，建议使用新版完整配置替换旧配置；如果以前单独订阅过旧规则，请检查并移除重复订阅。原有完整配置的订阅地址保持不变。

## 主要功能

- **分类分流**：国内服务直连，AI、Google、Apple、流媒体、社交平台及游戏等服务按分类选择策略。
- **灵活选路**：支持 `Proxy`、`Auto`、`Fallback` 等策略；`Final` 决定未命中其他规则的流量如何处理。
- **广告拦截**：`AdBlock` 可在 `REJECT` 与 `DIRECT` 之间切换。
- **网络诊断**：提供[网络辅助插件](./plugins/Network_Diagnostics.plugin)，可手动查看节点出口及 DNS 状态。
- **版本化规则**：v6.0.0 使用 26 份远程规则文件、106 条本地规则和 33 个策略组；规则资源固定版本，便于核查与回滚。

## 文档与维护

- [DNS 配置与问题排查](./docs/DNS_PRIVACY.md)
- [规则分类、来源与更新说明](./rules/README.md)
- [v6.0.0 更新记录](./release/phase-07/CHANGELOG-v6.0.0.md)
- [升级与回滚指南](./release/phase-07/MIGRATION_ROLLBACK.md)
- [第三方来源及许可声明](./release/phase-07/THIRD_PARTY_NOTICES.md)

遇到分流或配置问题，可以通过 [GitHub Issues](https://github.com/YohakuSama/loonkit/issues) 反馈。
