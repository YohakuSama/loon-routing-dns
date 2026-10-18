# LoonKit v5.10.0

适用于 **Loon** 的分流配置，包含常用服务策略、广告拦截、DNS 设置和网络辅助工具。**正式配置改为 LoonKit 自托管规则：33 个复合策略规则集 + 1 个受保护域名规则集。** 上游仍包括 blackmatrix7、v2fly 和项目自有规则，但设备只订阅本仓库发布的规则快照。

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

**首次使用请先确保代理节点可用，再更新 GitHub 规则资源。** 正式远程规则已改为 34 条 LoonKit 自托管订阅；17 个受保护域名由第一个 `ProxyProtect.list` 统一管理。配置仍将 GitHub Raw 交给 `Proxy` 策略。无节点时无法通过规则解决 GitHub 直连故障。

如果只需要辅助工具，可以[单独订阅网络辅助插件](./plugins/Network_Diagnostics.plugin)，不必导入整套配置。

## 网络辅助

| 工具 | 用途 |
|---|---|
| 节点出口信息 | 查看公网 IP、地区、运营商、ASN 和网络类型 |
| 网络与 DNS 诊断 | 检查直连、代理、DoH 和 Loon 原生 DNS |

**中国大陆 DNS 配置：** 默认使用阿里加密 DoH（`https://dns.alidns.com/dns-query`），恢复旧版已使用的阿里普通 DNS `223.5.5.5,223.6.6.6` 作为兼容/应急选项。普通 DNS 位于大陆且查询不加密。Loon **默认允许加密 DNS 失败回退到普通 DNS**；若要求禁止明文查询，请在 App 的 DNS 设置中关闭此回退开关。已删除之前额外加入的 DoH 域名固定 IP 映射，恢复旧版解析行为。加密 DoH 与代理节点出口不同不必然是明文泄漏。详见 [DNS 隐私排查](./docs/DNS_PRIVACY.md)。

**首次导入与更新：** `raw.githubusercontent.com` 在部分大陆网络不可直连。本项目不提供节点，DNS 修复不能让 GitHub 下载自动突破网络限制。可以先将 `.lcf` 保存到设备、在 Loon 本地导入，恢复可用节点后再更新远程规则和插件。

网络切换提醒、直连 IP 对照默认关闭，可在插件设置中按需开启。详见[插件使用说明](./docs/NETWORK_DIAGNOSTICS.md)。

## v5.10.0 自维护规则修复

本次从源头处理误直连，而不是继续在主配置堆叠例外：正式配置只订阅本仓库自己的 34 个规则文件（33 个分类规则集 + 首位 `ProxyProtect.list`）。源头保护名单位于 [routing_guardrails.json](./rules/routing_guardrails.json)，由 CI 保证保护文件的 17 条域名与名单完全一致。

- 正式远程规则顺序由 [active_profile.json](./rules/active_profile.json) 固定，与规则生成器的去重优先级对应。
- 自维护 `ChinaDirect.list` 已删除目前核实的错误匹配；生成器阻止未来把受保护域名再次归入任何 `DIRECT` 分组。
- 保留 66 条经历史验证的本地业务分流、原 DNS 设置、策略组和插件，避免迁移时同时改动大量网络行为。
- 上游刷新由 GitHub Actions 生成候选更新 PR，审核后才会进入正式订阅，不直接下载上游原始规则。
- **需要真机复测：** DNS 查询、Apple 更新、国内银行与支付、Steam、AI 登录、广告拦截、国内 CDN、IPv6。静态 CI 无法证明所有域名分类完全正确或不存在 DNS 泄漏。

## 可选隐私 DNS 配置（必须结合 Loon 设置验证）

除主配置外，仓库提供 [**LoonKit.PrivacyDNS.lcf**](./LoonKit.PrivacyDNS.lcf)，它仅替换 DNS 服务器，并保持 34 条自托管规则、66 条本地规则、策略组、插件与 IPv6 设置不变。

- 原始 `LoonKit.lcf` 继续使用 AliDNS，面向大陆兼容性，**不是零 DNS 泄漏保证**。
- 隐私配置使用 Cloudflare 的 `https://cloudflare-dns.com/dns-query`（官方 DoH），因此 Loon 自身的解析不再默认使用 AliDNS；但 **DoH 加密不代表请求随代理节点出口发出，也不能控制浏览器自带 DoH**。
- 在 Loon 的「DNS 服务器」页面**手动关闭加密 DNS 失败回退到普通 DNS**。配置中 `dns-server=1.1.1.1,1.0.0.1` 是兼容项；如果忘记关闭回退，仍可能发生明文 DNS 查询。
- 大陆网络可能无法访问境外 DoH，关闭回退后可能出现无法解析。遇到这种情况不要静默启用明文回退，应先排查当前网络与 DNS 连通性，必要时回到原配置。
- 参照 [DNS 实测与泄漏定位](./docs/DNS_PRIVACY.md) 核对 Loon DNS 日志的 `protocol`、`server`、`fromCache`，并区分网页出口 IP、DNS 递归解析器和运营商出口。仅靠 BrowserLeaks 显示的 DNS 地理位置无法证明明文泄漏。

## 更新与排查

更新规则时刷新远程规则资源；**从启用 33 个生成规则的旧 LoonKit 配置升级时，请确认旧的 `Our-*` 生成规则订阅没有作为额外列表继续启用**。更新完整配置前请备份个人设置和节点。

遇到网页无法打开，可依次检查：节点是否可用、当前策略、远程规则是否成功更新，以及 Loon 请求记录。登录、支付、图片加载异常时，也可暂时将 `AdBlock` 切换为 `DIRECT` 进行排查。

如果插件出现重复菜单，请检查是否同时启用了多个插件订阅。

## 自维护规则库质量门槛

自有复合规则不是盲目复制上游：已在 [候选库审计报告](./rules/AUDIT_2026-10-18.md) 中核对 `ChinaDirect` 误收录的 `browserleaks.com`、`whatismyip.com` 和 `DOMAIN-KEYWORD,stripe`，并从生成内容移除；未来刷新会通过 [规则保护名单](./rules/routing_guardrails.json) 和 CI 阻止同类误直连。正式配置现使用自托管规则库的已审计快照；后续候选更新不会自动发布，仍需真机和业务回归。

## 规则来源

**正式启用的远程规则由 LoonKit 自托管**；[blackmatrix7](https://github.com/blackmatrix7/ios_rule_script)、[v2fly](https://github.com/v2fly/domain-list-community) 等仍作为可审核的上游数据源。正式配置保留 66 条本地历史业务规则。详情见 [自维护规则库](./rules/README.md)。历史配置的节点订阅和访问凭证不会纳入仓库。

---

由 [YohakuSama](https://github.com/YohakuSama) 维护，非 Loon 官方项目。
