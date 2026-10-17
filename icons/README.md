# Loon Routing DNS 图标资源

此目录托管主配置使用的 **33 个策略组图标** 及插件专属 **Console.png**（共 34 个 512×512 PNG）。

## 正式版图片 URL 缓存修复

Loon 可能缓存旧 `icons/*.png` URL 的图片，因此 **v20261018 正式图标发布目录**固定为 [v20261018/](./v20261018/)。33 个策略组及 Console 插件改为使用 `https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/icons/v20261018/<图标文件名>.png`，与原始素材字节完全一致，但 URL 与之前不同。

本次只解决旧 URL 缓存问题；用户若在 Loon 中使用导入后生成的本地配置，需要重新导入或更新原配置，才能让新的 `img-url` 生效；插件亦需要更新；完整配置同时切换到 `plugins/v20261018/Network_Diagnostics.plugin`，避免插件文件也停留在旧缓存。若仍有旧图标，检查当前有效配置的图标 URL，而不是仅更新远程规则列表。

今后内容更新应采用新的版本目录并修改 URL，不能在同一路径反复覆盖文件期待客户端立即刷新。

## 设计与对应关系

- **24 枚应用图标**：来自对应地区的 Apple App Store 应用图标，每张以 512px PNG 素材处理圆角并固定到本仓库，保留品牌原有颜色，不额外改变商标本体。
- **9 枚非单一应用策略组**：Proxy、Auto、Fallback、AdBlock、Final、AI、Google、Microsoft、Apple。包含 6 枚原创功能符号和 3 枚以品牌向量标志为参照制作的图标。
- **Console.png**：Loon Routing DNS 自制插件 Logo，与九枚策略组图标使用相同的 SVG 来源管理方式。
- `動畫瘋` 对应 `AnimeCrazy.png`，其余策略组 PNG 与策略组名称一致。
- **Bilibili** 使用 <https://apps.apple.com/sg/app/id1517062289>，开发者 BILIBILI SINGAPORE PTE. LTD.，不使用中国大陆的节日/活动角标版本。

所有素材清单、国家/地区、App ID、版本来源和 PNG SHA256 见 [ICON_SOURCE_REPORT.json](./ICON_SOURCE_REPORT.json)。

自制的十枚 SVG 源文件保存在 [source/](./source/)。如需显式更新 App Store 图标，在开发分支执行：

```bash
python -m pip install requests pillow cairosvg
python scripts/build-appstore-icons.py --refresh-app-store
```

**注意**：这项脚本会从 Apple 获取新的应用版本图标，可能随着商标改版而发生变化。请在独立分支检查预览后再合并，不会定期自动替换正式图标。历史 `scripts/generate-policy-icons.mjs` 现仅为受保护的更新入口，避免旧式透明商标覆盖本次资源。

## 来源、权利与免责声明

项目不是 Apple、Loon、Bilibili 或其他品牌的官方产品，也未获得品牌官方认证。商标、应用图标、官方视觉元素仍属于各权利人。公开应用图标、开源或非商业性质**并不自动构成再分发许可**；如有权利问题，需依据权利人要求删除、调整或改为不含商标的自制替代图标。此套资源是本项目用途的视觉方案，不应冒用为各品牌官方背书。

修改仅限 icon 文件、图标说明和生成脚本；原有代理、DNS、规则、插件行为与 Loon 配置逻辑不变。最终 Loon 实机渲染效果请在更新后核验。
