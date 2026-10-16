# Loon Network Diagnostics（可选插件）

此插件与 Loon Routing DNS 主配置**完全独立**。不安装不影响主配置；安装后提供手动诊断以及 Wi-Fi / 蜂窝网络切换后自动诊断。无需 MITM、证书、Rewrite 或额外 DNS 服务器。

## 安装

要求 **Loon 3.5.1 (Build 983) 或更新版本**。打开 Loon → 配置 → 插件 → ＋ → 从 URL 导入，粘贴：

```text
https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/plugins/Network_Diagnostics.plugin
```

启用插件后，在 Loon 的脚本/通用脚本页面运行 **「手动网络诊断」**，查看结果。Loon 也可在网络变化时自动执行 **「网络切换诊断」**。

## 两种模式

| 模式 | 执行时机 | 内容 |
|---|---|---|
| 手动网络诊断 | 用户主动点击 | DIRECT 下 HTTP 204 探测、RFC 8484 DoH 查询、Proxy 组代理连通性 |
| 网络切换诊断 | Wi-Fi / 蜂窝网络切换 | DIRECT + DoH 两项轻量检测，失败后延迟复测，确认 DoH 故障才通知 |

自动模式不会检查代理节点，避免网络切换时额外触发代理测速；自动异常提醒会去重，同类故障最多每 30 分钟提醒一次。仅直连 HTTP 204 探测站点异常、DoH 正常时不发送网络故障通知，以减少误报。网络恢复后只记录日志，不打扰用户。

## 自定义 DNS

插件参数 **「待测 DoH 地址」** 默认是：

```text
https://dns.alidns.com/dns-query
```

如主配置改用其他服务商，请在**插件参数**中填写该服务商真实完整的 HTTPS DoH URL。探测使用 **RFC 8484 POST / application/dns-message**，目标查询为 `example.com` 的 A 记录，不依赖插件所配置 DNS 的其他代理路线。部分服务商若不支持标准 DoH POST，诊断可能失败，但不代表其专有 API 不可用。

可以通过插件参数 **「网络切换后自动诊断」** 关闭自动检测，仅保留手动检测。

## 常见结果

| 结果 | 排查方向 |
|---|---|
| DIRECT 正常，DoH 失败 | 检查 DoH URL、TLS、DNS 服务商可达性；若已经关闭加密 DNS 回退，网页可能无法解析 |
| DIRECT 和 DoH 都失败 | 网络可能仍在切换、受限或被拦截；检查 Wi-Fi、蜂窝网络和 Loon 日志 |
| DIRECT / DoH 正常，Proxy 失败 | 检查节点订阅、Proxy 策略组和代理节点 |
| 仅 DIRECT HTTP 204 失败，DoH 正常 | 可能只是探测网址不可达；不要直接认定设备断网 |
| DoH 成功 | 表示脚本在 DIRECT 下成功请求该 DoH 地址，**不代表 Loon 所有查询都通过 DoH** |

诊断请求固定以 `DIRECT` 检查公共网络/DoH，以 `Proxy` 检查主配置代理组。脚本不修改任何代理分流或系统设置。

## 隐私与局限

- 不读取或上传节点订阅、IP 出口、SSID 等个人信息；仅请求选定的连通性测试地址及用户设定的 DoH。
- 不打印用户的自定义 DoH 完整 URL（可能带个人配置 ID）。
- 不接管 Loon DNS 请求；无法判断是否存在系统或其他 App 的独立 DNS 请求，也不能直接证明零 DNS 泄漏。
- `http://wifi.vivo.com.cn/generate_204` 负责国内直连检查；`http://cp.cloudflare.com/generate_204` 负责 Proxy 路由测试；真实 DNS 查询使用 `example.com`。
- 若卸载插件，主配置不受影响。自动诊断仅通过独立的启用开关控制。

更多帮助请查看 [主 README](../README.md) 或 [Issues](https://github.com/YohakuSama/loon-routing-dns/issues)。
