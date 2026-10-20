# 正式版维护

## 唯一的正式规则构建链

`rules/inputs/` + `rules/custom/` + `rules/ProxyProtect.list` → `build/engine_manifest.json` / `build/sources.lock.json` → `scripts/rule_engine.py` → `rules/releases/vNext-RC2/`。

执行 `python3 scripts/source_lock.py --check` 和 `python3 scripts/verify_release.py --check` 验证 44 份源锁、26 份已发布规则、两份正式配置、插件、图标和资源哈希。执行 `python3 scripts/license_audit.py --check` 检查第三方许可正文和证据。CI 同时执行 Python/JavaScript 生产回归。

## 审核上游与准备新版本

`python3 scripts/review_source.py --source rules/inputs/Google.list --proposed /tmp/Google.list` 仅生成来源更新差异，不覆盖锁。

`python3 scripts/prepare_release.py --version v6.0.1-rc1 --output /tmp/loonkit-candidate --build` 在仓库外生成新规则候选、完整变更和校验文件。新增来源经单独核准、锁定后才能进入引擎。定期 `rules-update.yml` 只读获取上游数据摘要，正式发布前仍需审查许可证、行为测试、版本固定引用及实际设备运行。

`release.yml` 只做手工候选打包，**不自动推送、不改写用户配置、不创建 Release**。新正式版发布须单独批准。

## 稳定订阅与历史

两份正式配置中的 Raw 固定链接引用了 `d405e4be28c447b6e57a4790e965c89f342d6dd6`（规则及插件）、`95b6e0eb02d3cc6e82fc8e6998dd130a2c5b7a98`（图标）。还必须保留 `release/phase-07/assets/Network_Diagnostics.plugin` 这个旧路径。旧 `rules/generated/`、`rules/ProxyProtect.list` 与诊断插件兼容 URL 保留。

不删除 Git 历史对象、标签或远程分支。若将来单独批准独立新历史，应先用受保护可持续引用替换所有旧提交依赖，备份并在临时仓库验证完整资源和恢复路线。
