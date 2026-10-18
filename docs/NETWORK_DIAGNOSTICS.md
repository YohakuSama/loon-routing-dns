# Loon Routing DNS · 网络辅助插件 v2.4

随完整配置自动加载的轻量插件。提供 **三个手动入口**与 **一个可选的网络切换提醒**，不修改 Loon 的 DNS、规则、节点、VPN 或代理策略。

## 用户能做什么

| 入口 | 作用 | 限制 |
|---|---|---|
| **节点出口信息** | 显示出口 IP、位置、ASN/ISP/组织、VPN/代理/Tor 标签、可用的风险分数，以及本地 GeoIP/ASN/ASO 对照 | 查询的是公网出口，不一定是节点服务器入口；数据可能不准确 |
| **网络与 DNS 诊断** | 分项检查 DIRECT、Proxy、指定 DoH 服务，以及支持时的 Loon 原生 DNS 查询 | 服务检查不等于 DNS 泄漏测试，不保证所有网站可达 |
| **DNS 解析器泄漏检测** | 手动触发四个随机域名的 Loon 原生 DNS 查询，并通过 bash.ws 权威 DNS 观察实际递归解析器 | 不是“零 DNS 泄漏证明”；需 Loon Build 988+，第三方服务可用且未被拦截；无法采样时明确显示「无法判定」 |
| **网络变化异常提醒** | 可选：Wi-Fi/蜂窝切换后等待网络稳定并复测，连续失败才提醒 | 默认关闭；只有 Loon/iOS 触发事件时才执行 |

**默认配置只有 3 个选项：**

- `auto_check = false`：自动检查关闭，避免默认后台探测及通知。开启后只在 Loon 发出网络变化事件时运行。
- `target_policy = Proxy`：手动查询出口的策略；在有明确节点上下文时优先查询该节点。
- `compare_direct = false`：默认不查询真实直连公网 IP。若开启，将额外向第三方 IP 情报提供商发送 DIRECT 请求，暴露真实出口 IP。

IP 情报固定采用主源 ipquery.io、备用 ipwho.is；网络诊断探测默认使用 AliDNS DoH、vivo 直连 204 与 Cloudflare 代理 204。普通用户不需要配置 API、超时、缓存或诊断地址。

## 导入与版本

完整配置继续使用：

https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/Loon_Routing_DNS.lcf

**正式配置只有在合并本次 PR 后才指向新插件。** 旧版插件保留在 `plugins/v20261018r2/Network_Diagnostics.plugin`，旧版脚本仍为历史订阅保留，不再作为新版用户菜单入口。新版插件位于 `plugins/v20261018r8/`，详细节点情报脚本位于 `scripts/v20261018r5/`，网络诊断继续使用未修改的 `scripts/v20261018r4/`。旧版插件目录保留，方便回滚。

若曾单独订阅旧插件，请避免同时启用新旧两个插件；更新前备份个人参数。旧参数不再有对应功能，需重新开启需要的可选开关。

## 正确理解诊断结果

手动诊断输出每项结果。若原生 DNS 查询失败，**总状态必须显示异常**，不能因为 DIRECT 与 DoH 探测成功而显示“全部正常”。若 Loon 版本没有 `$dns.query`，该项显示“当前版本不支持”，总体为“部分项目不可用”。

独立 HTTP DoH 探测只能说明指定服务器响应情况；它不证明 Loon 全部 DNS 均经 DoH，也不能判断 DNS 泄漏。不同地域、CDN、重定向与网络环境可能返回不同状态，探测失败不必然意味着 Loon 配置错误。

自动模式默认关闭。开启后对 DIRECT 与 DoH 进行快速检查，失败才复测一次；同类提醒 30 分钟内不重复通知。默认不探测 Proxy，也不会改变代理节点、VPN 或 DNS 设置。

## DNS 解析器泄漏检测：检测内容和边界

