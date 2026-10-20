# LoonKit v6.0.0

适用于 [Loon](https://nsloon.app/) 的分流策略和广告拦截完整配置。节点订阅请自行添加。

**唯一正式配置：** [LoonKit.lcf](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf)

在 Loon 中通过 URL 导入配置，添加代理节点后更新远程规则与插件，并在策略组中选择节点。

## 功能

- **策略分流：** 国内服务直连，AI、搜索、流媒体、社交和游戏分组独立选路。
- **代理选择：** `Proxy`、`Auto`、`Fallback`；`Final` 决定未命中的连接如何处理。
- **广告拦截：** `AdBlock` 可在 `REJECT` 和 `DIRECT` 间切换。
- **DNS：** 采用 AliDNS DoH（`https://dns.alidns.com/dns-query`），现有 DNS/TUN/IPv4/IPv6 参数保持不变。
- **规则与插件：** 26 份固定版本远程规则与[网络诊断插件](./release/phase-07/assets/Network_Diagnostics.plugin)，不会因上游更新而自动改写。

## 文档

[DNS 配置](./docs/DNS_PRIVACY.md) · [规则与来源](./rules/README.md) · [网络诊断](./docs/NETWORK_DIAGNOSTICS.md) · [更新记录](./docs/CHANGELOG.md) · [维护](./docs/MAINTAINING.md) · [第三方许可](./docs/THIRD_PARTY_NOTICES.md)

[提交问题](https://github.com/YohakuSama/loonkit/issues)
