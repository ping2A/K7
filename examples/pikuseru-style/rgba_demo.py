# K7 32-bit RGBA demo — pset_rgba (gradients, custom colors), print_rgba (transparency).
# Load in editor: Example → RGBA (32-bit colors + transparency).

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
    t += 0.03


def draw():
    k7.cls(0)
    # Gradient background with pset_rgba (smooth colors outside 16-color palette)
    for y in range(H):
        r = int(32 + 32 * math.sin(t + y * 0.02))
        g = int(64 + 64 * math.sin(t * 0.7 + y * 0.015))
        b = int(128 + 80 * math.cos(t * 0.5 + y * 0.02))
        for x in range(0, W, 2):
            k7.pset_rgba(x, y, r & 255, g & 255, b & 255, 255)
    # Semi-transparent overlay
    for py in range(40, 120):
        for px in range(40, 216):
            k7.pset_rgba(px, py, 0, 0, 40, 180)
    # print_rgba: full opacity and semi-transparent
    k7.print_rgba("32-BIT RGBA", 52, 52, 255, 255, 255, 255)
    k7.print_rgba("pset_rgba + print_rgba", 36, 64, 255, 180, 80, 220)
    k7.print_rgba("transparency & gradients", 44, 88, 200, 220, 255, 200)
    k7.rect(38, 38, 218, 122, 7)
    k7.print("palette print", 80, 230, 9)
    k7.draw_to_canvas(CANVAS_ID)


def game_loop():
    update()
    draw()


init()
js.game_loop_js = game_loop
