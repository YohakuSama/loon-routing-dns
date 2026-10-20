# LoonKit vNext-RC2（未正式发布）

> **状态：BLOCKED_PENDING_MAINTAINER_TEST**。本分支为正式发布准备，不代表 main 已升级。不得把本页视为正式稳定版发布公告；未经专项真机测试、授权审查和维护者批准，不得合并 main 或启用自动更新。

适用于 Loon 的社区分流配置，**不提供任何代理节点或私人订阅**。两份正式配置候选采用同一套分流输出，保留各自原有 DNS / DoH / TUN 参数。

- [主配置候选](./release/phase-07/LoonKit.vNext-RC2.lcf)：AliDNS 原配置。
- [PrivacyDNS 配置候选](./release/phase-07/LoonKit.PrivacyDNS.vNext-RC2.lcf)：DNSPod 原配置；保留历史文件名，不保证 DNS 经代理出口。
- [完整规则 SHA256、固定 Commit 与文件清单](./release/phase-07/RC_MANIFEST.json)。
- [机器发布门槛](./release/phase-07/RELEASE_GATE.json) · [真机验证](./release/phase-07/DEVICE_TEST_PLAN.md) · [迁移及回滚](./release/phase-07/MIGRATION_ROLLBACK.md) · [许可证审查](./release/phase-07/LICENSE_REVIEW.md)。

## 本次候选的实际结构

- 26 条远程 LoonKit 自托管规则订阅，共 **197,765** 条远程规则；33 个策略组；106 条本地规则（含 26 条 AdBlock 本地优先级保护）。
- 不再订阅独立的 ProxyProtect；17 条历史名单保留为审计证据，不以检测网站表现证明 DNS 安全。
- 国内直连、流媒体、社交、AI、Apple、Microsoft、支付与海外服务保留独立或明确归属的策略入口。七项原有海外策略的有限基础域名入口已恢复，区域解锁和辅助域名**尚需实际验证**。
- 广告策略 `AdBlock` 可选 `REJECT` 和 `DIRECT`；排查登录、支付或内容异常时，切换 `DIRECT` 可帮助确定是否误杀，但并非保证所有请求恢复。
- `Final` 可选 `Proxy`、`Auto`、`Fallback` 和 `DIRECT`。若主动选择 `DIRECT`，未命中其他规则的国外域名也可能直连。国内 IP 的 GEOIP 保底仍然保留。
- 7 条 IP-ASN 已统一添加 `no-resolve`；7,331 项非等效域名父子覆盖仍待代表性运行时验收，不能宣称全数正常。

## 分流构建与更新

**不可变旧合并来源**位于 `rules/snapshots/phase03/generated/`，原始上游每条规则来源不可恢复的事实仍如实记录。来源版本由 `refactor/vnext/engine_manifest.json` 和 `sources.lock.json` 校验。生成器 `scripts/vnext_rule_engine.py` 仅从冻结来源和独立配置种子构建候选，**不会读取作为正式输出的 `rules/generated/`**。

RC2 锁定产物存放在 `rules/releases/vNext-RC2/`，两份候选订阅使用固定的 Git SHA，而非开发分支动态内容；图标、插件及插件内部脚本也已固定相应审核 Commit。

`rules/generated/` 继续作为旧用户兼容路径保留，尚不包含新版 RC2 规则；后续是否将其转为新版受审输出，仅在正式迁移/维护者批准后执行。任何来源刷新应先创建独立的候选与差异报告，再由 PR 审核并重新运行真机回归；CI **不自动覆盖**已发布资源。

离线检查命令：

```bash
python3 scripts/vnext_source_lock.py --check
python3 scripts/vnext_rule_engine.py --check
python3 scripts/phase07_release.py --check
python3 -m unittest discover -s tests -p 'test_phase07_release.py' -v
```

## 使用及 DNS 注意事项

请先在 Loon **本地备份原有配置、策略选择和私人节点订阅**。下载上述候选文件手动导入，恢复自己的节点后更新资源并核验规则命中；不要把个人节点 URL、日志原始 IP 或访问凭据提交到 GitHub。

两份配置分别沿用历史 AliDNS 和 DNSPod 设置；本阶段**没有修改 DNS、DoH、TUN、IPv6、绕过或解析回退参数**。若要求避免加密 DNS 失败时明文回退，请在 Loon App 的 DNS 服务器设置中手动检查并关闭相关回退开关。加密 DNS 不必经代理出口；单个网页上的 DNS 地理位置不代表全局是否泄漏。详见 [DNS 隐私说明](./docs/DNS_PRIVACY.md)。

首次获取 GitHub Raw 资源在部分网络可能需要可用代理节点。仓库不提供节点；`Proxy`、`Auto` 和 `Fallback` 需要用户自己配置。

## 网络辅助

[网络辅助插件](./plugins/Network_Diagnostics.plugin)（旧稳定入口，main 当前仍提供）及 [插件使用说明](./docs/NETWORK_DIAGNOSTICS.md)。RC2 候选采用固定提交的插件，提供「节点出口信息」和「网络与 DNS 诊断」。网络切换自动检查及「直连 IP 对照」默认关闭；插件报告只是网络观测，不是安全认证。

## 正式链接、旧版迁移和回滚

旧稳定版原有订阅地址在 main 未批准切换前保持不变：

```text
https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf
https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.PrivacyDNS.lcf
```

正式升级后，既有完整配置订阅入口计划保持兼容，但旧版 34 条远程规则变为 26 条，必须检查 Loon 内是否存在仍单独启用的旧规则条目，避免重复生效。**旧版远程订阅 URL 不会自动转换为新版本**；用户需通过经过批准的新完整配置迁移。出现问题时，先恢复原有配置和节点订阅，确认恢复 `Our-*` 历史顺序，刷新规则并核查 Loon 日志；缓存不会因 Git 回滚自动清除。完整步骤见 [迁移与回滚](./release/phase-07/MIGRATION_ROLLBACK.md)。

本 RC2 尚不能声明全部国内金融业务、海外地区解锁、IPv4/IPv6、DNS 出口或 Loon 插件真机通过；相关门槛仍为 `NOT_EXECUTED`。

[反馈问题](https://github.com/YohakuSama/loonkit/issues)
