# LoonKit v6.1.0

优化七项常用服务分流，并为服务连接和故障排查提供更方便的工具。

## 主要功能

- **七项服务分流优化**：在 Spotify、Twitch、Abema、BBC、Line、Reddit 和 LinkedIn 的现有基础规则上，新增 62 条精确范围的域名后缀匹配，涵盖部分官网、图片和服务入口。
- **手动服务诊断**：正式配置集成「服务连通性诊断」插件，可从插件菜单选择服务，分别查看主站和关联端点的 HTTPS 连接结果；不会定时运行或自动切换节点。
- **排查工具**：提供服务规则覆盖查询、离线规则命中模拟、候选覆盖审计与本地脱敏日志故障分类。
- **原有功能继续提供**：AI、国内直连、流媒体策略组、广告拦截、DNS 及网络辅助保持可用。

## 安装与升级

1. [下载 LoonKit.lcf](https://github.com/YohakuSama/loonkit/releases/download/v6.1.0/LoonKit.lcf)。
2. 从旧版升级前备份个人节点、订阅和自定义配置，再导入新版。
3. 添加自己的代理节点或订阅，选择适合的策略。
4. 在 Loon 中刷新远程规则与插件资源；需要时手动运行「服务连通性诊断」。

**LoonKit 不提供代理节点。** 新增规则不代表所有 API、登录、视频播放或地区限制必然正常。插件的连接结果和离线命中模拟也不能替代实际请求日志。

[使用说明](https://github.com/YohakuSama/loonkit#readme) · [配置校验](https://github.com/YohakuSama/loonkit/blob/main/docs/RELEASE_CHECKSUM_v6.1.0.md) · [问题反馈](https://github.com/YohakuSama/loonkit/issues) · [第三方许可](https://github.com/YohakuSama/loonkit/blob/main/docs/THIRD_PARTY_NOTICES.md)
