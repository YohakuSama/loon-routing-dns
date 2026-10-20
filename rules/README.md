# LoonKit v6.0.0 规则目录与可追溯来源

> **v6.0.0 使用经过验证的 vNext-RC2 规则数据快照。** `vNext-RC2` 是不可变规则快照目录名，不是完整配置的正式版本号。历史 v5.10.0 规则说明归档于 [legacy-v5.10-README.md](./legacy-v5.10-README.md)。

## 现役候选架构

- **26 份规则文件，197,765 条远程规则**：`rules/releases/vNext-RC2/`。版本固定在 `d405e4be28c447b6e57a4790e965c89f342d6dd6`，以 `release/phase-07/RC_MANIFEST.json` 的 SHA256、条数和路径为准。
- **两份正式候选配置**：`LoonKit.lcf` 与 `LoonKit.PrivacyDNS.lcf` 均引用完全相同的固定规则，106 条本地分流中有 26 条 AdBlock 本地优先级保护。两份 General 的 DNS/DoH/TUN 原文各自保持历史基线。
- **规则输入**：`rules/snapshots/phase03/generated/` 独立冻结 33 个历史合并快照。生成器**不从 `rules/generated/` 读取任何输入**。
- **源锁**：`refactor/vnext/engine_manifest.json`、`sources.lock.json` 锁定输入 SHA/ Git blob，`scripts/vnext_rule_engine.py` 可重复生成候选；`scripts/phase07_release.py --check` 验证版本化规则、正式候选配置及 SHA256。
- **旧订阅兼容**：`rules/generated/` 的老版本输出保留不删除、不在未批准时直接替换；现役 v6.0.0 配置只消费 `rules/releases/vNext-RC2/` 的固定版本规则。旧资源与新候选版本号不能混为一谈。
- **无独立 ProxyProtect**：v6.0.0 正式配置未订阅 `rules/ProxyProtect.list`。该文件及其 17 条历史保护匹配保留仅为旧客户端兼容和审计，不作为正式发布的 DNS 安全证据。
- **遗留风险**：来源清单 `sources.json` 的 87 条历史条目不能证明所有当前规则的实际行级版权/来源归属；历史上游混合正文不可恢复。7,331 项非等效域名覆盖需要代表性真机测试；不能标为全部通过。

## 离线可复现验证

```bash
python3 scripts/vnext_source_lock.py --check
python3 scripts/vnext_rule_engine.py --check
python3 scripts/vnext_phase05_report.py --check
python3 scripts/phase07_release.py --check
python3 scripts/phase07_resource_audit.py --check
python3 scripts/phase07_gate.py --lint
```

以上检查只验证来源、格式、生成结果和固定 Git 对象；DNS 出口、真实设备载入、地区解锁、银行支付、AdBlock 选择与 FINAL 出口需要维护者独立提供结构化真机数据。注意插件、图标、用户节点及缓存问题不一定是规则归属问题。

## 来源更新和审核

先从许可允许的固定版本获取拟更新的来源，形成新的不可变候选文件，绝不能将已经输出的正式规则反过来当原始输入。使用 `scripts/phase07_source_update_review.py` 生成只读新增/删除差异报告。更新后必须通过来源锁、审计、分流回归、许可证检查以及维护者的运行时专项回归，新建候选版本号才能替换正式资产。完整流程见 [来源更新说明](../release/phase-07/UPSTREAM_UPDATE.md)。

许可证正文和历史回溯资料见 `rules/LICENSE.*`、`rules/sources.json` 和 [许可证风险审查](../release/phase-07/LICENSE_REVIEW.md)。完整保留 GPL-2.0、MIT、WTFPL 许可正文及来源说明；许可疑义须按证据处理，不把逐行溯源作为通用强制条件。
