#!/usr/bin/env python3
"""One-shot App Store icon candidate QA. Does not write images or modify Loon configuration.
Fetched artwork is temporary; the public report contains source links and measurements only.
"""
from __future__ import annotations
import datetime as dt
import io
import json
import time
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlencode
import requests
from PIL import Image, ImageStat

REPO = "https://github.com/YohakuSama/loon-routing-dns"
CANDIDATES = [
    ("YouTube", 544007664, "us"), ("Netflix", 363590051, "us"),
    ("Disney", 1446075923, "us"), ("PrimeVideo", 545519333, "us"),
    ("Spotify", 324684580, "us"), ("TikTok", 835599320, "us"),
    ("Twitch", 460177396, "us"), ("HBO", 1666653815, "us"),
    ("Abema", 1074866833, "jp"), ("Dazn", 1129523589, "us"),
    ("BBC", 364147881, "us"), ("AnimeCrazy", 1102650114, "tw"),
    ("Bilibili", 736536022, "cn"), ("Steam", 495369748, "gb"),
    ("Paypal", 283646709, "us"), ("Telegram", 686449807, "us"),
    ("Whatsapp", 310633997, "us"), ("Instagram", 389801252, "us"),
    ("Facebook", 284882215, "us"), ("Twitter", 333903271, "gb"),
    ("Discord", 985746746, "us"), ("Line", 443904275, "gb"),
    ("Reddit", 1064216828, "gb"), ("Linkedin", 288429040, "gb"),
]
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; LoonRoutingDNSIconAudit/1.0)"})

def fetch_json(country, ids):
    url="https://itunes.apple.com/lookup?"+urlencode({"id":",".join(str(i) for i in ids),"country":country,"entity":"software"})
    last=None
    for attempt in range(4):
        try:
            res=session.get(url,timeout=40)
            if res.status_code==429 or res.status_code>=500:
                raise RuntimeError("HTTP "+str(res.status_code))
            res.raise_for_status()
            return res.json()
        except (requests.RequestException,ValueError,RuntimeError) as e:
            last=e
            time.sleep(2**attempt)
    raise RuntimeError(f"lookup for {country} failed: {last}")

def luminance(rgb):
    def comp(v):
        v=v/255
        return v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4
    r,g,b=[comp(x) for x in rgb]
    return 0.2126*r+0.7152*g+0.0722*b

def contrast(a,b):
    l1,l2=sorted((luminance(a),luminance(b)),reverse=True)
    return round((l1+0.05)/(l2+0.05),2)

