# 发布与维护检查

## v6.5.5 发布候选

[PR #119](https://github.com/YohakuSama/loonkit/pull/119) 将 beta.4 的有效指令确定性提升至正式入口。维护者已明确批准这一版的单次发布，详见 [版本专属决定](RELEASE_OWNER_DECISION_v6.5.5.json)，并保留严格的资源、CI、合并后检查。

- 原 beta 配置 SHA256：`fd1a01c6f8363a5dffaa1db9dbf044014c711fa48ea46e34a7c107180acbe0b7`。
- 原 beta 提交：`adc567168eed8e21dc8d80aebc40b85f35fc1a1b`；固定资源：`1b54e079486a06a5cfff5c5f03016628a52a7701`。
- 新的版本化路径：`python3 scripts/prepare_promoted_release.py --check`、`python3 scripts/verify_release.py --check --remote`；旧版 26 个 RC2 编译输出/197765 条匹配继续作为历史契约，不能和 36 个现役远程资源混用。
- 需准确 PR head 的 `production` 必需检查成功，随后再做最终 main 下载/哈希核对。

维护者反馈设备使用未发现问题，随后明确要求直接发布本准确候选。七天观察起止、逐项结果与设备 Build 未提供，记录保持未提供。例外仅适用 v6.5.5，不改变以后候选的默认门禁。


本页记录 LoonKit 的发布流程、版本核验和维护要求。正式配置为 [LoonKit.lcf](../LoonKit.lcf)，许可证与来源信息见 [第三方许可与来源](./THIRD_PARTY_NOTICES.md)。

## 发布流程

1. **变更审查**：通过独立分支和 Pull Request 审查代码、规则及文档改动。
2. **资源完整性**：核对正式配置、规则、插件、脚本及图标的固定版本引用和校验值。
3. **自动化验证**：运行规则确定性、上游解析、诊断模拟、配置完整性和许可证资料检查，通过必需的 `production` 状态检查。
4. **设备测试**：在实际 Loon 环境中验证配置加载、网络辅助入口、DNS 诊断及分流行为，记录测试反馈。
5. **人工发布**：维护者根据变更和验证记录决定是否创建新 Release 或 Tag。

### 核验命令

```bash
python3 scripts/source_lock.py --check
python3 scripts/verify_release.py --check
python3 scripts/license_audit.py --check
python3 scripts/license_evidence.py --check
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/diagnostics.test.cjs
node --check scripts/v20261022r11/node-intelligence.js
node --check scripts/v20261022r11/network-diagnostics.js
node --check scripts/v20261022r11/media-unlock.js
```

检查固定 Raw 资源的网络可达性和实际内容时执行：

```bash
python3 scripts/verify_release.py --check --remote
```

## 当前版本

| 项目 | 状态 |
| --- | --- |
| 正式配置 | v6.5.5 · [获取配置](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf) |
| 完整性核验 | [Production CI](https://github.com/YohakuSama/loonkit/actions/workflows/ci.yml) |
| 真机测试 | v6.5.5-beta.4 维护者反馈使用未发现问题；详细 Build、抓包和观察区间未提供；本次采用维护者一次性发布决定，见[测试记录](./DEVICE_TEST_STATUS.md) |
| GitHub Releases | [发布页](https://github.com/YohakuSama/loonkit/releases)（实时条目以 GitHub 为准） |

## 开源许可与来源

项目自有、可授权的贡献采用 [GPL-2.0-only](../LICENSE)。第三方内容依照各自的许可及版权声明使用，相关许可文本及 87 条历史来源记录见 [第三方许可与来源](./THIRD_PARTY_NOTICES.md)。

历史规则合并过程未保存逐条匹配的完整来源对应表。仓库保留冻结输入、来源记录和对应许可证，自动化检查验证这些资料的一致性；涉及具体权利问题时由维护者进行进一步核对。

[维护指南](./MAINTAINING.md) · [返回首页](../README.md)
