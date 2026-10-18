#!/usr/bin/env python3
"""Remove the outer glass rim from the existing HBO icon only.

Crops the perimeter containing the ornamental rim, scales artwork back to
the original canvas, and saves a new versioned PNG. No other icons touched.
"""
from pathlib import Path
from PIL import Image

src = Path("icons/v20261018r2/HBO.png")
dst = Path("icons/v20261018r3/HBO.png")
im = Image.open(src).convert("RGBA")
w, h = im.size
# The glass rim is confined to the outer perimeter; remove that perimeter.
# This preserves the logo in the central artwork, unlike a painted-over border.
inset = round(min(w, h) * 0.065)
im = im.crop((inset, inset, w - inset, h - inset))
im = im.resize((w, h), Image.Resampling.LANCZOS)
dst.parent.mkdir(parents=True, exist_ok=True)
im.save(dst, optimize=True)
print(f"Saved {dst} ({w}x{h}); outer rim cropped.")
