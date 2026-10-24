# LoonKit 维护与发布

## v6.5.5 正式发布准备

[独立发布 PR #119](https://github.com/YohakuSama/loonkit/pull/119) 保留已验收 beta.4 的全部 36 个固定远程资源。历史 v6.5.4 `LoonKit.lcf` 与正式 manifest 的独立、校验过的基线位于 `build/baselines/v6.5.4/`，供 beta 生成器持续重建；不是可删冗余。

发布候选先由 `scripts/prepare_promoted_release.py` 重建，再由 `scripts/verify_promoted.py` 验证实际配置和原始 beta 有效指令完全一致。正式发布仍需要设备门禁及准确 CI 通过；成功合入后应记录最终 main 提交、公开 checksum、真实工作流 URL 与历史回滚链接，再单开清理 PR。当前 main 版本保持 v6.5.4，直到实际合并验证成功。


正式配置为 `LoonKit.lcf`，通过 `release/Network_Diagnostics.plugin` 提供节点信息、网络检测和解锁检测三个入口。

## 当前固定依赖

- 规则：26 份 `rules/releases/vNext-RC2/`，固定提交 `9bbac4c9aa0ec33c82ab5fe03648127f3f4754f4`。
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
