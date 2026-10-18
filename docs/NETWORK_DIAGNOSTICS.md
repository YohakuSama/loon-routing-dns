# Loon Routing DNS · 轻量辅助插件（开发版）

本插件仅补充 Loon 原生功能未覆盖的节点出口情报，并提供可选的网络切换异常提醒。不修改 DNS、代理策略、VPN、远程规则，不使用 MitM。

## 功能

- **节点详情查询（唯一手动入口）**：查询指定节点/策略的出口 IP、ISP、ASN、国家地区及第三方网络类型标签。明确节点上下文会在本机记录最近一次出口 IP、ASN、ISP，并在下一次非缓存查询时提示变化；动态 Proxy 策略组不进行历史对比，以免节点切换造成误报。记录只存本机，30 天后不用于比较。出口 IP 不一定是节点入口 IP；机房、住宅、VPN 等标签均属于启发式信息，不能作为权威证明。
- **网络切换异常监测（默认关闭）**：仅在用户主动开启后进行 DIRECT 和指定 DoH 的健康探测；异常二次复测、同类告警 30 分钟冷却。它不能证明 DNS 未泄漏，也不替代 Loon 自带的网络检测。正常情况默认不通知。

## 安装与使用

开发版插件地址：

```text
https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/feat/console-rule-health-20261018/plugins/v20261018r2/Network_Diagnostics.plugin
```

正式配置仍引用 main 分支的正式版插件，开发版不会自动替换正式版。若单独导入开发版，请避免与内置正式版同时启用，以免重复监测。

节点查询默认通过 Proxy 访问 ipquery.io；主接口异常可选用 ipwho.is。**真实直连 IP 对照默认关闭**，只有主动开启才会向第三方 IP 情报服务发送 DIRECT 出口 IP。短时缓存仅对明确的节点上下文启用。

异常监测默认关闭。若主动开启，请在 Loon 中实际切换 Wi-Fi/蜂窝网络并观察脚本日志；后台触发行为取决于 Loon 和 iOS。监测脚本使用 Loon 的 network-changed 事件，不会自动切换代理。

## 开发与质量检查

- `node tests/test_console.js`：模拟运行时测试，覆盖节点查询、网络切换通知和精简菜单。
- `python3 scripts/validate_repo.py`：校验主配置和插件引用、默认隐私选项、脚本数量。
- `python3 scripts/audit_dns_config.py`：静态检查 DNS 配置风险，报告明文 DNS 回退、DoH 和 DNS 劫持配置；**不代表真实 DNS 泄漏检测**。\n- `python3 scripts/audit_rule_overlaps.py`：离线审计 33 组规则的跨组精确重复和潜在覆盖，属于 CI 工作，不占手机菜单。

以上模拟测试不能替代 Loon 真机验证。规则资源完整性、广告隐私 HTTP 探测、控制台参数摘要和重复的手动网络诊断已从轻量插件入口移除。原脚本留在开发分支以便回退，未被插件调用。
