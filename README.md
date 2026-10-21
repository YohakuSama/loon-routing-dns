<div align="center">

# LoonKit

**为 Loon 打造的完整分流配置**

精细分流 · 灵活选路 · 网络诊断

[![Production CI](https://github.com/YohakuSama/loonkit/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/YohakuSama/loonkit/actions/workflows/ci.yml)

[**获取配置**](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf) · [功能概览](#功能概览) · [快速开始](#快速开始) · [问题反馈](https://github.com/YohakuSama/loonkit/issues)

</div>

LoonKit 是一套面向 [Loon](https://nsloon.app/) 的完整分流配置，整合常用服务规则、独立策略组、广告拦截及网络辅助工具，让日常分流更清晰、管理更方便。

当前正式配置为 **v6.2.0**，入口统一为 `LoonKit.lcf`。**配置不提供代理节点**，需要自行添加节点或订阅。

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
| **服务问题排查** | 已整合进「网络辅助」插件，手动检查七项服务的 HTTPS 端点与 DNS，并支持离线命中和脱敏日志分析。 |
| **稳定的规则版本** | 保留 26 份固定远程规则；新版为七个服务增加 62 条本地精选域名匹配。 |

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

正式配置只包含一个 **「网络辅助」** 插件，无需另行安装服务诊断。主要提供：

- **节点出口信息**：查看公网 IP、地区、ASN、ISP 等信息。
- **网络与 DNS 诊断**：检查直连、代理连通性和 Loon 原生 DNS 解析状态，明确区分连接故障、解析成功和协议提示。
- **服务连通性诊断**：按服务检查主站、关联端点和 Loon DNS 解析，不会因为单个端点返回 404 就判断服务异常。
- **网络切换提醒**：检测到明确的持续连接异常时发送中文提醒，**默认关闭**，按需开启。

插件仅用于查询和提醒，不会自动更改节点、DNS 或分流设置。

> **诊断说明：** 连接检测、DNS 解析和 DNS 传输协议信息分别显示。遇到超时、异常状态码或信息不足时，可查看具体检测结果及 [排查说明](./docs/NETWORK_DIAGNOSTICS.md)。

更新旧配置后，请在 Loon 内刷新远程插件与脚本；缓存旧版本时可能仍显示原来的提示。详见 [网络辅助说明](./docs/NETWORK_DIAGNOSTICS.md)。

## 服务与分流问题排查

- [服务与分流排查指南](./docs/ROUTE_DIAGNOSTICS.md)：检查 Spotify、Twitch、Abema、BBC、Line、Reddit、LinkedIn 的已有主域名归属和候选规则覆盖差异；查询预计命中，并通过脱敏日志分类辅助定位问题。
- **服务连通性诊断**：已并入现有[「网络辅助」](./release/Network_Diagnostics.plugin)，在同一个插件中选择服务并手动查看主站、关联端点及 DNS 状态，**不会自动运行**。
- 对自己导出的 HAR 或文本日志，可在电脑上离线汇总服务类别、状态码区间、已知策略和疑似问题类型。**不会上传原始日志**。

上述工具仅辅助排查。预计规则命中不代表真机实际命中，连接端点有响应也不等于 App 登录或播放成功。这些排查工具不会自动修改 DNS、节点或分流策略；实际问题请结合 Loon 请求日志判断。

## DNS 与规则更新

默认提供 AliDNS DoH，并支持在 Loon 中使用自选 DNS。相关选项和常见问题见 [DNS 设置说明](./docs/DNS_PRIVACY.md)。

规则来源按计划检查更新，新增规则会先经过格式、重复项和策略冲突检查，再由维护者审核后发布新版本。详见 [规则说明](./rules/README.md)。

## 文档与支持

[规则与来源](./rules/README.md) · [服务与分流排查](./docs/ROUTE_DIAGNOSTICS.md) · [网络辅助](./docs/NETWORK_DIAGNOSTICS.md) · [DNS 说明](./docs/DNS_PRIVACY.md) · [更新记录](./docs/CHANGELOG.md)

[维护说明](./docs/MAINTAINING.md) · [正式资源依赖](./docs/DEPENDENCIES.md) · [开源许可与来源](./docs/THIRD_PARTY_NOTICES.md) · [发布指引](./docs/RELEASE_READINESS.md) · [反馈问题](https://github.com/YohakuSama/loonkit/issues)

## 开源许可

LoonKit 的原创代码与配置贡献采用 [GPL-2.0-only](./LICENSE) 许可；第三方规则与素材适用各自的许可及权利声明，详见 [第三方许可与来源](./docs/THIRD_PARTY_NOTICES.md)。

**[下载 v6.2.0 正式版](https://github.com/YohakuSama/loonkit/releases/tag/v6.2.0)** · [配置文件校验](./docs/RELEASE_CHECKSUM_v6.2.0.md)

---

<p align="center"><sub>LoonKit 是社区配置项目，与 Loon 官方无关联。</sub></p>
