# Beta 规则决策与证据登记

正式 v6.5.4 保持不变；当前配置身份以 build/beta_manifest.json 为准。以下为代码事实和离线结果，不冒充真机观测。

| 决策 | 实施结果 | 证据与边界 |
| --- | --- | --- |
| 广告开关 | 单个 Beta-AdBlock-Balanced 资源；关闭后恢复服务归属；Proxy 放行有独立含义 | 58 个离线场景中的 on/off 对照；其他插件和外部 DNS 过滤不受此开关影响 |
| 本地优先级 | 仅保留 Raw 访问和 Gemini/AI Studio/Copilot 的 4 条优先例外 | 去掉重复服务父后缀，避免遮蔽远程广告规则；补齐 Abema 与国内三个缺口 |
| 证书误杀 | 移除 crl.microsoft.com、ocsp.godaddy.com 拦截匹配 | 证书用途证据保存在 rules/beta/balanced_decisions.json，未放行整个微软或证书厂商 |
| 精确隐私增强 | Datadog Browser RUM、Fathom embed、Statsig exposure 三个精确主机进入广告资源 | 与功能配置 api.statsig.com、验证码接口分别处理，不默认封杀所有统计厂商 |
| Steam | 全球四个后缀归 Steam；13 个明确 CDN 候选保留 | 全局归属回归已测，CDN 地区/下载能力要真机确认 |
| 国际 WeChat 父域 | wechat.com、wechatapp.com 不再强制 DIRECT，未知子域使用 Final | 国内 qq.com、weixin.com 等保留；并非声称所有 WeChat 请求都在境外 |
| ChinaDirect | 精确排除总后缀/UA/国际父域，共 62 条 | 其余 114,775 条按原顺序保留，历史大表不等于每个目标的地区认证 |
| 共享 Google/AI | apis.google.com 跟随 Google，通用功能/实时通信平台跟随 Proxy | AI 自有租户继续 AI；单独指定不同服务节点时应复测验证码与语音依赖 |
| Apple | 82 条 AppleOTA 域名全部保留，策略跟随 Apple | 默认 DIRECT、real-ip 未改；切换 Apple 组时系统域名不再偷偷固定直连 |
| DNS | 用户指定保留默认 AliDNS | 不更换为 NovaXNS，不宣称解析一定经过代理；App 回退和私有 DoH 需实测 |
| 更新基线 | 原正式版 26 组 → 当前 beta 33 个来源组 | 复用同一个上游解析器；来源失败保留运行版本，无自动删除 |
| 更新权限 | 只自动创建受限草稿 PR，资产先提交、配置后 pin | 不自动合并 beta 或 main；显式 dispatch CI，避免 GITHUB_TOKEN 创建 PR 不触发检查 |
| 用户设备反馈 | 已记录“未发现问题”的概括反馈 | 精确版本/范围未记录，不补写 18 个 PASS，也不把新改动说成已经测试 |

## 来源优先级

按 Loon 官方的本地、插件、订阅规则来源优先级审查。公共诊断插件没有过滤规则；另行安装的用户插件不在公共配置静态分析范围内。相同文本的去重也要验证最终命中，不能只比较文本集合。

规则的离线类别、策略组默认选择、节点出口及 DNS 解析位置是不同层次。GEOIP,CN,DIRECT,no-resolve 保留；它不承诺所有未收录的国内域名都能自动直连。

## 仍需真实环境确认

- 新单广告资源关闭与 Proxy 放行的实际客户端行为。
- 关键功能、验证码、语音、系统更新、支付和下载的回归。
- AliDNS DoH 故障回退、IPv6、节点故障与网络切换的真实解析路径。
- CDN 的实际地区、账号地区及指定不同服务节点后的兼容性。
- 新版本的观察期与精确提交验收。

这些是明确的设备/现场证据缺项，不再以“尚未审计”掩盖已经做出的代码决策。
