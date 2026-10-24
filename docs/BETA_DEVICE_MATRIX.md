# 测试版设备验收记录

## 当前 v6.5.8-beta.1

当前候选来自 v6.5.7 的固定配置，SHA 和资源以 `build/beta_manifest.json` 为准。维护者授权的是 v6.5.7 审计修复及正式发布；新 beta 的设备矩阵不自动继承旧结果。需要复核时，优先观察各服务独立节点、OneSignal 通知、广告资源关闭、网络切换与 DNS 路径，真实结果再填写。

以下 beta.4 的反馈和表格是历史记录，不是当前候选的逐项验收结果。

## v6.5.5-beta.4 维护者反馈

维护者于 2026-10-24 报告本轮候选在真机上“未发现任何问题”；讨论中对应的 beta 配置 SHA256 为 `fd1a01c6f8363a5dffaa1db9dbf044014c711fa48ea46e34a7c107180acbe0b7`。该总体反馈与下面的逐项场景记录不是一回事。未提供网络环境、设备 Build、抓包、观察区间和场景明细时，全部 NOT_RECORDED/NOT_MEASURED 保持不变；正式发布门禁仍未通过。


已收到此前用户“真机测试未发现问题”的反馈，参见 BETA_OWNER_FEEDBACK.json。未提供的精确版本、设备、Loon Build、网络和逐项结果保持未记录；不能把这些字段补成已验证。

当前配置、SHA 与资源身份以 build/beta_manifest.json 为准。beta.4 引入单广告资源、证书误杀修正、共享接口归属和 Apple 策略跟随等新行为，需要对这些变化做有针对性的回归。下表是待填写的场景，未填不代表否定用户已报告的总体使用反馈。

| 场景 | 预期 | 新变更验收状态 |
| --- | --- | --- |
| 导入与刷新 36 个资源、插件、图标 | URL/内容完整，无隐式替代 | NOT_RECORDED |
| 清缓存、冷启动、重连 | 分流稳定恢复 | NOT_RECORDED |
| Wi-Fi/蜂窝、IPv4/IPv6 | 记录实际出口和解析路径 | NOT_RECORDED |
| AliDNS DoH 正常 | 记录请求使用的解析器与实际路径 | NOT_RECORDED |
| DoH 故障、App 明文回退关闭 | 不意外降级；记录失败与恢复 | NOT_RECORDED |
| 回退开启的对照组 | 识别明文查询，不能算防泄漏通过 | NOT_RECORDED |
| 节点不可用、bootstrap 故障、UDP 不支持 | 不意外直连或使用其他 DNS | NOT_RECORDED |
| IP 目标 TLS/SNI 与 ECH/非 TLS 对照 | 不作超出可见名称的推断 | NOT_RECORDED |
| 单个广告资源启用 | 精确广告拦截，登录/播放功能正常 | NOT_RECORDED |
| 关闭 Beta-AdBlock-Balanced | 各服务归属恢复，不强制直连 | NOT_RECORDED |
| AdBlock 组选择 Proxy | 明确是通用代理放行，不能误作恢复服务分流 | NOT_RECORDED |
| CRL/OCSP、验证码、Statsig 功能配置 | 证书检查与功能可用，遥测按决定处理 | NOT_RECORDED |
| Apple 组切换、更新/iCloud/推送/证书 | AppleOTA 跟随所选 Apple 策略 | NOT_RECORDED |
| 国内银行/支付/地图、微信 | 必要请求和跳转正常 | NOT_RECORDED |
| 国际 WeChat 与未知 .cn | 根据明确规则或 Final，不靠品牌/TLD 强制直连 | NOT_RECORDED |
| Steam 登录/商店/社区/全球内容/境内 CDN | 策略和下载符合预期，地区需实测 | NOT_RECORDED |
| AI 登录/API/附件/语音/验证码 | AI 与共享依赖在指定节点下功能正常 | NOT_RECORDED |
| 流媒体、社交媒体上传和 Abema | 测试实际播放与依赖，不只打开首页 | NOT_RECORDED |
| 同条件性能对照 | 仅记录实际测得的延迟/错误率/资源占用 | NOT_MEASURED |

记录测试日期、精确配置 SHA、设备/iOS/Loon Build、网络与节点协议；公开资料脱敏，不提交节点密码、个人 IP、Cookie、原始 HAR 或私人 DNS 标识。首次结构变化观察期为七天，记录真实起止时间，不补写未来日期。

NovaXNS 按用户最新要求延期，本轮四组云端过滤对照为 NOT_APPLICABLE，不是 PASS。
