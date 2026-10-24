# Loon App 设置与权限（v6.5.6）

LoonKit 配置文件不能远程更改 iOS VPN 权限、系统证书信任或 Loon App 的所有功能开关。参考 [Loon 配置文档](https://nsloon.app/docs/General/)与[社区功能图](https://raw.githubusercontent.com/luestr/ProxyResource/main/Tool/Loon/Lcf/zh-CN/Resource/ConfigDiagram.png)。

| 功能 | 适合 LoonKit 的设置 | 说明 |
| --- | --- | --- |
| Loon 连接 | 开启 | iOS 首次使用时由用户允许 VPN。 |
| 工作模式 | 自动分流 / Rule | 保证本配置国内直连与海外分流规则有效。 |
| 远程规则与插件 | 启用并刷新 | 36 份固定规则和现有一个网络辅助插件。 |
| 脚本 | 使用网络辅助时开启 | 既有诊断脚本已包含在单个插件内。 |
| Rewrite | 用到可信 Rewrite 时开启 | 当前未新增 Rewrite 规则，不随意加载第三方解密模块。 |
| MitM | 只在确有需求并限定域名时开启 | 安装、信任本机证书需用户操作；避免全局通配 MITM、证书验证绕过。 |
| DNS 域名拒绝 | DNS + LoopbackIP | v6.5.6 已写入配置，不需要为此启用 MitM。 |
| DNS 明文回退 | 用户按隐私/可用性取舍 | 可在 App 关闭回退，但 DoH 故障时可能不能解析。 |
| Wi-Fi 网络共享 | 默认关闭 | 避免无意开放本机代理端口。 |

使用 MITM 不等于广告规则更准确，可能与支付、证书固定和登录应用冲突。对 LoonKit 本次 DNS 拦截变更，无须新增 MITM hostname、CA 私钥或 HTTPS 复写规则。

导入后请核对实际脚本开关、刷新远程资源，并在真机验证 LoopbackIP 拒绝行为。不会把未经用户授权的系统级功能记录为已启用。
