# LoonKit · 网络辅助

> vNext-RC2 采用固定 Git Commit 的插件封装和内部脚本；本页底部 main 链接仍是**历史稳定插件**，不应代替未发布 RC2 的固定资产。RC2 固定插件见 [发布资源](../release/phase-07/assets/Network_Diagnostics.plugin)。

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
| Loon 原生 DNS | 检查 `example.com` 的实际查询协议、服务器与缓存状态（需要 Build 988+） |

如果查询返回 `udp`，将标记为明文 DNS 查询；如果使用与主配置不同的加密 DNS，则标记为需要人工检查。命中缓存时不会把缓存回答误认为刚刚发生的加密 DNS 请求。

任一已执行的检测失败，总结会标注异常；如果当前版本不支持原生 DNS 查询，则显示「不支持」，不会算作通过。

默认主配置预期 DNS 为 `https://dns.alidns.com/dns-query`，PrivacyDNS 入口则维持 `https://doh.pub/dns-query`。阶段07没有改变两份原始 DNS 参数。这几项用于检查网络和**Loon 自身 DNS 解析路径**，但无法证明设备中的所有 App 都没有 DNS 泄漏。完整排查见 [DNS 隐私说明](./DNS_PRIVACY.md)。诊断失败时先查看 Loon 请求及 DNS 日志，再确认所选策略和检测服务是否可用。

## 网络切换提醒

「网络切换提醒」默认关闭。开启后，插件在网络变化事件触发时仅检查直连 HTTP，初次失败会再次检测；同类问题在 30 分钟内不会重复提醒。

此功能不会自动切换节点，也不会修改 DNS。无需后台检测时可保持关闭。

## 安装与更新

[完整配置](../LoonKit.lcf) · [独立插件](../plugins/Network_Diagnostics.plugin)

独立订阅地址：

```text
https://raw.githubusercontent.com/YohakuSama/loonkit/main/plugins/v20261018r11/Network_Diagnostics.plugin
```

如果更新后菜单或报告未变化，请确认本地完整配置和插件列表使用了新版链接，并停用重复的旧插件。仅刷新远程分流规则不会更新插件脚本。
