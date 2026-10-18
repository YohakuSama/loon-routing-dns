# 网络辅助插件

插件包含两个手动工具。使用时不会修改 Loon 的 DNS、代理模式或分流规则。

## 节点出口信息

查看所选节点或策略的公网出口，包括 IP、地区、ASN、ISP、网络类型和 Loon 本地数据库结果。在线查询服务为 ipquery.io，主服务不可用时会尝试 ipwho.is。

- **查询策略**：默认 `Proxy`。从节点菜单调用时优先使用当前节点。
- **直连 IP 对照**：默认关闭。开启后会额外查询 DIRECT 公网 IP，并将其发送给第三方 IP 查询服务。
- **网络类型**：机房、VPN、代理等结果为数据库判断；「否」表示未被该数据库标记，不保证绝对准确。

报告会自动省略没有必要的重复字段，例如 ISP 和运营组织相同时只显示一次。未提供的资料显示为「未知」或不显示。

## 网络与 DNS 诊断

手动点击「网络与 DNS 诊断」，分别检查：

| 项目 | 检查内容 |
|---|---|
| 直连 | DIRECT HTTP 请求是否响应 |
| 代理 | `Proxy` 策略的 HTTP 请求是否响应 |
| DoH | AliDNS DoH 接口是否返回有效 DNS 应答 |
| 原生 DNS | Loon 是否能够查询 `example.com`（需支持 `$dns.query`） |

任一已执行的检测失败，总结会标注异常；如果当前版本不支持原生 DNS 查询，则显示「不支持」，不会算作通过。

这几项用于检查连接状态，**不能判断是否发生 DNS 泄漏**。诊断失败时先查看 Loon 请求及 DNS 日志，再确认所选策略和检测服务是否可用。

## 网络切换提醒

「网络切换提醒」默认关闭。开启后，插件在网络变化事件触发时检查直连与 DoH，初次失败会再次检测；同类问题在 30 分钟内不会重复提醒。

此功能不会自动切换节点，也不会修改 DNS。无需后台检测时可保持关闭。

## 安装与更新

[完整配置](../Loon_Routing_DNS.lcf) · [独立插件](../plugins/Network_Diagnostics.plugin)

独立订阅地址：

```text
https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/plugins/v20261018r10/Network_Diagnostics.plugin
```

如果更新后菜单或报告未变化，请确认本地完整配置和插件列表使用了新版链接，并停用重复的旧插件。仅刷新远程分流规则不会更新插件脚本。

## 技术信息

当前正式插件使用：

- [节点出口脚本](../scripts/v20261018r10/node-intelligence.js)
- [网络/DNS 诊断脚本](../scripts/v20261018r4/network-diagnostics.js)
- [插件回归测试](../tests/test_plugin_v2.js)
- [节点报告测试](../tests/test_node_copy.js)

`GEOIP,CN,DIRECT,no-resolve`、`FINAL,Final` 和所有分流规则不受插件界面更新影响。
