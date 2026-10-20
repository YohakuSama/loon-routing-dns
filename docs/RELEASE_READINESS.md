# LoonKit · 开源许可与发布检查

LoonKit 采用通常的社区开源项目做法：**按照实际上游许可证使用和再分发内容，保留来源、版权及许可证文本**。无需为 GPL、MIT、WTFPL 已授权的使用逐条联系规则作者，也无需购买规则。完整来源与声明见 [第三方许可与来源](./THIRD_PARTY_NOTICES.md)。

## 许可结构

- **LoonKit 有权授权的原创代码、脚本和配置贡献：** [GPL-2.0-only](../LICENSE)。
- **blackmatrix7 规则来源：** 以 [GPL-2.0 文本](../rules/LICENSE.GPL-2.0)及具体资源实际权利为准，并留意其 [README 特别声明](https://github.com/blackmatrix7/ios_rule_script/blob/master/README.md)。
- **v2fly 规则来源：** [MIT（含版权声明）](../rules/LICENSE.MIT-V2FLY)。
- **felixonmars 规则来源：** [WTFPL-2.0](../rules/LICENSE.WTFPL-FELIXONMARS)。
- **品牌标志、应用图标：** 不因仓库添加 GPL 而取得第三方商标或图片版权；仅依实际允许的用途使用，收到异议时针对素材核查/替换。

项目保留 [87 条历史来源记录](../build/license_sources.json) 以及冻结规则输入，提供可查证的上游说明。旧构建没有保存最终 197,765 条合并匹配的逐行来源，**这一限制应诚实公开，但不是要求给每一行规则单独取得许可的理由**。明确由原仓库许可覆盖的内容按许可条件处理；发现例外、混入未知来源或权利异议时，针对该内容处理。

## 建议的 GitHub Release 流程

1. **确认许可声明**：顶层 `LICENSE`、[第三方声明](./THIRD_PARTY_NOTICES.md)、上游署名及完整许可文本齐备；不宣称整个混合规则库都是 LoonKit 原创、全部通过独立法律审查，或有品牌官方授权。
2. **检查版本内容**：`LoonKit.lcf` 可导入，规则和插件的固定 URL 没有失效；没有包含私人节点订阅或凭据。
3. **运行已有 CI**，确认冻结输入、正式规则、脚本和回归测试通过。
4. **由维护者作实际使用验收**：至少覆盖导入、常用分流、DNS 与网络辅助；在发布说明中写出测试范围和已知限制，不需要假设存在未进行的真机测试。
5. **创建版本 Tag 和 Release**：选择已验证的提交，附上 [更新记录](./CHANGELOG.md)、[第三方许可声明](./THIRD_PARTY_NOTICES.md)，把下载入口指向该版本的 `LoonKit.lcf`。不要将尚未公开的内部审核证据说成已完成。

### 关于旧的内部状态字段

原有构建清单曾把历史来源审阅、独立法律认证和常规开源许可混为 `BLOCKED_REVIEW`、`NOT_CLEARED`。现将**可验证的许可证与署名资料**标为 `LICENSE_NOTICES_DOCUMENTED`，将**未做独立权利认证**单独标为 `NOT_INDEPENDENTLY_REVIEWED`；真机验收未执行仍记为 `NOT_EXECUTED`。这些状态不等于“GPL、MIT、WTFPL 都无效”，也不意味着必须付费取得逐条授权。

这些状态应与实际许可证义务分开理解。自动化可以核对保留的许可证和来源记录，**但既不能自动授予任何第三方权利，也不能代替维护者对具体争议素材的判断**。如果某一素材明确不允许当前用途，就针对素材调整、替换或取得单独许可，而不是让整个项目陷入不可执行的逐行审批。

### 常用核验命令

```bash
python3 scripts/source_lock.py --check
python3 scripts/verify_release.py --check
python3 scripts/license_audit.py --check
python3 scripts/license_evidence.py --check
python3 -m unittest discover -s tests -p 'test_production.py' -v
node tests/test_current_plugin.js
node tests/test_network_diagnostics.js
node tests/test_node_copy.js
```

其中许可证脚本核验的是资料与原文的一致性，不出具法律意见；输出中未执行的独立审核应如实保留。

[返回首页](../README.md) · [完整来源记录](../rules/sources.json) · [历史构建清单](../build/release_manifest.json)
