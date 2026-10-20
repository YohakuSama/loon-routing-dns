# LoonKit v6.0.0 · 正式发布准备清单

> **当前状态：暂不发布 GitHub Release。** `main` 已提供 `LoonKit.lcf`，但现有证据不能证明整套规则和素材的再分发权利已全部核实。CI 通过 ≠ 授权批准，也不等于真机验收完成。不要仅为填满 Releases 页面而创建正式发布或宣称许可已清理。

## 已确认的技术事实

- 当前使用统一正式入口 `LoonKit.lcf`，26 份远程规则固定引用不可变提交。
- `scripts/source_lock.py --check` 与 `scripts/verify_release.py --check` 用于核验冻结输入及正式输出；Production CI 另执行测试和许可证**证据完整性**检查。
- `build/license_sources.json` 记录 **87** 条历史来源：41 条 blackmatrix7、35 条 v2fly、1 条 felixonmars、10 条本地来源；这只是历史目录，**不是逐条规则的来源和授权证明**。
- `build/legal_evidence.json` 目前为 `NOT_CLEARED`，`build/license_sources.json` 的 `release_status` 为 `BLOCKED_REVIEW`。
- `build/release_manifest.json` 中 `licenses` 为 `BLOCKED_REVIEW`，`device_test` 和 `maintainer_approval` 均为 `NOT_EXECUTED`；未取得实际签核前不得修改为通过。

## 完成正式发布所需的工作

### 1. 核实来源和再分发权利

逐个审查 `build/license_sources.json` 的来源记录，对照 `rules/inputs/`、`rules/custom/` 与已冻结的 `rules/releases/vNext-RC2/`，补充可核实的上游提交、具体素材来源及许可依据。合并去重后的 197,765 条规则目前**无法仅凭现存目录还原逐行作者**，不能把“推定许可证”误当作已获得授权。

优先核查：

- **blackmatrix7 / GPL-2.0-only（41 条历史来源）**：核对每种所用规则的真实权利人、GPL 义务与源代码提供方式；其 README 的特别声明应单独评估，不能仅以仓库内存在 GPL 文本就推断所有第三方规则可再分发。
- **v2fly / MIT（35 条）**：确认被使用内容及上游版权声明，在适用范围内保留完整许可证和署名。
- **felixonmars / WTFPL-2.0（1 条）**：验证实际来源与许可范围。
- **本地规则（10 条）**：由维护者确认原创性、来源及相关权利。
- **图标、商标与插件脚本**：分别确认来源和使用权；规则库的许可证不会自动涵盖品牌图标或其他代码。

若某部分无法建立可靠权利依据，应在**新的发布候选**中替换为有明确许可或自主制作的内容，重新生成、校验并测试；不要通过删除警告或直接修改旧冻结输出“清理”问题。

### 2. 由责任人完成独立审核并保存证据

现有 `scripts/license_evidence.py` 要求审核结果与**准确的冻结规则提交**绑定，并覆盖以下六个主题：

1. 合并规则的再分发权利；
2. GPL 及其他 copyleft 义务；
3. blackmatrix7 的额外声明；
4. 原始来源与逐行溯源缺口；
5. 图标及商标权利；
6. 插件及脚本权利。

由能够承担相应审核责任的人员形成实质性判断，在 `build/legal-reviews/` 保存有依据的审核记录，再按 `scripts/license_evidence.py` 的既有结构更新 `build/legal_evidence.json` 的签核、提交号及证据哈希。**自动校验只能核对审核记录的格式和一致性，不能替代法律判断。**

### 3. 完成真机验收与维护者确认

在实际 Loon 环境中测试导入、节点选择、国内直连、海外策略、远程规则、广告拦截、DNS、网络诊断及默认关闭的切换提醒。保留机型、Loon 版本、测试日期和结果，获得维护者确认后，才更新发布清单中的相应状态。

### 4. 运行发布前检查

```bash
python3 scripts/source_lock.py --check
python3 scripts/verify_release.py --check
python3 scripts/verify_release.py --check --remote
python3 scripts/license_audit.py --check
python3 scripts/license_evidence.py --check
python3 -m unittest discover -s tests -p 'test_production.py' -v
node tests/test_current_plugin.js
node tests/test_network_diagnostics.js
node tests/test_node_copy.js
```

**重要**：`license_audit.py --check` 在证据未通过时也可能以退出码 0 输出 `"status": "BLOCKED_REVIEW"`，表示目录准确地记录了阻塞状态，**不是已准许发布**。必须检查输出的 `independent_clearance` 和审核记录，不能只看 CI 绿灯。

### 5. 通过审核后再创建 GitHub Release

在全部授权、测试、维护者确认完成后，冻结并验证准备发布的提交；将 `v6.0.0`（或实际重新审核的新版本号）指向正确的提交，在 GitHub **Releases → Draft a new release** 填写版本说明并核对资产，最后发布。

若审核需要替换大量规则，应使用**新版本**重新测试和发布，不要让旧版本号指向内容显著不同的配置。当前 `.github/workflows/release.yml` 仅构建审阅候选，**不会自动发布**，这属于现有的保护设计。

## 现存资料

[第三方声明](./THIRD_PARTY_NOTICES.md) · [历史来源目录](../build/license_sources.json) · [审核元数据](../build/legal_evidence.json) · [发布清单](../build/release_manifest.json) · [更新记录](./CHANGELOG.md)

本文是发布流程与技术证据清单，不构成许可结论或法律意见。
