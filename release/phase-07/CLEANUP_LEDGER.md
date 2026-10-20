# 文件清理、保留、迁移审计账本

| 原路径 | 分类/动作 | 调用方与原因 | 新路径或保留依据 | 用户影响 | 验证 |
|---|---|---|---|---|---|
| `rules/generated/*.list`（33 份） | **保留旧输出，迁移一份不可变输入快照** | 旧版订阅 + 新引擎原直接读取，导致循环 | `rules/snapshots/phase03/generated/` 33 份输入复制；`rules/generated/` 继续旧客户端兼容出口 | 老用户不改变下载 URL | `vnext_source_lock.py --check`、篡改/删除输出专项回归 |
| `LoonKit.lcf` / `LoonKit.PrivacyDNS.lcf` 旧正文 | **作为不可变模板保留**，根路径在重构分支改为 RC2 | 用户正式配置、旧生成器模板和阶段测试曾耦合 | `refactor/vnext/templates/*legacy-seed.lcf` | main 尚未变动，正式客户端不受影响 | 双 General 原文及旧 34 条基线断言 |
| `rules/ProxyProtect.list` | **仅保留历史证据及旧兼容 URL** | 旧版独立订阅曾依赖，RC2 不引用 | 原路径历史保留；规则不搬进隐藏白名单 | RC2 未命中时由正常规则/Final 决定 | 候选无 ProxyProtect，17 条历史退休台账 |
| `scripts/build_composite_rules.py`, `rules/active_profile.json` | **保留旧版维护/审计代码，禁止作为 RC2 正式输入** | 旧规则 CI 和历史回归使用 | `scripts/vnext_rule_engine.py` 与隔离输入锁 | 不改老规则 | 历史测试与新编译器测试分别跑 |
| `refactor/vnext/generated/*.list` | 保留锁定中间产物 | RC1/RC2 SHA 可重复生成 | `rules/releases/vNext-RC2/` 固定版本化待发布规则 | 尚未正式发布 | 原字节复制 + 每份 SHA256 |
| `baselines/`, `audits/phase-02/`, `design/phase-03/`，各阶段 reports | **必须保留** | 审计/追溯/历史可核验基线 | 保持原目录 | 无 | 历史专项校验 |
| `plugins/v20261018r11`, `scripts/v20261018r11`, `icons/v20261018r2/r3` | **保留** | 已发布用户/诊断脚本与图标 | RC2 插件 wrapper 在 `release/phase-07/assets/` 且内部 URL 固定 Commit | 新旧可恢复 | 静态路径及 URL 锁定 |
| 阶段 01-06 CI 工作流 | **阶段性只读回归继续保留** | 作为历史正确性证明，不删测试掩盖回归 | 新增阶段 07 主发布 Gate 工作流 | 可能增加 CI 耗时 | 阶段06旧候选 + 阶段07新产物都检查 |

没有无依赖证据的旧文件，不凭名称直接删除。正式宣布废弃旧代码前，须逐项获得实际调用方和客户端兼容性证明。

## 阶段07 补充：历史冻结 CI 工作流归档与只读迁移

- `.github/workflows/phase-02-audit.yml`：由 `contents: write`、`persist-credentials: true`、自动提交/推送改为 `contents: read`、无推送；以 `--check` 比较历史审计文件；历史文件仍完整保留。
- `.github/workflows/composite-rules.yml`：取消定时自动建立 PR 的写权限。仍能以只读权限下载上游并上传隔离候选 artifact，不更新线上规则。
- `refactor/vnext/templates/phase01-composite-rules.yml`：从冻结 Git 版本复制的**字节不变的旧工作流**，仅供阶段 01/02/03 哈希核验，不再执行。新工作流与历史报告的输入语义明确分离。
- `scripts/phase07_historical_attestation.py`：通过 `git cat-file` 实查阶段 03 固定 Commit 的 44 个历史 Git blob，验证新目录 33 个快照与旧 `rules/generated/` 原始字节一致。无需外部网络下载，不能自动证明原始上游逐行来源。
- `tests/test_phase07_release.py`：扫描全部现行 GitHub Actions 工作流，阻止未来回归写权限、自动提交/推送或自动创建 PR。

上述整改不删除任何阶段性测试，也不伪造客户端 DNS、IPv6 或缓存恢复结果。
