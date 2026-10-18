#!/usr/bin/env python3
"""Download App Store artwork candidates and render contact sheets for human review.

Run after audit_appstore_icons.py; NEVER treats the first search result as verified.
Requires Pillow. Outputs only to a preview folder, never overwrites icons/.
"""
import argparse
import io
import json
import pathlib
import urllib.request
from PIL import Image, ImageDraw

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--audit", default="appstore-icon-audit.json")
    p.add_argument("--output", default="appstore-preview")
    args=p.parse_args()
    data=json.loads(pathlib.Path(args.audit).read_text(encoding="utf-8"))
    out=pathlib.Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    manifest={}
    for name, markets in data["brand_candidates"].items():
        entries=[]
        seen=set()
        for country, matches in markets.items():
            if not isinstance(matches,list):
                continue
            for match in matches:
                tid=match.get("trackId")
                url=match.get("artworkUrl512")
                if not url or not tid or tid in seen:
                    continue
                seen.add(tid)
                entries.append((country,match))
        entries=entries[:12]
        sheet=Image.new("RGB",(800, ((len(entries)+3)//4)*242 or 242),"#eeeeee")
        draw=ImageDraw.Draw(sheet)
        saved=[]
        for i,(country,item) in enumerate(entries):
            try:
                req=urllib.request.Request(item["artworkUrl512"],headers={"User-Agent":"Mozilla/5.0"})
                with urllib.request.urlopen(req,timeout=20) as response:
                    payload=response.read(3_000_000)
                im=Image.open(io.BytesIO(payload)).convert("RGBA")
                im.thumbnail((168,168),Image.Resampling.LANCZOS)
                x=(i%4)*200+16
                y=(i//4)*242+8
                sheet.paste(im,(x,y),im)
                draw.text((x,y+174),f'{country} / {item["trackId"]}',fill="#111111")
                draw.text((x,y+191),item.get("trackName","")[:26],fill="#111111")
                draw.text((x,y+207),item.get("sellerName","")[:26],fill="#333333")
                saved.append(item)
            except Exception as e:
                print(name, item.get("trackId"), "download failed:",str(e))
        sheet.save(out/f"{name}.png")
        manifest[name]=saved
    (out/"candidates.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Generated",len(manifest),"brand candidate contact sheets in",out)
    print("No candidate has been automatically approved or published.")
if __name__=="__main__":
    main()
