#!/usr/bin/env python3
"""Convert logo.png to K7 map + sprite sheet data (base64). Outputs JS constants for editor.html."""
import base64
import json
import os
import sys

try:
    from PIL import Image
except ImportError:
    print("Install Pillow: pip install Pillow", file=sys.stderr)
    sys.exit(1)

# PICO-8 palette (16 colors) - from k7 palette.rs
PALETTE = [
    (0, 0, 0),       # 0 black
    (29, 43, 83),    # 1 dark_blue
    (126, 37, 83),   # 2 dark_purple
    (0, 135, 81),    # 3 dark_green
    (171, 82, 54),   # 4 brown
    (95, 87, 79),    # 5 dark_gray
    (194, 195, 199), # 6 light_gray
    (255, 241, 232), # 7 white
    (255, 0, 77),    # 8 red
    (255, 163, 0),   # 9 orange
    (255, 240, 36),  # 10 yellow
    (0, 231, 86),    # 11 green
    (41, 173, 255),  # 12 blue
    (131, 118, 156), # 13 indigo
    (255, 119, 168), # 14 pink
    (255, 204, 170), # 15 peach
]

def nearest_color(r, g, b):
    best = 0
    best_d = 1e9
    for i, (pr, pg, pb) in enumerate(PALETTE):
        d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if d < best_d:
            best_d = d
            best = i
    return best

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(script_dir, "logo.png")
    if not os.path.exists(logo_path):
        print(f"Not found: {logo_path}", file=sys.stderr)
        sys.exit(1)

    im = Image.open(logo_path).convert("RGB")
    # Logo in map: 24 cells wide, 8 cells tall = 192x64 pixels
    LOGOW, LOGOH = 24, 8
    pw, ph = LOGOW * 8, LOGOH * 8  # 192, 64
    im = im.resize((pw, ph), Image.Resampling.LANCZOS)

    # Build 192x64 palette indices
    grid = []
    for y in range(ph):
        row = []
        for x in range(pw):
            r, g, b = im.getpixel((x, y))
            row.append(nearest_color(r, g, b))
        grid.append(row)

    # Sprite sheet: 256x64 bytes. Each sprite 8x8. Sprites 0..191 in order (row-major 24x8).
    # Sprite (cx,cy) has index cy*24+cx, sheet position (cx*8, cy*8).
    sheet = bytearray(256 * 64)
    for cy in range(LOGOH):
        for cx in range(LOGOW):
            sprite_idx = cy * LOGOW + cx
            sheet_x0, sheet_y0 = cx * 8, cy * 8
            for dy in range(8):
                for dx in range(8):
                    px = sheet_x0 + dx
                    py = sheet_y0 + dy
                    col = grid[py][px]
                    idx = py * 256 + px
                    sheet[idx] = col

    # Map: 256x32 cells. Logo in (0,0)-(23,7): cell (cx,cy) = sprite index cy*24+cx.
    map_data = bytearray(256 * 32)
    for cy in range(LOGOH):
        for cx in range(LOGOW):
            map_data[cy * 256 + cx] = cy * LOGOW + cx

    sheet_b64 = base64.b64encode(bytes(sheet)).decode("ascii")
    map_b64 = base64.b64encode(bytes(map_data)).decode("ascii")

    # Output as JSON for easy embedding
    out = {
        "LOGOW": LOGOW,
        "LOGOH": LOGOH,
        "LOGO_SPRITE_B64": sheet_b64,
        "LOGO_MAP_B64": map_b64,
    }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
