# LoonKit DNS 隐私与路由排查（2026-10-18）

## 先关闭 Loon 的明文 DNS 回退

1. 备份现有 Loon 配置和节点订阅，导入最新 `LoonKit.lcf`；确保 Loon 工作于规则模式并已配置可用节点。
2. **前往 Loon > DNS 服务器，关闭「加密 DNS 失败回退到普通 DNS」**。官方文档明确说明此回退默认开启，目前不能通过已验证的 `[General]` 配置键代替这个 App 开关。
3. 本项目默认使用单一 Cloudflare DoH：`https://cloudflare-dns.com/dns-query`；`[Host]` 将解析器域名固定为 `1.1.1.1`，避免引导解析器时再做普通 DNS 查询。固定映射并不意味着 HTTPS 请求必然经过代理。
4. `dns-server = 223.5.5.5` 仍存在，作为兼容性及应急备用；**如果回退开关开启，DoH 故障时仍可产生明文 DNS 查询**。如果所在网络阻断 DoH，关闭回退可能使解析失败，这是明确的安全/可用性取舍。
5. 运行插件「网络与 DNS 诊断」（Build 988+），检查 `$dns.query` 的 `protocol`、`server`、`fromCache`。预期为 `doh` 及 Cloudflare 的 URL。若为 `udp` 则说明此次 Loon DNS 查询使用明文；如果命中缓存，就不能据此断定本次发生网络查询。
6. 在 Loon 的 DNS 日志以及请求日志复查其他域名；排除自定义 `[Host]`、SSID DNS、其他插件、节点配置、Safari/浏览器安全 DNS、其他 VPN 和 iCloud Private Relay 的干扰。

## DNS 解析并不等于代理出口

- `hijack-dns = *:53` 拦截传统 UDP/53，无法拦截所有 App 自带 DoH/DoT，更无法强制第三方解析器通过代理出口。
- DoH 加密并不表示 DNS 服务器与代理节点处于同一地区，DNS 检测网页看到 Cloudflare 而代理出口是另一个 IP **不必然是明文泄漏**。
- 如果希望远程站点在代理出口处解析域名，需要进一步核实使用的节点协议是否进行远端解析，并结合 Loon 的实际流量、DNS 日志和设备抓包；不能用本配置单独保证。
- 现有 `GEOIP,CN,DIRECT,no-resolve` 保留 `no-resolve`，是为了不因匹配国内 IP 而强迫原本可能远端解析的域名先在本地解析。未命中的国内域名可能落入最终 Proxy，推荐补充明确、可审计的国内域名规则，而不是无条件移除该标志。
- `ip-mode = dual` 会允许 IPv4 和 IPv6。DNS 与应用使用的 IPv6 路径都应单独检查；禁止 STUN 只能降低部分 WebRTC IP 暴露风险，不等于阻止 DNS 泄漏。

## 最小化复测

- 停止并重新启动 Loon 清除缓存，确认规则模式与最新配置已生效。
- 正常网络下检查测试结果是否是 `doh / https://cloudflare-dns.com/dns-query`，再检查国内服务与国外服务的日志策略。
- 在可控测试环境中阻断 DoH 请求后复测：若关掉了明文回退，预期是解析失败，不是静默使用 UDP。
- 若定位到浏览器或某 App 自带 DNS，则在该应用中检查其 DoH/安全 DNS 选项；先确认隐私需求，再决定是否改动。
- 遇到 DNS 失败不要为了恢复联网默认启用明文回退，先找出网络阻断、TLS/SNI 或代理节点问题。

## 参考

- [Loon DNS 查询与回退](https://nsloon.app/docs/DNS/)
- [Loon DNS 映射](https://nsloon.app/docs/DNS/hostmap/)
- [Loon 脚本 DNS API](https://nsloon.app/docs/Script/script_api/)
- [Loon IP 规则与 no-resolve](https://nsloon.app/docs/Rule/ip_rule/)

本文件说明修复与边界，不宣称可以通过单一网页测试证明整个设备不存在 DNS 泄漏。