# K7 Python game: drawing, sound (sfx), and input (btn, btnp).
# Click canvas to focus. Arrows or WASD = move, Z = jump / action, X = shoot.

import js
k7 = js.k7
CANVAS_ID = "k7canvas"
frame = 0
px, py = 128, 180

def init():
    global frame, px, py
    frame = 0
    px, py = 128, 180
    k7.set_sound(0, "c4 e4 g4 c5")
    k7.set_sound(1, "a3 e4")

def update():
    global frame, px, py
    frame += 1
    if k7.btn(0): px = max(8, px - 2)
    if k7.btn(1): px = min(248, px + 2)
    if k7.btn(2): py = max(8, py - 2)
    if k7.btn(3): py = min(248, py + 2)
    if k7.btnp(4):
        k7.sfx(0)
    if k7.btnp(5):
        k7.sfx(1)

def draw():
    k7.cls(0)
    t = frame * 0.02
    import math
    cx = 128 + int(60 * math.sin(t * 0.5))
    cy = 128 + int(40 * math.cos(t * 0.3))
    k7.rect(8, 8, 247, 247, 7)
    k7.circfill(128, 128, 40, 8)
    k7.circfill(cx, cy, 12, 11)
    k7.circfill(px, py, 8, 11)
    k7.line(128, 128, cx, cy, 6)
    k7.print("K7 + Python", 70, 218, 7)
    k7.print("arrows/WASD move  Z/X sfx", 40, 230, 6)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()
    k7.draw_to_canvas(CANVAS_ID)

init()
js.game_loop_js = game_loop
