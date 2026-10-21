# LoonKit v6.3.0

本次重点优化「网络辅助」的操作体验：名称与说明更加统一，服务选择更加直观，检测结果简洁明确。

## 更新内容

- **清晰的工具菜单**：节点信息、网络检测、服务检测，分别对应常用的三种操作。
- **先选服务，再检测**：默认显示「请选择服务」，不再预设 Spotify。可选项附带音乐、直播、视频、资讯、通讯、社区和职场等用途标注。
- **更容易理解的检测结果**：直接显示网站、相关资源和 DNS 解析状态。连接超时、解析失败或服务响应异常时提供简短建议；网站返回 HTTP 404 等状态不再被当成网络中断。
- **保留成熟的分流配置**：26 份固定远程规则、七项服务的精选域名规则、DNS、IPv6、TUN、节点策略及原有图标均不改变。

## 升级方法

1. 备份现有节点订阅及个性化配置。
2. [下载正式配置 LoonKit.lcf](https://github.com/YohakuSama/loonkit/releases/download/v6.3.0/LoonKit.lcf) 并导入 Loon。
3. 刷新「网络辅助」插件及脚本，在插件设置中选择需要检测的服务，再手动运行「服务检测」。

如果 Loon 中曾单独安装过旧的服务诊断插件，请删除那项单独安装的插件，避免重复显示。

服务检测验证的是选定线路的网络响应和 DNS 解析结果，不能代替实际登录、媒体播放、地区权限以及 UDP/IPv6 连接质量测试。

[使用说明](https://github.com/YohakuSama/loonkit#readme) · [文件校验](https://github.com/YohakuSama/loonkit/blob/main/docs/RELEASE_CHECKSUM_v6.3.0.md) · [问题反馈](https://github.com/YohakuSama/loonkit/issues)
