# LoonKit 阶段07 — vNext-RC2 工程交接与正式发布禁行条件

**2026-10-20 / 重构分支 `refactor/loonkit-vnext` / Draft PR #39**
**阶段状态：ENGINEERING_CANDIDATE_STAGED / BLOCKED_PENDING_MAINTAINER_TEST。**
正式版号未确定，未发布 Release Tag、未合并 main、未更改正式用户实时引用。不得把阶段07静态 CI 成功描述为真机、DNS 或许可全部通过。

## 生产迁移基线与不可变对象

- 基准 main：`f19421933d2177f95e7537f1208d990b3094f1f4`。
- 阶段06交接：`0a5cafefd18c28b16908502c1f3324b7272585c9`；RC1 资源已验证：`95b6e0eb02d3cc6e82fc8e6998dd130a2c5b7a98`。
- RC2 固定规则资源提交：`d405e4be28c447b6e57a4790e965c89f342d6dd6`，26 份、197,765 条（静态清点）。
- 两份根级配置与两份 RC2 候选镜像按原文冻结并列于 `release/phase-07/RC_MANIFEST.json`。两份规则/本地策略一致，General/DNS/DoH/TUN 各自与冻结基线一致。
- 26 份资源独立版本化 `rules/releases/vNext-RC2/`；旧 `rules/generated/` 仍保留旧正式客户端兼容，不作为 vNext 生成输入，亦不作未经审核的自动更新。
- 历史来源锁包含 44 份冻结输入；其中 33 份规则历史正文在 `rules/snapshots/phase03/generated/`。不仅锁住 SHA256 与 Git blob，还通过阶段03固定 Commit 原始路径校验字节；此证据无法推导原始上游每一行来源。

## 已提交且自动验证的工程工作

1. 完成生成器历史输入/正式输出隔离、可重复构建和旧路径更改/删除后重新生成测试。
2. 统一两份配置的 26 条自托管订阅和 106 条本地规则，保留 33 个策略组、AdBlock 的 26 条本地优先级覆盖、独立海外入口、`GEOIP,CN,DIRECT,no-resolve` 与 `FINAL,Final`。
3. 取消 RC2 的独立 ProxyProtect 运行时引用，17 条旧名单只保留历史兼容及退休审计证据。
4. 规则、图标、插件及插件内部脚本锁定固定 Git Commit，检查每份规则哈希和全部 Git 对象。
5. 将阶段01冻结工作流字节归档；阶段02和旧复合规则 CI 完成只读化。现行 9 个工作流不再包含写权限、自动推送或创建 PR 步骤；自动化回归保护此约束。
6. 独立 main 合并预演使用一次性 worktree，对合并配置、规则重建、两份配置哈希及 Git 合并撤销进行检查。不自动合并 main。
7. 许可证逐源核对记录 87 条历史来源：blackmatrix7 41、v2fly 35、felixonmars 1、维护者本地10。属历史候选来源分类，非当前逐行再分发授权证明。
8. 建立只读来源更新差异工具与 Loon 语法校验；更新的输出仅供 PR 审核，绝不自动升级现役规则。
9. Release Gate 分离已验证静态通过与实际阻断项，不会因静态通过将真机结果设为 PASS。

## 关键验收项目与真实证据状态

- **静态工程**：来源完整性、生成器确定性、双配置字节保持、固定资源 SHA、离线规则测试、独立工作树合并/撤销可以由 CI 验证，并按已运行的 SHA 登记 `RELEASE_GATE.json`。Git 层回滚通过**不证明** Loon 客户端缓存清除。
- **许可证**：**BLOCKED_REVIEW**。blackmatrix7 的 GPL-2.0 与仓库特别声明、历史混合规则版权归属、v2fly MIT 署名、FelixYan WTFPL、插件和图标权利，均需要最终审核；缺乏证据不得宣称允许完整再分发。
- **真机专项**：**NOT_EXECUTED**。包括 Loon 导入、私人节点恢复、国内银行/支付、海外服务/地区解锁、AdBlock REJECT/DIRECT、Final 四档、DNS 真实解析器与节点出口、IPv4/IPv6、异常 DIRECT、7331 项高风险父子规则的代表性测试。
- **客户端回滚**：**NOT_EXECUTED**。维护者须验证恢复旧规则订阅、缓存、节点及策略组选择，并收集匿名化证据。
- **批准**：**NOT_EXECUTED**。Draft PR #39 的 `maintainer-release-gate` 会主动失败防止误合并。

