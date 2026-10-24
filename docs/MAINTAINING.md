# LoonKit 维护与发布

## v6.5.7 当前维护方式

当前审核配方为 `rules/reviewed/v6.5.7/decisions.json`；检查 `python3 scripts/reviewed_release.py --check --remote` 与 `python3 scripts/verify_release.py --check --remote`。配置/资源的可复现结果、公开 checksum、准确 PR head 的真实 Production CI 和 main 合并后 Raw 都应一致。

历史 beta.4、v6.5.5 和 v6.5.6 校验改用独立冻结快照，不再要求工作树 beta 永远保持旧 SHA。发展中的 v6.5.8-beta.1 使用 v6.5.7 foundation，完整来源组和累计 overlay 一起校验。新增来源仍须通过受限草稿 PR，不能自动提升 main。

清理器先核实真实正式发布身份和当前配置 hash，再保护正式/测试配置、manifest、代码及必要冻结基线；当前 beta 版本递增不会自动使正式清理无效。`--verify-archives` 验证历史链接后才允许删除，Git 历史和原始输入始终保留。

旧 `prepare_release.py` 是 26 组历史编译器的预览工具，不用于替换当前 36 资源配置。手动发布工作流验证并打包当前已审核版本。以下 v6.5.6 及更早段落为历史记录。

## v6.5.6 DNS 行为维护

v6.5.6 已经由 [发布 PR #124](https://github.com/YohakuSama/loonkit/pull/124) 合入，原始 main SHA `d28aa3d71a3339aa7a540bd3bd31f90e1090e52d`，真实合并后 [Production CI](https://github.com/YohakuSama/loonkit/actions/runs/40101935676) 通过。v6.5.6 仅从 `build/baselines/v6.5.5/LoonKit.lcf` 迁移 `NOANSWER` 为 `LOOPBACKIP`，用 `scripts/prepare_release_v656.py` 与 `scripts/verify_release_v656.py` 确认确定性及旧版完整性，所有其他运行资源保持不变。版本 v6.5.5 的一次性发布授权不可用于新候选。App 级开关与证书安装无法由仓库远程设置，参阅 [Loon App 说明](./LOON_APP_SETTINGS.md)。

## v6.5.5 正式发布

[独立发布 PR #119](https://github.com/YohakuSama/loonkit/pull/119) 保留已验收 beta.4 的全部 36 个固定远程资源。历史 v6.5.4 `LoonKit.lcf` 与正式 manifest 的独立、校验过的基线位于 `build/baselines/v6.5.4/`，供 beta 生成器持续重建；不是可删冗余。

发布候选先由 `scripts/prepare_promoted_release.py` 重建，再由 `scripts/verify_promoted.py` 验证实际配置和原始 beta 有效指令完全一致。本次维护者明确授权对应候选的一次性放行；缺失的设备证据依然如实保留。必须通过当前 PR head 的 CI 和合并后 main 实际资源验证。之后独立创建清理 PR，不重写历史。


正式配置为 `LoonKit.lcf`，通过 `release/Network_Diagnostics.plugin` 提供节点信息、网络检测和解锁检测三个入口。

已发布 main 提交：[7c7ca4f67180437c962c3bc7eae07c6042e519d6](https://github.com/YohakuSama/loonkit/commit/7c7ca4f67180437c962c3bc7eae07c6042e519d6)。合并后实际 [production CI](https://github.com/YohakuSama/loonkit/actions/runs/40097998603) 已通过；回滚入口为 [v6.5.4 固定提交](https://raw.githubusercontent.com/YohakuSama/loonkit/62dcaa273ebff92176b510186f7b73ea994e72b6/LoonKit.lcf)。

## v6.5.5 历史固定依赖

- 规则：36 个不可变远程资源（22 个历史 RC2、14 个已验收 beta.4 资源）；准确引用和 SHA256 见 `build/release_manifest.json`。
- 图标：`icons/v20261021r1/`，固定提交 `97c48a5d14087597dbba35119d5ee8d43b1ce537`。
- 三份诊断脚本：`scripts/v20261022r11/`，固定提交 `db83bbe402c40c4ec5bb2421115989126fd5bf05`。
- 插件：`release/Network_Diagnostics.plugin`，固定提交 `5c2498084539bce76fd1f0f12fd8e5d4a0e989ea`。

完整资源路径与提交记录见 [依赖清单](./DEPENDENCIES.md)。固定提交为正式资源的版本依据，更新资源应发布新的引用版本。

## 维护检查

```sh
python3 scripts/source_lock.py --check
python3 scripts/verify_release.py --check
python3 scripts/license_audit.py --check
node --check scripts/v20261022r11/node-intelligence.js
node --check scripts/v20261022r11/network-diagnostics.js
node --check scripts/v20261022r11/media-unlock.js
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/diagnostics.test.cjs
```

规则来源每周通过 `rules-update.yml` 审阅；`release.yml` 生成手动发布候选，`ci.yml` 执行正式完整性及回归检查。GitHub Actions 使用固定完整提交 SHA，并由 Dependabot 提供更新 PR。发布新版本需维护者审核和操作。

漏洞反馈见 [安全政策](../SECURITY.md)。CI 核对正式配置、构建清单及对外 SHA-256 校验文件；正式配置发生变化时，须先审查变更，再更新发布资料。

## 显示与检测的边界

Loon 原生弹窗采用分区文本布局。三个诊断入口中的请求与判定独立于弹窗排版；节点入口地址、代理出口 IP 及第三方网络标签分别展示。维护者报告 v6.5.2 在 Loon 真机测试中未发现异常，测试记录见 [设备验收](./DEVICE_TEST_STATUS.md)。

[清理清单](./CLEANUP_AUDIT_2026-10-22.md) · [规则安全](./RULE_SAFETY.md) · [第三方许可](./THIRD_PARTY_NOTICES.md)
