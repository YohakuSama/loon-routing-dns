# LoonKit v6.0.0 — 更新记录

当前正式版本包含 26 份固定远程规则（197,765 条匹配）、106 条本地规则和 33 个策略组。

- 标准配置 `LoonKit.lcf` 的分流、DNS、TUN、IPv4、IPv6 和现役插件内容均保持不变。
- AdBlock 仍支持 `REJECT` / `DIRECT` 选择；`GEOIP,CN,DIRECT,no-resolve` 与 `FINAL,Final` 保留。
- 采用 43 份独立锁定输入（33 份冻结规则、10 份本地规则），正式版可离线重建并逐字节验证。
- 删除不再使用的 `LoonKit.PrivacyDNS.lcf`、旧 `rules/generated/`、`rules/ProxyProtect.list`、v5 活动清单和重复独立插件别名。旧订阅到这些地址将失效。
- 历史来源和许可证证据保留，尚未完成的第三方许可判断不被标记为已批准。

[安装说明](../README.md) · [正式构建清单](../build/release_manifest.json) · [维护](./MAINTAINING.md)
