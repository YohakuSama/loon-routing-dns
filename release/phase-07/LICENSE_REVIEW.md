# 正式发布许可证与来源审查（阻断项）

状态：**BLOCKED_REVIEW**。审查日期 2026-10-20。不能仅因已随仓库保存许可证副本，就认为所有合并规则具备充分再分发授权。

| 记录来源 | 可核验证据 | 发布前动作 |
|---|---|---|
| blackmatrix7/ios_rule_script | https://github.com/blackmatrix7/ios_rule_script/blob/master/LICENSE （GPL-2.0）；https://github.com/blackmatrix7/ios_rule_script （README 对公众号、自媒体转载作限制性声明） | 确定实际用于 Loon 规则的授权范围、免责声明与 GPL-2.0 的关系；明确完整的版权声明、可用源代码及相应义务。必要时联系原作者，或排除无法满足的部分。 |
| v2fly/domain-list-community | https://github.com/v2fly/domain-list-community/blob/master/LICENSE （MIT） | 逐文件核对来源 Commit，保留 MIT 著作权及许可说明。 |
| felixonmars/dnsmasq-china-list | https://github.com/felixonmars/dnsmasq-china-list/blob/master/LICENSE （仓库提供许可文本） | 确认被引用的具体文件及历史来源 Commit 确属该许可证、保存文件级署名及许可文本。 |
| LoonKit 自维护脚本、插件、图标 | rules/LICENSE.*、icons/ICON_SOURCE_REPORT.json 和实际源图 | 逐项确认自产/第三方资产权利，尤其品牌商标/素材、插件依赖；不能以源代码许可证替代图标授权。 |

## 实际证据边界

- 当前锁定的 44 个历史输入中包括 33 份原已合并的上游规则，来源字段标为 `UNKNOWN_MERGED_PROVENANCE`，不能精确逆推出上游仓库、分支、行号、Copyright。
- `rules/sources.json` 记录的 87 个历史来源只是当时启用清单；并不是对 197,765 条候选规则逐条的许可证明。
- 仓库内存在 `rules/LICENSE.GPL-2.0`、`rules/LICENSE.MIT-V2FLY` 和 `rules/LICENSE.WTFPL-FELIXONMARS` 等历史副本；它们不能替代进一步核实。
- 规则库如果是 GPL 受约束内容与 MIT/WTFPL 数据的衍生混合，应由维护者确认整体发布方案的 GPL 合规、著作权声明、等同许可与源码获取义务；如无法满足，隔离或替换不明确来源后重新生成候选、重新测试。
- 图标使用商标图样与品牌素材的具体授权还需分开审查；不能自动视作开源代码许可覆盖。

**准入**：维护者把逐源许可证结论、归属映射、文本和适用义务附到 PR，并由负责合规的审核者批准，才可以将机器门槛 `licenses` 更新为 PASS。此前不建议正式合并发布。

## 2026-10-20 逐源记录及法务审核门槛

经核对上游仓库提供的许可证正文：blackmatrix7 LICENSE 为 GPL-2.0，README 另有「公众号、自媒体禁止转载」等使用声明，需针对本项目**公开复制与再分发**核实其约束边界，不能把 README 声明等同于 GPL-2.0 条款，也不能无视原作者声明。v2fly 明确为 MIT，保留著作权及许可全文为显性条件。felixonmars 明确为 WTFPL-2.0。精确归属仍需依据实际历史内容校核。

依据 `rules/sources.json` 列出的历史清单（不是当前规则实际可证明的逐行归属）：**blackmatrix7 41 条、v2fly 35 条、felixonmars 1 条、项目本地 10 条，总计 87 条**。完整机器记录见 [LICENSE_SOURCE_LEDGER.json](./LICENSE_SOURCE_LEDGER.json)，每项列明历史 URL/本地路径、预期许可证、证据地址和归属状态；运行 `python3 scripts/phase07_license_audit.py --check` 可验证记录与历史目录一致。

证据地址：

- https://github.com/blackmatrix7/ios_rule_script/blob/master/LICENSE
- https://github.com/blackmatrix7/ios_rule_script#特别声明
- https://github.com/v2fly/domain-list-community/blob/master/LICENSE
- https://github.com/felixonmars/dnsmasq-china-list/blob/master/LICENSE

**严格限制**：机器检查仅说明历史来源及许可证声明存在，不表示 197,765 条混合输出取得了足够再分发授权。上游 `master` 动态链接不等同于当年使用的源提交；记录中的 `pinned_upstream_commit=null` 是尚未恢复的证据缺口。不能因 87 条记录无缺项便把 `licenses` 写成 PASS。需要独立确认上游许可证兼容性、所有保留版权/许可文本、组件权利、原作者要求、对应源代码提供方案；若无法取得可靠证据，则应替换存疑数据并重新出候选和验收。
