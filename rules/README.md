# v6.0.0 正式规则

正式配置 `LoonKit.lcf` 使用 `rules/releases/vNext-RC2/` 的 26 份固定版本规则，远程资源引用提交 `d405e4be28c447b6e57a4790e965c89f342d6dd6`。规则内容、顺序与策略归属不因仓库精简而改变。

**唯一构建输入：** `rules/inputs/`（33 份冻结规则）与 `rules/custom/`（10 份本地补充），共 43 个独立文件。输入由 `build/sources.lock.json` 的 SHA256 和 Git Blob SHA1 校验，策略在 `build/engine_manifest.json` 中锁定。正式生成器为 `scripts/rule_engine.py`。

`python3 scripts/verify_release.py --check` 验证冻结输入和 26 份已发布规则逐字节一致。来源更新先使用 `scripts/review_source.py` 检查差异，再通过 `scripts/prepare_release.py` 在仓库外准备候选，不自动发布。

旧版 `rules/generated/`、`rules/ProxyProtect.list` 和 v5 活动清单已应维护者要求删除；使用这些旧 Raw 地址的订阅将不再更新。许可正文仍保留在 `rules/LICENSE.*`，来源记录仍在 `rules/sources.json`，详情见[第三方声明](../docs/THIRD_PARTY_NOTICES.md)。
