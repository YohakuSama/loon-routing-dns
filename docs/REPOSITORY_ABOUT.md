# GitHub About 配置建议

当前 `YohakuSama/loonkit` 的公开描述已经准确：**适用于 Loon 的分流配置｜国内直连、AI 与流媒体独立选路、广告拦截及网络诊断。需自备代理节点。**

目前 GitHub 仓库的 `Homepage` 和 `Topics` 均为空。以下是与项目实际功能一致的配置，可由有仓库管理权限的账户直接设置：

- **Description：** 保留现有描述，不必反复修改。
- **Website / Homepage：** `https://github.com/YohakuSama/loonkit/releases/latest`（前提是版本 Release 已成功创建；此前可暂留空）。
- **Topics：** `loon`、`loon-configuration`、`proxy-rules`、`routing-rules`、`adblock`、`dns`、`network-diagnostics`。
- **Release：** `v6.0.0`；下载附件应包含 `LoonKit.lcf` 和 `SHA256SUMS`，资源及图标不随此版本发布流程而改变。

设置方法：打开 [仓库首页](https://github.com/YohakuSama/loonkit)，点击 About 右侧齿轮，填写 Description、Website 和 Topics 并保存。

**权限说明：** 本次 GitHub 连接提供文件/PR 操作，但没有修改仓库 About 的专用操作；普通 GitHub Actions `GITHUB_TOKEN` 也不能据此获得仓库 Administration 写入权限。除非实际调用成功，否则不得宣称 About 已经更新。
