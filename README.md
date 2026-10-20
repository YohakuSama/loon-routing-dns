<div align="center">

# LoonKit

**为 Loon 打造的完整分流配置**

精细分流 · 灵活选路 · 网络诊断

[![Production CI](https://github.com/YohakuSama/loonkit/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/YohakuSama/loonkit/actions/workflows/ci.yml)

[**获取配置**](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf) · [功能概览](#功能概览) · [快速开始](#快速开始) · [问题反馈](https://github.com/YohakuSama/loonkit/issues)

</div>

LoonKit 是一套面向 [Loon](https://nsloon.app/) 的完整分流配置，整合常用服务规则、独立策略组、广告拦截及网络辅助工具，让日常分流更清晰、管理更方便。

当前正式配置为 **v6.0.0**，入口统一为 `LoonKit.lcf`。**配置不提供代理节点**，需要自行添加节点或订阅。

## 快速开始

**[下载 / 导入 LoonKit.lcf](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf)** · [查看配置内容](./LoonKit.lcf)

1. 在 Loon 中通过上方 Raw 链接导入配置。
2. 添加自己的代理节点或节点订阅，在 `Proxy`、`Auto` 或 `Fallback` 中选择适合的线路。
3. 在 Loon 中刷新远程规则和插件资源，按需切换 AI、流媒体、社交等服务对应的策略组。

已有个人配置时，建议先备份节点及自定义设置。首次加载远程资源需要能够访问 GitHub Raw。

## 功能概览

| 功能 | 说明 |
| --- | --- |
| **精细分流** | 国内常用服务直连；AI、Google、Microsoft、Apple 等服务独立选路。 |
| **流媒体策略** | YouTube、Netflix、Disney、Prime Video、TikTok、Spotify 等按服务分组。 |
| **社交与游戏** | Telegram、Instagram、Discord、WhatsApp、Steam 等支持独立策略。 |
| **灵活选路** | 手动选择、延迟测试和故障回退相结合，满足不同网络需求。 |
| **广告拦截** | 通过 `AdBlock` 策略组快速切换拦截与放行。 |
| **网络辅助** | 集成节点出口查询、连通性与 DNS 诊断，以及可选的网络切换提醒。 |
| **稳定的规则版本** | 正式配置固定引用 26 份规则，规则变更经过审核后再发布。 |

### 常用策略组

| 策略组 | 用途 |
| --- | --- |
| `Proxy` | 手动指定节点，也可选择自动或回退策略。 |
| `Auto` | 根据连通性测试结果选择节点。 |
| `Fallback` | 优先使用可用节点，故障时尝试回退。 |
| `AdBlock` | `REJECT` 拦截，`DIRECT` 放行。 |
| `Final` | 决定未命中其他规则的连接如何处理。 |

AI、各流媒体与社交服务也有各自的策略组，可按需要选择线路，无须改动整份配置。

## 内置网络辅助

正式配置已经包含 **「网络辅助」** 插件，无需重复安装。主要提供：

- **节点出口信息**：查看公网 IP、地区、ASN、ISP 等信息。
- **网络与 DNS 诊断**：检查直连、代理连通性和 Loon 原生 DNS 解析状态，明确区分连接故障、解析成功和协议提示。
- **网络切换提醒**：检测到明确的持续连接异常时发送中文提醒，**默认关闭**，按需开启。

插件仅用于查询和提醒，不会自动更改节点、DNS 或分流设置。

> **诊断说明：** 如果直连、代理都返回 `HTTP 204`，DNS 也解析成功，主结论就是「网络连接与 DNS 解析正常」。当 Loon 返回 `auto / https://` 等不完整信息时，仅附上协议提示，**不代表 DNS 解析失败或发生泄漏**。用户可以自行选择 AliDNS、Cloudflare、Google 或其他 DNS；插件只判断解析和协议，不再因解析器不同而警告。新版本还会将 `HTTP 200`（非预期 204）列为待确认，避免门户页面造成误报。

更新旧配置后，请在 Loon 内刷新远程插件与脚本；缓存旧版本时可能仍显示原来的提示。详见 [网络辅助说明](./docs/NETWORK_DIAGNOSTICS.md)。

## DNS 与规则维护

默认配置提供 **AliDNS DoH**，用户可以在 Loon 中自行选择其他 DNS；插件不会强制使用某一家服务商。当前 DNS、TUN 及 IPv4 / IPv6 设置保持不变。需要查看相关设置或排查 DNS 问题，可参考 [DNS 说明](./docs/DNS_PRIVACY.md)。

**规则更新机制：** GitHub Actions 每周读取上游来源、解析四种输入格式，生成**来源快照、规范化候选、重复规则处理结果、完整增删差异和风险报告**。跨策略冲突、扩大匹配范围、收紧规则及来源不完整等情况均需审核；**不会自动修改冻结规则、覆盖正式分流或发布新版本**。此流程自动生成上游更新候选与风险分析，最终更新仍需人工确认及正式校验。

## 文档与支持

[规则与来源](./rules/README.md) · [网络辅助](./docs/NETWORK_DIAGNOSTICS.md) · [DNS 说明](./docs/DNS_PRIVACY.md) · [更新记录](./docs/CHANGELOG.md)

[维护说明](./docs/MAINTAINING.md) · [开源许可与来源](./docs/THIRD_PARTY_NOTICES.md) · [发布指引](./docs/RELEASE_READINESS.md) · [反馈问题](https://github.com/YohakuSama/loonkit/issues)

## 开源许可

LoonKit **自有、可授权的代码和配置贡献**采用 [GPL-2.0-only](./LICENSE)。第三方规则保留其原许可及署名，主要涉及 GPL-2.0-only、MIT 和 WTFPL-2.0，详见[第三方许可与来源](./docs/THIRD_PARTY_NOTICES.md)。第三方品牌图标不因本项目采用 GPL 而自动获得再授权。

> **版本说明：** 当前 v6.0.0 配置可直接从仓库获取；GitHub Release 尚未单独发布，准备流程见[发布指引](./docs/RELEASE_READINESS.md)。

---

<p align="center"><sub>LoonKit 是社区配置项目，与 Loon 官方无关联。</sub></p>
