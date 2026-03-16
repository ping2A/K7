# K7 Fire — classic flame buffer with fire gradient (black -> red -> orange -> yellow -> white).
# Effect from: https://democyclopedia.wordpress.com/2015/11/25/f-comme-feu/

import js
import random
k7 = js.k7
CANVAS_ID = "k7canvas"
FW, FH = 64, 64
CELL = 4
heat = []
t = 0
# PICO-8: 0 black, 4 brown/dark, 8 red, 9 orange, 10 yellow, 15 peach, 7 white
FIRE_COLORS = (0, 4, 8, 9, 10, 15, 7)
FIRE_THRESHOLDS = (0.02, 0.12, 0.28, 0.48, 0.68, 0.85, 1.01)

def heat_to_color(v):
    if v <= 0:
        return 0
    for i in range(len(FIRE_THRESHOLDS)):
        if v < FIRE_THRESHOLDS[i]:
            return FIRE_COLORS[i]
    return FIRE_COLORS[-1]

def init():
    global heat, t
    heat = [[0.0] * FW for _ in range(FH)]
    t = 0
    k7.set_sound(0, "e2:saw|reverb:large|lowpass:dark")
    k7.set_sound(1, "c2:noise|envelope:perc|lowpass:dark")

def update():
    global heat, t
    t += 1
    # Heat source: hotter in center, flickering bottom row
    for x in range(FW):
        center = 1.0 - 0.4 * abs(x - FW // 2) / (FW // 2)
        heat[FH - 1][x] = min(1.0, heat[FH - 1][x] + random.uniform(0.5, 0.95) * center)
        if random.random() < 0.6:
            heat[FH - 1][x] = min(1.0, heat[FH - 1][x] + 0.4)
        if random.random() < 0.15:
            heat[FH - 1][x] = 1.0
    # Propagate upward: 4-point average + small random for organic flicker
    for y in range(FH - 2, -1, -1):
        for x in range(FW):
            xl = (x - 1) % FW
            xr = (x + 1) % FW
            s = heat[y + 1][x] + heat[y + 1][xl] + heat[y + 1][xr]
            s += heat[y + 1][(x + (y % 2)) % FW] * 0.5  # extra sample for variation
            up = max(0, (s / 3.5) * 0.31 - 0.006)
            heat[y][x] = max(0, min(1.0, up + random.uniform(-0.015, 0.02)))
    if t % 45 < 2:
        k7.sfx(0)
    if random.random() < 0.04:
        k7.sfx(1)

def draw():
    k7.cls(0)
    for y in range(FH):
        for x in range(FW):
            v = heat[y][x]
            c = heat_to_color(v)
            if c > 0:
                k7.rectfill(x * CELL, y * CELL, x * CELL + CELL - 1, y * CELL + CELL - 1, c)
    k7.rectfill(0, 0, 255, 18, 0)
    k7.print("FIRE", 108, 4, 10)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
