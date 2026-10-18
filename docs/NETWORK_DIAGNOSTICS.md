# Loon Routing DNS 控制台插件 v1.3

这是随完整配置自动加载、可在 Loon 内关闭的 **Loon Routing DNS 控制台插件**，使用 Loon 官方 `[Argument]` 参数页面作为控制台设置，配合五个可以手动点击的 `generic` 脚本入口；**不是单独的网页或内嵌可视化 App 页面**。

> 不接管 Loon 自带的策略组选择、全局代理、原生节点测速、DNS 服务器、网络自动开关、系统 VPN、Rewrite 或 MitM。
> 更改控制台参数不会修改 `Loon_Routing_DNS.lcf`；只影响本插件发出的探测请求。

## 随主配置自动加载（v4.4.8 起）

**完整配置已内置这个控制台，无需手动订阅插件。** 使用下方正式配置地址导入并更新资源后，控制台会列在 **Loon → 配置 → 插件** 中。进入它的参数页面调整检测服务器、IP 数据源等选项。

```text
https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/Loon_Routing_DNS.lcf
```

旧配置、单独使用者仍可使用原插件地址：

```text
https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/plugins/Network_Diagnostics.plugin
```

**以前手动安装过的用户：** 切换到内置控制台的新主配置后，检查插件列表里有无重复条目；保持一份即可。个人参数在更新前应先备份。若没出现控制台，在 Loon 更新插件资源并查看错误日志。

控制台为可关闭的可选诊断功能，即使关闭，完整配置仍能正常分流。需 **Loon 3.5.1 Build 983+**；原生 DNS 查询需 **Build 988+**。脚本固定引用仓库 `main/scripts/*.js`，远程更新是否立即生效取决于 Loon 缓存与资源更新操作。

## 五个手动入口

| 通用脚本 | 做什么 |
|---|---|
| **控制台 · 状态与设置摘要** | 汇总插件专属检测设置、最近一次自动与手动诊断的时间和状态；敏感 DoH URL 仅展示主机名 |
| **手动网络与 DNS 诊断** | 分别测试 DIRECT、指定 DoH、Proxy 出口，Build 988+ 再执行 Loon 原生 `$dns.query()` |
| **模拟网络切换诊断** | 立即运行一次与自动模式相同的轻量探测，并写入“最近诊断”；不会发自动告警，也不能证明 iOS 事件钩子本身工作 |
| **已发布规则资源检查** | 通过 GitHub API 核对正式分支的 33 份规则文件是否存在、非空及是否异常偏小；不能读取 Loon 实际命中记录，也不能证明远程订阅已更新 | 
| **节点详情查询** | 查询指定策略/节点的出口 IP、国家、城市、ISP、ASN、数据中心特征等；有需要时开启 DIRECT 对照 |

## 控制台的 12 个参数

| 参数 | 默认值 | 意义 |
|---|---|---|
| `auto_check` | 开启 | Wi-Fi / 蜂窝网络变化后尝试自动探测 DoH、DIRECT |
| `notify_every_change` | **关闭** | 临时诊断：正常也显示“网络变化检测已触发”的通知 |
| `doh_url` | `https://dns.alidns.com/dns-query` | 通过 DIRECT 发标准 RFC 8484 DoH 查询 |
| `direct_probe_url` | `http://wifi.vivo.com.cn/generate_204` | 本插件自己的 DIRECT HTTP 健康检查服务器 |
| `proxy_probe_url` | `http://cp.cloudflare.com/generate_204` | 本插件手动代理连通性健康检查 |
| `probe_timeout` | 6500 毫秒 | 插件请求时限，2000–12000 毫秒；无效值恢复默认 |
| `target_policy` | `Proxy` | 出口 IP 情报查询所使用的节点或策略 |
| `compare_direct` | **关闭** | 额外查询真实公网 DIRECT 出口，数据会提供给 IP 情报服务商 |
| `primary_ip_url` | `https://api.ipquery.io/?format=json` | 主要公网 IP 情报查询地址 |
| `backup_ip_url` | `https://ipwho.is/` | 备用 IP 情报查询地址 |
| `enable_ip_backup` | 开启 | 主情报源无法访问或返回无效格式时才查询备用 |
| `cache_seconds` | 120 秒 | 仅明确节点入口可以使用的结果缓存，0–600 秒；0 禁用 |

