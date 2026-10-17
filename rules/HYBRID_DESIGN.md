# Loon Routing DNS v5 — 自建复合型规则库说明（人工审核版）

## 为什么不是直接复刻一份他人的规则？

用户在启用 Loon 后遇到国内哈啰 App 无法联网。仅增加哈啰域名可以改善部分路径，但不能证明故障原因。既有配置主要使用单一上游目录，增加例外的过程难以追踪：平台与大陆直连、广告过滤、服务 CDN 及 AI 部分功能容易产生交叉。我们需要的是**一个可复现生成、能追踪每条来源、出现问题能快速定位与回滚的规则库**，而非堆砌多个大规则包。

所谓「复合型」，是在明确策略的前提下汇聚不同上游各自的优势：

| 数据源 | 用途 | 许可证 |
|---|---|---|
| [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) | Loon 原生基本规则、国内分流、各类服务规则 | GPL-2.0 |
| [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) | 额外服务域名补全、AI、新媒体及平台的第一方域名 | MIT |
| [felixonmars/dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list) | 审核过的 Apple 中国加速域名；不导入整个加速域名库 | WTFPL-2.0 |
| 本项目 rules/custom | 哈啰、国内地图支付与之前手动维护的服务补充 | 项目自有规则 |

保留 [GPL-2.0 正文](./LICENSE.GPL-2.0)、[v2fly MIT 正文](./LICENSE.MIT-V2FLY)、[felixonmars WTFPL 正文](./LICENSE.WTFPL-FELIXONMARS)。复合列表含 GPL-2.0 规则，应在公开分发时遵守 GPL-2.0 的相应条款，并保留所有来源标识。其他许可尚未核对的项目暂不混合。

## 数据组织和发布方式

- 完整候选文件：[reviews/Loon_Routing_DNS_Hybrid_Review.lcf](../reviews/Loon_Routing_DNS_Hybrid_Review.lcf)
- 来源登记：[sources.json](./sources.json)，当前 **87 个启用源**，含 10 个项目自身规则文件，哈啰规则文件并入国内 `DomesticCore`。
- 生成器：[scripts/build_composite_rules.py](../scripts/build_composite_rules.py)，统一将来源映射到 **33 个策略目标**。
- 输出目录：[`rules/generated/`](./generated/)，在主分支仓库自托管，更新先经自动化构建再由人工审查 PR 合并。完整配置的 33 条规则订阅全部指向自己的 `rules/generated`。
- 新版默认使用 blackmatrix7 的 **AdvertisingLite + Privacy + Hijacking**（约 3.8 万条来源记录），而不是 29 万条的完整广告列表；保留在来源候选库中以便比较。
- 原本属于 `[Rule]` 的第一方域名迁移到 `rules/custom/` 参与构建，不再与远程规则重复维护。`[Rule]` 仅保留必要资源出口、`GEOIP` 和 `FINAL`。
- 哈啰已核验的 3 个官方域名已并入 `DomesticCore → DIRECT`，与高德地图、支付宝等国内关键服务一起维护；**不单独创建 HelloBike 策略组**。这些域名不是整个哈啰 App 的完整网络足迹，仍需看真机日志。

## 去重和安全

1. 同一组内相同类型、相同目标的规则统一为一条（域名统一小写，IP 网络规范化）。
2. `v2fly` 的普通域名转换为 `DOMAIN-SUFFIX`，`full:` 转为 `DOMAIN`，`keyword:` 转为 `DOMAIN-KEYWORD`；`@ads`、涉及跨境标记 `@!cn` 的非目标数据过滤；`include:` 依赖不自动递归，避免悄悄膨胀服务分类。RegExp 不擅自转换。
3. 对未知语法、URL-REGEX、缺失来源及源文件异常缩减拒绝或隔离。报告 `audit.json` 记录审查依据。
4. 跨策略组相同的精确匹配按发布订阅顺序仅保留最先命中组中的一条，并将去重前的归属记录到审计报告；跨策略的父子域名覆盖仅报告不自动修改语义。
5. 重要服务和中国直连排在广告过滤之前，优先保证正常业务功能；但这意味着部分广告域名可能被服务规则放行，这一权衡需要使用者验证。国内直连放在后面，`FINAL` 保持原来的代理优先配置。
6. DNS 没有变更。DoH 加密不等于 DNS 匿名；不能因网页 DNS 检测结果与代理出口不同，就认定泄漏。
7. 自动任务只提交候选 `rules/generated` 到更新 PR，**绝不自动覆盖 main 配置**；正式上主分支仍需手动审核与独立合并。

## 哈啰回归与最低发布门槛

备份原配置、确保节点订阅已添加。在 Loon 中检查 `DomesticCore = DIRECT`（无需单独策略组）、`AdBlock = REJECT`、`Final = Proxy`，分别验证：
- 哈啰登录 / 首页 / 定位 / 地图 / 行程 / 支付页面加载（不需要实际支付）；
- 切换广告拦截 `REJECT` 与 `DIRECT` 后的差异；查看请求日志中的精确失败域名；
- 中国大陆银行、地图、常用 App，Apple 更新、Steam 中国下载、Bilibili；
- AI、常见海外流媒体、社交平台、IPv6、UDP、网络切换和 DNS 查询模式。

**CI 通过只说明格式、源地址与规则转换通过。实际 App 无法联网也可能来自 TLS、代理节点、运营商、DNS、TUN、广告误杀及 UDP，不能保证靠域名规则单独解决。**

若新列表失效，将配置切回原稳定版；出现被误拦截的域名时，在项目 `rules/custom` 补充有证据的精确条目，而不是扩大整站直连或临时关闭所有防护。

## 更新与可维护性

合并规则管理能力后，已有的自动化会定期更新上游并创建待审的 Draft PR；禁止无审核的自动 merge。若上游长期不更新，仅标记审查，不因时间旧就直接删除。任何更新导致 40% 以上的来源规则骤减都会失败并要求人工确认。
