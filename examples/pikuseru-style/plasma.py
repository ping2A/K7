# K7 Plasma (adapted from pikuseru-examples/demos/plasma/plasma.pik)
# Original by rez: https://www.lexaloffle.com/bbs/?tid=29529
# Uses sin/cos for full-screen plasma; palette index from formula (no sget).

import js
import math
k7 = js.k7
CANVAS_ID = "k7canvas"

SIZE = 256
A = 0.0

def init():
    global A
    A = 0.0

def update():
    pass

def draw():
    global A
    k7.cls(0)
    a2 = A * 2
    step = 4
    for x in range(0, SIZE, step):
        x2 = x / 2048.0
        for y in range(0, SIZE, step):
            y2 = y / 1024.0
            v1 = 256 + 192 * math.sin(y2 + a2)
            v2 = math.sin(A - x2 + y2)
            r = 56 * math.cos(a2 + x / v1 + v2)
            g = 48 * math.sin((x + y) / v1 * v2)
            b = 40 * math.cos((x * v2 - y) / v1)
            val = (56 + r) + (48 - g) + (40 + b) + (24 - r + g)
            c = int(abs(val * 0.1) % 16)
            k7.rectfill(x, y, min(x + step - 1, SIZE - 1), min(y + step - 1, SIZE - 1), c)
    A += 0.0025
    if A > 1:
        A = 0
    k7.print("plasma", 4, 4, 7)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
