# 正式版依赖与固定版本引用

本文记录 **LoonKit v6.5.4** 的正式资源及其固定提交，供更新、排错和完整性校验使用。

## 正式运行链

| 类型 | 现役文件 | 固定资源提交 |
| --- | --- | --- |
| 唯一完整配置 | [`LoonKit.lcf`](../LoonKit.lcf) | 通过 `main` 下载或导入 |
| 26 份远程规则 | [`rules/releases/vNext-RC2/`](../rules/README.md) | `9bbac4c9aa0ec33c82ab5fe03648127f3f4754f4` |
| 33 个策略图标 + 1 个插件图标 | [`icons/v20261021r1/`](../icons/README.md) | `97c48a5d14087597dbba35119d5ee8d43b1ce537` |
| 网络辅助插件（内含服务诊断） | [`release/Network_Diagnostics.plugin`](../release/Network_Diagnostics.plugin) | `5c2498084539bce76fd1f0f12fd8e5d4a0e989ea` |
| 节点入口与出口脚本 | [`scripts/v20261022r11/node-intelligence.js`](../scripts/v20261022r11/node-intelligence.js) | `db83bbe402c40c4ec5bb2421115989126fd5bf05` |
| 网络与 DNS 诊断脚本 | [`scripts/v20261022r11/network-diagnostics.js`](../scripts/v20261022r11/network-diagnostics.js) | `db83bbe402c40c4ec5bb2421115989126fd5bf05` |
| 流媒体与 AI 地区检测脚本 | [`scripts/v20261022r11/media-unlock.js`](../scripts/v20261022r11/media-unlock.js) | `db83bbe402c40c4ec5bb2421115989126fd5bf05` |

网络辅助插件集成三个诊断入口，加载表中列出的版本化脚本。[离线规则与脱敏日志分析](../scripts/route_diagnostics.py) 可在本地电脑运行。

调用关系为 `LoonKit.lcf` → 固定提交的 `release/Network_Diagnostics.plugin` → 版本化节点入口与出口、网络/DNS、服务诊断脚本与插件图标。Loon 中更新正式配置后，还应刷新远程插件及脚本缓存。

新装用户必须自行添加代理节点或订阅。配置不包含节点；`AdBlock` 可由用户在 `REJECT` 与 `DIRECT` 之间选择。

## 规则构建与发布验证

冻结规则输入由 `rules/inputs/`（33 份）和 `rules/custom/`（10 份）构成，`build/engine_manifest.json` 与 `build/sources.lock.json` 固定其输入，`scripts/rule_engine.py` 构建 26 份固定正式远程规则。v6.1.0 在主配置中额外启用 62 条来源于冻结输入的审阅域名规则，审阅记录位于 [服务覆盖清单](../rules/service_coverage_v6.1.0.json)。正式规则由锁定的上游及本地输入生成，输出不参与源数据构建。

校验入口：`scripts/source_lock.py --check`、`scripts/verify_release.py --check`；需要逐个检查固定远程链接时另外执行 `scripts/verify_release.py --check --remote`。静态校验和语法检查由主 CI 执行；主 CI 为 [`ci.yml`](../.github/workflows/ci.yml)。

远程上游目录 `rules/sources.json` 记录 87 个历史来源，`scripts/upstream_review.py` 仅生成待审快照和差异，不覆盖冻结输入或正式规则。每周 [`rules-update.yml`](../.github/workflows/rules-update.yml) 负责只读候选审核，[`upstream-live-audit.yml`](../.github/workflows/upstream-live-audit.yml) 用于真实上游完整性复核；[`release.yml`](../.github/workflows/release.yml) **只生成手动候选，不自动发布**。

## 兼容性与许可

早期配置中的动态资源路径可能与当前版本不同；请使用上述固定资源路径更新配置。历史资源及变更记录可通过 Git 提交历史查阅。

项目原创且有权授权的部分采用 [GPL-2.0-only](../LICENSE)，第三方素材依照各自许可证与版权声明使用；见 [第三方来源](./THIRD_PARTY_NOTICES.md)。发布流程见 [发布检查](./RELEASE_READINESS.md)。

[维护流程](./MAINTAINING.md) · [DNS 说明](./DNS_PRIVACY.md) · [规则安全机制](./RULE_SAFETY.md) · [回到 README](../README.md)
