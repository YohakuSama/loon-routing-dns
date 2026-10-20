# LoonKit v6.0.0 — DNS 配置与问题排查

LoonKit 提供两份正式配置，使用相同的 26 份远程规则、106 条本地规则、策略组和网络辅助插件；它们各自的 DNS/TUN 参数在仓库清理中保持原样。

| 配置 | DNS | DoH |
| --- | --- | --- |
| [标准版](../LoonKit.lcf) | `223.5.5.5,223.6.6.6` | `https://dns.alidns.com/dns-query` |
| [DNSPod 版](../LoonKit.PrivacyDNS.lcf) | `119.29.29.29` | `https://doh.pub/dns-query` |

两份配置都保留 `hijack-dns = *:53`、`ip-mode = dual`、`ipv6-vif = auto` 及原有 `interface-mode`、`skip-proxy`、`bypass-tun`、`real-ip`。不建议只为完成仓库更新去更改这些参数。

## 首次导入

在 Loon 中先备份现有配置和节点订阅，再导入其中一份配置 URL，添加自己的代理节点订阅，确认 `Proxy` 策略可用并更新远程规则和插件。中国大陆的部分网络可能无法直连 `raw.githubusercontent.com`，必要时可先本地导入已保存的配置，再恢复可用节点下载远程资源。

## DNS 与代理出口是不同的指标

- 网站显示的公网 IP 是该连接的网络出口；如果显示了本机运营商 IP，应先检查命中的规则、`Final` 策略、代理节点和 Loon 工作模式。
- 检测站显示 AliDNS 或 DNSPod 的解析器地址，并不能单独证明 DNS 明文泄漏。DoH 解析器和代理出口可能位于不同地区。
- `hijack-dns = *:53` 作用于传统 53 端口解析，不等于拦截所有应用内置 DoH/DoT；浏览器、系统其他 VPN 和代理端 DNS 也可能参与解析。
- `ip-mode = dual` 允许 IPv4/IPv6；`GEOIP,CN,DIRECT,no-resolve`、ASN 的 `no-resolve` 与最终网络路径应结合 Loon 请求日志判断，不能只看 DNS 检测网页。
- `Final` 可以选择 `DIRECT`，选择它会使未命中其他分流规则的连接直连；`AdBlock` 在 `DIRECT` 下也不会拒绝匹配的广告流量。

## 排查顺序

1. 确认当前使用的是标准版还是 DNSPod 版，以及是否已恢复节点、策略组和最新规则。
2. 在 Loon 的 DNS 服务器设置中核查「加密 DNS 失败回退到普通 DNS」的开关。如果需要避免故障时使用普通 UDP DNS，应将该回退关闭；关闭后 DoH 不可达可能导致解析失败。
3. 打开 [网络辅助插件](./NETWORK_DIAGNOSTICS.md) 的「网络与 DNS 诊断」，检查 `protocol`、`server`、`fromCache` 和 Loon DNS 日志。若 `protocol=udp`，此次 Loon DNS 查询使用普通 DNS；缓存命中并不代表发生了新查询。
4. 在同一个节点、同一网络和同一时段对照 Loon 请求命中、出口 IP、DNS 记录、IPv4/IPv6。检查浏览器是否启用了单独的安全 DNS 设置。
5. 如需定位无法解释的实际 DNS 请求路径，应结合设备或网络侧流量记录；单一网站测试不能给出全部结论。

参考：[Loon DNS 文档](https://nsloon.app/docs/DNS/) · [Loon 通用配置](https://nsloon.app/docs/General/) · [DNSPod 文档](https://cloud.tencent.com/document/product/302/110786)。
