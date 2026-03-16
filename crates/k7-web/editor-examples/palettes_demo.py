# K7 Palettes demo — switch_palette: pico8, gameboy, cga, commodore64, atari2600.
# Draw the 16 colors; cycle palette with Z or show palette name.

import js
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
PALETTES = ["pico8", "gameboy", "cga", "commodore64", "atari2600"]
idx = 0

def init():
    global idx
    idx = 0
    if hasattr(k7, "switch_palette"):
        k7.switch_palette(PALETTES[idx])

def update():
    global idx
    if k7.btnp(4):
        idx = (idx + 1) % len(PALETTES)
        if hasattr(k7, "switch_palette"):
            k7.switch_palette(PALETTES[idx])
    if k7.btnp(5):
        idx = (idx - 1) % len(PALETTES)
        if hasattr(k7, "switch_palette"):
            k7.switch_palette(PALETTES[idx])

def draw():
    k7.cls(0)
    for i in range(16):
        x0 = (i % 8) * 32
        y0 = (i // 8) * 64 + 24
        k7.rectfill(x0, y0, x0 + 30, y0 + 62, i)
        k7.rect(x0, y0, x0 + 30, y0 + 62, 7)
    k7.rect(0, 0, W - 1, H - 1, 7)
    k7.print("Palettes demo", 70, 4, 7)
    k7.print(PALETTES[idx], 90, 220, 11)
    k7.print("Z = next  X = prev", 50, 236, 6)
    k7.print("switch_palette(name)", 40, 248, 5)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
