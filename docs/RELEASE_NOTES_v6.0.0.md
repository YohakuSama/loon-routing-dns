# LoonKit v6.0.0

面向 Loon 的分流配置，提供常用服务独立选路、广告拦截和网络诊断。

## 主要功能

- **精细分流**：26 份固定版本规则，覆盖国内常用网站、AI、流媒体、社交及游戏服务。
- **灵活选路**：33 个策略组，支持手动选择、自动延迟测试和故障回退。
- **广告拦截**：通过 `AdBlock` 在 `REJECT` 和 `DIRECT` 之间切换。
- **网络辅助**：查看节点出口信息，检测直连、代理连接与 DNS 解析状态。
- **DNS 设置**：提供默认解析设置，也可以自行选择 DNS 服务。

## 安装

1. [下载 LoonKit.lcf](https://github.com/YohakuSama/loonkit/releases/download/v6.0.0/LoonKit.lcf)。
2. 备份已有 Loon 配置后导入文件。
3. 添加自己的代理节点或订阅，并在策略组中选择使用的线路。
4. 刷新远程规则和插件资源。

**LoonKit 不提供代理节点或节点订阅。**

[使用说明](https://github.com/YohakuSama/loonkit#readme) · [配置校验](https://github.com/YohakuSama/loonkit/blob/main/docs/RELEASE_CHECKSUM_v6.0.0.md) · [问题反馈](https://github.com/YohakuSama/loonkit/issues) · [开源许可与来源](https://github.com/YohakuSama/loonkit/blob/main/docs/THIRD_PARTY_NOTICES.md)
