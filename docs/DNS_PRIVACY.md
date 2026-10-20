# LoonKit v6.0.0 — DNS 设置与检查

当前唯一的正式配置是 [LoonKit.lcf](../LoonKit.lcf)。本次清理未修改配置中的任何 DNS、DoH、TUN、IPv4 或 IPv6 参数。

| 项目 | 现有配置 |
| --- | --- |
| 普通 DNS | `223.5.5.5,223.6.6.6` |
| DoH | `https://dns.alidns.com/dns-query` |
| DNS 劫持 | `hijack-dns = *:53` |
| IP 模式 | `ip-mode = dual` |
| IPv6 虚拟接口 | `ipv6-vif = auto` |

`interface-mode`、`skip-proxy`、`bypass-tun` 与 `real-ip` 的具体内容以正式配置为准。

在 Loon 中导入完整配置后添加自己的节点订阅，并确保策略组已选中可用节点。若需要避免加密 DNS 故障时回退到普通 UDP DNS，可在 Loon 的 DNS 设置中关闭「加密 DNS 失败回退到普通 DNS」；此操作可能导致 DoH 不可达时无法解析。

**注意：** 根据 Loon DNS 官方说明，同时配置普通 DNS 与 DoH 时优先加密解析，但可能并行查询多个服务器并采用较快的结果；默认加密 DNS 故障时还可能回退普通 DNS。因此配置存在 `doh-server` 不能单独证明每次 DNS 查询都走了 DoH。如对明文回退敏感，请关闭应用中的「加密 DNS 失败回退到普通 DNS」选项，结合 DNS 日志确认行为。

网站显示的公网出口 IP 与 DNS 解析器身份并非同一概念。DNS 检测站显示 AliDNS 不等于证明明文泄漏；`hijack-dns = *:53` 也不能拦截所有应用自带 DoH/DoT。必要时结合 Loon DNS 日志、网络请求策略与[网络诊断插件](./NETWORK_DIAGNOSTICS.md)检查。

参考：[Loon DNS 文档](https://nsloon.app/docs/DNS/)。
