# v6.0.0 正式规则

正式配置 `LoonKit.lcf` 使用 `rules/releases/vNext-RC2/` 的 26 份固定版本规则，远程资源引用提交 `9bbac4c9aa0ec33c82ab5fe03648127f3f4754f4`。规则内容、顺序与策略归属不因仓库精简而改变。

**唯一构建输入：** `rules/inputs/`（33 份冻结规则）与 `rules/custom/`（10 份本地补充），共 43 个独立文件。输入由 `build/sources.lock.json` 的 SHA256 和 Git Blob SHA1 校验，策略在 `build/engine_manifest.json` 中锁定。正式生成器为 `scripts/rule_engine.py`。

`python3 scripts/verify_release.py --check` 验证冻结输入和 26 份已发布规则逐字节一致。来源更新先使用 `scripts/review_source.py` 检查差异，再通过 `scripts/prepare_release.py` 在仓库外准备候选，不自动发布。

旧版 `rules/generated/`、`rules/ProxyProtect.list` 和 v5 活动清单已应维护者要求删除；使用这些旧 Raw 地址的订阅将不再更新。第三方规则沿用实际适用的上游许可：blackmatrix7（GPL-2.0-only）、v2fly（MIT）、felixonmars（WTFPL-2.0）；完整许可文本保留在 `rules/LICENSE.*`，历史来源记录位于 `rules/sources.json`。无需逐条联系已通过相应许可证授权的规则作者；最终合并规则的逐行来源没有全部记录，不应宣称 LoonKit 拥有第三方内容版权。详见[第三方许可与来源声明](../docs/THIRD_PARTY_NOTICES.md)。

## 上游更新与规则收紧的实际能力

`.github/workflows/rules-update.yml` 每周检查 87 条历史来源记录的当前资源，并产生**只读审核附件**，不会自动写入冻结输入或正式规则。更新要经过来源差异审阅、许可证及策略回归、重新锁定输入和发布新的固定规则版本。

现有 `scripts/rule_engine.py` 对锁定的 33 份冻结规则及 10 份本地规则执行规范化、精确去重、同策略的 DOMAIN / DOMAIN-SUFFIX 覆盖去重、跨策略冲突隔离，并针对审阅过的关键字及共享网段进行局部收紧。**这并不是对所有上游来源的自动智能合并，也无法保证所有规则始终最新或完全不存在误分流。**
