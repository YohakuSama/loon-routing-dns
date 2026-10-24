# 正式发布与测试版验收

v6.5.7 的范围是维护者于 2026-10-25 明确请求的审计修复、保留 GEOIP,CN,DIRECT,no-resolve、合并和正式发布。版本专属请求见 RELEASE_OWNER_DECISION_v6.5.7.json；自动验证绑定准确配置和受审配方，合并仍须实际 PR head CI 通过，之后核对 main Raw。

历史批准候选保存在 build/baselines/v6.5.5-beta.4/，历史正式验证不再读取工作树 beta 来强制固定旧 SHA。当前正式构建与规则检查使用 reviewed_release.py 和 verify_release.py；它们核对所有 General/Rule/策略设置未越界、资源字节与顺序、历史 checksum 及来源锁。

v6.5.8-beta.1 是独立发展候选，模板仍是 TEMPLATE_NOT_EVIDENCE，不继承本轮或旧版设备批准。没有提供的 Build、逐项结果、观察日期不得写成 PASS。历史 beta_promotion_gate.py / release_promotion_gate.py 保留旧模型的回归与预检，不代表 v6.5.7 当前发布授权，也不能用它们的旧版常量锁死今后 beta。

```bash
python3 scripts/verify_release.py --check --remote
python3 scripts/reviewed_release.py --check
python3 scripts/beta_channel.py --remote
python3 scripts/beta_promotion_gate.py --assert-template-blocked
```

清理器独立检查已核实的正式发布身份，保护正式配置、活跃 beta 和必要基线；不要以清理为由删除历史批准快照或覆盖原资源。
