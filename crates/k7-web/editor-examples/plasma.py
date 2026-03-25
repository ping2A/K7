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
    global A, t
    k7.cls(0)
    a2 = A * 6.283 * 0.5
    step = 2
    drift = t * 0.018
    for x in range(0, SIZE, step):
        xf = x * 0.045 + drift
        for y in range(0, SIZE, step):
            yf = y * 0.045 + drift * 0.73
            s1 = math.sin(yf * 1.7 + a2)
            s2 = math.sin(xf * 1.3 - yf * 1.1 + A * 4.2)
            s3 = math.cos((xf + yf) * 0.85 + a2 * 0.5)
            s4 = math.sin(math.hypot(x - 128, y - 128) * 0.06 - t * 0.12)
            w = s1 * 5.5 + s2 * 4.0 + s3 * 3.0 + s4 * 2.5
            c = int((w * 1.15 + 8) % 16)
            if c == 0:
                c = 13
            elif c == 1:
                c = 12
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
