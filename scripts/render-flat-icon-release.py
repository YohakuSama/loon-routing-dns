#!/usr/bin/env python3
"""Render the 9 approved flat icon masters for versioned Loon release.
Original review PNGs are not assumed to be byte-identical; SVGs are pinned.
The remaining 25 icons are copied unchanged from v20261018.
"""
from __future__ import annotations
import hashlib,io,json
from pathlib import Path
from PIL import Image
import cairosvg

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"icons"
DEST=DIR/"v20261018r2"
NINE=("Proxy","AI","Console","Spotify","Netflix","Telegram","Discord","Instagram","TikTok")
BASE=("Spotify","Netflix","Telegram","Discord","Instagram","TikTok")
REFHASH={
    "Spotify":"9d8e8b9d94c51207f7871b5138d880cdcbe411a642c3d9227cb840b8443cf91f",
    "Netflix":"7d47e5e4a638e778896b4c9b496314ec7d960eea3e5a8e41d850d513666777fe",
    "Telegram":"ea82567e78dc868c54dbaeaf481d636dce4855aeb7ab01e06538581ee09399aa",
    "Discord":"dbe23463cd518265baefab3cf445db78db14414d059831aaf3962f7c1e6e4724",
    "Instagram":"a938fb88d9cd93bd41e6be20646e0bc7b7f99cfba0ff93953c8dfc8b7e37bcf5",
    "TikTok":"8d8777a1dd49d82372526409df1c453d04ab01686630112190776817436dc604"
}
SOURCES={
    "Spotify":"https://github.com/simple-icons/simple-icons/blob/develop/icons/spotify.svg",
    "Netflix":"https://github.com/simple-icons/simple-icons/blob/develop/icons/netflix.svg",
    "Telegram":"https://github.com/glincker/thesvg/blob/main/public/icons/telegram/default.svg",
    "Discord":"https://github.com/simple-icons/simple-icons/blob/develop/icons/discord.svg",
    "Instagram":"https://github.com/simple-icons/simple-icons/blob/develop/icons/instagram.svg",
    "TikTok":"https://github.com/simple-icons/simple-icons/blob/develop/icons/tiktok.svg",
}
def verify_png(path:Path)->None:
    with Image.open(path) as im:
        im.load()
        assert im.format=="PNG" and im.size==(512,512) and im.mode=="RGBA",str(path)
        assert im.getpixel((0,0))[3]==0, str(path)
def main():
    assert DEST.is_dir()
    src={p.stem for p in (DIR/"source").glob("*.svg")}
    assert set(NINE)<=src
    entries=json.loads((DIR/"ICON_SOURCE_REPORT.json").read_text(encoding="utf-8"))
    assert len(entries)==34
    names={e["file"].removesuffix(".png") for e in entries}
    assert len(names)==34 and set(NINE)<=names
    stored={p.stem for p in DEST.glob("*.png")}
    assert stored==names,(names-stored,stored-names)
    for name in BASE:
        sha=hashlib.sha256((DIR/"source"/(name+".svg")).read_bytes()).hexdigest()
        if sha!=REFHASH[name]:
            raise RuntimeError(f"{name}: SVG differs from previously reviewed master {sha}")
    for name in NINE:
        source=DIR/"source"/f"{name}.svg"
        source_bytes=source.read_bytes()
        raw=cairosvg.svg2png(bytestring=source_bytes,output_width=1024,output_height=1024)
        image=Image.open(io.BytesIO(raw)).convert("RGBA")
        image=image.resize((512,512),Image.Resampling.LANCZOS)
        output=io.BytesIO()
        image.save(output,format="PNG",optimize=True)
        for path in (DIR/f"{name}.png", DEST/f"{name}.png"):
            path.write_bytes(output.getvalue())
            verify_png(path)
        entry=next(e for e in entries if e["file"]==name+".png")
        # Remove Apple artwork pointers: these nine are NOT Apple App Store artworks.
        for k in ("artworkUrl","appId","storeFront","appTitle","developer","appStore"):
            entry.pop(k,None)
        entry["source"] = ("Brand vector adaptation (not App Store artwork)"
            if name in BASE else "Loon Routing DNS original vector design")
        entry["sourceSvg"]=f"icons/source/{name}.svg"
        if name in BASE:
            entry["brandMarkReference"]=SOURCES[name]
        else:
            entry.pop("brandMarkReference",None)
        entry["sha256"]=hashlib.sha256(output.getvalue()).hexdigest()
        print(f"{name}: rendered 512x512 PNG",flush=True)
    for e in entries:
        name=e["file"]
        release=DEST/name
        original=DIR/name
        verify_png(release)
        verify_png(original)
        assert release.read_bytes()==original.read_bytes(),name
        actual=hashlib.sha256(release.read_bytes()).hexdigest()
        assert e.get("sha256")==actual,(name,actual)
    assert len([x for x in entries if x["source"]=="Apple App Store official app artwork"])==18
    assert next(e for e in entries if e["file"]=="HBO.png")["source"]=="Apple App Store official app artwork"
    assert next(e for e in entries if e["file"]=="Bilibili.png")["appId"]==1517062289
    (DIR/"ICON_SOURCE_REPORT.json").write_text(
        json.dumps(entries,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS: 34 versioned PNGs, 9 newly rendered, 25 unchanged, HBO official preserved.")
if __name__=="__main__":main()
