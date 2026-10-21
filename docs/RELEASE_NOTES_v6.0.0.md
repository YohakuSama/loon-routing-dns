# LoonKit v6.0.0

**面向 Loon 的完整分流配置**：常用服务独立选路、广告拦截、固定版本远程规则和网络诊断插件。

## 下载与使用

- **正式配置**：[LoonKit.lcf](../LoonKit.lcf)（[Raw 导入链接](https://raw.githubusercontent.com/YohakuSama/loonkit/main/LoonKit.lcf)）
- 导入 Loon 后，**自行添加节点或订阅**，在 `Proxy`、`Auto`、`Fallback` 中选择节点策略，再按需设置服务策略组。
- 从旧配置升级前先备份个人节点及设置；部分已删除的历史 Raw 路径不再提供更新。

## 主要内容

- 26 份固定版本远程规则，覆盖 AI、主流视频与音乐服务、社交平台及国内直连等场景。
- 33 个服务及功能策略组，包括 `Proxy`、`Auto`、`Fallback`、`AdBlock`、`Final`。
- 保留既有 AliDNS DoH 与 IPv4/IPv6 等配置。
- 内置网络辅助插件：节点出口信息、网络与 DNS 连通性诊断；网络切换提醒默认关闭。
- 冻结规则输入及正式输出可由 Production CI 重建并验证。
- 策略及插件图标使用原创中性缩写图案，避免将第三方 App 标志打包为正式资产。

## 使用限制与许可

- 本仓库**不提供代理节点**，需要使用者自备。
- GitHub Raw 不可访问时，部分规则、图标和插件可能无法首次加载。
- DNS 诊断仅反映 Loon 原生解析相关证据，不保证覆盖所有 App 自行建立的加密 DNS。
- LoonKit 有权授权的原创内容采用 [GPL-2.0-only](../LICENSE)。第三方来源遵循各自许可，并保留相关版权、署名与文本；详情见[第三方许可声明](./THIRD_PARTY_NOTICES.md)。
- 本项目与 Loon 官方或第三方平台无关联；包含的品牌图标不代表官方背书或其版权转移。

[更新记录](./CHANGELOG.md) · [安装说明](../README.md) · [规则与来源](../rules/README.md) · [发布检查](./RELEASE_READINESS.md)

> 本次真机测试由项目用户报告已通过，未收集独立的自动化设备日志；代码 CI、规则输入校验与实际 DNS/代理真机运行属于不同的验证范围。历史上游规则的完整逐行权属仍有来源记录限制。
