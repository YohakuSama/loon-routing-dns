# LoonKit v6.0.0 更新记录

v6.0.0 从 v5.10.0 调整为 26 份冻结的远程规则、106 条本地规则和 33 个策略组。两份正式配置维持原有导入入口，并分别保留 AliDNS 和 DNSPod 的 DNS/DoH/TUN/IPv4/IPv6 参数。

## 已发布功能

- 固定版本的规则订阅：`rules/releases/vNext-RC2/`，197,765 条远程匹配器；现役完整配置不使用旧 `rules/generated/`。
- 国内服务直连与海外分类策略组；7 条明确设置 `no-resolve` 的 ASN 匹配；`GEOIP,CN,DIRECT,no-resolve` 和 `FINAL,Final`。
- `AdBlock` 提供 `REJECT` / `DIRECT` 选择，保留 26 项本地优先级例外。
- 版本化的图标、网络辅助插件与其 JavaScript 资源。
- 当前仓库的冻结规则输入迁移至 `rules/inputs/`，锁文件集中在 `build/`，正式规则可离线构建并与既有发布文件逐字节比较。
- 历史审计/候选工件移除，保留兼容旧 Raw 订阅路径；CI 合并为正式校验、来源差异预览和手动发布候选。

## 升级

从旧版导入时，建议备份当前节点与策略选择，重新导入上层 README 中的一份完整配置，检查是否仍独立订阅旧规则以避免重复。网络诊断、不同地区应用解锁、广告拦截和 Final 出口以实际设备测试为准。

当前发布文件和哈希见 [正式发布清单](../build/release_manifest.json)；[维护及更新](./MAINTAINING.md)；[第三方许可](./THIRD_PARTY_NOTICES.md)。历史来源的行级归属不能完全恢复，尚未将授权人工复核标记为通过。
