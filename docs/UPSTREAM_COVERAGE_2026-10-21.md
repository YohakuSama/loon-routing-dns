# 上游来源审计结果（2026-10-21）

本报告来自 [Full Upstream Live Audit](https://github.com/YohakuSama/loonkit/actions/workflows/upstream-live-audit.yml) 的 GitHub Actions Runner **真实下载及解析**，不是仅通过 GitHub 文件预览接口的抽查。所有数据只用于生成风险审阅证据，**不会自动修改 LoonKit 的固定规则**。

## 本轮已完成

| 指标 | 实际结果 |
| --- | ---: |
| 登记来源 | **87 / 87 已读取并保存原始快照** |
| 其中远程来源 | 77 / 77 |
| 其中本地来源 | 10 / 10 |
| 展开的 V2Fly `include:` 文件 | **10**，单独保存来源内容与 SHA256 |
| 无法下载或存在未知语法的来源 | **0** |
| 已识别但无法安全等价转换的表达式 | **8 条，来自 4 个登记来源** |
| 规则是否自动发布 | **否** |

初次工具抽查曾无法读取的 `bm-chinamaxnomedia-domain` 大文件，已在 GitHub Actions Runner 成功下载并保存。**GitHub API 的单文件响应限制并不是规则源无效。**

### 8 条有意隔离的正则

| 来源 | 数量 | 类型 | 不自动转换的原因 |
| --- | ---: | --- | --- |
| `bm-advertising-lite` | 2 | Loon `URL-REGEX` | 需要 URL / MITM 语义，不能当作普通域名后缀规则 |
| `v2-openai` | 1 | V2Fly `regexp:` | 主机名正则不能直接扩成整个云服务商的后缀 |
| `v2-netflix` | 4 | V2Fly `regexp:` | 涉及动态 AWS 域名，泛化为 AWS 后缀可能误代理其他客户 |
| `v2-disney` 引用的 `hotstar` | 1 | V2Fly `regexp:` | 原始正则为有限模式，未单独验证匹配全集，保留为人工审阅项 |

这些表达式**没有被默默忽略**：它们的原文、所在审阅文本行号、表达式 SHA256、类型及拒绝转换原因，均记录在审核产物 `UPSTREAM_REVIEW.json` 的 `excluded_expressions` 中。V2Fly 的 10 个引用文件另外保存在 `include_snapshots/`，且其摘要记录于对应的登记来源。

**8 条被记录并分类 ≠ 8 条都已进入规则库。** 若日后要使用，需要单独实现与上游语义等价的 Loon 规则并验证真实请求；不能一概变成 `DOMAIN-SUFFIX`。

## 自动检查结果的两个不同概念

- **来源覆盖完整：** 每个登记来源的字节与哈希都可追溯，每行内容已转成候选或明确分类为不可自动转换的正则；无未知语法、缺失快照或缺失来源。
- **规则可完整转换：** 本轮 **否**；有 8 条已登记排除项。

`scripts/verify_upstream_coverage.py` 将这两个结果分别显示为 `All source lines classified` 与 `All rules safely translated`。缺失或无法取得来源、未知语法、排除记录与哈希不一致时，工作流**失败**。而仅存在完整审计记录的 8 条特殊表达式时，来源覆盖审计可以通过，但仍明确声明**未完成全规则转换**。

## 规则质量安全约束

- 一切新增、删除、按策略重归属、扩大或缩小匹配都仅属于审核建议。
- `candidate/*.list` 与现役规则完全相同，不包含未批准新增或自动删除。
- `FULL_DIFF.json` 保留完整增删；`FULL_RISK_AUDIT.json` 保留逐条新增的风险标签与来源。
- `scripts/upstream_review.py` 的 `include:` 解析限定为 V2Fly 官方数据源、限定文件名、递归深度、总大小，并对循环引用直接报错。

本次**没有修改** 26 份正式规则、`LoonKit.lcf`、DNS/TUN、代理策略与已安装插件。审核任务的绿色表示「已登记来源均被完整核查和分类」，并不代表新规则获得发布许可。

[查看规则安全机制](./RULE_SAFETY.md) · [上游目录](../rules/sources.json) · [返回 README](../README.md)
