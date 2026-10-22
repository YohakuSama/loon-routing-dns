# LoonKit 维护与发布

唯一正式入口：`LoonKit.lcf`。网络辅助插件只有一份：`release/Network_Diagnostics.plugin`；节点、网络和解锁工具均由其调用。

## 当前固定依赖

- 规则：26 份 `rules/releases/vNext-RC2/`，固定提交 `9bbac4c9aa0ec33c82ab5fe03648127f3f4754f4`。
- 图标：`icons/v20261021r1/`，固定提交 `97c48a5d14087597dbba35119d5ee8d43b1ce537`。
- 三份诊断脚本：`scripts/v20261022r11/`，固定提交 `db83bbe402c40c4ec5bb2421115989126fd5bf05`。
- 插件：`release/Network_Diagnostics.plugin`，固定提交 `5c2498084539bce76fd1f0f12fd8e5d4a0e989ea`。

完整明细参见 [依赖清单](./DEPENDENCIES.md)。禁止重写正在被配置引用的固定提交历史。已删除的旧文件仍可通过历史固定提交 URL 访问。

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

每周只读规则审阅保留 `rules-update.yml`，手动候选保留 `release.yml`，正式检查保留 `ci.yml`；旧版自动发布工作流已清理。当前版本必须由维护者确认后发布，不自动修改历史 Release。当前 GitHub Releases 为空，历史下载链接不能假设有效。五个工作流的外部 Actions 统一按经官方仓库核验的完整提交 SHA 固定，并由 Dependabot 提供更新 PR。

安全漏洞请参阅 [SECURITY.md](../SECURITY.md)。公共校验文档和 SHA256SUMS 与 profile、manifest 的一致性由只读 CI 强制检查；**不要以重新生成正式清单的方式掩盖非预期的 LoonKit.lcf 改动**。

## 显示与检测的边界

Loon 原生弹窗不可使用 HTML 网格；只输出紧凑的分区文本，不用对齐空格硬凑列宽。七项解锁请求与判定逻辑独立于展示函数，不因排版修改而改变。代理出口和代理配置入口不保证是同一 IP；网络特征与风险标签仅供参考。维护者目前报告已进行真机检查，暂未发现其他问题，但 v6.5.2 的逐项正式验收没有完整记录，不能把 CI 或旧版测试写成当前正式通过。具体事项见 [设备验收](./DEVICE_TEST_STATUS.md)。

[清理清单](./CLEANUP_AUDIT_2026-10-22.md) · [规则安全](./RULE_SAFETY.md) · [第三方许可](./THIRD_PARTY_NOTICES.md)
