#!/usr/bin/env python3
"""Test PNG artwork endpoint against Apple's official 512px JPEG, without distributing imagery."""
import io, json, time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import requests
from PIL import Image, ImageChops, ImageStat

REPORT=Path("reviews/APP_STORE_ICON_AUDIT_2026-10-18.json")
SAVE=Path("reviews/APP_STORE_ICON_FORMAT_TEST_2026-10-18.md")
data=json.loads(REPORT.read_text(encoding="utf-8"))
session=requests.Session()
session.headers["User-Agent"]="Mozilla/5.0 (compatible; LoonRoutingDNSIconAudit/1.0)"
lines=[
    "# Apple 官方图标 PNG 与 JPEG 素材格式对照（2026-10-18）","",
    "从官方 iTunes Search API 的 artworkUrl512 路径出发，将输出后缀改成 `png` 测试 Apple 的图像转换端点。",
    "这些结果只说明素材 API 返回的图像格式，**不能证明 Loon 客户端的显示质量**，不推导授权状态。",
    "",
    "| 图标 | JPEG | PNG 接口 | PNG 图像模式 | RGB 平均像素差 | 备注 |",
    "|---|---:|---:|---|---:|---|"
]
ok=0
for entry in data["entries"]:
    name=entry["policy"]
    jpeg=entry.get("artwork")
    if not jpeg:
        lines.append(f"| {name} | 缺失 | 未测试 | — | — | 无官方来源 |")
        continue
    png=jpeg[:-4]+".png" if jpeg.endswith(".jpg") else jpeg
    try:
        j=session.get(jpeg,timeout=30)
        j.raise_for_status()
        p=session.get(png,timeout=30)
        p.raise_for_status()
        ji=Image.open(io.BytesIO(j.content))
        pi=Image.open(io.BytesIO(p.content))
        ji.load();pi.load()
        if pi.format!="PNG" or pi.width<512 or pi.height<512:
            raise ValueError(f"unexpected PNG response: {pi.format} {pi.size}")
        diff=ImageStat.Stat(ImageChops.difference(ji.convert("RGB"),pi.convert("RGB"))).mean
        score=round(sum(diff)/3,3)
        ok+=1
        note=("明显不同，人工看稿" if score>3 else "有像素差异" if score>.1 else "像素近似")
        lines.append(f'| {name} | {len(j.content)} B | {len(p.content)} B | {pi.mode}, {pi.width}×{pi.height} | {score} | {note} |')
    except Exception as ex:
        lines.append(f'| {name} | {len(j.content) if "j" in locals() else "—"} B | 获取失败 | — | — | {str(ex)[:90].replace("|","/")} |')
    time.sleep(.15)
lines.extend(["",f"**PNG 接口实际验证通过：{ok}/{len(data['entries'])}。**","",
    "注：PNG 的无损编码能避免额外的 JPEG 块状压缩，但如果上游已经有失真，转换成 PNG 不会自动恢复原始细节。建议优先试用有官方授权且质量合格的原始 PNG。",
    ""])
SAVE.write_text("\n".join(lines),encoding="utf-8")
print(f"Verified PNG conversions: {ok}/{len(data['entries'])}")
