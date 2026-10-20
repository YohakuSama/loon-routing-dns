# LoonKit v6.0.0 — 更新记录

当前正式版本包含 26 份固定远程规则（197,765 条匹配）、106 条本地规则和 33 个策略组。

- 标准配置 `LoonKit.lcf` 的分流、DNS、TUN、IPv4、IPv6 和现役插件内容均保持不变。
- AdBlock 仍支持 `REJECT` / `DIRECT` 选择；`GEOIP,CN,DIRECT,no-resolve` 与 `FINAL,Final` 保留。
- 采用 43 份独立锁定输入（33 份冻结规则、10 份本地规则），正式版可离线重建并逐字节验证。
- 删除不再使用的 `LoonKit.PrivacyDNS.lcf`、旧 `rules/generated/`、`rules/ProxyProtect.list`、v5 活动清单和重复独立插件别名。旧订阅到这些地址将失效。
- 历史来源和许可证证据保留，尚未完成的第三方许可判断不被标记为已批准。

[安装说明](../README.md) · [正式构建清单](../build/release_manifest.json) · [维护](./MAINTAINING.md)

## 网络诊断修复

- 将代理探测改为 HTTPS 204 目标，避免旧 HTTP 目标返回 301 时误报代理故障。
- HTTP 重定向和远端站点非预期状态码改为待确认；超时、TLS 错误等传输错误仍报告故障。
- Loon DNS 返回 `auto`、不完整元数据或缓存时明确标记协议未验证，不推断发生或未发生 DNS 泄漏。
- 新增版本化 JS 和 HTTP 301、自动提醒、DNS auto / 缓存回归测试。
