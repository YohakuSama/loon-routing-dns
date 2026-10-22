# LoonKit · 开源许可、维护与发布检查

LoonKit 采用通常的社区开源项目做法：**按照实际上游许可证使用和再分发内容，保留来源、版权及许可证文本**。无需为 GPL、MIT、WTFPL 已授权的使用逐条联系规则作者，也无需购买规则。完整来源与声明见 [第三方许可与来源](./THIRD_PARTY_NOTICES.md)。

## 许可结构

- **LoonKit 有权授权的原创代码、脚本和配置贡献：** [GPL-2.0-only](../LICENSE)。
- **blackmatrix7 规则来源：** 以 [GPL-2.0 文本](../rules/LICENSE.GPL-2.0)及具体资源实际权利为准，并留意其 [README 特别声明](https://github.com/blackmatrix7/ios_rule_script/blob/master/README.md)。
- **v2fly 规则来源：** [MIT（含版权声明）](../rules/LICENSE.MIT-V2FLY)。
- **felixonmars 规则来源：** [WTFPL-2.0](../rules/LICENSE.WTFPL-FELIXONMARS)。
- **品牌标志、应用图标：** 不因仓库添加 GPL 而取得第三方商标或图片版权；仅依实际允许的用途使用，收到异议时针对素材核查/替换。

项目保留 [87 条历史来源记录](../build/license_sources.json) 以及冻结规则输入，提供可查证的上游说明。旧构建没有保存最终 197,765 条合并匹配的逐行来源，**这一限制应诚实公开，但不是要求给每一行规则单独取得许可的理由**。明确由原仓库许可覆盖的内容按许可条件处理；发现例外、混入未知来源或权利异议时，针对该内容处理。

## 当前发布流程

1. 保留许可证、来源说明和所有正式固定资源提交。
2. 执行静态验证与 JavaScript 语法检查。
3. 在实际 iOS/iPadOS Loon 中检查三个入口、弹窗断行以及七项平台判定，确认没有回归。
4. 由维护者单独决定是否发布新 Release；不会因 CI 成功而更新历史版本。

发布记录参见 [Releases](https://github.com/YohakuSama/loonkit/releases)。历史 GitHub Actions 运行记录不属于 Git 版本文件，删除工作流 YAML 不会删除历史运行记录。

### 关于旧的内部状态字段

原有构建清单曾把历史来源审阅、独立法律认证和常规开源许可混为 `BLOCKED_REVIEW`、`NOT_CLEARED`。现将**可验证的许可证与署名资料**标为 `LICENSE_NOTICES_DOCUMENTED`，将**未做独立权利认证**单独标为 `NOT_INDEPENDENTLY_REVIEWED`；**历史 v6.0.0** 的设备测试曾由使用者报告正常。当前 **v6.5.2** 的维护者反馈为“已完成真机测试，暂未发现其他问题”；但缺少逐项测试结果、设备与 Loon 版本信息，不能标记为已完成全面验收。这些状态不等于“GPL、MIT、WTFPL 都无效”，也不意味着必须付费取得逐条授权。

这些状态应与实际许可证义务分开理解。自动化可以核对保留的许可证和来源记录，**但既不能自动授予任何第三方权利，也不能代替维护者对具体争议素材的判断**。如果某一素材明确不允许当前用途，就针对素材调整、替换或取得单独许可，而不是让整个项目陷入不可执行的逐行审批。

### 当前发布入口与历史

截至 2026-10-22 复核，GitHub Releases 当前为空。旧 Release/Tag 不自动恢复；历史下载链接可能失效。唯一当前下载入口：[main/LoonKit.lcf](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf)，发布新版本需维护者明确授权。

### 常用核验命令

```bash
python3 scripts/source_lock.py --check
python3 scripts/verify_release.py --check
python3 scripts/license_audit.py --check
python3 scripts/license_evidence.py --check
node --check scripts/v20261022r11/media-unlock.js
node --check scripts/v20261022r11/node-intelligence.js
node --check scripts/v20261022r11/network-diagnostics.js
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/diagnostics.test.cjs

```

其中许可证脚本核验的是资料与原文的一致性，不出具法律意见；输出中未执行的独立审核应如实保留。

[返回首页](../README.md) · [完整来源记录](../rules/sources.json) · [历史构建清单](../build/release_manifest.json)
