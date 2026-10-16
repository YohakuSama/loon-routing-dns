# Loon Routing DNS

一份面向 **Loon iOS** 的第三方完整配置：国内直连、国外按策略代理、AliDNS 加密解析、广告拦截，以及常用服务与 CDN 分流。

**版本：v4.4.6 · AliDNS**　·　[获取配置](https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/Loon_Routing_DNS.lcf)　·　[查看源码](./Loon_Routing_DNS.lcf)　·　[报告问题](https://github.com/YohakuSama/loon-routing-dns/issues)

> **这是完整配置，不是插件，也不包含节点。** 导入后必须添加自己的节点订阅。请先备份原配置和订阅地址。本项目与 Loon 官方无关联。

## 一、首次使用：先完成这 4 步

### 1. 备份并导入配置

在 Loon 中备份当前配置，**单独保存自己的节点订阅 URL**。新的完整配置不会自动合并旧订阅。

复制配置地址：

```text
https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/Loon_Routing_DNS.lcf
```

在 **Loon → 配置文件 →「＋」→ 从链接导入** 粘贴并导入，再切换到此配置。菜单名称可能因 App 版本略有差异。

### 2. 添加自己的节点订阅

在 Loon 的远程节点管理中添加并更新自己的订阅。也可以编辑配置文件的 `[Remote Proxy]` 段，按照 Loon 语法添加一行，例如：

```ini
[Remote Proxy]
MySubscription = https://example.com/subscription.txt,enabled=true
```

**上面是无效的演示地址，必须替换成自己的订阅。** 不要把含令牌的订阅链接上传至公开仓库。

### 3. 设置 Loon：这几项不要混淆

| 设置位置 / 项目 | 推荐设置 | 原因 |
|---|---|---|
| **Loon 运行模式** | **RULE（规则）** | 用策略组决定国内直连、国外代理 |
| **DNS 服务器 → DoH 流量模式** | **DIRECT（直连）** | 阿里云 DoH 在国内可直接连接，无须经过代理规则 |
| **DNS 服务器 → 加密 DNS 查询回退** | **关闭** | 防止 DoH 失败后静默回退到普通明文 DNS |
| **配置 → 高级配置 → 排除路由 `0.0.0.0/31`** | **关闭** | 避免使用隐藏 VPN 图标的方式影响网络兼容性 |

**注意：两个“模式”完全不同。** 整体运行模式仍然使用 `RULE`；只有 **DoH 流量模式使用 `DIRECT`**。不要为了直连 DNS，把整个 Loon 切成全局直连。

**关闭加密 DNS 回退是必须手动进行的 App 设置，配置文件无法替你关闭。** 在关闭前建议确认 AliDNS DoH 可以访问；关闭后如果加密 DNS 故障，网站可能无法解析，这是不使用明文 DNS 回退的代价。遇到这种情况应先检查/恢复 DoH 连接，不要长期依靠关闭 Loon 解决。

### 4. 更新规则并选择节点

在 Loon 内更新节点订阅和远程规则，确认没有资源加载失败。进入 `Proxy` 选择一个能正常连接的节点，或选择 `Auto`。

初次使用建议保持：

| 策略组 | 推荐选择 | 用途 |
|---|---|---|
| `Proxy` | 可用节点或 `Auto` | 主要代理出口 |
| `Auto` / `Fallback` | 默认 | 自动测速 / 故障转移 |
| `Final` | `Proxy` | 未匹配到其他规则时走代理 |
| `AdBlock` | `REJECT` | 启用广告过滤 |
| `Apple` / `Microsoft` / `Bilibili` | `DIRECT` | 常见可直连服务 |
| `AI`、流媒体、社交平台 | 默认 `Proxy` | 可分别指定不同地区节点 |
| `Steam` | `Proxy` | 国际服务代理，部分国内下载 CDN 单独直连 |

**验证完成：** 节点列表非空、远程规则正常加载、国内网站可用、国外网站按所选策略访问。

### 可选插件 v1.2：网络诊断 + 节点详情

**[安装 Loon Network Diagnostics & Node Intelligence](https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/plugins/Network_Diagnostics.plugin)** · [查看插件使用教程](./docs/NETWORK_DIAGNOSTICS.md)

主配置无需安装插件也能正常工作。本插件包含三项独立功能：

- **手动网络诊断：** 检测 DIRECT、AliDNS DoH、Proxy，并在 **Loon Build 988+** 上通过 `$dns.query()` 查询 Loon 原生 DNS 栈，显示解析协议、A/AAAA 记录数量和缓存状态。Build 983–987 会自动跳过原生功能。
- **网络切换故障诊断：** Wi-Fi / 蜂窝变化后进行轻量检测，异常复测和去重通知。**不负责开启/关闭 VPN，也不切换 RULE/DIRECT 模式**。
- **节点详情查询：** 获取实际出口 IP、ASN、运营商、所在国家/城市、疑似机房或移动网络标记，并与本地 GeoIP/ASN 数据交叉核对；从明确节点入口执行时可短时缓存结果。

**隐私改进：DIRECT 出口对照默认关闭。** 只有手动开启参数「同时查询本地 DIRECT 出口」，才向第三方情报 API 额外查询真实直连公网 IP；即便关闭，查询代理节点时情报商仍可看到代理出口 IP。

配置页 → 插件 → ＋ → 从 URL 导入，启用后在通用脚本中使用「手动网络诊断」或「节点详情查询」。插件还拥有独立图标。节点 IP 类型是数据库推断，**不等于证明真家宽或精确机房位置**。

## 二、DNS：默认值与自行替换

默认配置使用免费的 **阿里云公共 DNS（AliDNS）**，不需要注册账户：

```ini
[General]
dns-server = 223.5.5.5,223.6.6.6
doh-server = https://dns.alidns.com/dns-query
hijack-dns = *:53
```

**默认 DoH 走 DIRECT，不需要额外添加 `DOMAIN,dns.alidns.com,DIRECT` 规则。** 项目中已去掉旧版这条冗余规则。不要把 DoH 模式改回 RULE，除非你有明确的自定义路由需要。

### 想换成自己的 DNS？

打开当前配置的 `[General]`，按自己的服务商资料更换：

- `dns-server`：传统 DNS 的 IP 地址，用英文逗号分隔；它们不是 DoH 地址。
- `doh-server`：服务商提供的**完整 HTTPS URL**，不要自行猜测路径。
- `hijack-dns`：一般无需修改。

如果使用个人 NextDNS、NovaXNS 等配置，不要将带有个人 ID、令牌或其他凭据的地址推送到公开 GitHub。更换至国外 DoH 时，要先验证 **DIRECT 下在当前网络能否连接**；不能保证每个国外 DoH 都可在中国大陆直接使用。

### 为什么保留传统 DNS，却要求关闭回退？

Loon 在同时配置传统 DNS 和加密 DNS 时，优先使用加密 DNS；默认情况下加密 DNS 失败可能回退到传统 DNS。**关闭“查询回退”之后，传统 DNS 地址仍出现在文件里，不代表网页请求会按默认回退策略使用它们。**

`hijack-dns = *:53` 处理传统 53 端口查询，不能劫持所有应用自带的 DoH。DoH 只加密 DNS 传输，解析服务商仍会接收查询域名，因此 **DoH 不等于匿名，也不能保证绝对零泄漏**。

### 如何判断 DNS 是否正常？

建议先查看 **Loon → DNS 记录 / 请求记录**，确认实际查询使用 AliDNS DoH；再用 [DNSLeakTest](https://www.dnsleaktest.com/) 和 [BrowserLeaks DNS](https://browserleaks.com/dns) 交叉参考。

- **没有 DoH 记录、只有普通 DNS：** 检查 DoH 服务器地址、流量模式是否 DIRECT、是否已关闭回退、网络能否直连 AliDNS。Loon 的展示方式可能因版本不同，必要时查看错误日志。
- **DNS 的 IP、ASN、国家和代理节点不同：** 不一定是泄漏；DNS 解析器与网页代理出口本来就可以在不同位置。
- **检测不到 DNS 服务器：** 不等于零泄漏，可能是测试失败。
- **`GEOIP,CN,DIRECT,no-resolve`：** 为 GEOIP 判断减少额外 DNS 解析；**它不是 DNS 泄漏保护开关**。

## 三、广告拦截及误杀处理

使用 blackmatrix7 的 **Loon 原生 Advertising 规则**及对应域名集合，不再叠加第二套大型广告黑名单，也不默认启用 HTTPS MITM 去广告插件。

日常保持 `AdBlock = REJECT`。出现登录失败、支付页面异常、视频或图片不显示时：

1. 暂时将 `AdBlock` 由 `REJECT` 切为 `DIRECT`，重新尝试。
2. 如果问题消失，在 Loon 请求记录中定位被拒绝的**具体域名**。
3. 在配置的 `[Rule]` 中添加精确放行规则，例如 `DOMAIN,example.com,DIRECT`；把 `AdBlock` 切回 `REJECT` 再验证。
4. 必要时重新打开目标 App、刷新 DNS 缓存或重启 Loon 连接，以排除旧的拒绝结果。

**`DIRECT` 是放行，不是通过代理去广告。** 如果关闭广告拦截后仍然异常，应继续排查服务分流、节点及 DNS。完整广告列表覆盖面大，但无法保证零误杀；本地宽泛平台规则也可能覆盖部分远程广告规则的命中。

## 四、国内与 CDN 分流

国内直连使用 ChinaMaxNoMedia 和 `GEOIP,CN,DIRECT,no-resolve`；Apple 系统更新、Steam 中国区下载有专用规则；Bilibili 默认直连。

配置不锁定 CDN IP、不将共享 CDN（如整个 `akamaized.net`）强制直连。实际速度依赖运营商线路、DNS 位置及 CDN 调度。

IPv4 / IPv6 默认使用 `ip-mode = dual` 和 `ipv6-vif = auto`，允许自动双栈，但不等于永远使用延迟最低的 IP。

## 五、常见问题：直接按症状排查

| 遇到的问题 | 怎么处理 |
|---|---|
| 导入后没有节点、`Proxy` 为空 | **先加自己的节点订阅并更新**；检查 `ALL_Filter` 和订阅是否解析成功 |
| 国内能访问，国外不能访问 | 检查 `Proxy`、`Final` 和实际节点是否可用；核对命中规则 |
| 规则或配置更新失败 | 确认 `raw.githubusercontent.com` 可达；先切回可用配置/节点再更新 |
| 网站全部无法解析 | 检查 AliDNS DoH 的 DIRECT 连接；关闭 DNS 回退后，DoH 故障会更明显 |
| 只有传统 DNS，看不到 DoH | 核对 `doh-server`、**DoH 流量模式 DIRECT** 和 DNS 错误记录 |
| DNS 检测出现不同 ASN | 对照 Loon DNS 记录；单看 ASN 不足以判断泄漏 |
| 某个 App 登录或支付失败 | `AdBlock` 临时切为 `DIRECT` 排除误杀，再添加精确域名例外 |
| Bilibili / App Store 下载异常 | 检查是否命中 DIRECT、远程 CDN 规则是否更新成功 |
| FaceTime / 语音 / 游戏异常 | `disable-stun = true` 可能影响实时通信；备份后可短暂改为 `false` 对照测试 |
| 切换 Wi-Fi / 蜂窝后异常 | 关闭「排除路由 `0.0.0.0/31`」，重新连接 Loon |
| IPv6 不符合预期 | 查看 IPv4/IPv6 出口、节点能力、TUN 接管与实际规则命中 |

建议一次只调整一项：**节点 → DNS → 分流 → 广告 → iOS 兼容性**，避免无法确认问题来源。

## 六、托管更新和个人配置

配置直链指向 `main` 分支最新版 `Loon_Routing_DNS.lcf`。更新前先备份自己的订阅和手动规则。

Loon 的「全覆盖更新」可能影响本地修改；不确定时不要开启。**主配置、节点订阅和远程规则是不同的更新项目**。即使关闭全覆盖，也不能保证所有个人改动会在每次主配置更新后保留。

个人 DoH 地址、节点链接、密钥和 token 请保存在私人配置中，**不要提交到本公开仓库**。

## 七、自动化测试与更新质量

每次向主分支提交修改，都由 [GitHub Actions](./.github/workflows/loon-ci.yml) 运行主配置结构、33 个策略组、28 条远程订阅、插件参数引用、JavaScript 语法及模拟测试。每周及手动触发时，另检查图标、远程规则和脚本 URL 是否可用。

**通过静态检查不代表已经通过 iPhone 上的 Loon 实机验证。** 如远程检测失败，先排除临时的 GitHub 网络故障或限流，再修复已确认的失效链接。

## 八、来源与反馈

| 用途 | 上游项目 |
|---|---|
| Loon 语法与 DNS 机制 | [Loon General](https://nsloon.app/docs/General/) · [Loon DNS](https://nsloon.app/docs/DNS/) |
| 广告、国内分流、平台与 CDN 规则 | [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) |
| 常规策略组图标 | [Hawaiine/Oasisic-Icons](https://github.com/Hawaiine/Oasisic-Icons) |
| Fallback 图标 | [lige47/lige_icon](https://github.com/lige47/lige_icon) |
| 公共解析服务 | [AliDNS](https://alidns.com/) |

配置默认 `disable-stun = true`、`udp-fallback-mode = REJECT`，用于减少部分 STUN/WebRTC 地址暴露及不支持 UDP 时的意外直连，但可能影响实时语音视频，不保证绝对防泄漏。

有问题请提交 [Issue](https://github.com/YohakuSama/loon-routing-dns/issues)，尽量提供 Loon/iOS 版本、网络环境、出问题的域名或 App、命中策略、DNS 错误记录，以及 `AdBlock` 开关前后的结果。

**不要公开订阅 URL、节点凭据、未脱敏日志或个人信息。**

---

维护者：[YohakuSama](https://x.com/yohakusama) · 第三方社区项目，与 Loon 官方无关联。
