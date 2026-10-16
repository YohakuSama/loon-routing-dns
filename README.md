# Loon Routing DNS

面向 **Loon iOS** 的第三方分流配置：国内网站直连、国外服务按策略连接、DoH、广告过滤、平台独立策略组及必要的 CDN 直连。

**当前版本：v4.4.5 · AliDNS**

**[配置直链](https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/Loon_Routing_DNS.lcf)** · [查看配置](./Loon_Routing_DNS.lcf) · [报告问题](https://github.com/YohakuSama/loon-routing-dns/issues) · [作者 X](https://x.com/yohakusama)

> 这是一份**完整配置，不是插件**。不提供代理节点、机场或订阅链接。第一次使用需要自己添加节点订阅。项目与 Loon 官方无关联。

## 1. 首次安装：从零开始

**第一步：备份。** 在 Loon 中备份正在使用的配置，并单独保存自己的机场订阅 URL。切换到本项目配置后，原订阅**不会自动合并**。不要把私人订阅链接上传到 GitHub。

**第二步：导入。** 复制以下地址：

```text
https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/Loon_Routing_DNS.lcf
```

打开 **Loon → 配置文件 → 右上角「＋」→ 从链接导入**，粘贴并导入，然后切换到该配置。运行模式保持 **RULE（规则）**。

**第三步：添加节点订阅（必须）。** 通过 Loon 远程节点管理添加自己的订阅，或编辑当前配置的 `[Remote Proxy]` 部分，例如：

```ini
[Remote Proxy]
MySubscription = https://example.com/subscription,enabled=true
```

这是占位示例，须替换为自己的有效订阅地址。保存后更新订阅。没有节点时，`Proxy`、`Auto`、`Fallback` 都无法提供代理连接。

**第四步：更新并选择策略。** 在 Loon 中更新节点订阅和远程规则，确认没有下载或解析错误。打开 `Proxy` 选择一个可用节点，或选 `Auto`，然后检查国内网站和国际网站能否正常访问。

| 策略组 | 建议 | 作用 |
|---|---|---|
| `Proxy` | 手动选节点，或选 `Auto` | 主要代理出口 |
| `Auto`、`Fallback` | 默认即可 | 自动测速 / 故障转移 |
| `Final` | `Proxy` | 未命中规则时的兜底策略 |
| `AdBlock` | `REJECT` | 拦截命中的广告和跟踪请求 |
| `Apple`、`Microsoft`、`Bilibili` | `DIRECT` | 常见直连服务 |
| `AI`、视频与社交平台 | 默认跟随 `Proxy` | 必要时单独切换节点 |
| `Steam` | `Proxy` | 国际服务走代理，部分国内 CDN 直连 |

如果 `Proxy` 中没有可选节点，先解决订阅问题，而不是更换 DNS。

## 2. DNS 与 Loon 必要设置

默认使用**阿里云公共 DNS**，无需注册个人账户：

```ini
dns-server = 223.5.5.5,223.6.6.6
doh-server = https://dns.alidns.com/dns-query
hijack-dns = *:53
```

请在 Loon 中核实这些设置：

- **运行模式：RULE**。
- **DoH 流量模式：RULE**。本地 `DOMAIN,dns.alidns.com,DIRECT` 使 DoH 请求选择直连。
- **加密 DNS 回退：先验证 DoH 成功后再决定是否关闭。** 关闭回退后 DoH 出故障可能造成域名解析失败；开启则可能退回明文 DNS。
- **配置 → 高级配置 → 排除路由 `0.0.0.0/31`：关闭。** 不建议使用隐藏 VPN 图标的技巧，可能导致 iOS 网络异常。这项设置不能靠导入配置自动关闭。

默认使用 `ip-mode = dual`、`ipv6-vif = auto` 支持双栈网络，但不代表始终自动选出最低延迟的 IP。

**DoH 不是匿名服务。** HTTPS 可保护查询的传输过程，阿里云作为上游 DNS 仍能处理用户查询的域名。`hijack-dns = *:53` 也不能拦截所有第三方加密 DNS。

### DNS 检测结果怎么读？

可结合 [DNSLeakTest](https://www.dnsleaktest.com/)、[BrowserLeaks DNS](https://browserleaks.com/dns) 与 **Loon 的 DNS/请求记录**检查：

- DNS 服务器的 **ASN 或国家与代理出口不同，不一定是 DNS 泄漏**。检测站通常显示递归解析器的出口。
- 如果 Loon 只有传统 DNS 记录，先检查 DoH 连接是否成功、是否启用了回退。
- `GEOIP,CN,DIRECT,no-resolve` 只是不为 GEOIP 匹配主动解析域名，**不是防 DNS 泄漏的开关**。
- 测试网站显示 0 个 DNS 服务器也不能证明零泄漏，可能是网站测试失败。

## 3. 广告拦截与误杀解决

采用 blackmatrix7 的 Loon 原生 **Advertising 两份配套规则**，不重复加载另一套大型广告黑名单，也不默认配置 MITM 解密去广告插件。

日常保持 `AdBlock = REJECT`。如果出现 App 登录、支付、视频、图片异常，按顺序操作：

1. 临时将 `AdBlock` 改为 `DIRECT`，重试有问题的操作。
2. 如果恢复正常，打开 Loon 请求记录，找到被拒绝的**准确域名**。
3. 在本地 `[Rule]` 增加精确例外（例如 `DOMAIN,example.com,DIRECT`），再把 `AdBlock` 改回 `REJECT`。
4. 必要时重新启动目标 App 或刷新 DNS 缓存，避免旧的拒绝结果影响判断。

`DIRECT` 表示放行，不是代理过滤广告。完整规则可能误杀，也无法去除所有使用相同域名的 App 内广告。本地宽泛的平台域名规则优先于远程规则，可能覆盖部分广告匹配。

## 4. CDN 与国内分流

国内直连使用 ChinaMaxNoMedia 与 `GEOIP,CN,DIRECT,no-resolve`；Apple 系统更新和 Steam 中国区下载使用专用 Loon 原生规则，Bilibili 默认直连。**不锁定 CDN IP，不让共享 CDN 整体直连**，以降低误分流风险。速度仍取决于运营商、节点和 CDN 调度。

## 5. 常见故障：按现象排查

| 现象 | 优先检查 | 解决方法 |
|---|---|---|
| 导入后没有节点 | 是否添加个人订阅 | 添加/更新订阅并确认 `ALL_Filter` 能筛选节点 |
| 国内网站正常，国外网站打不开 | `Proxy` 和 `Final` | 选用可连接的节点，检查命中策略 |
| 配置或远程规则下载失败 | GitHub Raw 连通性 | 先切回可用节点再更新，检查请求错误 |
| 只有传统 DNS，没有 DoH 记录 | DoH 是否建立连接、回退状态 | 检查 `dns.alidns.com` 命中 DIRECT，验证成功后测试关闭回退 |
| DNS 结果出现陌生 ASN | DNS 解析器还是网页出口 | 核对 DNS 服务和 Loon 日志，不仅凭 ASN 判断泄漏 |
| App 登录/支付失败 | 是否被 Advertising 误杀 | `AdBlock` 暂改 DIRECT，再添加精确例外 |
| Bilibili 或国内资源下载慢 | 是否误走代理、CDN 分配 | 查看请求记录，避免写死 CDN IP |
| FaceTime、语音或部分游戏异常 | `disable-stun = true` | 备份后可临时改 false 对照测试，并了解隐私代价 |
| Wi-Fi 与蜂窝切换后断网 | 路由排除选项 | 关闭「排除路由 `0.0.0.0/31`」，重启 Loon 连接 |
| IPv6 出口和预期不同 | 节点双栈支持、流量接管 | 检查 IPv4/IPv6 出口、TUN 与分流日志 |
| 关闭 Loon 后正常，开启后异常 | DNS、广告和策略组 | 依次排查；一次只改变一个设置 |

**排查顺序：** 节点可用性 → DNS → 命中规则 → 广告误杀 → iOS 网络兼容性。不要同时更换多个参数。

## 6. 更新配置而不丢订阅

主配置 URL 始终指向 `main` 分支最新的 `Loon_Routing_DNS.lcf`。托管更新前请备份个人修改、节点订阅和手动规则。

如 Loon 显示「全覆盖更新」，请先阅读应用对节点、证书和本地修改保留行为的说明。不了解后果时，**不建议贸然开启全覆盖更新**。主配置、个人节点订阅和远程规则是独立的更新资源。

## 7. 来源与隐私说明

| 组件 | 上游 |
|---|---|
| Loon 配置文档 | [Loon 官方](https://nsloon.app/docs/General/) |
| 广告、国内直连、平台与 CDN 规则 | [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) |
| 策略组图标 | [Hawaiine/Oasisic-Icons](https://github.com/Hawaiine/Oasisic-Icons) |
| Fallback 图标 | [lige47/lige_icon](https://github.com/lige47/lige_icon) |
| DNS | [阿里云公共 DNS](https://alidns.com/) |

旧版未被配置引用的本地图标不再随仓库维护。第三方规则及图标的使用许可以其上游项目为准。

`disable-stun = true` 和 `udp-fallback-mode = REJECT` 可减少部分 WebRTC/STUN 地址暴露和 UDP 意外直连，但可能影响实时通信，**不能保证完全防止 DNS 或 WebRTC 泄漏**。

## 反馈问题

请通过 [GitHub Issues](https://github.com/YohakuSama/loon-routing-dns/issues) 反馈。尽量提供 Loon 与 iOS 版本、Wi-Fi/蜂窝环境、故障 App/域名、命中策略、DoH 记录和 `AdBlock` 切换前后的差异。

**请勿上传订阅 URL、节点密钥、账号密码、未脱敏完整日志或其他个人信息。**

---

维护者：[YohakuSama](https://x.com/yohakusama)。第三方社区配置，与 Loon 官方无关联。
