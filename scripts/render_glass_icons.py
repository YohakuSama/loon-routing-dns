#!/usr/bin/env python3
"""Apply a restrained, consistent glass rim to already-approved square PNG icons.

Usage: python scripts/render_glass_icons.py --source icons/v20261018r2 --output /tmp/glass-preview
Requires: Pillow. Never overwrites the source directory.
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

def render(path, destination, size=512):
    image = Image.open(path).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    # Round the artwork into a consistent iOS-style squircle-like container.
    # Pillow rounded_rectangle is an approximation, not Apple's proprietary mask.
    radius = round(size * .225)
    mask = Image.new("L", (size, size))
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((2, 2, size-3, size-3), radius=radius, fill=255)
    image.putalpha(Image.composite(image.getchannel("A"), Image.new("L", image.size), mask))
    # Keep existing brand artwork intact; place highlights only on the outer rim.
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for inset, opacity in ((2, 118), (4, 55), (7, 22)):
        draw.rounded_rectangle((inset, inset, size-1-inset, size-1-inset),
                               radius=max(1, radius-inset), outline=(255,255,255,opacity), width=2)
    # Lower edge contrast gives definition on white backgrounds as well.
    draw.arc((3,3,size-4,size-4), 15, 165, fill=(0,0,0,55), width=2)
    # Gentle top-edge reflection; no opaque border.
    draw.arc((4,4,size-5,size-5), 195, 345, fill=(255,255,255,90), width=3)
    result = Image.alpha_composite(image, overlay)
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.save(destination, optimize=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.source.resolve() == args.output.resolve():
        p.error("Output must differ from source; review previews before publishing.")
    files = sorted(args.source.glob("*.png"))
    if not files:
        p.error("No PNG files found in source")
    for file in files:
        render(file, args.output / file.name)
    print(f"Rendered {len(files)} previews into {args.output}")
    print("Inspect on light and dark backgrounds before publishing.")
if __name__ == "__main__":
    main()