**注意“测速服务器”的含义：** 上述 `direct_probe_url` 和 `proxy_probe_url` 只是控制台自行发出的健康探测，不是 Loon 内置节点测速服务器。要修改 Loon 原生 `proxy-test-url` 或 `url-test` 的 `url`，请直接编辑主配置或使用 Loon 相应原生功能，控制台不会替你设置。

自定义 HTTP 探测网址要求 HTTP 或 HTTPS，200/204 视为可达；真实监测可能受重定向、鉴权和探测服务器地域限制影响。不要填写要求登录才能访问的地址。

自定义 IP API 要求返回 **ipquery.io 或 ipwho.is 兼容 JSON 格式**，例如包含 `ip`、`location` 与 `isp` / `risk`，或 `ip` 与 `connection`。**不是任意返回公网 IP 的网页都能用。** 自定义 API 地址中若包含 token，将作为 HTTPS URL 发送给服务商，因此不应把包含私密密钥的插件配置提交到公开仓库。脚本报告不打印完整 URL。

## 网络切换自动诊断为什么看不到？

Loon 官方新版 Script 支持：

```ini
network-changed then script("network-diagnostics.js") with tag="网络切换诊断"
```

它只在 **Loon 检测到系统网络变化**时触发。不是每次打开网页、切换策略组或重新测速时都会执行，也不能保证被 iOS 后台挂起时立即执行。

原版插件默认 **只有确认为 DoH 故障才通知**，正常时没有弹窗。因此你可能没有看到它触发。

### 如何验证

1. 打开插件参数，确认 **网络变化自动诊断=开启**。
2. 临时启用 **每次网络变化都通知**。
3. 保持 Loon 运行，尝试切换 **Wi-Fi → 蜂窝数据 → Wi-Fi**（不要通过 Loon 停止运行来完成切换）。
4. 返回控制台，运行 **「控制台 · 状态与设置摘要」** 查看“最近网络变化检测”时间。
5. 也可以先运行 **「模拟网络切换诊断」**，确认探测代码能执行。但模拟只测试脚本，不证明 Network Changed 事件从 iOS 发出了通知。
6. 完成测试后关闭 **每次网络变化都通知**，避免骚扰。

如果真实切换后仍无记录：检查插件是否启用、脚本入口开关是否生效、Loon 脚本执行日志及 iOS 后台限制，记录 Loon Build 号反馈。部分 Wi-Fi 之间的变化是否触发取决于 Loon 自己的网络变化判定。

自动诊断仅做 **DIRECT 和 DoH 的快速探测**；失败后延迟复测；同类异常 30 分钟内不反复告警。正常结果写本地“最近诊断”状态，不上传其他日志。自动模式**不会查询 IP 情报，也不对所有代理节点测速**。

## 节点详情与隐私

节点出口查询通过 `$httpClient.get({node:target_policy})` 指定网络路径；返回的是**查询站点观察到的出口 IP**，不一定是订阅服务器入口 IP。

机房、移动、VPN、代理、Tor 和风险分数属于第三方情报源标签，不是权威证明。没有被标记为机房也**不等于确认家宽**。Loon 本地 GeoIP/ASN/ASO（如可用）用于交叉核对。

DIRECT 出口对照**默认关闭**：只有你开启此功能，脚本才主动请求并暴露直连公网 IP 给第三方情报商。即便对照关闭，主要 IP 情报 API 仍然会看到所用代理的出口 IP。若不想进行 IP 情报请求，不运行「节点详情查询」即可。

## 项目维护和排错

- [正式配置](../Loon_Routing_DNS.lcf)
- [控制台插件](../plugins/Network_Diagnostics.plugin)
- [控制台脚本](../scripts/console.js)
- [网络与 DNS 诊断脚本](../scripts/network-diagnostics.js)
- [节点情报脚本](../scripts/node-intelligence.js)
- [项目专属控制台图标](../icons/v20261018r2/Console.png)
- [开发与模拟测试](../tests/test_console.js)

**自动模拟检查通过不代表已经在真实 iOS Loon 环境下验证。** 脚本有问题请提供 Loon Build 号和经过脱敏的脚本日志。

## 已发布规则资源检查的边界

该功能只请求公开的 GitHub 仓库树元数据，核对 `rules/generated/*.list` 的文件存在性和大小；不下载规则正文，不读取 Loon 请求日志，不需要 MITM。检查结果不代表 iPhone 上规则已更新、匹配正确或广告拦截有效。GitHub API 无法连接、限流或数据不完整时会显示失败原因。运行时通过 DIRECT 访问 GitHub API，若当前网络无法直连 GitHub，请勿将其误判为规则失效。
