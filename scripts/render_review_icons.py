#!/usr/bin/env python3
"""Render review-only Loon icons from source SVG. No production icons overwritten."""
from pathlib import Path
from io import BytesIO
import cairosvg
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
SVG=ROOT/"icons"/"svg"
OUT=ROOT/"icons"/"review"
NAMES=("Proxy","Apple","HBO","Dazn","Twitter")
OUT.mkdir(parents=True,exist_ok=True)
for name in NAMES:
    markup=(SVG/f"{name}.svg").read_bytes()
    rgba=Image.open(BytesIO(cairosvg.svg2png(bytestring=markup,
                                             output_width=2048,
                                             output_height=2048))).convert("RGBA")
    rgba=rgba.resize((512,512),Image.Resampling.LANCZOS)
    assert rgba.getbbox(),name+" is empty"
    assert rgba.getpixel((0,0))[3]==0,name+" has opaque background"
    rgba.save(OUT/f"{name}.png",optimize=True)

# A static review preview, not a substitute for a live iPhone test.
canvas=Image.new("RGB",(1000,920),"#101123")
draw=ImageDraw.Draw(canvas)
font="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
bold="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
heading=ImageFont.truetype(bold,26); regular=ImageFont.truetype(font,18)
draw.text((48,30),"Loon - first five icon review",font=heading,fill="#F6F7FC")
for i,name in enumerate(NAMES):
    y=90+i*139
    draw.rounded_rectangle((32,y,968,y+125),radius=25,fill="#24253A")
    icon=Image.open(OUT/f"{name}.png").convert("RGBA").resize((54,54),Image.Resampling.LANCZOS)
    canvas.paste(icon,(77,y+34),icon)
    draw.text((162,y+29),name,font=heading,fill="#FFFFFF")
    draw.text((162,y+75),"DIRECT" if name=="Apple" else "Proxy",font=regular,fill="#B2B5C5")
    draw.text((818,y+53),"select",font=regular,fill="#ADB2C4")

for j,(bg,title) in enumerate((("#24253A","Dark mode"),("#F3F4F7","Light mode"))):
    x=32+j*486
    draw.rounded_rectangle((x,802,x+449,900),radius=17,fill=bg)
    draw.text((x+16,809),title,font=regular,fill="#FFFFFF" if j==0 else "#272A36")
    for i,name in enumerate(NAMES):
        icon=Image.open(OUT/f"{name}.png").convert("RGBA").resize((34,34),Image.Resampling.LANCZOS)
        canvas.paste(icon,(x+17+i*85,852),icon)
canvas.save(OUT/"review-preview.png",optimize=True)
print("Rendered 5 transparent PNGs at 512x512 with 4x supersampling")
