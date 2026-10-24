# 发布与维护检查

## v6.5.5 发布候选

[PR #119](https://github.com/YohakuSama/loonkit/pull/119) 将 v6.5.5-beta.4 的有效指令逐项固定为待发布根配置。**截至本次审阅，该 PR 仍是草稿，main 仍使用 v6.5.4。**

- 原 beta 配置 SHA256：`fd1a01c6f8363a5dffaa1db9dbf044014c711fa48ea46e34a7c107180acbe0b7`。
- 原 beta 提交：`adc567168eed8e21dc8d80aebc40b85f35fc1a1b`；固定资源：`1b54e079486a06a5cfff5c5f03016628a52a7701`。
- 新的版本化路径：`python3 scripts/prepare_promoted_release.py --check`、`python3 scripts/verify_release.py --check --remote`；旧版 26 个 RC2 编译输出/197765 条匹配继续作为历史契约，不能和 36 个现役远程资源混用。
- 需准确 PR head 的 `production` 必需检查成功，随后再做最终 main 下载/哈希核对。

维护者已报告总体真机使用未发现问题，但**七天观察起止、逐项结果和设备 Build 均未提供**。现有严格门禁不允许将其等同于全部矩阵 PASS 或七天完成；空白模板与模拟结果不是证据。无门禁放行时不得合并、打标签、删除历史资源。


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
| 正式配置 | v6.5.4 · [获取配置](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf) |
| 完整性核验 | [Production CI](https://github.com/YohakuSama/loonkit/actions/workflows/ci.yml) |
| 真机测试 | v6.5.2 真机反馈未发现异常；v6.5.3 调整测速和自动选路，真机回归待补充；v6.5.4 仅整理注释，未修改有效配置项，见[测试记录](./DEVICE_TEST_STATUS.md) |
| GitHub Releases | [发布页](https://github.com/YohakuSama/loonkit/releases)（截至 2026-10-22 未发布条目） |

## 开源许可与来源

项目自有、可授权的贡献采用 [GPL-2.0-only](../LICENSE)。第三方内容依照各自的许可及版权声明使用，相关许可文本及 87 条历史来源记录见 [第三方许可与来源](./THIRD_PARTY_NOTICES.md)。

历史规则合并过程未保存逐条匹配的完整来源对应表。仓库保留冻结输入、来源记录和对应许可证，自动化检查验证这些资料的一致性；涉及具体权利问题时由维护者进行进一步核对。

[维护指南](./MAINTAINING.md) · [返回首页](../README.md)
