#!/usr/bin/env python3
"""Review-only contact sheets of App Store icons, from iTunes artwork URLs.
Never touches main configuration or the icons directory.
"""
import io, json, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import requests

entries=json.loads(Path("reviews/APP_STORE_ICON_AUDIT_2026-10-18.json").read_text(encoding="utf-8"))["entries"]
assert len(entries)==24
outdir=Path("reviews")
outdir.mkdir(exist_ok=True)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
bold=ImageFont.truetype(FONT,19)
small=ImageFont.truetype(FONT,14)
s=requests.Session()
s.headers.update({"User-Agent":"Mozilla/5.0 (compatible; LoonRoutingDNSIconReview/1.0)"})
thumbnails=[]
failed=[]
for e in entries:
    url=e.get("artwork","")
    if url.endswith(".jpg"): url=url[:-4]+".png"
    try:
        r=s.get(url,timeout=40);r.raise_for_status()
        src=Image.open(io.BytesIO(r.content)).convert("RGB")
        src.thumbnail((512,512),Image.Resampling.LANCZOS)
        thumbnails.append(src)
    except Exception as error:
        failed.append((e["policy"],str(error)))
        thumbnails.append(None)
    time.sleep(.15)

CW,CH=148,143
cols,rows=6,4
pad=24;top=78
full_w=cols*CW+pad*2
full_h=top+rows*CH+pad+40

def build(theme):
    dark=theme=="dark"
    bg="#18191D" if dark else "#F2F3F7"
    card="#272930" if dark else "#FFFFFF"
    label="#EDEFF3" if dark else "#1B2230"
    paper=Image.new("RGB",(full_w,full_h),bg)
    draw=ImageDraw.Draw(paper)
    draw.text((pad,20),f"Official App Store artwork / {theme.title()} UI",font=bold,fill=label)
    draw.text((pad,47),"24 policies | 512x512 source | 84px preview",font=small,fill=label)
    for i,(e,img) in enumerate(zip(entries,thumbnails)):
        col,row=i%cols,i//cols
        x,y=pad+col*CW,top+row*CH
        draw.rounded_rectangle((x,y,x+CW-12,y+CH-10),12,fill=card)
        if img:
            icon=img.resize((84,84),Image.Resampling.LANCZOS)
            # Preview Apple's expected rounded display. Does not modify or save the source artwork.
            mask=Image.new("L",(84,84),0)
            md=ImageDraw.Draw(mask)
            md.rounded_rectangle((0,0,83,83),radius=17,fill=255)
            paper.paste(icon,(x+26,y+8),mask)
        name=e["policy"] if e["policy"]!="AnimeCrazy" else "AnimeCrazy (TW)"
        if name=="PrimeVideo": name="Prime Video"
        if name=="Linkedin": name="LinkedIn"
        if name=="Whatsapp": name="WhatsApp"
        draw.text((x+11,y+104),name,font=small,fill=label)
    draw.text((pad,full_h-33),"Design reference only: titles and artwork URLs are sourced from the Apple iTunes API.",font=small,fill=label)
    file=outdir/f"APP_STORE_24_{theme.upper()}_REVIEW.png"
    paper.save(file,optimize=True)
    print(str(file),file.stat().st_size)

build("light");build("dark")
report=[
"# 官方 App Store 24 枚图标并排参照（2026-10-18）","",
"本审核为辨识度和视觉语言对照，不代表商标或素材再发布授权。图片均以 Apple iTunes Search API 所返回的应用图标为来源。",
"",
"![24 official apps on light UI](./APP_STORE_24_LIGHT_REVIEW.png)","",
"![24 official apps on dark UI](./APP_STORE_24_DARK_REVIEW.png)","",
"## 观察的共同设计原则",
"",
"- 同样采用圆角方形显示范围，但品牌之间**不共用同一种渐变模板**。",
"- 每个品牌通常有自己稳定的识别锚点：几何标记、单字母、拟物图形或字标，依其品牌而定。",
"- 图标设计**不强制统一主色**；把颜色限制在每个品牌自己的系统之内，更容易识别。",
"- 留白比例并非完全一致，取决于主体本身的外形。不能用相同百分比放大所有图形。",
"- 有的品牌本身就使用渐变，但渐变用于识别品牌而不是装饰背景。",
"- 不应以纯背景边缘采样低对比度就判定 App Store 图标有显示缺陷，圆角掩膜、外层轮廓和主体才决定小尺寸识别。",
"",
"## 对自制图标的设计修正",
"",
"- Proxy：用一个明确的转发/中继符号，不再与 Auto 共用环形箭头。",
"- Auto：明确区别于 Proxy，采用选择/测试/优选语义，而非重复循环图形。",
"- Fallback：保持主路与备路的层级关系，避免看起来像普通分享或分支。",
"- AdBlock：简化盾牌内的重叠禁止符号，减少双重视觉中心。",
"- Final：使用结果/终点语义，不做与常见地图定位图标雷同的长路径。",
"- AI：选择独立的 AI 服务聚合概念，减少与插件控制台同源的芯片与线路形态。",
"- Google / Microsoft / Apple：以官方品牌素材为准，不做不准确的伪立体商标改绘。",
"- Console：设计为 Loon Routing DNS 的唯一品牌主标，不能只是另一张带滑块的蓝色策略组图标。",
"",
"## 审核状态",
"",
f"本次预览成功下载 {len(entries)-len(failed)}/{len(entries)} 张官方候选图标。","",
"这些图标图纸是设计参照文件，不修改正式配置，不改变线上图标。",
]
if failed:
    report+=["","下载失败："]+[f"- {name}: {error}" for name,error in failed]
(outdir/"APP_STORE_VISUAL_REFERENCE_2026-10-18.md").write_text("\n".join(report)+"\n",encoding="utf-8")
