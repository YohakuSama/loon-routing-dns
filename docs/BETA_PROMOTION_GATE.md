# 测试版正式发布预检

## 独立发布 PR 模型

v6.5.5 的测试来源提交是 `adc567168eed8e21dc8d80aebc40b85f35fc1a1b`，发布 PR 的 head 是独立 release 分支，最终 main 提交必须在合并后重新核对。不能把这个 PR 当作原生 beta→main PR 假装旧版门禁直接通过；新模型必须同时约束精确测试来源、固定资源及哈希、head 的 production CI 与 main 目标。

当前七天观察、全部设备场景逐项证据未记录；任何静态检查或总体“未发现问题”反馈不能代替现有强制要求。保持草稿，不自动绕过或禁用。


此前用户已经报告真机运行未发现问题，记录在 BETA_OWNER_FEEDBACK.json。该记录缺少精确 SHA 和逐项场景；新 beta.4 的改动仍需有针对性的验收。

docs/BETA_ACCEPTANCE_TEMPLATE.json 是空白模板，不是测试结果。仅凭本地 JSON 中的 true 或 success 不能授权正式发布。

    python3 scripts/beta_promotion_gate.py --assert-template-blocked
    python3 scripts/beta_promotion_gate.py --evidence /path/to/REDACTED_ACCEPTANCE.json
    python3 scripts/beta_promotion_gate.py --evidence /path/to/REDACTED_ACCEPTANCE.json --live --promotion-pr PR_NUMBER

静态门禁检查精确配置和版本、回滚指针、完整场景与风险审核、至少七天真实观察以及非未来时间。--live 使用 GITHUB_TOKEN 只读核对 GitHub 中的准确 workflow、实际成功 job、提交、配置/manifest、当前 beta HEAD 与独立的非草稿 beta→main PR；不执行合并。

CI 中的模拟成功只是回归测试，不是设备证据。缺少真实资料时保持阻断。当前 user feedback 不被扩写为 DNS 故障、七天观察或所有场景已通过。

预检也不自动改写正式入口：正式发布仍需单独的版本化发布变更，保留已验收的资源 SHA，核对正式校验值和既有 production CI。仅把 beta 分支合入 main 而不更新正式入口，不等于配置升级。

正式发布前不得运行历史资源删除；scripts/beta_cleanup.py 提供先盘点、再审核的计划与发布后清理门禁。历史 Git 对象和原始冻结输入始终保留。
