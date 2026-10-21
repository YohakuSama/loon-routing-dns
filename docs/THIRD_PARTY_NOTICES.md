# 第三方许可与来源声明

LoonKit 是社区维护的 Loon 配置项目。**LoonKit 维护者有权授权的原创代码、脚本和配置贡献**按 [GPL-2.0-only](../LICENSE) 开源；第三方规则、已有代码、图标和商标**保留各自的权利与适用许可**。顶层 `LICENSE` 不代表我们能替其他作者重新授权其作品。

开源许可证通常已经授予符合条件的使用、修改和再分发权利；使用 GPL、MIT、WTFPL 许可的资源，不需要逐条联系作者或购买所谓的「规则授权」。是否允许再分发，仍以**相应内容实际适用的许可证**和其他权利为准。非商业使用并不会自动免除署名、许可文本、同许可证发布或源代码提供等义务。

## 主要规则来源

| 历史来源 | 记录数 | 上游声明的许可 | 许可文本 / 来源 |
| --- | ---: | --- | --- |
| [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) | 41 | GPL-2.0-only（以实际适用内容为准） | [许可证](../rules/LICENSE.GPL-2.0) · [上游 LICENSE](https://github.com/blackmatrix7/ios_rule_script/blob/master/LICENSE) |
| [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) | 35 | MIT | [许可证及版权声明](../rules/LICENSE.MIT-V2FLY) · [上游 LICENSE](https://github.com/v2fly/domain-list-community/blob/master/LICENSE) |
| [felixonmars/dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list) | 1 | WTFPL-2.0 | [许可证](../rules/LICENSE.WTFPL-FELIXONMARS) · [上游 LICENSE](https://github.com/felixonmars/dnsmasq-china-list/blob/master/LICENSE) |
| LoonKit 本地规则 | 10 | 自有贡献按 GPL-2.0-only；来源未确认部分不作原创断言 | [历史目录](../rules/sources.json) |

表中为 **87 条历史来源记录**，并非 87 位作者或 87 份逐行已追溯的许可。完整索引见 [build/license_sources.json](../build/license_sources.json)，冻结构建输入和正式输出见 [规则说明](../rules/README.md)。

## 应如何遵守

- **GPL-2.0-only：** 保留版权、许可与修改说明；对所分发的 GPL 派生部分遵守同许可证和对应源代码提供要求。许可原文位于仓库及 `rules/LICENSE.GPL-2.0`。
- **MIT：** 对适用部分保留上游完整版权和 MIT 许可声明（当前记录为 V2Ray 2018–2019），详见 `rules/LICENSE.MIT-V2FLY`。
- **WTFPL-2.0：** 依据上游许可使用，保留本仓库的来源说明和上游文本以便追溯。
- **LoonKit 原创部分：** 采用 GPL-2.0-only；不借此宣称上游第三方素材已转为本项目版权。

### blackmatrix7 特别声明

[blackmatrix7 的 README](https://github.com/blackmatrix7/ios_rule_script/blob/master/README.md) 除 GPL 文本外，还声明禁止公众号、自媒体转载发布，并说明部分资源取自互联网。这一点**不能忽略，也不能简单解释成任何人在任何场景都必须付费授权**。LoonKit 是 GitHub 上的社区规则项目，仍需遵守实际适用的许可证，并在收到明确的权利异议时核查具体内容、必要时移除或替换。上游仓库自身的 GPL 文件不能替所有外部来源作权利保证。

## 原始来源的实际限制

发布版的 26 份规则由冻结输入合并、去重后形成，共 197,765 条匹配。旧版构建时未保留每一行最终规则的原始作者信息，现有目录**无法用于证明所有合并行的确切权属**。这是一项来源透明度限制，**并不意味着开源许可必须逐行人工审批**。

对明确来自上述上游、且实际受其许可证覆盖的内容，按许可证履行义务即可；对混入的其他来源、例外条款或被提出异议的具体内容，应单独核查并在必要时替换。不要将来源目录等同于对每一个字符的授权保证。

## 图标与插件

- LoonKit 自行编写、可授权的脚本与配置贡献按顶层 GPL-2.0-only 处理。
- 现役策略图标已迁移为由项目确定性生成的抽象色块及英文字母缩写，不包含第三方品牌标志图形；品牌名称作为策略用途说明，未声明与其官方存在合作或授权关系。历史固定提交可能仍存有已移除的品牌素材，不能视为本项目拥有第三方商标或旧图像权利。
- 维护和替换图标时遵循 [图标说明](../icons/README.md)，必要时使用具有明确许可的素材。

如发现来源遗漏、署名错误、许可冲突或希望移除某项规则/素材，请通过 [Issues](https://github.com/YohakuSama/loonkit/issues) 提供资源路径及来源链接，我们会针对具体问题检查和处理。

> 这里列出可核实的上游许可与来源，不构成对所有历史混合规则和品牌素材的无条件权利保证；发布审阅记录见 [发布说明](./RELEASE_READINESS.md)。
