# 正式版文件与依赖

清理后的唯一完整配置为 `LoonKit.lcf`。固定 Raw URL 引用的 26 份正式规则位于 `rules/releases/vNext-RC2/`，图标位于 `icons/v20261018r2/` 和 `icons/v20261018r3/`，插件固定路径为 `release/phase-07/assets/Network_Diagnostics.plugin`，插件使用 `scripts/v20261018r11/`。

正式构建仅需 `rules/inputs/`、`rules/custom/`、`build/engine_manifest.json`、`build/sources.lock.json`、`rules/sources.json`、`rules/routing_guardrails.json` 和 `scripts/rule_engine.py`。43 份规则输入均经校验，输出不得作为自己的输入。许可证位于 `rules/LICENSE.*`，证明材料位于 `build/legal_evidence.json`、`build/license_sources.json` 和 `docs/THIRD_PARTY_NOTICES.md`。

测试位于 `tests/`，工作流仅为 `ci.yml`、`rules-update.yml` 与 `release.yml`。

按维护者明确要求，不再保留 DNSPod 的完整配置、旧 `rules/generated/`（34 文件）、`ProxyProtect.list`、`rules/active_profile.json`，以及重复的两个 `plugins/` 插件别名。删除旧 Raw 路径会中断对此类旧资源的订阅；正式标准版从未读取这些被清理的兼容资源。

现有 Git 历史仍被保留。正式配置使用旧提交固定 Raw URL；若希望在同一仓库建立全新历史，必须先改动这些 URL 并完成发布验证，再单独批准强制更新主分支及清理分支/标签。

## 当前诊断插件运行时链

`LoonKit.lcf` → 固定提交 `97ec3554465ba5c338a00a5e2f7e8598b9f26b3a` 中的 `release/phase-07/assets/Network_Diagnostics.plugin` → 固定提交 `ea2a2d87ae57c7854ee037cba3174f7881041051` 中的 `scripts/v20261020r1/network-diagnostics.js`、节点出口脚本及插件图标。老版 `scripts/v20261018r11/network-diagnostics.js` 保留为已发布历史路径；正式插件不再使用它。
