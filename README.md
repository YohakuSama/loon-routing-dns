# Loon Routing DNS

适用于 **Loon iOS** 的分流与 DNS 配置。按服务分类管理代理策略，国内服务直连，海外服务按策略组选择节点，提供基础广告拦截和网络诊断。

[完整配置](./Loon_Routing_DNS.lcf) · [网络辅助插件](./plugins/Network_Diagnostics.plugin) · [规则列表](./rules/generated/) · [问题反馈](https://github.com/YohakuSama/loon-routing-dns/issues)

## 主要功能

- **服务分流**：33 个策略组，覆盖 AI、视频、社交、游戏、常用国内服务等。
- **国内直连**：中国 IP 和常见国内服务优先 DIRECT。
- **广告拦截**：可通过 `AdBlock` 策略组切换拦截或放行。
- **网络辅助**：查询节点出口和网络/DNS 连通情况；网络切换提醒可选择开启。

## 安装

完整配置地址：

```text
https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/Loon_Routing_DNS.lcf
```

1. 备份现有 Loon 配置、节点订阅和个人规则。
2. 在 Loon 中通过上面的链接导入配置。
3. 添加自己的节点订阅，更新远程资源，使用 `RULE` 模式。
4. 在「策略」中选择 `Proxy`、`Auto`、`Fallback` 等策略组的节点。

**本仓库不提供代理节点或订阅。** 如果配置已在手机中保存为本地副本，仓库更新不会自动替换其中的插件、图标或策略设置。

## 网络辅助插件

随完整配置加载，也可以 [单独添加插件](./plugins/Network_Diagnostics.plugin)。

| 工具 | 用途 |
|---|---|
| 节点出口信息 | 公网 IP、位置、ASN、ISP、网络类型及本地数据库对照 |
| 网络与 DNS 诊断 | 检查直连、代理、DoH 服务和 Loon 原生 DNS 是否响应 |

插件设置包含网络切换提醒、查询策略及直连 IP 对照。**网络切换提醒与直连 IP 对照默认关闭。** 节点位置信息和网络类型来自第三方查询，仅供参考。

使用说明：[网络辅助插件](./docs/NETWORK_DIAGNOSTICS.md)。

## 分流与 DNS

正式配置使用 AliDNS：

- 普通 DNS：`223.5.5.5`、`223.6.6.6`
- DoH：`https://dns.alidns.com/dns-query`

保留的本地兜底规则：

```ini
GEOIP,CN,DIRECT,no-resolve
FINAL,Final
```

`IP-CIDR` 和 `IP-CIDR6` 规则继续使用 `no-resolve`，避免改变现有 DNS 解析与规则匹配顺序。

`AdBlock` 可临时改为 `DIRECT` 排查登录、图片或支付问题。基础 DoH 连通测试不等于 DNS 泄漏测试。

## 规则来源

项目从 [blackmatrix7](https://github.com/blackmatrix7/ios_rule_script)、[v2fly](https://github.com/v2fly/domain-list-community)、[dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list) 及 [本地补充规则](./rules/custom/) 构建分流列表。

所有来源与许可证见 [规则来源配置](./rules/sources.json) 和 [规则说明](./rules/README.md)。主配置订阅的规则文件托管在本仓库 `rules/generated/`。

## 更新与排查

更新分流规则请刷新远程规则资源；更新插件、图标或配置结构则需更新**完整配置**。如使用过单独安装的旧插件，请停用重复插件。

遇到连接问题，可先检查当前节点和命中策略，再查看 Loon 的请求及 DNS 日志。提交反馈时附上 Loon 版本、问题域名、匹配策略和脱敏后的错误信息，请勿公开订阅链接、令牌或个人 IP。

项目通过 GitHub Actions 检查配置、脚本和生成规则。自动化测试不能替代实际设备验证。

---

维护者：[YohakuSama](https://github.com/YohakuSama) · 非 Loon 官方项目。
