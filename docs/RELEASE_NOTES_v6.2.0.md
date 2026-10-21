# LoonKit v6.2.0

这次将服务诊断合并进现有「网络辅助」，在 Loon 中使用一个插件即可查看网络、DNS、节点出口和七项服务的连接情况。

## 主要更新

- **统一网络辅助插件**：节点出口信息、网络与 DNS 诊断、服务连通性诊断集中到一个插件；网络切换提醒仍默认关闭。
- **精简服务诊断结果**：主站及关联 HTTPS 端点返回 200、301、403、404 等，明确显示“端点有响应”，不再将 favicon 缺失误判为应用故障；超时、证书错误和服务端 5xx 另行提示。
- **补充 DNS 检查**：手动检测服务时使用 Loon 原生 DNS API 查看 A/AAAA 记录；无 AAAA 记录不代表 IPv6 故障，旧版本不支持该 API 时不会误报断网。
- **分流配置不变**：保留 v6.1.0 的七项服务精选规则、26 份固定远程规则、33 个策略组、广告拦截、DNS、IPv6、TUN 和现有节点策略。

## 安装

1. 备份已有节点、订阅和个性化配置。
2. [下载最新 LoonKit.lcf](https://github.com/YohakuSama/loonkit/releases/download/v6.2.0/LoonKit.lcf) 并导入。
3. 在 Loon 中刷新插件及脚本资源；打开一个「网络辅助」插件，通过「检测服务」选择需要检查的服务，再手动运行「服务连通性诊断」。

**注意：** 如果此前单独安装了「服务连通性诊断」插件，请在 Loon 中删除旧的单独安装项，避免列表中保留两个入口。v6.2.0 配置本身只引用一个插件。

诊断结果只能说明端点连接或 DNS 解析情况，不代表账号登录、视频播放、地区限制或所有运营商网络都可正常使用。Loon 的真实请求命中与 UDP/IPv6 行为仍需在实际网络环境核查。本次版本的真机验收由使用者完成。

[使用说明](https://github.com/YohakuSama/loonkit#readme) · [校验配置](https://github.com/YohakuSama/loonkit/blob/main/docs/RELEASE_CHECKSUM_v6.2.0.md) · [反馈问题](https://github.com/YohakuSama/loonkit/issues)
