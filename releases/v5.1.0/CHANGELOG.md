# Loon Routing DNS v5.1.0 — 正式版

发布日期：2026-10-17

## 核心改动
- 将原有直接引用外部订阅，改为本仓库 `main/rules/generated/` 中维护的 **33 条自托管规则列表**，保持 **33 个原有策略组** 不变。
- 87 个输入源：blackmatrix7 的 Loon 原生分流、AdvertisingLite/Privacy/Hijacking；v2fly 增补主流 AI、流媒体、社交、游戏平台域名；felixonmars 部分 Apple 中国解析域名；项目自维护大陆服务。
- 广告及隐私统一使用 AdBlock 策略组的 `REJECT`，保留 DOMAIN/DOMAIN-SUFFIX，不默认使用宽泛关键词、共享 IP 封禁、URL-REGEX 和 MITM。
- 中国大陆重要地图、支付及哈啰官方域名统一走 DomesticCore→DIRECT，不新增 App 专属策略组。
- 格式归一化、相同规则去重、同组父域覆盖精简、跨组相同精确匹配按订阅优先级保留第一条；对无法自动安全处理的交叉冲突在 `audit.json` 报告。
- DNS、WebRTC/STUN、UDP、节点订阅占位、控制台插件保留旧版设置，避免同时引入难以定位的网络行为变化。

## GitHub Actions 构建校验（不是 iPhone 实测）
- 输入来源：87
- 输出策略列表：33
- 规则输出：206,503 行（不含注释）
- 同组精确重复：1,309 条
- 不同组重复精确匹配：150 条已按优先级消除
- 同组父域覆盖精简：见 `rules/generated/audit.json`
- 广告隐私宽泛匹配隔离：196 条 DOMAIN-KEYWORD、239 条 IP-CIDR、1 条 IP-CIDR6
- 其余含 v2fly include/regexp 和上游 URL-REGEX 的条目单独审计，未盲目转换

## 升级方式
1. 备份原有节点订阅和配置，防止覆盖个人 URL/凭据。
2. 从 `https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/Loon_Routing_DNS.lcf` 导入完整配置。
3. 重新添加私人节点订阅，更新远程规则，运行模式设为 RULE。
4. 分别检查国内 App（哈啰/地图/银行/支付）、AI、视频、苹果 OTA、IPv6、UDP。
5. 登录/支付异常时临时将 AdBlock 从 REJECT 切成 DIRECT，查看 Loon 请求日志定位具体误杀域名后做精确例外。

## 风险与局限
- 仅完成 CI 静态校验和规则上游读取，没有用实际 iPhone 验证所有应用，也无法保证每条上游域名仍有实际用途。
- “最近未更新”不直接等于失效；来源元数据、变更指纹保留，维护人员应按使用日志复核。
- 更谨慎的广告默认策略会减少部分误杀，但可能放过依赖 URL 正则或关键词匹配的广告。
- 广泛国内规则和广告域名列表可能带来设备内存/加载开销，遇到性能问题应收集日志和设备型号后优化。

## 回滚
上一版配置原文已保存于 [releases/v4.4.8/Loon_Routing_DNS.lcf](../v4.4.8/Loon_Routing_DNS.lcf)。如遇严重兼容性问题，使用它重新导入，不要继续把有问题的规则直接覆盖线上配置。

来源许可及授权见 [rules/LICENSE.GPL-2.0](../../rules/LICENSE.GPL-2.0)、[rules/LICENSE.MIT-V2FLY](../../rules/LICENSE.MIT-V2FLY)、[rules/LICENSE.WTFPL-FELIXONMARS](../../rules/LICENSE.WTFPL-FELIXONMARS)。
