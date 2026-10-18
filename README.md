# Loon Routing DNS

适用于 Loon 的分流配置，包含常用服务策略组、国内直连、广告拦截和网络辅助工具。

[获取完整配置](./Loon_Routing_DNS.lcf) · [网络辅助插件](./plugins/Network_Diagnostics.plugin) · [使用说明](./docs/NETWORK_DIAGNOSTICS.md)

## 主要功能

- **服务分流**：按应用和服务选择代理策略。
- **国内直连**：常用国内服务及国内网络走直连。
- **广告拦截**：通过 `AdBlock` 策略控制。
- **自动选线**：支持 `Auto` 延迟测试和 `Fallback` 故障切换。
- **网络辅助**：查看节点出口信息、检查网络及 DNS 连通性。

## 快速开始

1. 备份 Loon 中已有的节点订阅和自定义设置。
2. 导入以下完整配置：

```text
https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/Loon_Routing_DNS.lcf
```

3. 添加自己的节点订阅，并更新远程资源。
4. 在「策略」中为 `Proxy`、`Auto` 等策略组选择节点。

本项目不提供代理节点或订阅。

## 网络辅助

完整配置已包含插件，也可[单独添加](./plugins/Network_Diagnostics.plugin)。

| 功能 | 内容 |
|---|---|
| 节点出口信息 | 公网 IP、位置、运营商、ASN、网络类型及本地数据库信息 |
| 网络与 DNS 诊断 | 检查直连、代理和 DNS 服务的连接情况 |

插件可设置查询策略、直连 IP 对照及网络切换提醒。后两项默认关闭。

## 使用与更新

- 更新分流内容：在 Loon 中刷新远程规则资源。
- 更新完整配置或插件：重新获取对应配置或插件订阅。
- 插件显示异常或重复：检查插件列表中是否启用了多个订阅。
- 网站无法访问：检查选中的节点、策略组和 Loon 请求记录。

遇到问题可在 [Issues](https://github.com/YohakuSama/loon-routing-dns/issues) 反馈，请勿公开订阅链接或个人 IP。

## 开源规则

规则来自 [blackmatrix7](https://github.com/blackmatrix7/ios_rule_script)、[v2fly](https://github.com/v2fly/domain-list-community)、[dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list) 和本项目维护的补充列表。许可证及来源详见 [规则说明](./rules/README.md)。

---

维护者：[YohakuSama](https://github.com/YohakuSama) · 非 Loon 官方项目。
