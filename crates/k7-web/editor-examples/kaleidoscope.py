# K7 Trippy Kaleidoscope — 6-fold mirror + morphing colors. Synced pad.
# Sound: slow pad sequence with heavy reverb. Visuals drift with the notes.

import js
import math
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
t = 0.0
last_beat = -1
last_sub = -1

def init():
    global t, last_beat, last_sub
    t = 0.0
    last_beat = -1
    last_sub = -1
    k7.set_sound(0, "c4:sine|reverb:large e4:sine|reverb:large g4:sine|reverb:large b4:sine|reverb:large c5:sine|reverb:large")
    k7.set_sound(1, "a3:sine|reverb:hall|tremolo:2:0.3")

def update():
    global t, last_beat, last_sub
    t += 0.15
    beat = int(t) // 20
    if beat != last_beat:
        last_beat = beat
        k7.sfx(0)
    sub = int(t * 0.5) // 40
    if sub != last_sub:
        last_sub = sub
        k7.sfx(1)

def draw():
    k7.cls(0)
    cx, cy = 128, 128
    segments = 6
    for seg in range(segments):
        base_angle = (seg / segments) * 2 * math.pi + t * 0.2
        for r in range(20, 130, 6):
            hue_off = t * 2 + r * 0.1 + seg * 0.5
            col = (int(hue_off) % 14) + 1
            pts = []
            for i in range(5):
                a = base_angle + (i / 4) * (math.pi / segments)
                x = cx + r * math.cos(a)
                y = cy + r * math.sin(a)
                pts.append((int(x), int(y)))
            for i in range(4):
                x1, y1 = pts[i]
                x2, y2 = pts[i + 1]
                k7.line(x1, y1, x2, y2, col)
            k7.line(pts[4][0], pts[4][1], pts[0][0], pts[0][1], col)
    k7.circfill(cx, cy, 8, (int(t * 4) % 16))
    k7.print("KALEIDOSCOPE", 70, 4, 11)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
