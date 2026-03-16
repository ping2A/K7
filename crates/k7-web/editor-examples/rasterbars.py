# K7 Raster Bars — copper bars with sine distortion. Synced beat.
# Effect from: https://democyclopedia.wordpress.com/2016/03/29/r-for-raster-bars/

import js
import math
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
t = 0.0

def init():
    global t
    t = 0.0
    k7.set_sound(0, "c2:square|envelope:perc")
    k7.set_sound(1, "e5:square|envelope:perc|hp:bright")
    k7.set_sound(2, "g4:saw|reverb:small b4:saw|reverb:small")

def update():
    global t
    t += 0.5
    frame = int(t)
    if frame % 8 == 0:
        k7.sfx(0)
    if frame % 4 == 0:
        k7.sfx(1)
    if frame % 16 == 0:
        k7.sfx(2)

def draw():
    k7.cls(0)
    phase = t * 2
    amp = 12
    for y in range(H):
        i = (y + int(phase * 4)) % 32
        col = (i % 14) + 1
        if col == 0:
            col = 8
        offset = int(amp * math.sin(y * 0.08 + t * 3))
        x1 = max(0, 0 + offset)
        x2 = min(W, W + offset)
        k7.line(x1, y, x2, y, col)
    k7.rectfill(0, 0, W - 1, 22, 0)
    k7.print("RASTER BARS", 72, 6, 15)
    k7.print("COPPER SINE", 76, 14, 9)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
