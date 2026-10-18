# LoonKit

适用于 **Loon** 的分流配置，包含常用服务策略、广告拦截、DNS 设置和网络辅助工具。

[完整配置](./LoonKit.lcf) · [网络辅助插件](./plugins/Network_Diagnostics.plugin) · [插件使用说明](./docs/NETWORK_DIAGNOSTICS.md) · [问题反馈](https://github.com/YohakuSama/loonkit/issues)

## 功能

- **服务分流**：为视频、社交、AI、游戏平台等选择不同策略。
- **国内直连**：常用国内网站和服务优先直连。
- **节点选择**：提供手动选择、自动测速和故障切换策略。
- **广告拦截**：通过 `AdBlock` 策略控制。
- **网络辅助**：查看出口 IP、节点网络信息，并识别 Loon 实际 DNS 协议与解析器。

## 安装

使用前请备份已有 Loon 配置和节点订阅。本项目**不提供代理节点**，需要使用自己的有效订阅。

**完整配置地址：**

```text
https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf
```

1. 在 Loon 中通过链接导入完整配置。
2. 添加或恢复自己的节点订阅，并更新节点。
3. 在「策略」中为 `Proxy` 选择一个可用节点，或配置 `Auto`、`Fallback`。
4. **在 Loon 的 DNS 服务器页面关闭「加密 DNS 查询失败回退到普通 DNS」**。此开关无法仅凭配置文件控制。
5. 更新远程规则和插件资源，确认下载成功。
6. 运行网络与 DNS 诊断，在 DNS 日志中检查实际查询所用协议与解析器，并检查各 App 分流。

**首次使用请先确保代理节点可用，再更新 GitHub 规则资源。** 配置中的 GitHub 资源默认经 `Proxy` 策略访问。无节点时无法通过规则解决 GitHub 直连故障。

如果只需要辅助工具，可以[单独订阅网络辅助插件](./plugins/Network_Diagnostics.plugin)，不必导入整套配置。

## 网络辅助

| 工具 | 用途 |
|---|---|
| 节点出口信息 | 查看公网 IP、地区、运营商、ASN 和网络类型 |
| 网络与 DNS 诊断 | 检查直连、代理、DoH 和 Loon 原生 DNS |

**中国大陆 DNS 配置：** 默认使用阿里加密 DoH（`https://dns.alidns.com/dns-query`），恢复旧版已使用的阿里普通 DNS `223.5.5.5,223.6.6.6` 作为兼容/应急选项。普通 DNS 位于大陆且查询不加密。Loon **默认允许加密 DNS 失败回退到普通 DNS**；若要求禁止明文查询，请在 App 的 DNS 设置中关闭此回退开关。已删除之前额外加入的 DoH 域名固定 IP 映射，恢复旧版解析行为。加密 DoH 与代理节点出口不同不必然是明文泄漏。详见 [DNS 隐私排查](./docs/DNS_PRIVACY.md)。

**首次导入与更新：** `raw.githubusercontent.com` 在部分大陆网络不可直连。本项目不提供节点，DNS 修复不能让 GitHub 下载自动突破网络限制。可以先将 `.lcf` 保存到设备、在 Loon 本地导入，恢复可用节点后再更新远程规则和插件。

网络切换提醒、直连 IP 对照默认关闭，可在插件设置中按需开启。详见[插件使用说明](./docs/NETWORK_DIAGNOSTICS.md)。

## 更新与排查

更新规则时刷新远程规则资源；更新完整配置时请先备份个人设置，以免覆盖节点或自定义规则。

遇到网页无法打开，可依次检查：节点是否可用、当前策略、远程规则是否成功更新，以及 Loon 请求记录。登录、支付、图片加载异常时，也可暂时将 `AdBlock` 切换为 `DIRECT` 进行排查。

如果插件出现重复菜单，请检查是否同时启用了多个插件订阅。

## 规则来源

规则整理自 [blackmatrix7](https://github.com/blackmatrix7/ios_rule_script)、[v2fly](https://github.com/v2fly/domain-list-community)、[dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list) 和本项目补充的规则。具体来源与许可信息见[规则说明](./rules/README.md)。

---

由 [YohakuSama](https://github.com/YohakuSama) 维护，非 Loon 官方项目。
