# DNS 设置与检查（v6.5.3）

当前配置及 DNS 设置详见 [LoonKit.lcf](../LoonKit.lcf)。

| 项目 | 现有配置 |
| --- | --- |
| 普通 DNS | `223.5.5.5,223.6.6.6` |
| DoH | `https://dns.alidns.com/dns-query` |
| DNS 劫持 | `hijack-dns = *:53` |
| IP 模式 | `ip-mode = dual` |
| IPv6 虚拟接口 | `ipv6-vif = auto` |

`interface-mode`、`skip-proxy`、`bypass-tun` 与 `real-ip` 的具体内容以正式配置为准。

在 Loon 中导入完整配置后添加自己的节点订阅，并确保策略组已选中可用节点。若需要避免加密 DNS 故障时回退到普通 UDP DNS，可在 Loon 的 DNS 设置中关闭「加密 DNS 失败回退到普通 DNS」；此操作可能导致 DoH 不可达时无法解析。

按照 [Loon DNS 文档](https://nsloon.app/docs/DNS/)，同时配置普通 DNS 与 DoH 时可能发生并行查询或故障回退。需要限制明文回退时，可在 Loon 中关闭「加密 DNS 失败回退到普通 DNS」并结合应用日志核对实际解析结果。

公网出口 IP、DNS 解析器与具体 DNS 请求的传输方式是不同的指标。对于应用内置的 DoH/DoT 请求，可结合 Loon DNS 日志、请求策略及[网络辅助](./NETWORK_DIAGNOSTICS.md)进一步排查。

参考：[Loon DNS 文档](https://nsloon.app/docs/DNS/)。