## 维护者收尾操作

1. 在 https://github.com/YohakuSama/loonkit/pull/39 审查工程差异、授权证据和全部 CI；重点查看 `release/phase-07/RELEASE_GATE.json`。
2. 下载阶段07 CI artifact `phase07-rc2-dual-profile-unreleased`；核对 `RC_MANIFEST.json` 中的两份配置 SHA256，与最终实测文件严格一致。**若候选文件字节变化，必须重新执行受影响真机测试。**
3. 在私人设备保留原节点订阅，仅加载候选并依据 `release/phase-07/DEVICE_TEST_PLAN.md` 和 `validation/phase-05/RESULT_TEMPLATE.json` 执行专项测试，先用 `scripts/validate_device_results.py` 验证脱敏记录再共享。
4. 请明确处理授权及混合来源可再分发问题。必要时更换风险来源并冻结新的候选版本，重新静态回归、真机验收。
5. 审核 `MIGRATION_ROLLBACK.md` 并手动演练真机缓存回滚。完成前不得把 `rollback_rehearsal` 设为 PASS。
6. 获得明确审批后方能确定正式版本号、修改 Gate 的真实证据状态、使用受保护 PR 合并 main 和发布；任何时候不允许工作流自动推送或自动合并。

## 补充资料

- `release/phase-07/RELEASE_GATE.json` 机器可读发布门槛。
- `release/phase-07/RC_MANIFEST.json` 26 份固定规则和双配置哈希。
- `release/phase-07/LICENSE_SOURCE_LEDGER.json` 87 个历史来源许可审查记录。
- `release/phase-07/CLEANUP_LEDGER.md` 文件级清理/迁移/保留依据。
- `release/phase-07/UPSTREAM_UPDATE.md` 后续输入锁定与差异审核制度。
- `release/phase-07/MIGRATION_ROLLBACK.md` 迁移与 Git/客户端分层回滚方案。

最终状态并非“正式发布通过”，而是“已准备受控 RC2 工程候选，等待独立授权和维护者运行时验收”。

## 阶段07持续维护与设备证据锁定补充

- `scripts/phase07_source_update_review.py`：除最多30条审查样例外，输出 `full_change_set` 全量增删 matcher、全部变更的 SHA256 和高风险规则类型统计；导出报告不可覆盖配置、来源锁与发布资源。
- `scripts/phase07_next_release.py`：仅在维护者明确指定新候选名称时、在仓库外的空目录预构建下一版；输出动态规则数、26份规则文件、逐文件 SHA256、对 RC2 的完整规则差异及摘要哈希；不可写入正式规则目录、不可发布、不可自动确定正式版本。
- `scripts/phase07_device_attestation.py`：将未来真实的脱敏 `validation/phase-07/device-results.redacted.json` 与已测试配置的 Git Blob SHA256 和候选远程规则固定 Commit 绑定，要求两份配置独立通过 AdBlock 双模式、Final 四模式等对应 scope 的机器检查。不存在数据时不能将真机类发布门槛改成 PASS；即便格式检查通过仍需维护者审核真实设备结论。
- `scripts/phase07_gate.py`：真机类门槛 PASS 必须触发上述实际证据核验，不能只凭手写文本或随意填写一个40位提交号绕过。许可证和维护者审批继续保持独立阻断。
- 下一次生成不同字节的新候选，必须重新固定资源 Commit 与 SHA256，并按影响范围重新跑真机测试；RC2 原规则和配置字节不得静默更换。
