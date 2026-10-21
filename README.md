<div align="center">

# LoonKit

**为 Loon 打造的完整分流配置**

精细分流 · 灵活选路 · 网络诊断

[![Production CI](https://github.com/YohakuSama/loonkit/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/YohakuSama/loonkit/actions/workflows/ci.yml)

[**获取配置**](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf) · [功能概览](#功能概览) · [快速开始](#快速开始) · [问题反馈](https://github.com/YohakuSama/loonkit/issues)

</div>

LoonKit 是一套面向 [Loon](https://nsloon.app/) 的完整分流配置，整合常用服务规则、独立策略组、广告拦截及网络辅助工具，让日常分流更清晰、管理更方便。

配置入口为 `LoonKit.lcf`。**配置不提供代理节点**，需要自行添加节点或订阅。

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
| **网络辅助** | 查看节点信息、网络状态与所选节点的服务可用性，并支持可选的网络切换提醒。 |
| **服务问题排查** | 可快速查看所选节点的流媒体和 AI 地区状态，另有离线分流排查工具。 |
| **规则维护** | 使用固定版本的分流规则，并补充经过审阅的服务域名。 |

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

配置内置一个 **「网络辅助」** 插件，主要提供：

- **节点信息**：查看节点配置的服务器入口，以及实际代理出口 IP、地区和运营商；可选直连出口对照。
- **网络检测**：检查直连、代理连接与 DNS 解析，区分连接失败和暂时无法确认的结果。
- **解锁检测**：通过所选节点检查流媒体及 AI 服务，区分平台地区支持、网站访问和受限信息；可在插件设置中启用完整检测。
- **网络切换提醒**：网络切换后连续检测失败才提醒，**默认关闭**。

插件仅用于查询和提醒，不会自动更改节点、DNS 或分流设置。

> 解锁检测区分平台响应、CDN 出口地区和普通网页连通；检测结果不能代替实际账号和播放验证。检测结果与注意事项见 [网络辅助说明](./docs/NETWORK_DIAGNOSTICS.md)。

更新配置后，请在 Loon 中刷新插件与脚本。

## 服务与分流问题排查

- [服务与分流排查指南](./docs/ROUTE_DIAGNOSTICS.md)：检查 Spotify、Twitch、Abema、BBC、Line、Reddit、LinkedIn 的已有主域名归属和候选规则覆盖差异；查询预计命中，并通过脱敏日志分类辅助定位问题。
- **解锁检测**：在[「网络辅助」](./release/Network_Diagnostics.plugin)中选中节点并运行，查看 Netflix、Disney+、YouTube Premium、Spotify、TikTok 及 AI 服务地区状态；不在后台自动运行。
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

[历史版本](https://github.com/YohakuSama/loonkit/releases) · [当前配置校验](./docs/RELEASE_CHECKSUM_v6.3.9.md)

---

<p align="center"><sub>LoonKit 是社区配置项目，与 Loon 官方无关联。</sub></p>
