# LoonKit v6.0.0

LoonKit 是面向 Loon 的自托管分流规则和策略配置，不提供代理节点。v6.0.0 是从 v5.10.0 迁移至 vNext 分流引擎的大版本更新。

**完整配置订阅（继续兼容原入口）**

- [LoonKit 主配置](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf) — 保留原 AliDNS / TUN / DoH / IPv6 设置。
- [LoonKit PrivacyDNS](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.PrivacyDNS.lcf) — 保留原 DNSPod / TUN / DoH / IPv6 设置；不会仅凭名称自动成为“零 DNS 泄漏”配置。
- [源代码与回滚](https://github.com/YohakuSama/loonkit) · [第三方许可说明](./release/phase-07/THIRD_PARTY_NOTICES.md) · [变更记录](./release/phase-07/CHANGELOG-v6.0.0.md)。

## v6 的规则与策略

- 26 条远程规则订阅，共 **197,765** 条远程规则；106 条本地规则、33 个策略组。
- 两份配置使用相同的分流规则和策略组，分别保留原先独立的 General DNS/DoH/TUN 参数。
- 远程规则固定在 Git Commit `d405e4be28c447b6e57a4790e965c89f342d6dd6`，目录 `rules/releases/vNext-RC2/`。RC2 是经过锁定的规则数据快照标识，正式配置版本为 v6.0.0。日后更新需要受审 PR，**不会自动从开发分支加载未审核规则**。
- 去掉独立的 ProxyProtect 运行时订阅，不复制旧 17 条规则成为隐形白名单；其他业务由分流规则及 Final 策略决定。
- 保留 26 条 AdBlock 本地优先级保护、海外基础服务入口、七条 IP-ASN `no-resolve` 修复、国内直连 GEOIP 保底和原 Final 策略行为。
- AdBlock 可选 `REJECT` / `DIRECT`。关闭拦截（DIRECT）便于排查支付、登录或反欺诈相关的误杀；不是保证所有广告规则都会被解除。
- Final 可选 `Proxy` / `Auto` / `Fallback` / `DIRECT`。**Final=DIRECT 时，未分类的海外域名可能直连**。

## 从 v5.10.0 升级

请先在 Loon 备份原始完整配置、节点订阅及策略组选择。仓库从不提供或上传私人节点。使用上面的完整配置 URL 替换旧版本入口，在 Loon 恢复自己的节点后重新下载规则、插件并检查策略组。v5 使用的 34 条远程订阅与 v6 的 26 条并不一一对应；仍单独启用旧订阅的用户需检查重复、过期或相互冲突的规则。

原 `rules/generated/` 仍保持历史兼容内容，**不会因为升级完整配置就被悄悄改写**。新规则使用 `rules/releases/vNext-RC2/` 的固定 SHA 引用。旧客户端若直接订阅旧单个 .list，需要自己迁移到新版完整配置。

出现异常时先恢复备份的旧版配置、节点和策略选择；确认 Loon 已重新获取旧版远程规则及插件，避免客户端缓存沿用新版本。若已更新 main，请参考 [完整回滚方案](./release/phase-07/MIGRATION_ROLLBACK.md) 及旧 main 固定提交 `f19421933d2177f95e7537f1208d990b3094f1f4`。

## DNS 与代理出口

**此次规则重构没有修改任何一个入口原有的 DNS、DoH、TUN 参数、解析回退设置和节点信息**，也没有统一两份配置的解析器。Loon 应用中原有的“加密 DNS 失败回退到普通 DNS”选项由用户自行确认。DNS 服务器位置和代理出口位置可能不同；一个检测网页不足以证明所有 App 均不存在 DNS 泄漏。实际命中须以 Loon 请求日志和解析日志为准。[完整 DNS 说明](./docs/DNS_PRIVACY.md)。

## 网络辅助

[网络辅助插件](./plugins/Network_Diagnostics.plugin) 提供手动「节点出口信息」和「网络与 DNS 诊断」功能。联网检测只提供观测，不是全设备隐私保证。额外「直连 IP 对照」**默认关闭**，网络切换自动检查也默认关闭。正式完整配置的插件和相关脚本固定 Git Commit；单独历史插件 URL 继续保留兼容。

## 更新、来源与许可

新规则只从独立的历史快照和锁定来源生成；发布目录不再是规则引擎输入。更新走差异报告、许可证/来源记录、人工 PR 审核、自动化回归和版本化资源锁定。详见 [规则维护说明](./rules/README.md)、[发布清单与 SHA256](./release/phase-07/RC_MANIFEST.json)、[发布门槛](./release/phase-07/RELEASE_GATE.json)。

整合的第三方项目包括 blackmatrix7、v2fly、felixonmars。保留 GPL-2.0、MIT、WTFPL 原始许可证和来源说明，但不能声称所有混合规则均可逐行归属原作者。相关第三方声明和适用义务见 [NOTICE](./release/phase-07/THIRD_PARTY_NOTICES.md)。

维护者报告已完成日常真机使用测试且未发现明显异常；这不是所有 DNS、IPv6、解锁地区和支付场景的结构化成功记录。7,331 项非等效规则覆盖关系亦未被逐一运行时认证。

[提交问题反馈](https://github.com/YohakuSama/loonkit/issues)
