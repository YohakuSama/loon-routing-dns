# 正式版依赖与固定版本引用

> 本文描述当前 `main` 的 **LoonKit v6.2.0**，不包含已移除的旧版插件或图标目录。引用的提交号是为了保持远程资源不可变，**不能随意改写 Git 历史**。

## 正式运行链

| 类型 | 现役文件 | 固定资源提交 |
| --- | --- | --- |
| 唯一完整配置 | [`LoonKit.lcf`](../LoonKit.lcf) | 通过 `main` 下载或导入 |
| 26 份远程规则 | [`rules/releases/vNext-RC2/`](../rules/README.md) | `9bbac4c9aa0ec33c82ab5fe03648127f3f4754f4` |
| 33 个策略图标 + 1 个插件图标 | [`icons/v20261021r1/`](../icons/README.md) | `97c48a5d14087597dbba35119d5ee8d43b1ce537` |
| 网络辅助插件（内含服务诊断） | [`release/Network_Diagnostics.plugin`](../release/Network_Diagnostics.plugin) | `8122c6993e3f13a3152449d3d4ec62717a96cded` |
| 节点出口脚本 | [`scripts/v20261021r1/node-intelligence.js`](../scripts/v20261021r1/node-intelligence.js) | `97c48a5d14087597dbba35119d5ee8d43b1ce537` |
| 网络与 DNS 诊断脚本 | [`scripts/v20261021r2/network-diagnostics.js`](../scripts/v20261021r2/network-diagnostics.js) | `af78ebb6b75bdbb341996db446d87cb2be719af4` |
| 手动服务诊断脚本 | [`scripts/v20261021r6/service-diagnostics.js`](../scripts/v20261021r6/service-diagnostics.js) | `17ca5380fc24e4950bc5a5f5bcc8237853119f97` |

**服务诊断工具：** 现有网络辅助插件已加入第三个手动工具，使用上述版本化服务诊断脚本，无需单独添加第二个插件。旧的 [独立插件](../release/Service_Diagnostics.plugin) 仅用于历史版本，不在当前配置中启用；[离线规则与脱敏日志分析](../scripts/route_diagnostics.py) 仍在用户电脑上运行。

调用关系为 `LoonKit.lcf` → 固定提交的 `release/Network_Diagnostics.plugin` → 版本化节点出口、网络/DNS、服务诊断脚本与插件图标。Loon 中更新正式配置后，还应刷新远程插件及脚本缓存。

新装用户必须自行添加代理节点或订阅。配置不包含节点；`AdBlock` 可由用户在 `REJECT` 与 `DIRECT` 之间选择。

## 规则构建与发布验证

冻结规则输入由 `rules/inputs/`（33 份）和 `rules/custom/`（10 份）构成，`build/engine_manifest.json` 与 `build/sources.lock.json` 固定其输入，`scripts/rule_engine.py` 构建 26 份固定正式远程规则。v6.1.0 在主配置中额外启用 62 条来源于冻结输入的审阅域名规则，审阅记录位于 [服务覆盖清单](../rules/service_coverage_v6.1.0.json)。**正式输出不能作为自己的输入**。

校验入口：`scripts/source_lock.py --check`、`scripts/verify_release.py --check`；需要逐个检查固定远程链接时另外执行 `scripts/verify_release.py --check --remote`。对应测试位于 `tests/`，主 CI 为 [`ci.yml`](../.github/workflows/ci.yml)。

远程上游目录 `rules/sources.json` 记录 87 个历史来源，`scripts/upstream_review.py` 仅生成待审快照和差异，不覆盖冻结输入或正式规则。每周 [`rules-update.yml`](../.github/workflows/rules-update.yml) 负责只读候选审核，[`upstream-live-audit.yml`](../.github/workflows/upstream-live-audit.yml) 用于真实上游完整性复核；[`release.yml`](../.github/workflows/release.yml) **只生成手动候选，不自动发布**。

## 历史兼容与权利声明

旧 DNSPod 完整配置、旧版 `rules/generated/`、`ProxyProtect.list`、`rules/active_profile.json` 及旧插件别名已从主分支清理。引用**已删除的动态路径**的旧配置可能无法更新；使用历史固定提交 URL 的资源仍可访问。清理主分支文件不等于改写 Git 历史。

项目自有可授权部分采用 [GPL-2.0-only](../LICENSE)，第三方素材沿用各自许可证与版权；详见 [第三方声明](./THIRD_PARTY_NOTICES.md)。发布验收还应区分 CI 完整性检查、Loon 真机验证和正式 GitHub Release，不能把任一项混为全部完成。

[维护流程](./MAINTAINING.md) · [DNS 说明](./DNS_PRIVACY.md) · [规则安全机制](./RULE_SAFETY.md) · [回到 README](../README.md)
