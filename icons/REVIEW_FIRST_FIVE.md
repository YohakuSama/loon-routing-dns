# 首批 5 枚图标：仓库风格一致性修订（审核候选）

**不影响当前 main / Loon 配置。** 此目录 `icons/review/` 只放候选 PNG，正式 `icons/{Name}.png` 暂不替换。审核后另开独立合并步骤。

## 为什么重做
上一版的冰蓝渐变、玻璃光泽、浮雕立体效果与仓库中原有 33 枚扁平图标不一致。第一批重绘恢复原项目的扁平化语言，解决深色卡片里的黑色符号无法看清、缩小边缘不清晰的问题。

依据仓库 [现有图标规范](../README.md) 和 [旧版生成器](../../scripts/generate-policy-icons.mjs)：

- **尺寸：512×512 RGBA、透明底，不带 App 背景板**；不再使用 256 像素。
- **单色简洁**：无高光、浮雕、阴影、渐变，不影响其它 28 枚图标。
- **品牌轮廓优先**：Apple、HBO、DAZN、X 保留字形特征，浅色主体配细深灰轮廓增强深色/浅色兼容性。
- **Proxy 保持蓝色系**，但改成简单的三节点网络连接符号，避免与 Auto/Fallback 同样使用循环箭头。
- **图形先用 SVG 绘制**，再 4 倍超采样导出 PNG，减轻锯齿。

审核顺序：先看 [预览图](./review/review-preview.png)，再用 Loon 真机分别检查深色、浅色，以及策略列表小尺寸下是否清晰。图片预览为 UI 模拟而不是真实 Loon 截图。

### 生成流程

```bash
python3 -m pip install CairoSVG==2.7.1 Pillow==11.3.0
python3 scripts/render_review_icons.py
```

矢量源：`icons/svg/Proxy.svg`、`Apple.svg`、`HBO.svg`、`Dazn.svg`、`Twitter.svg`。生成文件：`icons/review/*.png`，不覆盖 `icons/*.png`。

这批图标是本项目用来替换原来的有对比度问题的标志图稿，非品牌官方素材。品牌标志与名称仍属于相应权利人。
