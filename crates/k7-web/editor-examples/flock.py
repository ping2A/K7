# K7 Flock / Boids (from pikuseru-examples/demos/flocking)
# By laurent victorino; leader moves in circle.

import js
import math
import random
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
MAX_VEL = 3
MIN_DIST = 8
BOIDS = []
frame = 0

def dist_vec(p, q):
    return math.sqrt((p["x"] - q["x"]) ** 2 + (p["y"] - q["y"]) ** 2)

def magnitude(v):
    return math.sqrt(v["x"] ** 2 + v["y"] ** 2)

def init():
    global BOIDS
    BOIDS = []
    for _ in range(25):
        BOIDS.append({"x": random.uniform(0, W - 1), "y": random.uniform(0, H - 1), "vx": 0, "vy": 0})

def update():
    global BOIDS, frame
    frame += 1
    leader_x = 128 + 50 * math.cos(frame * 0.02)
    leader_y = 128 + 50 * math.sin(frame * 0.02)
    for b in BOIDS:
        v1x, v1y, cx, cy, n = 0, 0, 0, 0, 0
        for o in BOIDS:
            if o is not b:
                cx += o["x"]; cy += o["y"]; n += 1
        if n > 0:
            cx, cy = cx / n, cy / n
            v1x, v1y = (cx - b["x"]) * 0.01, (cy - b["y"]) * 0.01
        v2x, v2y = 0, 0
        for o in BOIDS:
            if o is not b and dist_vec(b, o) < MIN_DIST:
                v2x -= (o["x"] - b["x"]); v2y -= (o["y"] - b["y"])
        v3x, v3y = 0, 0
        for o in BOIDS:
            if o is not b:
                v3x += o["vx"]; v3y += o["vy"]
        if n > 0:
            v3x = (v3x / n - b["vx"]) * 0.125
            v3y = (v3y / n - b["vy"]) * 0.125
        v4x = (leader_x - b["x"]) * 0.01
        v4y = (leader_y - b["y"]) * 0.01
        b["vx"] += v1x + v2x + v3x + v4x
        b["vy"] += v1y + v2y + v3y + v4y
        m = magnitude({"x": b["vx"], "y": b["vy"]})
        if m > MAX_VEL:
            b["vx"] = (b["vx"] / m) * MAX_VEL
            b["vy"] = (b["vy"] / m) * MAX_VEL
        b["x"] = max(0, min(W - 1, b["x"] + b["vx"]))
        b["y"] = max(0, min(H - 1, b["y"] + b["vy"]))

def draw():
    k7.cls(0)
    for b in BOIDS:
        x, y = int(b["x"]), int(b["y"])
        k7.line(x, y - 1, x, y + 1, 6)
        k7.line(x - 1, y, x + 1, y, 6)
    leader_x = 128 + 50 * math.cos(frame * 0.02)
    leader_y = 128 + 50 * math.sin(frame * 0.02)
    k7.rect(int(leader_x) - 1, int(leader_y) - 1, int(leader_x) + 1, int(leader_y) + 1, 8)
    k7.print("flock (leader in circle)", 4, 4, 7)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
