# 正式规则

v6.0.0 使用 `rules/releases/vNext-RC2/` 的 26 份冻结规则。两份正式配置均固定引用提交 `d405e4be28c447b6e57a4790e965c89f342d6dd6`，其字节、优先级和订阅顺序不在本次清理中修改。

`rules/inputs/` 是 33 份受锁定的源规则快照，结合 `rules/custom/` 十份本地资源及 `rules/ProxyProtect.list`，形成 44 份受 SHA256 校验的构建输入。生成器 `scripts/rule_engine.py` 读取 `build/engine_manifest.json`、`build/sources.lock.json` 及独立输入。使用 `python3 scripts/verify_release.py --check` 验证能否确定性重建全部发布规则。

`rules/generated/` 是只读的旧版订阅兼容路径；`rules/ProxyProtect.list` 兼具冻结输入与旧 URL 兼容作用。正式 v6 配置不订阅这两条旧发布路径。

上游目录见 `rules/sources.json`，新版本通过 `scripts/review_source.py` 形成变更报告，`scripts/prepare_release.py` 在仓库外输出候选快照，不自动覆盖正式文件。第三方许可正文保留在 `rules/LICENSE.*`，权利状态与来源限制见 [第三方说明](../docs/THIRD_PARTY_NOTICES.md)。
