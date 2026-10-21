# 服务与分流排查

LoonKit 提供七个常用服务的规则覆盖检查、离线规则匹配分析，以及内置的手动服务检测。分析只用于排查，不会修改当前分流、DNS、TUN 或节点设置。

## 1. 检查七个服务的规则归属

通过电脑终端运行（需要 Python 3.10+，无需额外安装软件）：

`python3 scripts/route_diagnostics.py coverage`

检查 Spotify、Twitch、Abema、BBC、Line、Reddit、LinkedIn **已登记的服务主域名和 v6.1.0 新增的 62 条精选域名**是否进入对应策略组。这不是对 App 所有 API、图片、CDN、直播或登录请求的完整覆盖证明。新增规则仍需先审核，不能只因检查发现某个域名就直接加到正式规则里。

## 2. 审核尚未启用的上游规则（维护者使用）

`python3 scripts/route_diagnostics.py audit`

读取 `rules/inputs/` 已冻结的七个服务上游域名候选，与当前正式规则的预计命中比较，并按「已覆盖」「AdBlock 待审」「落入 Final」「由其他策略处理」统计。每个服务仅显示最多八条供人工审核的示例。IP 网段、USER-AGENT 和其他非域名语义单独计数，不自动推断它们安全或应该启用。

**这不是自动发布命令。** 共享 CDN、广告分析域名、支付及地区服务的处理必须逐项审查；审核结果不会修改 `LoonKit.lcf`、26 份正式规则或 DNS/TUN。

## 3. 查询某个域名或 IP 会进入哪个策略

`python3 scripts/route_diagnostics.py match open.spotify.com`

`python3 scripts/route_diagnostics.py match analytics.spotify.com`

可以查看预计匹配的策略、首条规则及是否还被其他规则覆盖。工具读取当前正式配置的本地规则与固定版本远程规则，按声明顺序推演域名和 IP 的直接匹配。

**注意：** 这是离线推演，不是 Loon 实时请求记录。它不会进行 DNS 解析，不推断 GEOIP、IP-ASN、URL 正则、系统决策或节点可用性；插件额外注入的规则也不在当前分析范围内。实际请求应以 Loon 的请求日志为准。

## 4. 私密日志汇总

在自己的电脑上，对手动导出的 HAR 文件运行：

`python3 scripts/route_diagnostics.py logs my-export.har`

对文本格式请求记录运行：

`python3 scripts/route_diagnostics.py logs my-requests.txt --text`

工具只显示服务类别、HTTP 状态码段、经过允许名单校验的公开策略名称和数量，不显示原始 URL、路径、查询参数、节点名称、IP、Cookie 或访问令牌。不属于已登记主域名或 v6.1.0 精选域名的主机名归入「其他站点」。输入文件默认只在本地读取，不会自动上传；请不要把原始日志分享给其他人。它不会臆测没有记录的请求为何失败。

## 5. 将离线预计命中与脱敏日志关联

`python3 scripts/route_diagnostics.py triage my-export.har`

文本日志可以执行：

`python3 scripts/route_diagnostics.py triage my-requests.txt --text`

结果将每条有效 HTTP 记录的服务类别、离线预计策略、已知导出策略、HTTP 状态码范围和初步排查信号归类计数。可以提示已识别服务是否落入 Final、是否遇到 AdBlock 策略、4xx/5xx 或记录策略与预计策略不一致等情况。

**隐私边界：** 只输出聚合统计，不输出原始域名、URL、路径、查询参数、IP、Cookie、Token、私人节点名称；未知导出策略名统一标为「未知」。处理仍完全离线，单个输入文件最多 10 MiB、至多 10,000 条记录。HAR 的 `_policy` 是非标准扩展字段，不一定代表 Loon 实际命中；文本日志没有该字段时会显示未知。此工具不直接读取 Loon 实时日志，不会根据 HTTP 403、404 或 5xx 武断宣称代理损坏。

## 6. 使用 Loon 内置的解锁检测

LoonKit 已将服务检测整合到[「网络辅助」](../release/Network_Diagnostics.plugin)中，不需要安装第二个插件。

从节点菜单运行「解锁检测」会使用该节点；插件设置中可指定检测策略，也可启用「完整检测」。不需要逐项选择服务。

检测分别使用流媒体标题、地区接口、CDN 地区及服务页面字段，结果区分片库可访问、地区支持、地区受限、接口可访问、无法确认、检测超时与连接异常。仅网站可访问不会被当成已解锁。检测不会修改 DNS 或分流策略，也不能替代账号登录和播放验证。

曾额外安装过旧的独立诊断插件的用户，升级后可在 Loon 中删除旧插件，避免重复入口。

[回到 README](../README.md) · [网络辅助说明](./NETWORK_DIAGNOSTICS.md)
