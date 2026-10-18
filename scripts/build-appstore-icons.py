#!/usr/bin/env python3
"""Install verified App Store icon artwork beside the ten approved vector masters.

Intended for review/release branch, not as a recurring automatic updater.
Does not change proxy/DNS/rule settings. Network is used only for iTunes artwork.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlencode
import requests
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "icons"
SVG_DIR = DIR / "source"
# Official application identifiers verified against the specified store fronts.
# (Policy name, iTunes application ID, store front, expected publisher hint)
APPS = [
    ("YouTube",544007664,"us","google"),
    ("Netflix",363590051,"us","netflix"),
    ("Disney",1446075923,"us","disney"),
    ("PrimeVideo",545519333,"us","amzn"),
    ("Spotify",324684580,"us","spotify"),
    ("TikTok",835599320,"us","tiktok"),
    ("Twitch",460177396,"us","twitch"),
    ("HBO",1666653815,"us","warner"),
    ("Abema",1074866833,"jp","abema"),
    ("Dazn",1129523589,"us","dazn"),
    ("BBC",364147881,"us","bbc"),
    ("AnimeCrazy",1102650114,"tw","oneup"),
    # 国际版 Bilibili：新加坡开发者，不是带国区活动角标的版本。
    ("Bilibili",1517062289,"sg","bilibili singapore"),
    ("Steam",495369748,"gb","valve"),
    ("Paypal",283646709,"us","paypal"),
    ("Telegram",686449807,"us","telegram"),
    ("Whatsapp",310633997,"us","whatsapp"),
    ("Instagram",389801252,"us","instagram"),
    ("Facebook",284882215,"us","meta"),
    ("Twitter",333903271,"gb","twitter"),
    ("Discord",985746746,"us","discord"),
    ("Line",443904275,"gb","ly corporation"),
    ("Reddit",1064216828,"gb","reddit"),
    ("Linkedin",288429040,"gb","linkedin"),
]
LOCAL = ("Proxy","Auto","Fallback","AdBlock","Final","AI","Google","Microsoft","Apple","Console")
GROUPS = {n for n,_,_,_ in APPS} | (set(LOCAL)-{"Console"})
assert len(APPS)==24 and len(GROUPS)==33 and len(LOCAL)==10

def download(session: requests.Session, url: str) -> bytes:
    err = None
    for tries in range(4):
        try:
            response=session.get(url, timeout=40)
            response.raise_for_status()
            if not 1000 <= len(response.content) <= 8_000_000:
                raise ValueError("unexpected image byte count")
            return response.content
        except (requests.RequestException, ValueError) as exc:
            err=exc
            import time
            time.sleep(1.5*(tries+1))
    raise RuntimeError("artwork fetch failed") from err

def official_art(session, name, app_id, country, publisher):
    url="https://itunes.apple.com/lookup?"+urlencode({"id":app_id,"country":country,"entity":"software"})
    result=session.get(url,timeout=35)
    result.raise_for_status()
    matches=[x for x in result.json().get("results",[]) if x.get("trackId")==app_id]
    if len(matches)!=1:
        raise RuntimeError(f"{name}: application ID {app_id} missing/ambiguous in {country}")
    meta=matches[0]
    seller=(meta.get("sellerName") or meta.get("artistName") or "").lower()
    if publisher not in seller:
        raise RuntimeError(f"{name}: developer mismatch, expected {publisher!r}, got {seller!r}")
    artwork=meta.get("artworkUrl512")
    if not artwork:
        raise RuntimeError(f"{name}: App Store does not provide 512px artwork")
    if not artwork.startswith("https://is") or ".mzstatic.com/" not in artwork:
        raise RuntimeError(f"{name}: unexpected non-Apple artwork host")
    # Prefer Apple's losslessly delivered PNG. Never save JPEG renamed as PNG.
    png_url=artwork[:-4]+".png" if artwork.lower().endswith(".jpg") else artwork
    image_raw=download(session,png_url)
    original=Image.open(io.BytesIO(image_raw))
    original.load()
    if original.size!=(512,512) or original.format!="PNG":
        raise RuntimeError(f"{name}: invalid asset {original.format} {original.size}")
    return meta,png_url,original.convert("RGBA")

def mask_app(image):
    """One iOS-like rounded rectangle mask; four-times antialiasing at 512."""
    h=4
    large=Image.new("L",(512*h,512*h),0)
    draw=ImageDraw.Draw(large)
    draw.rounded_rectangle((0,0,512*h-1,512*h-1),radius=110*h,fill=255)
    alpha=large.resize((512,512),Image.Resampling.LANCZOS)
    rgba=image.copy()
    # Avoid two rounds of resampling on the already-sharp official app artwork.
    rgba.putalpha(alpha)
    return rgba

def check_final_icons(expected):
    from io import BytesIO
    for policy in expected:
        p=DIR / f"{policy}.png"
        if not p.is_file():
            raise RuntimeError(f"missing icon {p}")
        im=Image.open(p)
        im.load()
        if im.size!=(512,512) or im.format!="PNG":
            raise RuntimeError(f"bad PNG {p}: {im.size} {im.format}")
        if im.mode!="RGBA" or im.getpixel((0,0))[3]!=0:
            raise RuntimeError(f"bad transparent corner {p}")

def check_config():
    text=(ROOT/"Loon_Routing_DNS.lcf").read_text(encoding="utf-8")
    groups=text.split("[Proxy Group]",1)[1].split("[Remote Rule]",1)[0]
    entries=re.findall(r"(?m)^([^#\s][^=\n]*?)\s*=\s*(?:select|url-test|fallback),[^\n]*img-url\s*=\s*(\S+)",groups)
    names={name.strip() for name,_ in entries}
    if len(entries)!=33 or names!={("動畫瘋" if x=="AnimeCrazy" else x) for x in GROUPS}:
        raise RuntimeError(f"Expected 33 unique strategy groups, got {len(entries)}: {names ^ GROUPS}")
    for group, link in entries:
        filename=("AnimeCrazy" if group.strip()=="動畫瘋" else group.strip())+".png"
        expected_version="v20261018r3" if filename=="HBO.png" else "v20261018r2"
        expected_icon="https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/icons/"+expected_version+"/"+filename
        if link.rstrip(",")!=expected_icon:
            raise RuntimeError(f"unexpected strategy icon link: {group} {link}")
    plugin=(ROOT/"plugins/Network_Diagnostics.plugin").read_text()
    pinned=(ROOT/"plugins/v20261018r10/Network_Diagnostics.plugin").read_text()
    if pinned!=plugin:
        raise RuntimeError("Published plugin differs from standalone entry")
    if "#!icon = https://raw.githubusercontent.com/YohakuSama/loon-routing-dns/main/icons/v20261018r2/Console.png" not in plugin:
        raise RuntimeError("Console plugin icon link changed unexpectedly")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--refresh-app-store", action="store_true", help="generate local icon previews for review")
    parser.add_argument("--check-config", action="store_true", help="validate current versioned icon and plugin links without network requests")
    args=parser.parse_args()
    if args.check_config:
        check_config()
        print("Icon and plugin references are consistent")
        return
    if not args.refresh_app_store:
        parser.error("Requires --refresh-app-store; avoid inadvertently replacing pinned official artwork.")
    check_config()
    for name in LOCAL:
        if not (SVG_DIR/f"{name}.svg").is_file():
            raise RuntimeError(f"Missing custom vector {name}.svg")
    session=requests.Session()
    session.headers.update({"User-Agent":"LoonRoutingDNSIconRelease/1.0 (design-review; 24 public App Store listings)"})
    done=[]
    temp={}
    for name,app_id,country,expected_publisher in APPS:
        metadata,url,im=official_art(session,name,app_id,country,expected_publisher)
        pic=mask_app(im)
        buff=io.BytesIO()
        pic.save(buff,format="PNG",optimize=True)
        final=buff.getvalue()
        temp[name]=final
        done.append({
            "name":("動畫瘋" if name=="AnimeCrazy" else name),
            "file":name+".png",
            "source":"Apple App Store official app artwork",
            "appId":app_id,"storeFront":country,
            "developer":metadata.get("sellerName") or metadata.get("artistName"),
            "appTitle":metadata.get("trackName"),
            "appStore":metadata.get("trackViewUrl"),
            "artworkUrl":url,
            "sha256":hashlib.sha256(final).hexdigest(),
        })
        print(f"[appstore] {name}: 512x512 PNG ({len(final)} bytes); {metadata.get('trackName')}",flush=True)
    # Local unversioned previews are ignored by git; publishing requires a reviewed versioned directory.
    for name,raw in temp.items():
        (DIR/f"{name}.png").write_bytes(raw)
    # Generate vector icons from the checked-in SVG using CairoSVG for 512px.
    import cairosvg
    for name in LOCAL:
        svg=(SVG_DIR/f"{name}.svg").read_bytes()
        data=cairosvg.svg2png(bytestring=svg,output_width=512,output_height=512)
        (DIR/f"{name}.png").write_bytes(data)
        done.append({
            "name":name,"file":name+".png","source":"project vector artwork" if name not in ("Google","Microsoft","Apple") else "brand mark based on public vector geometry",
            "sourceSvg":f"icons/source/{name}.svg",
            "sha256":hashlib.sha256(data).hexdigest()
        })
    check_final_icons(GROUPS|{"Console"})
    if len({x["file"] for x in done})!=34:
        raise RuntimeError("Invalid icon release set: expected 34 PNGs")
    (DIR/"ICON_SOURCE_REPORT.json").write_text(json.dumps(done,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SUCCESS: 24 official App Store PNGs + 10 custom PNGs, 33 policy groups + Console")
if __name__=="__main__":
    main()
