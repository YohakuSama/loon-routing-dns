#!/usr/bin/env python3
"""Create original, trademark-neutral strategy icons without outside artwork.

All shapes and the bitmap lettering are defined in this file. The letters
are descriptive abbreviations, not copies of any service's official logo.
PNG encoding uses only the Python standard library.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct
import zlib

ASSETS = {
    "AI":"AI", "Abema":"AB", "AdBlock":"AD", "AnimeCrazy":"AN", "Apple":"AP",
    "Auto":"AU", "BBC":"BC", "Bilibili":"BI", "Console":"CO", "Dazn":"DZ",
    "Discord":"DC", "Disney":"DS", "Facebook":"FB", "Fallback":"FA",
    "Final":"FI", "Google":"GO", "HBO":"HB", "Instagram":"IG", "Line":"LN",
    "Linkedin":"LI", "Microsoft":"MS", "Netflix":"NF", "Paypal":"PY",
    "PrimeVideo":"PV", "Proxy":"PX", "Reddit":"RD", "Spotify":"SP",
    "Steam":"ST", "Telegram":"TG", "TikTok":"TT", "Twitch":"TW",
    "Twitter":"TX", "Whatsapp":"WA", "YouTube":"YT"
}
# Simple, manually authored 5x7 pixel alphabet, not a vendor/logo font.
GLYPHS = {
 "A":["01110","10001","10001","11111","10001","10001","10001"],
 "B":["11110","10001","10001","11110","10001","10001","11110"],
 "C":["01111","10000","10000","10000","10000","10000","01111"],
 "D":["11110","10001","10001","10001","10001","10001","11110"],
 "E":["11111","10000","10000","11110","10000","10000","11111"],
 "F":["11111","10000","10000","11110","10000","10000","10000"],
 "G":["01111","10000","10000","10111","10001","10001","01111"],
 "H":["10001","10001","10001","11111","10001","10001","10001"],
 "I":["11111","00100","00100","00100","00100","00100","11111"],
 "J":["00111","00010","00010","00010","10010","10010","01100"],
 "K":["10001","10010","10100","11000","10100","10010","10001"],
 "L":["10000","10000","10000","10000","10000","10000","11111"],
 "M":["10001","11011","10101","10101","10001","10001","10001"],
 "N":["10001","11001","10101","10011","10001","10001","10001"],
 "O":["01110","10001","10001","10001","10001","10001","01110"],
 "P":["11110","10001","10001","11110","10000","10000","10000"],
 "Q":["01110","10001","10001","10001","10101","10010","01101"],
 "R":["11110","10001","10001","11110","10100","10010","10001"],
 "S":["01111","10000","10000","01110","00001","00001","11110"],
 "T":["11111","00100","00100","00100","00100","00100","00100"],
 "U":["10001","10001","10001","10001","10001","10001","01110"],
 "V":["10001","10001","10001","10001","10001","01010","00100"],
 "W":["10001","10001","10001","10101","10101","10101","01010"],
 "X":["10001","10001","01010","00100","01010","10001","10001"],
 "Y":["10001","10001","01010","00100","00100","00100","00100"],
 "Z":["11111","00001","00010","00100","01000","10000","11111"],
}
COLORS = [
 (40,74,104),(56,85,81),(80,68,112),(114,75,75),
 (49,75,119),(68,90,100),(90,69,102),(95,82,56)
]
SIDE=512
SCALE=21

def chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data))+tag+data+struct.pack(">I",zlib.crc32(tag+data)&0xffffffff)

def corner_inside(x: int, y: int, r=100) -> bool:
    if r <= x < SIDE-r or r <= y < SIDE-r:
        return True
    px=r if x<r else SIDE-r-1
    py=r if y<r else SIDE-r-1
    return (x-px)**2+(y-py)**2 <= r*r

def create_png(name: str, letters: str) -> bytes:
    base=COLORS[hashlib.sha256(name.encode()).digest()[0]%len(COLORS)]
    pixels=bytearray()
    dx=5*SCALE+15
    begin=(SIDE-(len(letters)*dx-15))//2
    glyph_top=(SIDE-7*SCALE)//2-1
    # 4 channels; original rounded tile, an abstract upper accent and
    # a minimal 5x7 abbreviation instead of app-store artwork.
    for y in range(SIDE):
        pixels.append(0)
        for x in range(SIDE):
            if not corner_inside(x,y):
                pixels.extend((0,0,0,0))
                continue
            shift=round(16*(1-(x+y)/(2*(SIDE-1))))
            rgb=tuple(min(255,max(0,c+shift)) for c in base)
            ring=((x-391)**2+(y-122)**2)
            if 81*81 < ring < 98*98 and x>285 and y<229:
                rgb=tuple(min(255,c+19) for c in rgb)
            if 105<y<111 and 114<x<238:
                rgb=(188,216,219)
            for i,ch in enumerate(letters):
                gx=x-begin-i*dx
                gy=y-glyph_top
                if 0<=gx<5*SCALE and 0<=gy<7*SCALE and GLYPHS[ch][gy//SCALE][gx//SCALE]=="1":
                    rgb=(247,249,245)
            pixels.extend((*rgb,255))
    raw=bytes(pixels)
    compressed=zlib.compress(raw,9)
    return (b"\x89PNG\r\n\x1a\n"
            +chunk(b"IHDR",struct.pack(">IIBBBBB",SIDE,SIDE,8,6,0,0,0))
            +chunk(b"IDAT",compressed)+chunk(b"IEND",b""))

def render(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for name,label in sorted(ASSETS.items()):
        (output/(name+".png")).write_bytes(create_png(name,label))
    print(f"Generated {len(ASSETS)} independent neutral icons in {output}")

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--out",type=Path,default=Path("icons/v20261021r2"))
    args=cli.parse_args()
    render(args.out)
