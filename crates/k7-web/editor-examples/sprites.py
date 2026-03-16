# K7 Sprite demo — draws sprites from the sheet.
# Edit sprites in the Sprites tab; they appear here as 8x8 tiles.

import js
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
sprites = []

def init():
    global sprites
    sprites = []
    for i in range(12):
        sprites.append({
            "n": i % 32,
            "x": 40 + (i % 4) * 56,
            "y": 60 + (i // 4) * 50,
            "vx": 0.8 + (i % 3) * 0.2,
            "vy": 0.5 + (i % 2) * 0.3,
        })

def update():
    for s in sprites:
        s["x"] += s["vx"]
        s["y"] += s["vy"]
        if s["x"] <= 0 or s["x"] >= W - 8: s["vx"] = -s["vx"]
        if s["y"] <= 0 or s["y"] >= H - 8: s["vy"] = -s["vy"]
        s["x"] = max(0, min(W - 8, s["x"]))
        s["y"] = max(0, min(H - 8, s["y"]))

def draw():
    k7.cls(0)
    for s in sprites:
        k7.spr(s["n"], int(s["x"]), int(s["y"]), 1, 1, 0, 0)
    k7.print("sprite demo — edit Sprites tab", 20, 4, 7)
    k7.print("spr(n,x,y,1,1,0,0)", 40, 236, 6)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
