# LoonKit 测试渠道

## v6.5.5 已发布及后续测试

截至 PR #119 准备时，已验收的 beta.4 仍为当前测试版，SHA256 为 `fd1a01c6f8363a5dffaa1db9dbf044014c711fa48ea46e34a7c107180acbe0b7`。[v6.5.5 发布 PR](https://github.com/YohakuSama/loonkit/pull/119) 将该候选确定性迁移到正式配置，未引入任何上游增量或新的 DNS 参数。

发布候选包含独立 `build/baselines/v6.5.4/` 模板，避免根目录正式配置变更之后影响 beta 重新构建。下一轮候选需更新独立 manifest 和审核记录，不得继承本轮总体设备反馈作为新的 PASS。


测试渠道身份以 [beta manifest](../build/beta_manifest.json) 为准；正式入口已采用 v6.5.5，下一轮 beta 保留独立构建和验收。

- 正式入口：https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf
- 测试入口：https://raw.githubusercontent.com/YohakuSama/loonkit/beta/beta/LoonKit.lcf
- 导入前备份个人节点、订阅和 App 开关。公共配置不含节点或私人 DNS。
- DNS 保持默认 AliDNS；推荐的最低客户端沿用 Loon 3.5.1 (983)，新特性仍以实际客户端支持为准。

## beta.4 已实施的变化

1. 合并为一个 Beta-AdBlock-Balanced 远程规则，默认 REJECT。关闭这个资源即可恢复各服务规则；AdBlock 策略中的 Proxy 仅表示“通过通用代理放行”，不能冒充恢复原分流。已移除易造成意外直连的 DIRECT 选项。
2. 旧版所有 26 条本地广告规则已经被原始广告规则集覆盖，合并后去重。排除 crl.microsoft.com、ocsp.godaddy.com 两个证书相关误杀；新增三个有官方用途证据的精确遥测/统计主机，保留验证码、登录和功能配置接口。
3. 公共本地域名规则由 beta.3 的 54 条减为 4 条必要优先例外，其余服务归属交由固定远程规则和生成器管理。保留 Abema 的 9 条域名与 3 条明确国内补充，避免去重后丢失功能。
4. Steam 全球四类后缀归 Steam，13 条境内 CDN 候选保留；仍需用真实下载结果验证地理调度。
5. 从 ChinaDirect 排除 .cn 总后缀、59 条 User-Agent，以及 wechat.com、wechatapp.com 两个缺乏 CN-only 依据的国际服务父域；保留其余 114,775 条和微信国内明确域名。未知目标遵循 Final，不臆造地区。
6. apis.google.com 归 Google；Statsig/验证码/通用 LiveKit 基础设施使用通用 Proxy，避免强行归入 AI 的单独节点；明确 AI 自有域名继续归 AI。
7. AppleOTA 保留全部系统/更新/证书域名，但跟随 Apple 策略组，不再成为绕过用户选择的硬编码 DIRECT。Apple 默认 DIRECT 和 General 中的 real-ip 均保持兼容性基线。
8. AliDNS、IPv4/IPv6、TUN、UDP fallback、节点筛选和现有 33 个策略组保留；sni-sniffing 仍为上一轮已经启用的测试功能，不新增全局 QUIC/IPv6/MITM 限制。

## 构建和验收

配置由 scripts/beta_profile.py 从 v6.5.4 冻结历史模板与审核后的策略输入生成；资源必须先提交，再使用真实提交 SHA 生成配置，禁止自引用 SHA。36 份资源均由 scripts/beta_channel.py 校验实际字节、数量和不可变引用，支持 --remote 核对线上资源。

    python3 scripts/beta_assets.py --check
    python3 scripts/beta_domestic_rules.py --check
    python3 scripts/beta_policy_review.py --check
    python3 scripts/beta_channel.py --remote
    python3 scripts/beta_effective_audit.py --output /tmp/beta-effective.json
    python3 -m unittest discover -s tests -p 'test_*.py' -v
    node --test tests/diagnostics.test.cjs

当前离线路由覆盖 58 个独立预期场景，包括全部现有服务类型和关键误杀反例。静态结果不证明登录、支付、播放、DNS 或客户端行为已经通过。

## DNS 与用户反馈

AliDNS 普通服务器 223.5.5.5/223.6.6.6、DoH https://dns.alidns.com/dns-query 和其他 DNS/TUN 设置均未更换。加密 DNS 失败回退是 Loon App 设置，配置不能替用户保证开关状态。UDP/53 劫持也不能证明所有应用的私有解析均被接管。

[已记录此前用户“真机测试未发现问题”的反馈](BETA_OWNER_FEEDBACK.json)。该反馈没有附精确版本/SHA、设备和逐项场景，不能伪造为全部矩阵 PASS；原始用户反馈与本次单次发布批准分别记录，缺少的逐项场景仍不标为完成。NovaXNS 根据用户最新要求延期，不再作为本轮阻塞输入。

## 自动上游更新

见 [自动更新说明](BETA_UPSTREAM_AUTOMATION.md)。候选现在与当前 beta 的全部 33 个来源组比较，覆盖 Spotify、Twitch、Abema、BBC、Line、Reddit、Linkedin，不再只比较旧正式版的 26 组。

只对来源完整、无损解析、无跨策略冲突、数量受限的精确主机新增创建草稿 PR；广告、直连、Apple/Microsoft/AI、共享设施、宽规则、移除和异常变化保留人工审核。正式版运行时仍使用固定资源，不直接跟随可变上游。

## 正式发布和回滚

[发布预检](BETA_PROMOTION_GATE.md)保持先静态、再 GitHub 实时检查的双层门禁。空模板、未来观察日期、错 SHA、伪造 CI 成功和未完成的风险审核都会阻断。默认观察期仍保留七天；本轮依据 [维护者对准确候选的一次性批准](RELEASE_OWNER_DECISION_v6.5.5.json) 直接发布，不声称七天或逐项测试已完成。

出现问题可重新导入正式入口，或使用 [历史测试版引用](../build/beta_history.json) 对应的精确提交。正式发布后才能运行 scripts/beta_cleanup.py --apply，且必须先确认历史固定 URL 的原始字节仍可访问；清理只在实际发布核验后单独审阅，保留所有正式引用与回滚依赖。
