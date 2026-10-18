# Loon Routing DNS · 网络辅助插件 v2.5

完整配置自动加载的轻量插件。**仅两个手动入口、三个设置项，以及默认关闭的网络变化提醒。** 不修改 Loon DNS、规则、VPN、节点或代理策略。先前独立的「DNS 解析器泄漏检测」因真实 iPhone 环境中的 HTTPS/TLS 读取不稳定、不能可靠完成判断，已从正式插件及仓库中移除。

## 功能

| 入口 | 作用 | 限制 |
|---|---|---|
| **节点出口信息** | 出口 IP、国家/地区/城市、ASN、ISP、组织、机房/移动/VPN/代理/Tor 特征、第三方风险分数，以及可用时的 Loon 本地 GeoIP/ASN/ASO 对照 | 出口 IP 不一定是节点服务器入口；第三方地区、风险与网络类型信息可能不准确 |
| **网络与 DNS 诊断** | 检测 DIRECT、Proxy、指定 DoH 服务和可用时的 Loon 原生 DNS 查询 | 检测到 DoH 服务可连接不代表没有 DNS 泄漏，也不保证所有域名都通过 DoH |
| **网络变化异常提醒** | 可选，网络变化后检查并在异常时提醒 | 默认关闭；只有用户开启才会在网络切换时探测 |

**三个设置项：**

- `auto_check = false`：网络变化提醒默认关闭，避免无需求时自动探测。
- `target_policy = Proxy`：手动出口信息查询的默认策略；若有明确节点上下文，优先查询该节点。
- `compare_direct = false`：真实 DIRECT 公网 IP 对照默认关闭。开启后会向第三方 IP 情报服务发送 DIRECT 查询，可能暴露真实出口 IP。

IP 情报主源为 ipquery.io，备用为 ipwho.is。基础诊断使用 AliDNS DoH、vivo 直连 HTTP 探测和 Cloudflare 代理 HTTP 探测。不开放自定义 API、探测网址、超时和缓存参数，以减少不必要的设置。

## 安装和升级

正式完整配置：

https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/Loon_Routing_DNS.lcf

[独立网络辅助插件 v2.5](../plugins/v20261018r9/Network_Diagnostics.plugin)

完整配置中的 [Plugin] 已指向 `plugins/v20261018r9/Network_Diagnostics.plugin`。单独订阅插件的用户可以使用 `plugins/Network_Diagnostics.plugin`。当前脚本分别为：

- [节点出口情报脚本](../scripts/v20261018r5/node-intelligence.js)
- [网络与 DNS 基础诊断脚本](../scripts/v20261018r4/network-diagnostics.js)

如果 Loon 仍然显示第三个「DNS 解析器泄漏检测」入口，说明旧插件订阅或旧的本地配置仍在启用。请先备份当前配置，再确认插件订阅及完整配置中的 URL 已更新到 `v20261018r9`，并停用重复的旧插件。仅更新远程分流规则不会替换已经保存在本地配置中的插件引用。

先前包含独立 DNS 泄漏检测的插件版本以及对应脚本、测试和预览资源已清理，**不再提供已移除功能的旧版下载地址**。保留早期无此功能的 `v20261018r2`、`r4`、`r5` 插件供排障和回退。

## 正确理解基础诊断结果

手动诊断分项显示 DIRECT、Proxy、DoH 接口、Loon 原生 DNS 的检测状态。若原生 DNS 查询失败，总结必须显示异常；若当前 Loon 版本不支持 `$dns.query`，则标注「不支持」，不把未检测等同于正常。

DoH 接口主动探测只能确认某个 DoH 服务是否响应；不说明 Loon 全部域名都经该服务器解析，更不能代替独立 DNS 泄漏测试。探测服务暂时不可达也不一定说明 Loon 的分流配置有问题。若需要核对 DNS 解析行为，可结合 Loon DNS / 请求日志及独立浏览器测试自行验证，插件不再发起第三方权威 DNS 泄漏测试。

自动提醒在开启后检查 DIRECT 与 DoH，失败则复测；同类提醒在 30 分钟内去重。该流程不会修改代理策略、DNS 或 VPN。

## 出口信息和隐私

节点情报按照地理位置、网络归属、风险/网络标签及本地数据库对照分组呈现。缺少字段时标注未知；机房、VPN、Tor 等标签来自第三方推断，不等于安全认证或节点质量评分。公网出口查询默认只使用目标节点或策略，DIRECT 公网 IP 对照需要明确开启。

## 维护

- [插件回归测试](../tests/test_plugin_v2.js)
- [详细节点情报回归测试](../tests/test_node_details.js)
- [历史精简插件 v2.1](../plugins/v20261018r5/Network_Diagnostics.plugin)

自动化模拟测试不能替代真实 iPhone 上的 Loon 回归测试。本次移除不涉及 `GEOIP,CN,DIRECT,no-resolve`、`FINAL,Final` 或 IP-CIDR/IP-CIDR6 强制 `no-resolve`，也未修改 DNS 服务器与远程规则。
