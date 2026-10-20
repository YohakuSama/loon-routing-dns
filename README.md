# LoonKit

**v6.0.0 · 适用于 Loon 的分流配置**

LoonKit 为 [Loon](https://nsloon.app/) 提供常用服务分流、策略组、广告拦截及网络诊断。配置**不包含代理节点**，使用前需自行添加节点或订阅。

## 快速开始

**[获取正式配置 LoonKit.lcf](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf)**

1. 在 Loon 中使用上方 URL 导入完整配置。
2. 添加自己的代理节点或节点订阅，并在 `Proxy` 中选择可用节点；也可以选择 `Auto` 或 `Fallback`。
3. 更新远程规则与插件，按需调整各服务策略组。

已有配置升级前建议备份节点与个人设置。首次下载远程资源时，请确保当前网络能够访问 GitHub Raw。

## 主要功能

| 功能 | 说明 |
| --- | --- |
| **分类分流** | 国内常用服务直连；AI、Google、Microsoft、Apple 等独立选择策略。 |
| **流媒体** | YouTube、Netflix、Disney、TikTok、Spotify 等分组管理。 |
| **社交与游戏** | Telegram、Instagram、Discord、Steam 等可分别选路。 |
| **节点策略** | `Proxy` 手动选择、`Auto` 延迟测试、`Fallback` 故障回退。 |
| **广告拦截** | `AdBlock` 在 `REJECT`（拦截）和 `DIRECT`（放行）之间切换。 |
| **最终策略** | `Final` 决定未命中其他规则的连接使用代理还是直连。 |

## 网络辅助插件

正式配置已内置「网络辅助」，无需重复添加。插件提供**节点出口信息**（公网 IP、地区、ASN、ISP）、**网络与 DNS 诊断**（直连、代理及 DNS 解析结果）以及可选的**网络切换提醒**（默认关闭，连续失败时发送中文通知）。

如果诊断显示「网络连接正常，DNS 协议信息待确认」，表示 DNS 已返回解析结果，但本次查询的元数据不足以确认实际传输协议，**不是 DNS 解析失败的报告**。详细说明见 [网络诊断插件](./docs/NETWORK_DIAGNOSTICS.md)。

## DNS 与规则更新

正式配置采用 AliDNS DoH（`https://dns.alidns.com/dns-query`），保留现有 DNS、TUN、IPv4、IPv6 设置。DNS 行为与实际网络出口可以在 [DNS 说明](./docs/DNS_PRIVACY.md) 中了解。

当前正式配置使用 **26 份固定版本远程规则**。上游更新会先生成候选差异，审核后才发布，不自动覆盖现有规则。

## 相关文档

[规则与来源](./rules/README.md) · [更新记录](./docs/CHANGELOG.md) · [维护说明](./docs/MAINTAINING.md) · [第三方许可](./docs/THIRD_PARTY_NOTICES.md) · [问题反馈](https://github.com/YohakuSama/loonkit/issues)
