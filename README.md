# LoonKit

适用于 **Loon** 的分流配置，包含常用服务策略、广告拦截、DNS 设置和网络辅助工具。

[完整配置](./LoonKit.lcf) · [网络辅助插件](./plugins/Network_Diagnostics.plugin) · [插件使用说明](./docs/NETWORK_DIAGNOSTICS.md) · [问题反馈](https://github.com/YohakuSama/loonkit/issues)

## 功能

- **服务分流**：为视频、社交、AI、游戏平台等选择不同策略。
- **国内直连**：常用国内网站和服务优先直连。
- **节点选择**：提供手动选择、自动测速和故障切换策略。
- **广告拦截**：通过 `AdBlock` 策略控制。
- **网络辅助**：查看出口 IP、节点网络信息，检查直连、代理和 DNS 连通性。

## 安装

使用前请备份已有 Loon 配置和节点订阅。本项目**不提供代理节点**，需要使用自己的有效订阅。

**完整配置地址：**

```text
https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf
```

1. 在 Loon 中通过链接导入完整配置。
2. 添加或恢复自己的节点订阅，并更新节点。
3. 在「策略」中为 `Proxy` 选择一个可用节点，或配置 `Auto`、`Fallback`。
4. 更新远程规则和插件资源，确认下载成功。
5. 使用常见国内及海外网站，检查分流是否符合预期。

**首次使用请先确保代理节点可用，再更新 GitHub 规则资源。** 配置中的 GitHub 资源默认经 `Proxy` 策略访问；若没有可用节点，下载可能失败。

如果只需要辅助工具，可以[单独订阅网络辅助插件](./plugins/Network_Diagnostics.plugin)，不必导入整套配置。

## 网络辅助

| 工具 | 用途 |
|---|---|
| 节点出口信息 | 查看公网 IP、地区、运营商、ASN 和网络类型 |
| 网络与 DNS 诊断 | 检查直连、代理、DoH 和 Loon 原生 DNS |

网络切换提醒、直连 IP 对照默认关闭，可在插件设置中按需开启。详见[插件使用说明](./docs/NETWORK_DIAGNOSTICS.md)。

## 更新与排查

更新规则时刷新远程规则资源；更新完整配置时请先备份个人设置，以免覆盖节点或自定义规则。

遇到网页无法打开，可依次检查：节点是否可用、当前策略、远程规则是否成功更新，以及 Loon 请求记录。登录、支付、图片加载异常时，也可暂时将 `AdBlock` 切换为 `DIRECT` 进行排查。

如果插件出现重复菜单，请检查是否同时启用了多个插件订阅。

## 规则来源

规则整理自 [blackmatrix7](https://github.com/blackmatrix7/ios_rule_script)、[v2fly](https://github.com/v2fly/domain-list-community)、[dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list) 和本项目补充的规则。具体来源与许可信息见[规则说明](./rules/README.md)。

---

由 [YohakuSama](https://github.com/YohakuSama) 维护，非 Loon 官方项目。
