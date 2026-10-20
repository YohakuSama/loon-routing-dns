# vNext-RC2 生产迁移预案与回滚演练

状态：`DRY_RUN_REQUIRED`。此文档中的人工操作**尚未执行**，不是 GitHub main 的合并授权。

## 准备与旧用户兼容性

基准正式版 main `f19421933d2177f95e7537f1208d990b3094f1f4`。迁移前固定新的 main HEAD，与基准对比，记录是否有其他合法提交。先由维护者保存当前 Loon 配置及私人订阅备份到本地设备（不得进入仓库），导出所选组策略；确认稳定入口 `main/LoonKit.lcf`、`main/LoonKit.PrivacyDNS.lcf`，及原有 `main/rules/generated/*.list` 的所有访问者。

冻结版本规则文件：`rules/releases/vNext-RC2/` 26 份；固定资源 Git SHA：`d405e4be28c447b6e57a4790e965c89f342d6dd6`；完整 SHA256 在 `release/phase-07/RC_MANIFEST.json`。正式版本号**待维护者批准**，不可视 RC2 为稳定 SemVer。

新配置两个入口（本分支文件名保持不变）都从独立种子生成，使用相同的固定 26 规则和固定图标、插件。原有 `rules/generated/` 保留旧版原文兼容，不再作为新版生成器输入。不要悄悄把旧 URL 的内容自动换成规则数变化的新版本；逐步指导旧用户通过完整配置 URL 迁移。

## 在非生产环境模拟合并

```bash
git fetch origin main refactor/loonkit-vnext
git worktree add --detach /tmp/loonkit-main-sim origin/main
cd /tmp/loonkit-main-sim
git merge --no-commit --no-ff origin/refactor/loonkit-vnext
# 如果检测到冲突、非预期生产变动，停止并先修复。
python3 scripts/vnext_source_lock.py --check
python3 scripts/vnext_rule_engine.py --check
python3 scripts/phase07_release.py --check
python3 -m unittest discover -s tests -p 'test_*.py' -v
node tests/test_node_copy.js
node tests/test_network_diagnostics.js
node tests/test_current_plugin.js
git diff --check
git merge --abort
cd -
git worktree remove --force /tmp/loonkit-main-sim
```

将工作树命令输出与 SHA 存入 PR 的 CI 证据；此模拟不请求 GitHub 权限、不改 main。上述步骤只在无冲突时适用；变更 main HEAD 时必须重新演练。另须在 CI 中增加实际合并树检查，不能仅靠此文档。

## 正式上线门槛

同时满足机器 Gate 静态各项 PASS、RC2 真机导入及日常/专项测试结构化记录、解析器/出口对照、许可证结论、合并/回滚演练和维护者书面批准。无授权不得 merge、push main 或覆盖规则。合并前检查主配置与 PrivacyDNS 各自 General 原文保持不变、原规则兼容路径仍存在。部署过程中 CI 全程仅只读。

## 回滚步骤（包含客户端缓存）

1. 立即暂停向用户发布新配置，固定问题发生时的候选 Commit、两个配置哈希和 26 个规则文件哈希。
2. 将 main 回滚到已记录的上一正式版本（若期间存在合法新提交，必须使用可审核的 revert PR，而不能对 main 强制 reset）。
3. 设备端停用新版配置，恢复此前导出的完整原配置、私人节点订阅、策略组选择及 DNS/TUN 设置；注意别把隐私敏感文件上传公开仓库。
4. Loon 内手动停用/删除 RC2 额外远程规则项，清除过期或失败的资源缓存（以 Loon 当前版本提供的界面方式操作），强制重新下载正式原规则与插件，逐条确认 URL 和 SHA/版本。
5. 再次检查 Loon 的实际命中、国内金融支付、海外服务、AdBlock 两种选择、Final 各档和 DNS/出口；仅客户端页面显示旧配置并不足以证明规则已回滚。
6. 记录回滚时间、所用原 main Commit、回滚后远程资源版本、客户端 DNS/TUN 与业务结果，纳入事故单。

模拟回滚仍需通过自动化工作树与实际设备验证，机器 gate 保持 `NOT_EXECUTED` 直到出现完整证据。
