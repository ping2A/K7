# K7 Plasma — classic sine/cos full-screen morph. Synced pad.
# Original by rez; demoscene plasma effect.

import js
import math
k7 = js.k7
CANVAS_ID = "k7canvas"
SIZE = 256
A = 0.0
t = 0.0
last_beat = -1

def init():
    global A, t, last_beat
    A = 0.0
    t = 0.0
    last_beat = -1
    k7.set_sound(0, "c3:sine|reverb:large e3:sine|reverb:large g3:sine|reverb:large")
    k7.set_sound(1, "c5:sine|reverb:small|tremolo:1:0.2")

def update():
    global A, t, last_beat
    A += 0.004
    if A > 1:
        A = 0
    t += 0.3
    beat = int(t) // 30
    if beat != last_beat:
        last_beat = beat
        k7.sfx(0)
    if int(t) % 15 == 0 and int(t) > 0:
        k7.sfx(1)

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
            if c == 0:
                c = 8
            k7.rectfill(x, y, min(x + step - 1, SIZE - 1), min(y + step - 1, SIZE - 1), c)
    k7.rectfill(0, 0, SIZE - 1, 18, 0)
    k7.print("PLASMA", 100, 4, 11)
    k7.print("SYNC", 112, 12, 9)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
