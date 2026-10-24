# 发布与维护检查

## v6.5.7 审计修复

版本配方：rules/reviewed/v6.5.7/decisions.json。正式配置 SHA256：9dbcb5bff0cae6be233053e13b464176a0af4ad714efd27b3fa290f3c86ee84b。

- 正式入口继续为 main/LoonKit.lcf；36 个固定规则资源，196624 条记录，33 个策略组。
- 新规则资源固定提交：8f144d9d74dfae4e5064e4c1eeed23addd62199d；旧资源、原始来源和许可文本保持可追溯。
- AliDNS、LOOPBACKIP、所有 General、完整 Rule 段和策略默认值与 v6.5.6 一致，包含用户指定保留的 GEOIP,CN,DIRECT,no-resolve。
- 本版本发布依据维护者明确请求，见 RELEASE_OWNER_DECISION_v6.5.7.json。新增设备结果没有被伪造为 PASS；未新增等待天数。
- 回滚：[固定 v6.5.6 配置](https://raw.githubusercontent.com/YohakuSama/loonkit/67c9060fc41c0fc9c7960612f33c9eb6e4c33cbe/LoonKit.lcf)。历史 checksum 和 build/baselines 保留。

已通过正式发布 [PR #128](https://github.com/YohakuSama/loonkit/pull/128) 合并，运行时发布提交为 `425433e0c4e7d3e5d8c5494d8767fa9560883479`。最终审阅 head `f22bd7379fae615cff453126642b338b5e5bd429` 的 [Production CI](https://github.com/YohakuSama/loonkit/actions/runs/40113803904) 与 [Beta CI](https://github.com/YohakuSama/loonkit/actions/runs/40113804107) 均通过；合并后的 [main CI](https://github.com/YohakuSama/loonkit/actions/runs/40113944093) 也通过。实际下载 main/LoonKit.lcf 已核对 v6.5.7 标题、上述 SHA256 与原样保留的 GEOIP 指令。后续元数据提交不改变该配置内容。

测试渠道通过 [PR #129](https://github.com/YohakuSama/loonkit/pull/129) 同步，beta 合并提交 `a0898bd422b7335cc705932c0ab36f7375a53562` 的 [Beta CI](https://github.com/YohakuSama/loonkit/actions/runs/40113948082) 通过。发展中 beta 的正式回滚基线已改为本次发布提交；冻结 foundation manifest 保留构建时原字节及其 hash。

[合并后的真实上游审阅](https://github.com/YohakuSama/loonkit/actions/runs/40113944082) 成功，stage 实际 checkout 上述 beta 合并提交，验证 v6.5.8-beta.1 的 36 个资源，来源完整并比较 33 组，结果为 `NO_ROUTINE_ADDITIONS`，写入 job 按条件跳过。自动 PR 创建权限和真实 CI dispatch 仍待首次合格增量核实；本轮未添加合成规则或创建空草稿。

本地 101 项 Python、12 项 Node 测试通过；CI 同时覆盖全量不可变资源校验、历史构建、许可资料一致性与 11 个历史回滚资源。清理盘点没有新增可删候选，继续保留现役依赖与必要冻结基线。发布状态以 build/release_manifest.json.publication 为准。

## 必要检查

```bash
python3 scripts/source_lock.py --check
python3 scripts/verify_release.py --check --remote
python3 scripts/reviewed_release.py --check
python3 scripts/prepare_promoted_release.py --check
python3 scripts/prepare_release_v656.py --check
python3 scripts/beta_channel.py --remote
python3 scripts/license_audit.py --check
python3 scripts/license_evidence.py --check
python3 scripts/beta_cleanup.py --verify-archives
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/diagnostics.test.cjs
```

历史 v6.5.5 与 v6.5.6 构建检查使用冻结快照，发展中的 beta 更新不应使其失败。新增回归覆盖共享云/同意平台反例、关键词误分流、通知 SDK、精确遥测、真实排查 CLI、清理器配置引用保护，以及三轮 beta 更新后完整正式校验。

## 合并和后续维护

核对准确发布 PR head 的 Production CI 成功，再合并 main；实际下载正式入口确认版本、hash 和资源，记录真实 main 提交。按正常合并方向同步 beta，运行实际默认分支上游审阅。没有合格新增时保持不创建空草稿，不向运行配置添加合成主机。

旧版本 checksum、历史批准快照、冻结输入、当前资源和回滚 URL 均继续保留。许可检查仅证明资料保留与一致性，不等于逐行权利获得独立认证。
