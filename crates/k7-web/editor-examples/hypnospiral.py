# K7 Hypno Spiral — spinning spiral + strobe colors. Synced crazy arp.
# Sound: fast arpeggio with distortion + reverb. Visuals spin with the beat.

import js
import math
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
t = 0.0

def init():
    global t
    t = 0.0
    k7.set_sound(0, "c4:square|distortion:medium|reverb:small e4:square|distortion:medium g4:square|distortion:medium c5:square|distortion:medium")
    k7.set_sound(1, "c3:saw|reverb:large")
    k7.set_sound(2, "e5:square|echo:short|hp:bright")

def update():
    global t
    t += 0.5
    frame = int(t)
    if frame % 4 == 0:
        k7.sfx(0)
    if frame % 16 == 0:
        k7.sfx(1)
    if frame % 8 == 0:
        k7.sfx(2)

def draw():
    k7.cls(0)
    cx, cy = 128, 128
    spin = t * 3
    for i in range(120):
        angle = (i / 120) * 4 * math.pi + spin
        r = 15 + (i / 120) * 110
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        col = (i + int(t * 8)) % 16
        if col == 0:
            col = 9
        k7.circfill(int(x), int(y), 3, col)
    for i in range(0, 120, 3):
        angle = (i / 120) * 4 * math.pi + spin + math.pi
        r = 15 + (i / 120) * 110
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        col = (i + int(t * 8) + 8) % 16
        if col == 0:
            col = 2
        k7.circfill(int(x), int(y), 2, col)
    k7.circfill(cx, cy, 12, int(t * 2) % 16)
    k7.print("HYPNOSPIRAL", 72, 4, 15)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
