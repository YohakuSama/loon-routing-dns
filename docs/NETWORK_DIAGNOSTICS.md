# LoonKit 网络诊断插件

当前唯一正式插件文件：[Network_Diagnostics.plugin](../release/phase-07/assets/Network_Diagnostics.plugin)。完整配置已经引用该插件，通常不需要重复订阅。

独立插件地址（仅在需要单独安装时使用）：

```text
https://raw.githubusercontent.com/YohakuSama/loonkit/d405e4be28c447b6e57a4790e965c89f342d6dd6/release/phase-07/assets/Network_Diagnostics.plugin
```

## 节点出口信息

查询所选策略或节点的公网 IP、地区、ASN、ISP 和网络特征。默认使用 `Proxy`，可选启用 DIRECT IP 对照（默认关闭）。

## 网络与 DNS 诊断

检查直连、代理和 Loon 原生 DNS 查询（原生 DNS 诊断需要受支持的 Loon 版本）。显示解析协议、服务器和是否来自缓存。标准配置默认使用 `https://dns.alidns.com/dns-query`。

## 网络切换提醒

默认关闭；手动开启后，在网络变化时检查直连网络状态，不自动改变 DNS、分流规则或节点。避免使用后重复加载相同插件。

详细 DNS 排查见 [DNS 配置](./DNS_PRIVACY.md)。
