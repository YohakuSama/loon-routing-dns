# LoonKit DNS 隐私与路由排查（2026-10-18）

## 先关闭 Loon 的明文 DNS 回退

1. 备份现有 Loon 配置和节点订阅，导入最新 `LoonKit.lcf`；确保 Loon 工作于规则模式并已配置可用节点。
2. **前往 Loon > DNS 服务器，关闭「加密 DNS 失败回退到普通 DNS」**。官方文档明确说明此回退默认开启，目前不能通过已验证的 `[General]` 配置键代替这个 App 开关。
3. 本项目恢复迁移前的解析配置：`dns-server = 223.5.5.5,223.6.6.6` 加上 `doh-server = https://dns.alidns.com/dns-query`。此前额外添加的 `[Host] dns.alidns.com = 223.5.5.5` 已删除，避免强制覆盖 DoH 域名的正常解析。加密 DNS 不等于请求一定经过代理节点。
4. `dns-server = 223.5.5.5,223.6.6.6` 提供两个阿里大陆公共 UDP DNS 作为兼容性及应急备用；**如果回退开关开启，DoH 故障时仍可产生明文 DNS 查询**。如果所在网络阻断 DoH，关闭回退可能使解析失败，这是明确的安全/可用性取舍。
5. 运行插件「网络与 DNS 诊断」（Build 988+），检查 `$dns.query` 的 `protocol`、`server`、`fromCache`。预期为 `doh` 及 AliDNS 的 URL。若为 `udp` 则说明此次 Loon DNS 查询使用明文；如果命中缓存，就不能据此断定本次发生网络查询。
6. 在 Loon 的 DNS 日志及请求日志复查其他域名，核对是否出现以前版本没有的解析器或出口；其他设置可能影响最终行为，但不应仅因 BrowserLeaks 列出多个服务器就断言有明文泄漏。

## DNS 解析并不等于代理出口

- `hijack-dns = *:53` 拦截传统 UDP/53，无法拦截所有 App 自带 DoH/DoT，更无法强制第三方解析器通过代理出口。
- DoH 加密并不表示 DNS 服务器与代理节点处于同一地区，DNS 检测网页看到阿里 DNS 而代理出口是另一个 IP **不必然是明文泄漏**。
- 如果希望远程站点在代理出口处解析域名，需要进一步核实使用的节点协议是否进行远端解析，并结合 Loon 的实际流量、DNS 日志和设备抓包；不能用本配置单独保证。
- 现有 `GEOIP,CN,DIRECT,no-resolve` 保留 `no-resolve`，是为了不因匹配国内 IP 而强迫原本可能远端解析的域名先在本地解析。未命中的国内域名可能落入最终 Proxy，推荐补充明确、可审计的国内域名规则，而不是无条件移除该标志。
- `ip-mode = dual` 会允许 IPv4 和 IPv6。DNS 与应用使用的 IPv6 路径都应单独检查；禁止 STUN 只能降低部分 WebRTC IP 暴露风险，不等于阻止 DNS 泄漏。

## 规则层回退与历史验证

- 迁移前的工作配置与当前配置 DNS 基本相同，**规则来源和顺序曾有显著差异**：复合库使用 33 个生成分组、远端源超过 80 个，旧版配置使用 28 个原始远程订阅与 66 条显式本地规则。
- 正式版已经恢复旧版 28/66 分流基线；`rules/generated/` 保留作候选但不再默认启用。旧配置曾正常不代表复合规则必然导致了 DNS 泄漏，仍须在同一设备及代理节点下复测 BrowserLeaks。
- 旧版 `Our-*` 生成规则订阅如果仍单独存在于 App 中，应停用以避免新旧两套同时执行；导入完整配置不一定会自动删除单独添加的订阅。
- 私人节点的订阅 URL 含身份验证参数，不应提交到公开 GitHub，也不应发到公开问题页面；若已公开，建议到服务商撤换链接。

## 历史基线与真实设备验证

- 迁移前的正式版已使用 `dns-server = 223.5.5.5,223.6.6.6`、`doh-server = https://dns.alidns.com/dns-query`、`ip-mode = dual` 和 `ipv6-vif = auto`。因此不能把原本存在的 IPv6 配置误判为新版本独有错误。
- 回归补丁仅撤回新增的 DoH 固定 Host 映射并恢复第二个备用 DNS；它能减少相对已知历史版本的变更，但**并不等于已经真机证明 BrowserLeaks 上的多解析器现象被消除**。
- 若 Loon 请求记录显示某域名的出口已代理，DNS 日志只显示 AliDNS DoH，BrowserLeaks 的 Cloudflare 解析器也可能来自所用代理节点/远端递归链路，而非手机明文 DNS 流量。必须结合设备抓包或实际 DNS 查询日志区分。
- 要判断浏览器网站显示真实中国移动出口是否直连，应查对应网站的请求记录、缓存/刷新情况及域名可能的其他服务请求，不能使用不同站点的代理命中记录替代。

## 中国大陆网络及首次下载

- 已移除境外 Cloudflare DoH，改为 `https://dns.alidns.com/dns-query`。该地址由阿里官方运营；不同运营商、区域及网络环境仍可能出现个别不可达，不能保证所有网络均成功。
- `223.5.5.5` 和 `223.6.6.6` 属于阿里公共 DNS，支持中国大陆网络接入；普通 UDP DNS 的查询本身未加密，严格隐私要求下必须关闭 Loon 内的普通 DNS 回退。
- `raw.githubusercontent.com` 是资源托管与下载依赖，部分大陆网络无法直连。DNS 设置无法取代代理节点。首次导入可以使用已保存到设备的 `.lcf` 文件，然后恢复代理节点，再更新远程规则与插件。
- 当前规则 `DOMAIN-SUFFIX,raw.githubusercontent.com,Proxy` 专门让**已经有可用代理节点的设备**下载 GitHub 原始资源，不能自行创造代理连接。

## 最小化复测

- 停止并重新启动 Loon 清除缓存，确认规则模式与最新配置已生效。
- 正常网络下检查测试结果是否是 `doh / https://dns.alidns.com/dns-query`，再检查国内服务与国外服务的日志策略。
- 在可控测试环境中阻断 DoH 请求后复测：若关掉了明文回退，预期是解析失败，不是静默使用 UDP。
- 若定位到浏览器或某 App 自带 DNS，则在该应用中检查其 DoH/安全 DNS 选项；先确认隐私需求，再决定是否改动。
- 遇到 DNS 失败不要为了恢复联网默认启用明文回退，先找出网络阻断、TLS/SNI 或代理节点问题。

## 参考

- [Loon DNS 查询与回退](https://nsloon.app/docs/DNS/)
- [Loon DNS 映射](https://nsloon.app/docs/DNS/hostmap/)
- [Loon 脚本 DNS API](https://nsloon.app/docs/Script/script_api/)
- [Loon IP 规则与 no-resolve](https://nsloon.app/docs/Rule/ip_rule/)

本文件说明修复与边界，不宣称可以通过单一网页测试证明整个设备不存在 DNS 泄漏。
阿里公共 DNS 官方地址：https://alidns.com/。阿里免费公共 DNS 有流量管控与服务限制，是否正常以实际网络测试为准。
