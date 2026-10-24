# 发布与维护检查

## v6.5.7 审计修复

版本配方：rules/reviewed/v6.5.7/decisions.json。正式配置 SHA256：9dbcb5bff0cae6be233053e13b464176a0af4ad714efd27b3fa290f3c86ee84b。

- 正式入口继续为 main/LoonKit.lcf；36 个固定规则资源，196624 条记录，33 个策略组。
- 新规则资源固定提交：8f144d9d74dfae4e5064e4c1eeed23addd62199d；旧资源、原始来源和许可文本保持可追溯。
- AliDNS、LOOPBACKIP、所有 General、完整 Rule 段和策略默认值与 v6.5.6 一致，包含用户指定保留的 GEOIP,CN,DIRECT,no-resolve。
- 本版本发布依据维护者明确请求，见 RELEASE_OWNER_DECISION_v6.5.7.json。新增设备结果没有被伪造为 PASS；未新增等待天数。
- 回滚：[固定 v6.5.6 配置](https://raw.githubusercontent.com/YohakuSama/loonkit/67c9060fc41c0fc9c7960612f33c9eb6e4c33cbe/LoonKit.lcf)。历史 checksum 和 build/baselines 保留。

当前修复分支的发布状态以 build/release_manifest.json.publication 为准。真实 PR、准确 head CI、合并后 main 和上游运行结果在发生后追加，不能在准备阶段预先标记已发布。

准备阶段记录：正式发布 [PR #128](https://github.com/YohakuSama/loonkit/pull/128)，测试渠道 [PR #129](https://github.com/YohakuSama/loonkit/pull/129)。原始候选提交 `3388b2565af8e7b660c4af7a46ede011692e0c02` 的 [Beta CI #40113536649](https://github.com/YohakuSama/loonkit/actions/runs/40113536649) 已通过；正式合并仍需最终 PR head 的实际 Production CI 通过，不能使用旧提交的结果代替。

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
