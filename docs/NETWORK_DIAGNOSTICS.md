# LoonKit 网络诊断插件

当前唯一正式插件文件：[Network_Diagnostics.plugin](../release/phase-07/assets/Network_Diagnostics.plugin)。完整配置已经引用该插件，通常不需要重复订阅。

独立插件地址（仅在需要单独安装时使用）：

```text
https://raw.githubusercontent.com/YohakuSama/loonkit/97ec3554465ba5c338a00a5e2f7e8598b9f26b3a/release/phase-07/assets/Network_Diagnostics.plugin
```

## 节点出口信息

查询所选策略或节点的公网 IP、地区、ASN、ISP 和网络特征。默认使用 `Proxy`，可选启用 DIRECT IP 对照（默认关闭）。

## 网络与 DNS 诊断

已修正 HTTP 301 重定向的误报：代理目标返回 3xx 或 4xx/5xx 时列为**无法确认**，不等同于代理节点故障。代理检测使用 HTTPS 204 地址，并关闭自动重定向。

当 Loon 原生 DNS 返回 `auto` 或缺少完整服务器信息时，插件会说明“解析成功，但实际传输协议未验证”；缓存结果也不会被标为本次 DoH 请求。只有明确返回普通 DNS 协议的本次查询才标注相应风险。

检查直连、代理和 Loon 原生 DNS 查询（原生 DNS 诊断需要受支持的 Loon 版本）。显示解析协议、服务器和是否来自缓存。标准配置默认使用 `https://dns.alidns.com/dns-query`。

## 网络切换提醒

默认关闭；手动开启后，在网络变化时检查直连网络状态，不自动改变 DNS、分流规则或节点。避免使用后重复加载相同插件。

详细 DNS 排查见 [DNS 配置](./DNS_PRIVACY.md)。
