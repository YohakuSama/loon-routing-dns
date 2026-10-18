# 图标资源

正式配置使用 **33 个策略组图标**和 **1 个插件图标**。所有正式 PNG 均使用固定版本路径，避免同名文件在 Loon 中被旧缓存覆盖。

## 当前版本

- [策略组图标](./v20261018r2/)：除 HBO 外的 32 个策略组。
- [HBO 图标](./v20261018r3/HBO.png)：HBO 策略组。
- [插件图标](./v20261018r2/Console.png)：网络辅助插件。

完整配置的图标路径均指向上述正式文件。图标 SVG 原稿存放在 [source/](./source/)，已发布素材的来源记录见 [ICON_SOURCE_REPORT.json](./ICON_SOURCE_REPORT.json)。

## 更新方式

更换图标时，**不要覆盖已经发布的 URL**。请在独立分支准备新 PNG、检查尺寸与内容，并将新图标发布到新的版本目录后，再更新完整配置中的 `img-url` 或插件的 `#!icon`。

如果手机仍显示旧图标，先确认本地 Loon 配置引用的是新的版本化 URL。仅更新远程分流规则不会改变图标。

## 图标构建工具

仅需核对当前配置引用时：

```bash
python3 scripts/build-appstore-icons.py --check-config
```

若需要重新获取支持的 App Store 图标并生成**本地预览文件**：

```bash
python3 scripts/build-appstore-icons.py --refresh-app-store
```

预览输出为 `icons/*.png`，已加入 `.gitignore`，不会作为正式版自动发布。需人工审核并复制到新版本目录后再更新配置。此工具不会修改 DNS 或分流规则。

历史已发布的版本化图标继续保留，以免仍在使用旧配置的用户遇到资源失效。
