# LoonKit 正式规则

当前 **v6.5.2** 使用 `rules/releases/vNext-RC2/` 中的 26 份固定版本远程规则，引用提交 `9bbac4c9aa0ec33c82ab5fe03648127f3f4754f4`。配置还包含自 v6.1.0 起审阅的七项服务 62 条域名规则，详见 [服务覆盖清单](./service_coverage_v6.1.0.json)。

## 规则构建

构建输入包括 `rules/inputs/` 的 33 份冻结规则和 `rules/custom/` 的 10 份本地规则，共 43 份文件。输入哈希由 [sources.lock.json](../build/sources.lock.json) 固定，策略定义见 [engine_manifest.json](../build/engine_manifest.json)。

正式规则编译脚本：`scripts/rule_engine.py`。使用以下命令检查固定输入、已发布规则及配置一致性：

```bash
python3 scripts/source_lock.py --check
python3 scripts/verify_release.py --check
```

## 上游审阅与发布

[规则更新工作流](../.github/workflows/rules-update.yml) 每周读取登记的上游来源，解析 Loon、domainset、v2fly、dnsmasq 规则，生成来源快照、规范化候选、增删差异和跨策略冲突报告。

构建过程会进行规则规范化、去重、域名覆盖分析和策略冲突隔离。公共后缀、共享基础设施、过宽网段及广告拦截影响在候选审阅中单独标记。维护者审阅差异并完成回归后，再决定是否生成新版本的固定资源引用。

候选输出与当前已发布基线分离；自动来源审阅不会更新正式规则。具体机制见 [规则安全审阅](../docs/RULE_SAFETY.md)。

## 许可与来源

第三方规则的来源、许可及署名保留在 [第三方许可与来源](../docs/THIRD_PARTY_NOTICES.md)，维护和发布流程见 [维护说明](../docs/MAINTAINING.md)。