def probe_icon(url):
    last=None
    for attempt in range(3):
        try:
            resp=session.get(url,timeout=40)
            resp.raise_for_status()
            if len(resp.content)>8_000_000:
                raise RuntimeError("icon too large")
            image=Image.open(io.BytesIO(resp.content))
            image.load()
            rgba=image.convert("RGBA")
            w,h=rgba.size
            # Sample colors near left/right mid-edge within the square, before any iOS mask.
            positions=[(int(w*p),int(h*q)) for p,q in ((.025,.50),(.975,.50),(.50,.025),(.50,.975))]
            colors=[rgba.getpixel(pos) for pos in positions]
            opaque=[(r,g,b) for r,g,b,a in colors if a>=245]
            dark=(25,27,31); light=(248,249,250)
            low_dark=min((contrast(c,dark) for c in opaque),default=None)
            low_light=min((contrast(c,light) for c in opaque),default=None)
            center_alpha=rgba.getpixel((w//2,h//2))[3]
            corners=[rgba.getpixel((x,y))[3] for x,y in ((0,0),(w-1,0),(0,h-1),(w-1,h-1))]
            small=rgba.resize((64,64),Image.Resampling.LANCZOS)
            # Do not claim quantitative anti-aliasing quality: inspecting source pixels does not
            # prove icon rendering in Loon is free from jagged edges.
            return {
                "width":w,"height":h,"mode":image.mode,"format":image.format,
                "bytes":len(resp.content),"corner_alpha":corners,
                "center_alpha":center_alpha,"edge_contrast_dark_min":low_dark,
                "edge_contrast_light_min":low_light,
                "visually_inspect":bool(w<512 or h<512 or low_dark is None or low_dark<1.6 or low_light is None or low_light<1.6)
            }
        except Exception as e:
            last=e
            time.sleep(1+attempt)
    raise RuntimeError("download/decode failed: "+str(last))

def main():
    by_region=defaultdict(list)
    for name,app_id,country in CANDIDATES:
        by_region[country].append(app_id)
    metadata={}
    region_errors={}
    for region,ids in by_region.items():
        try:
            data=fetch_json(region,ids)
            for app in data.get("results",[]):
                if app.get("trackId"):
                    metadata[(region,int(app["trackId"]))]=app
        except Exception as err:
            region_errors[region]=str(err)
        time.sleep(0.5)
    output=[]
    for name,app_id,country in CANDIDATES:
        item={"policy":name,"app_id":app_id,"country":country,
              "store":f"https://apps.apple.com/{country}/app/id{app_id}"}
        app=metadata.get((country,app_id))
        if not app and country in region_errors:
            item["status"]="LOOKUP_ERROR"
            item["notes"]=region_errors[country]
        elif not app:
            item["status"]="MISSING"
            item["notes"]="ID not returned by the App Store lookup endpoint in specified storefront"
        else:
            item["app_name"]=app.get("trackName")
            item["developer"]=app.get("sellerName") or app.get("artistName")
            item["current_version"]=app.get("version")
            item["store"]=app.get("trackViewUrl",item["store"])
            item["artwork"]=app.get("artworkUrl512") or app.get("artworkUrl100")
            if not item["artwork"]:
                item["status"]="MISSING_ARTWORK"
            else:
                try:
                    item["metrics"]=probe_icon(item["artwork"])
                    item["status"]="CHECK_VISUAL" if item["metrics"]["visually_inspect"] else "METADATA_OK"
                except Exception as err:
                    item["status"]="IMAGE_ERROR"
                    item["notes"]=str(err)
        output.append(item)
        print(name,item["status"],item.get("app_name"),item.get("metrics",{}).get("width"),flush=True)
    root=Path("reviews")
    root.mkdir(exist_ok=True)
    (root/"APP_STORE_ICON_AUDIT_2026-10-18.json").write_text(
        json.dumps({"date":dt.datetime.now(dt.timezone.utc).isoformat(),"entries":output},
                   ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# App Store 图标候选质量审核（2026-10-18）","",
        "> 本报告为自动化素材预检，不是商标授权审查、iPhone 真机或 Loon 渲染实测。",
        "> 仅临时读取 Apple 返回的远程图像，不将品牌图标复制进本仓库。",
        "",
        "## 标准与限制","",
        "- 当前市场（US/GB/JP/TW/CN）的应用 ID、标题、开发者及图片来源核对。",
        "- 实际图片下载后，验证尺寸不低于 512×512、图片格式及四角 Alpha。",
        "- 对图标上下左右边缘采样，按 WCAG 亮度对比度初步识别可能融入深/浅背景的图片。阈值 1.6 仅用于**触发人工复核**，不是 WCAG 文字合规判定。",
        "- App Store 交付的图标通常是方形原始素材；iOS 圆角是显示裁切效果。Loon 是否额外圆角、是否加边框须真机测试。",
        "- 高分辨率不意味着无锯齿。最终要用 Loon 策略组实际显示尺寸检查锐度。",
        "- Apple iTunes Search API 素材使用条件有限；不能因仓库开源而推断图标允许再分发。",
        "",
        "## 24 个候选结果","",
        "| 策略组 | 官方 App / 开发者 | 图片像素 | 深色边缘最低对比 | 浅色边缘最低对比 | 状态 |",
        "|---|---|---:|---:|---:|---|"]
    for item in output:
        m=item.get("metrics",{})
        dims=f'{m["width"]}×{m["height"]}' if m else "—"
        deep=m.get("edge_contrast_dark_min")
        pale=m.get("edge_contrast_light_min")
        deep=str(deep) if deep is not None else "—"
        pale=str(pale) if pale is not None else "—"
        link=f'[{item["policy"]}]({item["store"]})'
        label=str(item.get("app_name","未取得")).replace("|","/")
        developer=str(item.get("developer","")).replace("|","/")
        lines.append(f'| {link} | {label} / {developer} | {dims} | {deep} | {pale} | {item["status"]} |')
    flags=[x for x in output if x["status"]!="METADATA_OK"]
    lines.extend(["","## 待人工复核或待处理","",
        f"共 {len(flags)}/{len(output)} 个需进一步处理（含无法拉取的情况）。",""])
    for entry in flags:
        flag=entry.get("notes") or ("边缘对比不足或素材尺寸不足，须看实际图标再决定边框/圆角修整" if entry.get("metrics") else "素材未验证")
        lines.append(f'- **{entry["policy"]}**：{entry["status"]} — {flag}')
    lines.extend(["","## 特别说明","",
        "- BBC 的候选是 BBC News，不一定代表 BBC 全部服务；建议确认图标与策略组语义。",
        "- HBO 候选是 HBO Max；如果分流覆盖 Max 与其他 HBO 服务，需要统一名称及应用视觉。",
        "- Netflix、X、Disney、TikTok、Steam 等深色底图标应重点看暗色列表的轮廓；白底图标则看浅色列表。",
        "- 即使全部通过技术预检，也不能自动得出已获权利人商标授权的结论。",
        "",
        f"原始明细：[JSON](./APP_STORE_ICON_AUDIT_2026-10-18.json)。",""])
    (root/"APP_STORE_ICON_AUDIT_2026-10-18.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("Audit finished:",len(output),"candidates",len(flags),"flags")

if __name__=="__main__":
    main()
