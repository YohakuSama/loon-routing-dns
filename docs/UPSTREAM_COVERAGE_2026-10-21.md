# 上游来源审阅记录（2026-10-21）

本报告汇总 [Full Upstream Live Audit](https://github.com/YohakuSama/loonkit/actions/workflows/upstream-live-audit.yml) 对登记来源的下载、解析及覆盖检查。审阅产物独立于正式规则发布。

## 审阅结果

| 指标 | 结果 |
| --- | ---: |
| 登记来源 | 87 / 87 |
| 远程来源 | 77 / 77 |
| 本地来源 | 10 / 10 |
| V2Fly 展开引用文件 | 10 |
| 下载失败或未知语法 | 0 |
| 保留为审阅证据的特殊表达式 | 8（涉及 4 个来源） |
| 正式规则变更 | 0 |

审阅材料包括原始来源快照、规范化候选及 SHA-256 校验记录。大体量来源 `bm-chinamaxnomedia-domain` 已在 GitHub Actions Runner 成功下载。

## 需要人工处理的表达式

| 来源 | 数量 | 类型 | 处理依据 |
| --- | ---: | --- | --- |
| `bm-advertising-lite` | 2 | Loon `URL-REGEX` | 使用 URL/MITM 匹配语义 |
| `v2-openai` | 1 | V2Fly `regexp:` | 主机名正则需要独立转换审核 |
| `v2-netflix` | 4 | V2Fly `regexp:` | 匹配动态 AWS 域名范围 |
| `v2-disney` 引用的 `hotstar` | 1 | V2Fly `regexp:` | 需要确认等价规则范围 |

这 8 条表达式的原文、审阅行号、SHA-256 和分类依据保存在 `UPSTREAM_REVIEW.json` 的 `excluded_expressions` 中。10 份展开的 V2Fly 引用文件保存在 `include_snapshots/`。

## 校验机制

`scripts/verify_upstream_coverage.py` 分别报告两项指标：

- **来源覆盖完整性**：87 个登记来源均已读取，表达式已解析或记录排除原因；本次检查通过。
- **规则表达式转换完整性**：8 条正则表达式需要人工处理，因此本次尚未达到完全转换状态。

`FULL_DIFF.json` 保存完整增删差异，`FULL_RISK_AUDIT.json` 保存新增规则的风险分类和来源记录。审阅结果提供候选和变更证据，正式更新需经过维护者审核、规则构建与回归验证。

[规则安全说明](./RULE_SAFETY.md) · [来源目录](../rules/sources.json) · [返回首页](../README.md)
