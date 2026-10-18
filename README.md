# Loon Routing DNS

面向 **Loon iOS** 的独立复合型分流与 DNS 配置。使用自托管 Loon 规则集，统一管理国内直连、海外平台、广告过滤和隐私追踪拦截。

**正式版：v5.1.0（2026-10-17）** · [完整配置](./Loon_Routing_DNS.lcf) · [规则目录](./rules/generated/) · [规则来源](./rules/sources.json) · [提交问题](https://github.com/YohakuSama/loon-routing-dns/issues)

> 社区项目，不属于 Loon 官方。**配置不包含节点订阅**；导入前备份现有配置、节点 URL 和自定义插件。此版本经过自动化静态校验，不代表所有 App / 网络环境均经过 iPhone 实测。

## 为什么采用复合型规则

单一上游大型规则很难同时覆盖国内移动服务、境外 AI / 社交 / 视频平台、广告和隐私保护；直接堆叠多份订阅又会产生重复匹配和分流冲突。实际使用中出现过哈啰 App 开启代理后无法联网的反馈，说明需要对国内关键业务、广告误拦截以及 DNS 等问题进行可追溯诊断。**这不是对原上游项目的整体否定，也不表示已确认哈啰故障的根因。**

因此项目选择不同来源各自合适的部分，转换、去重、审计后发布在本仓库：

| 来源 | 角色 | 许可 |
|---|---|---|
| [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) | Loon 原生国内/境外分类，AdvertisingLite、Privacy、Hijacking | GPL-2.0 |
| [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) | AI、社交、流媒体、游戏平台域名补全 | MIT |
| [felixonmars/dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list) | 经筛选的 Apple 中国相关域名 | WTFPL-2.0 |
| [项目自维护规则](./rules/custom/) | 国内地图/支付、哈啰及精确服务例外 | 随仓库源文件管理 |

原始来源及许可证保留在 `rules/sources.json` 与 `rules/LICENSE.*`。**主配置里的 33 条远程订阅全部指向自己的 `main/rules/generated/*.list`，不是第三方规则地址。**

## 图标更新（v20261018r2；HBO 单独更新至 v20261018r3）

为处理 Loon 对旧图标地址的缓存，**除 HBO 外的 32 个策略组**与 Console 插件图标使用版本化链接 `main/icons/v20261018r2/`；**HBO 单独使用 `main/icons/v20261018r3/HBO.png`**，网络辅助插件使用 `main/plugins/v20261018r9/Network_Diagnostics.plugin`（旧版仍保留在 `v20261018r2`）。已经导入 Loon 的本地配置不会因仓库更改而必然自动替换内含的 `img-url`；需先备份含节点订阅与私人改动的配置，再更新本地配置中的图标 URL，或按 Loon 的配置更新流程重新获取完整配置。只更新规则列表不足以更新策略组图标。

### 图标材质一致性调整

本次图标修订将 Spotify、Netflix、Telegram、Discord、Instagram、TikTok 的玻璃边缘替换为品牌标准矢量轮廓加完整底板，并将 Proxy、AI、Console 替换为经审核的原创符号。HBO 图标在 v20261018r3 中单独裁去外围装饰圈，其余图标仍采用 `icons/v20261018r2/`，插件采用 `plugins/v20261018r9/`，保留相同控制台图标。请备份已有配置后更新**完整配置**才能看到变化；仅更新远程规则不改变策略组图标。

## 快速安装

完整配置永久地址：

```text
https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/Loon_Routing_DNS.lcf
```

在 Loon 的配置文件页面从链接导入，将私人订阅添加到远程节点，切换至 `RULE` 模式，更新规则和节点后确认每条来源正常。不要把含 token 的私人订阅上传 GitHub。

初始建议：`Final=Proxy`，`Apple/Microsoft/Bilibili` 默认直连，其他海外平台走独立策略组；`AdBlock=REJECT` 可临时切换为 `DIRECT` 排查登录、支付、图片或定位误拦截。

国内移动服务统一走 `DIRECT`：哈啰不另设策略组，主域名由 `rules/custom/HelloBike.list` 导入 `DomesticCore.list`，并在国内直连基础集合之前加载。但这不能代表已覆盖哈啰全部实际请求域名，定位故障仍需 Loon 的请求记录。

## 广告与隐私保护

`AdBlock.list` 合并轻量广告、追踪隐私和劫持防护，并剔除同组重复、父域已覆盖的子规则及跨分组完全重复匹配；为降低误伤，默认仅把 `DOMAIN` 与 `DOMAIN-SUFFIX` 加入广告拒绝列表，**不自动启用笼统 `DOMAIN-KEYWORD`、IP 封禁、`URL-REGEX` 或 HTTPS MITM**。某些广告因此可能无法拦截，这是兼容性与覆盖率之间的取舍。

某个平台同时命中服务和广告规则时，生成器按配置列表优先顺序保留一份精确匹配项，审计报告记录去除的归属；不能仅凭规则数量多就声称效果更好。

## DNS 与隐私边界

配置默认继续使用 `223.5.5.5,223.6.6.6` 和 `https://dns.alidns.com/dns-query`。Loon 的 DoH 流量模式建议选择 `DIRECT`；是否禁用加密 DNS 查询失败时回退到普通 DNS，需在 Loon App 手动设置。**控制台的真实直连出口 IP 对照默认关闭，以减少诊断时意外暴露真实 IP。DoH 不等于零泄漏或匿名**；浏览器检测所展示的 DNS 机房与代理出口不一致，不能单凭此判定 DNS 泄漏。

`disable-stun = true` 与 `udp-fallback-mode = REJECT` 延续原隐私优先设置；可能影响部分语音、游戏或实时通信，需要按真实业务测试。

## 更新、审核与回滚

每次改动通过 CI 进行配置语法、策略组与远程引用、脚本回归、规则构建及冲突检查；定期自动检查上游并为变更创建 **Draft PR**，不自动覆盖正式版。被隔离的格式、来源数据突然减少以及异常冲突必须人工审查。

- [复合规则库设计与审计](./rules/HYBRID_DESIGN.md)
- [最新生成统计和冲突列表](./rules/generated/audit.json)
- [网络辅助插件 v2.5：完整节点情报 + 网络/DNS/泄漏检查](./docs/NETWORK_DIAGNOSTICS.md) · [Network_Diagnostics.plugin](./plugins/Network_Diagnostics.plugin)
- [历史配置 v4.4.8（回滚参考）](./releases/v4.4.8/Loon_Routing_DNS.lcf)：旧图标与插件入口已固定至清理前 Commit；第三方订阅和插件内部脚本仍可能随上游变化，不能视为完全离线、不可变的历史快照。

**插件 v2.5：** 提供「节点出口信息」「网络与 DNS 诊断」「DNS 解析器泄漏检测」三个手动入口；节点信息恢复完整分组：公网出口、地区、ASN/ISP/组织、机房与代理标签、风险分数（若有）、本地 GeoIP/ASN/ASO 对照。自动网络变化提醒默认关闭；设置项维持 3 项。DNS 检测利用 bash.ws 权威 DNS 观测递归解析器，只在手动点击时运行；v2.3 通过十个独立域名、六次轮询和失败阶段说明改善网页正常但插件无法判定的情况；结果不会声称绝对无泄漏，第三方接口不可用或无观测时明确显示无法判定。旧插件脚本保留作为版本兼容，不再显示旧版控制台摘要或模拟网络切换入口。插件不接管原生 Loon DNS 或分流。

**发布前验证：** `ChinaDirect` 与 `AdBlock` 体积较大，需在 iPhone 上记录规则加载和更新时间、内存、常用国内 App、登录支付、Apple OTA、流媒体、UDP、IPv6 及 Wi-Fi/蜂窝网络切换表现。规则生成器对 `IP-CIDR` / `IP-CIDR6` **继续强制使用 `no-resolve`**，维持实测过的 DNS 解析与规则命中顺序；不能将其作为普通冗余标志删除。候选规则的其他差异仍须审核并真机验证后才能更新 `rules/generated/*.list`，更新生成器本身不会立即改变线上规则。

**发布说明：** 静态测试不是 Loon 真机认证。遇到 App 不能联网，按节点 → DNS → 命中规则 → 广告开关 → UDP/IPv6 顺序排查；报告问题时请提交脱敏的 Loon/iOS 版本、错误域名、命中策略和网络情况，勿公开任何节点凭据。

---

维护者 [YohakuSama](https://x.com/yohakusama) · 第三方社区项目，与 Loon 官方无关联。

**DNS 检测兼容修复（v2.4）：** 已实测 bash.ws `/id` 返回 16 位字母数字混合字符串，旧版误用纯数字校验，使检测在发起任何 DNS 请求前结束。新版本接受安全 DNS 标签（8–63 位），拒绝路径、点号、空格及网页错误响应；网页测试正常不代表 Loon 测试也必定正常，仍需真机复测。

**DNS 检测 TLS 兼容改进（v2.5 候选）：** iPhone 报告显示 10/10 次 DNS 回调成功，但 bash.ws 结果 HTTPS 返回 `LNGCDAsyncSocketTLSError Code=16777`。只有出现 TLS 错误才从默认 HTTP/1.1 尝试 HTTP/2，不关闭证书校验，不强制 DIRECT；两者均失败时尽早提示 TLS/路由问题。提交 PR 后仍需真机核验，此变更不能保证所有设备的 TLS 问题都会解决。