点击「DNS 解析器泄漏检测」才会运行，不随网络变化自动执行。脚本从 `https://bash.ws/id` 获取一次性会话 ID，调用 Loon Build 988+ 的 `$dns.query()` 通过当前 DNS 配置查询四个未缓存域名，再读取 `https://bash.ws/dnsleak/test/<id>?json` 返回的真实递归解析器观测数据。服务来源与测试方式可参阅 [bash.ws](https://bash.ws/dnsleak) 和 [开源客户端](https://github.com/macvk/dnsleaktest)。

报告包含观测到的 DNS 解析器 IP、国家、ASN 和测试服务看到的 HTTP 出口地址，以及与**项目默认** AliDNS 的有限名称比对。**不能因为 DNS ASN 不等于代理出口 ASN 就判为泄漏；也不能因为解析器名称包含 AliDNS 就判为绝对安全。** 如果用户改过 DNS、路由或使用远程代理 DNS，需以实际配置为准。无法观测、返回格式错误、服务请求失败、Loon 接口缺失或超时均显示**无法判定**，绝不显示「无泄漏」。

隐私提示：检测会向第三方 bash.ws 发送本次随机测试域名，解析器实际出口会被其权威 DNS 观测到；查询结果 API 也能看到 HTTP 请求的网络出口。脚本不强制 DIRECT，不运行系统全局 DNS 扫描，也不会修改 Loon DNS 设置、规则或代理。它只能采样此时 **Loon 自身 DNS 栈**，无法证明 Safari 或其他 App、系统旁路 DNS、VPN 重连瞬间绝不泄漏。建议结合 Loon DNS 日志和独立浏览器 DNS 泄漏测试人工核验。

## 节点信息与隐私

节点查询仅在手动点击时访问第三方接口。首选服务失败可尝试备用服务，备用服务缺少机房判断时明确标识为“未知”。恢复分组展示国家/地区、州/省、城市、有效时区/邮编/近似坐标、ASN、ISP、运营组织、机房/移动/VPN/代理/Tor 标签及有数据时的服务商风险分数；同时读取 Loon 本地 GeoIP、ASN、ASO（API 可用时）交叉对照。未知字段明确显示“无数据”，风险评分不是节点质量评分，不能把“未标记”当作安全证明。

开启“对照直连出口 IP”会让第三方服务获知真实直连公网 IP，默认关闭。出口 IP 不等于订阅节点入口 IP；住宅、VPN、机房等第三方标签不是确切结论，也不是节点质量评分。

## 维护与回退

- [新版插件](../plugins/v20261018r8/Network_Diagnostics.plugin)
- [节点出口脚本](../scripts/v20261018r5/node-intelligence.js)
- [诊断脚本](../scripts/v20261018r4/network-diagnostics.js)
- [DNS 解析器测试脚本](../scripts/v20261018r8/dns-leak-check.js)
- [DNS 解析器测试回归](../tests/test_dns_leak_check.js) · [v2.3 可靠性回归](../tests/test_dns_probe_reliability.js)
- [新版模拟测试](../tests/test_plugin_v2.js)
- [旧版插件（历史兼容）](../plugins/v20261018r2/Network_Diagnostics.plugin)

测试使用 Node 模拟环境，不能代表真实 iPhone Loon 测试。发布前应验证旧版插件停用后新版显示三个入口、节点查询不意外走 DIRECT、原生 DNS 错误能显示，以及网络变化提醒默认不产生后台请求。

路由配置中的 `GEOIP,CN,DIRECT,no-resolve`、`FINAL,Final` 与 CIDR 强制 `no-resolve` 不在本次插件重构范围内。

### v2.3 诊断改进与单独测试

v2.3 使用 10 个一次性 DNS 测试域名，结果轮询最多六次，不依赖所有 $dns.query 回调都成功返回。仍不能证明全系统无泄漏；如果最后没有观测数据，会列出 **失败阶段、DNS 发起与回调数量、轮询次数**，不会误报“安全”。

在正式合并前可通过分支内独立 [预览插件](https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/fix/dns-leak-probe-reliability-20261018/plugins/preview/DNS_Leak_Check_v2_3.plugin) 手动进行 iPhone 测试。预览仅包含一个检测按钮，无后台监测，不修改配置，测试结束请停用预览插件以避免菜单重复。注意这份预览依赖临时分支，非长期稳定订阅。

### v2.4：bash.ws 测试 ID 校验兼容性修复

使用真实 HTTPS 接口与一次独立 DNS 查询核对后，确认 bash.ws `/id` 返回的是纯文本 **16 位字母数字混合 ID**，不是旧版 v2.3 校验器要求的纯数字。旧版会在「创建会话」阶段停止，显示「DNS 查询 0/0」和「结果检查 0 次」；此时根本没有进行泄漏检查。v2.4 将 ID 验证更改为严格合法的 DNS 标签字符和长度校验（8–63 位），禁止点号、路径、空格、HTML 和 URL 注入，同时支持旧的纯数字测试会话。已补充 Loon 模拟回归测试；手机真实网络运行仍须验证。
