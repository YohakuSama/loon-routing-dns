# 服务与分流排查

LoonKit 提供七个常用服务的规则覆盖检查、离线规则匹配分析，以及可选的手动服务连接检查。分析只用于排查，不会修改当前分流、DNS、TUN 或节点设置。

## 1. 检查七个服务的规则归属

通过电脑终端运行（需要 Python 3.10+，无需额外安装软件）：

`python3 scripts/route_diagnostics.py coverage`

检查 Spotify、Twitch、Abema、BBC、Line、Reddit、LinkedIn **当前已登记的主域名**是否进入对应策略组。这不是对 App 所有 API、图片、CDN、直播或登录请求的完整覆盖证明。新增规则仍需先审核，不能只因检查发现某个域名就直接加到正式规则里。

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

工具只显示服务类别、HTTP 状态码段、经过允许名单校验的公开策略名称和数量，不显示原始 URL、路径、查询参数、节点名称、IP、Cookie 或访问令牌。未登记的主机名归入「其他站点」。输入文件默认只在本地读取，不会自动上传；请不要把原始日志分享给其他人。它不会臆测没有记录的请求为何失败。

## 5. 将离线预计命中与脱敏日志关联

`python3 scripts/route_diagnostics.py triage my-export.har`

文本日志可以执行：

`python3 scripts/route_diagnostics.py triage my-requests.txt --text`

结果将每条有效 HTTP 记录的服务类别、离线预计策略、已知导出策略、HTTP 状态码范围和初步排查信号归类计数。可以提示已识别服务是否落入 Final、是否遇到 AdBlock 策略、4xx/5xx 或记录策略与预计策略不一致等情况。

**隐私边界：** 只输出聚合统计，不输出原始域名、URL、路径、查询参数、IP、Cookie、Token、私人节点名称；未知导出策略名统一标为「未知」。处理仍完全离线，单个输入文件最多 10 MiB、至多 10,000 条记录。HAR 的 `_policy` 是非标准扩展字段，不一定代表 Loon 实际命中；文本日志没有该字段时会显示未知。此工具不直接读取 Loon 实时日志，不会根据 HTTP 403、404 或 5xx 武断宣称代理损坏。

## 6. 可选：在 Loon 手动检查服务连接

[安装可选服务诊断插件](../release/Service_Diagnostics.plugin)。

这与正式配置已经内置的「网络辅助」插件相互独立，不必替换原来的插件。检测脚本直接指定同名策略发送请求，**不是读取 Loon 实时规则命中结果**。导入新插件后，在插件参数中选择以下名称之一，再手动运行「服务连通性检测」：

`Spotify`、`Twitch`、`Abema`、`BBC`、`Line`、`Reddit`、`Linkedin`

脚本会通过所选服务的同名策略，依次对主站和一个关联服务端点发起 HTTPS 请求（公开 favicon 地址），分别汇报响应或错误。两次检测在 18 秒的脚本截止时间内进行，不会自动重试。HTTP 401/403/404 等也只能证明端点返回了响应；**不代表登录、播放、地区权限和所有功能正常**。它不会自动定时测试，也不会修改代理设置。检测会向对应服务的主站与关联端点请求公开的 favicon 地址，不发送账号或其他个人资料。诊断显式验证 TLS 证书，遇到证书错误会报告连接失败。

这项可选功能随 main 分支提供；原有 **v6.0.0 Release 附件及内置网络辅助插件不变**。双端点检测尚未做覆盖所有服务和网络的 iPhone 真机验证，因此不能宣称任意网络条件下均可用。

[回到 README](../README.md) · [原有网络与 DNS 诊断](./NETWORK_DIAGNOSTICS.md)
