# K7 32-bit RGBA — smooth gradients, transparency, glows. (Optimized for FPS.)

import js
import math
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
t = 0.0
S = 4

def init():
    global t
    t = 0.0

def update():
    global t
    t += 0.04

def draw():
    k7.cls(0)
    cx, cy = W // 2, H // 2
    # 1) Gradient: step S (fewer pixels = better FPS)
    for y in range(0, H, S):
        for x in range(0, W, S):
            u, v = x / W, y / H
            hue = (t * 0.3 + u * 0.5 + v * 0.3) % 1.0
            r = max(0, min(255, int(128 + 127 * math.sin(hue * 6.28))))
            g = max(0, min(255, int(128 + 127 * math.sin(hue * 6.28 + 2.09))))
            b = max(0, min(255, int(128 + 127 * math.sin(hue * 6.28 + 4.18))))
            k7.pset_rgba(x, y, r, g, b, 255)
    # 2) Vignette at step S
    for y in range(0, H, S):
        for x in range(0, W, S):
            d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2) / 180.0
            a = int(80 * (1.0 - min(1.0, d)))
            if a > 0:
                k7.pset_rgba(x, y, 0, 0, 0, a)
    # 3) Glass panel at step S
    for py in range(32, 100, S):
        for px in range(24, 232, S):
            k7.pset_rgba(px, py, 255, 255, 255, 25)
    # 4) Fewer glow orbs, coarser step
    step = 4
    for i in range(3):
        ox = cx + int(50 * math.sin(t + i * 2.09))
        oy = cy - 20 + int(30 * math.cos(t * 0.8 + i * 1.4))
        for dy in range(-20, 21, step):
            for dx in range(-20, 21, step):
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < 20:
                    a = int(140 * (1.0 - dist / 20.0) * (0.7 + 0.3 * math.sin(t + i)))
                    if a > 0:
                        rr, gg, bb = 40 + i * 80, 100 + (i * 60) % 256, 220
                        k7.pset_rgba(ox + dx, oy + dy, rr, gg, bb, max(0, min(255, a)))
    # 5) Text
    a1 = max(0, min(255, int(128 + 127 * math.sin(t))))
    k7.print_rgba("32-BIT RGBA", 56, 38, 255, 255, 255, 255)
    k7.print_rgba("smooth gradients", 64, 50, 255, 200, 100, a1)
    k7.print_rgba("transparency & glows", 52, 62, 180, 220, 255, 200)
    k7.rect(20, 28, 236, 92, 7)
    k7.print("palette border", 72, 238, 9)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
