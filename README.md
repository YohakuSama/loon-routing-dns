# Loon Routing DNS

> **复合型规则库建设中（不会影响当前稳定配置）：** 本项目将以已使用的上游 Loon 规则为基础，逐步增加 AI、社交、流媒体等补全来源，并建立统一的去重、冲突审计、来源追踪和定期更新机制。之所以采用复合型方案，是因为实际使用中发现部分特殊场景存在可能影响体验、且不符合现阶段精细化分流规划的遗漏与交叉覆盖；这不代表原作者的项目整体有问题，也不能把 DNS、节点或 CDN 问题一概归因于规则。新增来源先在独立分支测试，**不直接堆叠到现有配置**。详细原则、规则来源、版权声明、更新与回滚方案见 [复合规则库建设说明](./rules/README.md)。

一份面向 **Loon iOS** 的第三方完整配置：国内直连、国外按策略代理、AliDNS 加密解析、广告拦截，以及常用服务与 CDN 分流。

**版本：v4.4.8 · AliDNS**　·　[获取配置](https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/Loon_Routing_DNS.lcf)　·　[查看源码](./Loon_Routing_DNS.lcf)　·　[报告问题](https://github.com/YohakuSama/loon-routing-dns/issues)

> **这是完整配置（已内置项目控制台插件），但不包含代理节点。** 导入后仍需添加自己的节点订阅。请先备份原配置、私人订阅地址和个人修改；本项目与 Loon 官方无关联。

**图标：** 33 枚策略组图标已由本项目自行托管，参见 [icons](./icons/README.md)。

## 一、首次使用：先完成这 4 步

### 1. 备份并导入配置

在 Loon 中备份当前配置，**单独保存自己的节点订阅 URL**。新的完整配置不会自动合并旧订阅。

复制配置地址：

```text
https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/Loon_Routing_DNS.lcf
```

在 **Loon → 配置文件 →「＋」→ 从链接导入** 粘贴并导入，再切换到此配置。菜单名称可能因 App 版本略有差异。

**控制台自动包含在配置内：** 导入后进入 **Loon → 配置 → 插件**，确认能看到「Loon Routing DNS · 控制台」。无需额外订阅插件。若以前已经单独导入过相同 URL，请在插件列表检查是否重复，保留一个有效条目即可；如果加载失败，先手动更新远程资源并查看 Loon 日志。

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
| `Final` | `Proxy`（当前默认） | 未匹配到其他规则时走代理；可手动改为 `DIRECT`，但海外冷门域名可能直连失败 |
| `AdBlock` | `REJECT` | 启用广告过滤 |
| `Apple` / `Microsoft` / `Bilibili` | `DIRECT` | 常见可直连服务 |
| `AI`、流媒体、社交平台 | 默认 `Proxy` | 可分别指定不同地区节点 |
| `Steam` | `Proxy` | 国际服务代理，部分国内下载 CDN 单独直连 |

**验证完成：** 节点列表非空、远程规则正常加载、国内网站可用、国外网站按所选策略访问。

### 已内置：Loon Routing DNS 控制台 v1.3

完整配置的 `[Plugin]` 段已经引用并启用本项目控制台。**无需另外复制订阅地址、无需手动添加插件。** 导入完整配置并更新资源后，在 **Loon → 配置 → 插件** 查找「Loon Routing DNS · 控制台」，进入参数页面即可调整项目的检测设置。

**[查看控制台 12 项参数、工具和触发检查方法](./docs/NETWORK_DIAGNOSTICS.md)** · [查看插件源码](./plugins/Network_Diagnostics.plugin)

控制台使用独立图标，提供「状态与参数摘要」「手动网络和 DNS 诊断」「模拟网络变化诊断」「节点详情查询」四个手动功能，以及仅在网络变化时运行的轻量诊断。**正常时默认静默**，需要确认是否真正触发时，可以暂时打开「每次网络变化都通知」，在 Wi-Fi 和蜂窝网络之间切换，并查看最新检测时间。

控制台参数能调整 **探测网址、DoH 测试地址、超时、IP 情报来源与备用源、情报缓存时长**，但**不会修改 Loon 原生测速、DNS、代理模式、策略组选择或 VPN 状态**。**DIRECT 公网 IP 对照默认关闭**，避免普通节点查询时额外向情报服务暴露真实出口。

如不需要诊断功能，可直接在 Loon 的插件页面关闭本控制台；**主配置的 DNS 与分流规则不依赖它**。更新旧版个人配置时请备份自己的插件参数及私人订阅信息。

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
| 导入后看不到内置控制台 | 在 **配置 → 插件** 检查是否启用，更新插件资源；若之前手动安装过，清理重复条目 |
| 某个国内应用异常走代理 | 查看是否命中国内直连规则；未命中的流量由默认 `Final → Proxy` 处理，可针对具体域名补精准 DIRECT |
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

配置直链指向 `main` 分支最新版 `Loon_Routing_DNS.lcf`，同时包含一个启用的控制台插件引用。更新前先备份自己的订阅、插件参数和手动规则。

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
| 策略组和控制台图标 | [本仓库 icons](./icons/README.md)（已自托管；部分品牌造型以 Simple Icons 为基础） |
| 公共解析服务 | [AliDNS](https://alidns.com/) |

配置默认 `disable-stun = true`、`udp-fallback-mode = REJECT`，用于减少部分 STUN/WebRTC 地址暴露及不支持 UDP 时的意外直连，但可能影响实时语音视频，不保证绝对防泄漏。

有问题请提交 [Issue](https://github.com/YohakuSama/loon-routing-dns/issues)，尽量提供 Loon/iOS 版本、网络环境、出问题的域名或 App、命中策略、DNS 错误记录，以及 `AdBlock` 开关前后的结果。

**不要公开订阅 URL、节点凭据、未脱敏日志或个人信息。**

---

维护者：[YohakuSama](https://x.com/yohakusama) · 第三方社区项目，与 Loon 官方无关联。
