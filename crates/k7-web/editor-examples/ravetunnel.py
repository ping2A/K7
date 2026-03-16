# K7 Rave Tunnel — zooming tunnel synced to a beat. No input.
# Sound: kick + hat every beat. Visuals pulse with the bass.

import js
import math
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
cx, cy = 128, 128
t = 0.0

def init():
    global t
    t = 0.0
    k7.set_sound(0, "c2:square|envelope:perc")
    k7.set_sound(1, "c6:square|envelope:perc|hp:bright")
    k7.set_sound(2, "e4 g4 b4 e5:saw|reverb:large")

def update():
    global t
    t += 0.4
    frame = int(t)
    if frame % 8 == 0:
        k7.sfx(0)
    if frame % 4 == 0:
        k7.sfx(1)
    if frame % 32 == 0:
        k7.sfx(2)

def draw():
    k7.cls(0)
    pulse = 0.7 + 0.3 * math.sin(t * 0.5)
    for ring in range(16, 0, -1):
        r = ring * 14 * pulse
        if r < 2:
            continue
        angle_off = t * 2 + ring * 0.4
        col = (int(t * 3) + ring * 2) % 16
        if col == 0:
            col = 8
        n = 32
        for i in range(n):
            a1 = (i / n) * 2 * math.pi + angle_off
            a2 = ((i + 1) / n) * 2 * math.pi + angle_off
            x1 = cx + r * math.cos(a1)
            y1 = cy + r * math.sin(a1)
            x2 = cx + r * math.cos(a2)
            y2 = cy + r * math.sin(a2)
            k7.line(int(x1), int(y1), int(x2), int(y2), col)
    k7.circfill(cx, cy, 4, 15)
    k7.print("RAVE TUNNEL", 75, 4, 11)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
