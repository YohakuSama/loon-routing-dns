# 来源更新与候选差异审核（只读）

RC2 当前来源基准为 `rules/snapshots/phase03/generated/` 的不可变合并快照；其原始上游行级血统 **NOT_RECOVERABLE_FROM_MERGED_SNAPSHOT**，此工具不能假定每条规则来自哪一家仓库。

## 预审单个来源文件

```bash
python3 scripts/phase07_source_update_review.py \
  --source rules/snapshots/phase03/generated/Google.list \
  --proposed /tmp/Google.proposed.list \
  --report /tmp/google-update-review.json
```

输出固定的 SHA256、新旧规则计数、按 matcher 类型分组的新增/删除计数与最多 30 行样例。输出标为 `PENDING_REVIEW_NOT_PUBLISHED`，不会修改任何正式规则、冻结来源或订阅。

确认合法授权与归属、可用来源 Commit、回归结果后，维护者可在 **新的 PR** 中物化新不可变快照，逐项更新 `engine_manifest.json` 与 `sources.lock.json` 的哈希、Git blob 以及来源描述。必须运行阶段 02/04/05/06/07 全套离线审计并生成新的候选差异报告；发布版本不得复用已经冻结的 `vNext-RC2` 目录或改写旧候选 SHA。受影响的真机验证须重新执行。

新来源绝对不能从 `rules/generated/` 或 `rules/releases/` 生产输出中提取，不能直接从 `main` 或任何上游动态 URL 无审核同步到现役配置。CI 对新 PR **只读**，若许可未核实或测试证据未齐全即阻止正式发布。

## 完整差异证明（阶段07发布门槛）

`scripts/phase07_source_update_review.py` 生成的 JSON 同时包含 `full_change_set.added` 和 `full_change_set.removed` 的**全量规则清单**，不截断；`added_sample` / `removed_sample` 的 30 行仅用于快速浏览。 `change_set_sha256` 是对排序后的完整列表 JSON 采用 UTF-8、无多余空格编码的 SHA256，方便不同审查者对照同一份报告。 `high_risk_matcher_changes` 与 `risk_sample` 会提示 IP、ASN、DOMAIN-KEYWORD 等高风险新增或移除规则，但不会仅凭语法校验认定行为正确。

上游候选应导出到**仓库外的文件路径**（例如 `/tmp/source-review.json`），不可通过 `--report` 覆盖规则、配置、版本锁或发布证据。 `--proposed` 仅用于读取新的候选来源，不能指向正式规则输出目录。所有变更仍由人工审查原始文件、完整 diff、许可与来源归属；`PENDING_REVIEW_NOT_PUBLISHED` 不构成通过。

## 下一候选规则版本化构建（独立只读发布流程）

新增 `scripts/phase07_next_release.py` 用于下一次**明确由维护者决定名称**的候选预构建。工具只使用已锁定的独立来源和当前 vNext 引擎，要求输出目录在仓库外且初始为空；绝不提交、下载、推送、修改 `rules/generated/`、覆盖 `rules/releases/vNext-RC2/` 或直接影响用户。

```bash
# 以下 RC3 仅为使用示例，不代表已批准 RC3 或正式版本号
python3 scripts/phase07_next_release.py --version vNext-RC3 --output /tmp/loonkit-new-candidate --build
python3 scripts/phase07_next_release.py --version vNext-RC3 --output /tmp/loonkit-new-candidate --check
```

该目录包含 26 份按版本命名的规则、`NEXT_RELEASE_MANIFEST.json`、`NEXT_RELEASE_DIFF.json`；清单列出每个输出的 SHA256、动态规则数、对 RC2 的基准 SHA256、全部增删 matcher 的精确 JSON 差异与摘要哈希。无需重新采用 RC2 的固定 197,765 断言来掩盖新版本的真实增减。只有经过合规审核、GitHub PR、规则差异审核和真机回归，才可把新版本资源固定在不可变 Commit，进一步构建新正式配置。此工具**不做最终公开发布或授权**，仍须由维护者明示决定稳定版本号及新资源引用。
