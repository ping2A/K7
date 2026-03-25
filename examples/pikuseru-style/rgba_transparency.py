# K7 RGBA transparency — fade text and shapes with alpha (pset_rgba, print_rgba).

import js
import math
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
t = 0.0


def init():
    global t
    t = 0.0


def update():
    global t
    t += 0.04


def draw():
    k7.cls(0)
    k7.rectfill(0, 0, W - 1, H - 1, 1)
    # Pulsing alpha text
    a = int(128 + 127 * math.sin(t))
    if a < 0:
        a = 0
    if a > 255:
        a = 255
    k7.print_rgba("FADE ME", 80, 80, 255, 255, 255, a)
    k7.print_rgba("alpha = " + str(a), 72, 100, 200, 255, 200, 200)
    # Transparent colored circles
    for i in range(5):
        cx = 80 + i * 24
        cy = 160 + int(20 * math.sin(t + i * 0.8))
        for dy in range(-12, 13):
            for dx in range(-12, 13):
                if dx * dx + dy * dy <= 12 * 12:
                    r = 40 + i * 50
                    g = 100 + i * 30
                    b = 200
                    k7.pset_rgba(cx + dx, cy + dy, r, g, b, 80 + a // 3)
    k7.rect(0, 0, W - 1, H - 1, 6)
    k7.print("RGBA transparency", 48, 4, 11)
    k7.draw_to_canvas(CANVAS_ID)


def game_loop():
    update()
    draw()


init()
js.game_loop_js = game_loop
