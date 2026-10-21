# v6.0.0 正式规则

正式配置 `LoonKit.lcf` 使用 `rules/releases/vNext-RC2/` 的 26 份固定版本规则，远程资源引用提交 `9bbac4c9aa0ec33c82ab5fe03648127f3f4754f4`。规则按固定版本发布。

**唯一构建输入：** `rules/inputs/`（33 份冻结规则）与 `rules/custom/`（10 份本地补充），共 43 个独立文件。输入由 `build/sources.lock.json` 的 SHA256 和 Git Blob SHA1 校验，策略在 `build/engine_manifest.json` 中锁定。正式生成器为 `scripts/rule_engine.py`。

`python3 scripts/verify_release.py --check` 验证冻结输入和 26 份已发布规则逐字节一致。来源更新先使用 `scripts/review_source.py` 检查差异，再通过 `scripts/prepare_release.py` 在仓库外准备候选，不自动发布。

第三方规则的来源、许可和署名详见 [第三方许可与来源](../docs/THIRD_PARTY_NOTICES.md)。历史构建和发布说明见 [维护文档](../docs/MAINTAINING.md)。

## 上游更新与规则收紧的实际能力

`.github/workflows/rules-update.yml` 每周拉取公开上游与本地来源，使用 `scripts/upstream_review.py` 解析 Loon、domainset、v2fly、dnsmasq 四种格式，生成**来源快照、规范化候选、完整增删差异、去重结果和跨策略冲突报告**。V2Fly `include:` 引用按受限方式展开，无法安全等价转换的正则单独记录；不会自动修改正式规则。更新要经过来源差异审阅、许可证及策略回归、重新锁定输入和发布新的固定规则版本。

现有 `scripts/rule_engine.py` 对锁定的 33 份冻结规则及 10 份本地规则执行规范化、精确去重、同策略的 DOMAIN / DOMAIN-SUFFIX 覆盖去重、跨策略冲突隔离，并针对审阅过的关键字及共享网段进行局部收紧。**这并不是对所有上游来源的自动智能合并，也无法保证所有规则始终最新或完全不存在误分流。**

**稳定性原则：** 自动审核只拒绝**确实格式无效**的来源匹配；语法合法但可能过宽的公共后缀、多租户托管域名、短关键字和广泛 IP 网段会保留在候选审阅数据中，明确标记风险优先级，不会因启发式阈值而丢失。域名及 IPv4/IPv6 跨策略覆盖、AdBlock 误杀支付/登录/CDN、IP/ASN 与所有新增或移除都记录到 `FULL_RISK_AUDIT.json`，附具体来源和风险。**`candidate/*.list` 仅含已发布的完整基线**，不能自动添加或删除规则；正式更新必须独立审核、重新锁定及回归。详见[规则安全机制](../docs/RULE_SAFETY.md)。
