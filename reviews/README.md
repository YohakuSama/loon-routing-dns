# Loon Routing DNS v4.5.0 — 哈啰兼容审查版

> **独立完整配置，当前不替换 main。** 用于排查“哈啰 App 在启用 Loon 后无法联网”。目前无法拿到哈啰运行时域名日志，**不能证明具体失败原因，也不保证仅凭域名白名单就能修复**。不要将静态检查视为真机兼容验证。

## 复制与导入

完整配置：[Loon_Routing_DNS_HelloBike_Review.lcf](./Loon_Routing_DNS_HelloBike_Review.lcf)。

完整配置直链（分支已核实）：

```text
https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/fix/hellobike-compat-review/reviews/Loon_Routing_DNS_HelloBike_Review.lcf
```

在 Loon 中备份现有配置、自己的节点订阅和个人覆盖规则后，从链接导入**新的配置文件**，不要覆盖原来正在使用的文件。新文件本身无私人订阅，需要你在 Loon 的远程节点管理中添加自己的订阅。只有设备实测稳定后才考虑改动 main。

## 改动清单

- 原版 v4.4.8 的 DNS、Loon 通用设置、插件、28 条上游远程规则、原有 33 策略组及规则全部保留。
- 新增第 34 个策略组 `HelloBike = select,DIRECT,Proxy,Auto,ALL_Filter`；默认 DIRECT，便于需要时手动覆盖。
- 将第一方可核实的 `hello-inc.com`、`hellobike.com`、`helloglobal.com` 放在本地 `[Rule]` 开头，指向 `HelloBike`，优先于远程分类及广告列表。域名来源：<https://www.hello-inc.com/>, <https://hellobike.com/>.
- 兼容性例外：`amap.com`、`autonavi.com`、`alipay.com`、`alipayobjects.com` 设为 DIRECT（**对使用这些域名的所有 App 生效**）。这是排查地图、定位与支付依赖的保守起点，不是已经证实哈啰必需的完整清单。
- `AdBlock` 默认临时选 `DIRECT` 作为排查步骤：关闭广告拦截可能增加广告和跟踪请求，**不应长期无意识保持此设置**。哈啰能正常使用后，切为 `REJECT` 复测。如果再次出现异常，收集触发 REJECT 的精确域名，以单条例外替代永久关闭广告拦截。
- 不修改 `disable-stun = true`、`udp-fallback-mode = REJECT`、AliDNS DNS/DoH，避免同时改变隐私属性或让 UDP 隐式直连。如果定位、车锁蓝牙、语音或其他服务仍异常，再分辨 App 权限/蓝牙/网络、UDP 或 STUN 与网络规则问题。

## 实测步骤

1. 先确保 Loon 的 `Proxy` 节点能访问国际站点，`HelloBike = DIRECT`、`AdBlock = DIRECT`、运行模式为 `RULE`。
2. 关闭哈啰后台后重开，测试首页、定位、地图加载、登录、骑行/顺风车页面；支付类操作**不要为测试而实际下单付款**。
3. 测试 Wi-Fi 与蜂窝数据。使用 Loon 请求记录筛选失败或 REJECT 的域名，记录命中策略、状态与时间，注意对 IP/令牌脱敏。
4. 哈啰成功后把 `AdBlock` 切回 `REJECT`，重试；如果复现，再从 REJECT 日志锁定误杀目标。
5. 如果 `AdBlock=DIRECT` 仍然失败，说明不能简单归因于广告规则；先看哈啰域名是否命中 `HelloBike`、地图/支付流量的连接错误，再检查 DNS DoH 直连可用性、UDP、设备定位/权限以及网络 IP 环境。

## 取舍

- Loon iOS 规则配置无法保证按“整个 App 进程”直接旁路所有网络请求；这是基于域名的修复，不是应用进程级分流。
- 国内精确直连规则降低了哈啰被默认代理或广告误杀的概率，但也会把相关域名请求交给直连网络；不能宣称 DNS 测试一定与代理出口地址相同。
- `dns-server` 和 `doh-server` 未动。原文档强调：DoH 流量模式应选择 DIRECT，加密 DNS 失败时是否允许明文回退需由 Loon App 设置；请沿用原版推荐设置，注意 DoH 失败可能导致无法联网。
- `rules/custom/HelloBike.list` 是本项目自维护的域名来源登记；当前完整配置已把这 3 条作为本地规则加载，为保证本地优先级**没有重复远程订阅**。
- GitHub CI 验证配置的静态结构与差异，不代表已通过真实 iPhone 上的 Loon 实机验证。

## 为什么不立即切换到全部自建规则？

之前构建的 46 源复合规则库仍处于 [独立审查 PR #3](https://github.com/YohakuSama/loon-routing-dns/pull/3)；其中 83 条不同策略的相同规则和逾万条域名后缀覆盖关系需要进一步核验。哈啰问题应先用最小、可回退的兼容差异定位根因，而不是在同一个版本里一口气替换几十万条远程规则，导致无法判断问题来自哪里。
