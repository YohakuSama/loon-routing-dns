# 发布与维护检查

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
| 正式配置 | v6.5.2 · [获取配置](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf) |
| 完整性核验 | [Production CI](https://github.com/YohakuSama/loonkit/actions/workflows/ci.yml) |
| 真机测试 | 原 v6.5.2 基线维护者反馈未发现异常；自动选路参数调整需另行进行真机回归，见[测试记录](./DEVICE_TEST_STATUS.md) |
| GitHub Releases | [发布页](https://github.com/YohakuSama/loonkit/releases)（截至 2026-10-22 未发布条目） |

## 开源许可与来源

项目自有、可授权的贡献采用 [GPL-2.0-only](../LICENSE)。第三方内容依照各自的许可及版权声明使用，相关许可文本及 87 条历史来源记录见 [第三方许可与来源](./THIRD_PARTY_NOTICES.md)。

历史规则合并过程未保存逐条匹配的完整来源对应表。仓库保留冻结输入、来源记录和对应许可证，自动化检查验证这些资料的一致性；涉及具体权利问题时由维护者进行进一步核对。

[维护指南](./MAINTAINING.md) · [返回首页](../README.md)
