# LoonKit v6.0.0

适用于 [Loon](https://nsloon.app/) 的分流、策略组与广告拦截配置。**不包含代理节点**，请自行添加节点或订阅。

## 选择正式配置

| 配置 | DNS / DoH | 订阅地址 |
| --- | --- | --- |
| 标准版 | 阿里 AliDNS | [LoonKit.lcf](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf) |
| DNSPod 版 | 腾讯 DNSPod | [LoonKit.PrivacyDNS.lcf](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.PrivacyDNS.lcf) |

在 Loon 中通过 URL 导入其中一份完整配置，再添加自己的代理节点订阅并选择策略组。两份配置使用相同的规则、策略和插件，仅 DNS 解析设置不同。

## 功能与更新

- **分类分流**：国内直连；AI、搜索、流媒体、社交及游戏等分类选择策略。
- **节点策略**：`Proxy`、`Auto`、`Fallback`；`Final` 处理未命中的连接。
- **广告拦截**：`AdBlock` 在 `REJECT` / `DIRECT` 间切换。
- **DNS**：标准版使用 AliDNS DoH，DNSPod 版使用 DNSPod DoH，其他现有 DNS/TUN/IPv4/IPv6 参数保持原样。
- **诊断插件**：[网络诊断](./plugins/Network_Diagnostics.plugin)，查看节点出口和 DNS 状态。
- **远程规则**：26 份版本固定规则，更新需先生成候选并通过审核，不会自动替换正式资源。

## 文档

[规则与来源](./rules/README.md) · [DNS 使用说明](./docs/DNS_PRIVACY.md) · [插件指南](./docs/NETWORK_DIAGNOSTICS.md) · [更新记录](./docs/CHANGELOG.md) · [维护流程](./docs/MAINTAINING.md) · [第三方许可](./docs/THIRD_PARTY_NOTICES.md)

[GitHub Issues](https://github.com/YohakuSama/loonkit/issues)
