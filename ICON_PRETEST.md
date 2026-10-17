# Loon Routing DNS — 33 枚自托管图标预更新测试

**仅供实机验收，不属于正式发布。** 当前基于 v4.4.6 的配置，33 个策略组已在测试分支换用本仓库 `icons/*.png`；DNS、节点相关字段与分流规则保持正式版原样。

## 直接导入测试版配置

复制以下完整 URL 到 Loon → 配置文件 → 从链接导入：

```text
https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/icon-pretest/Loon_Routing_DNS.lcf
```

- [完整测试配置（GitHub 文件，可查看和复制）](./Loon_Routing_DNS.lcf)
- [33 枚图标可视化预览画廊](./icons/README.md)
- [本次图标来源和重绘说明](./icons/ICON_SOURCE_REPORT.json)

**先备份现有配置、个人订阅和手动规则。** 从链接导入的是一份完整配置，不会自动合并你的私人订阅。

## 实机检验要点

1. 策略列表中 33 枚图标能否全部显示，不出现空白、404 或比例变形。
2. Loon 浅色与深色主题下，黑色/深蓝色品牌图标是否仍然清楚。
3. 24–32px 的实际显示尺寸，重点检查 PrimeVideo、HBO、BBC、DAZN、動畫瘋、Abema 等较复杂图形。
4. 切换 Proxy、Auto、Fallback 等策略组，确认原有分流和节点仍正常。
5. Loon 运行模式保持 **RULE**，AliDNS DoH 流量模式使用 **DIRECT**，手动关闭加密 DNS 查询回退（这些设置不由图标测试文件改变）。

**图片来源说明：** 由于当前跨工具二进制上传限制，本次 GitHub 测试分支的图标是依据先前审核的扁平化视觉方向生成的**矢量重制 PNG**，与本地已审核的原始 PNG 文件并非完全相同。它们可以用于验证 Loon 中的排版比例和识别度；如果外形需要调整，可先在此测试分支替换，**不要未经确认合并 main**。

## 回退办法

直接切回 Loon 中原来的正式 v4.4.6 配置。测试分支与 `main` 完全独立，不会自动影响已在使用的正式版。

## 当前状态

- 测试分支：`icon-pretest`
- 策略组：33
- 自托管图标文件：33
- 单张图标：512×512、PNG、透明 RGBA
- 正式主分支：未改图标
- 是否已经通过 iPhone 实机：**否，待使用者验收**
