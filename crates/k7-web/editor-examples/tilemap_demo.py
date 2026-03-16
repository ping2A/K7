# K7 Tilemap flags demo — map_draw with mget_flags / mset_flags.
# Flags: 1=flip_x, 2=flip_y, 4=rotate 90° CW. Scroll with Left/Right.

import js
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
CELL = 8
FLIP_X, FLIP_Y, ROTATE = 1, 2, 4
cam_x = 0.0
MAP_W, MAP_H = 64, 12

def init():
    global cam_x
    cam_x = 0.0
    # Sprite 0: empty
    for sy in range(8):
        for sx in range(8):
            k7.sset(sx, sy, 0)
    # Sprite 1: block (brick)
    for sy in range(8):
        for sx in range(8):
            c = 4 if (sx + sy) % 2 == 0 else 5
            k7.sset(8 + sx, sy, c)
    # Sprite 2: arrow right
    for sy in range(8):
        for sx in range(8):
            k7.sset(16 + sx, sy, 0)
    for i in range(8):
        k7.sset(16 + i, 3, 9)
        k7.sset(16 + 3, i, 9)
    k7.sset(16 + 4, 2, 9)
    k7.sset(16 + 4, 4, 9)
    k7.sset(16 + 5, 1, 9)
    k7.sset(16 + 5, 5, 9)
    k7.sset(16 + 6, 0, 9)
    k7.sset(16 + 6, 6, 9)
    # Sprite 3: L-shape corner
    for sy in range(8):
        for sx in range(8):
            k7.sset(24 + sx, sy, 0)
    for i in range(6):
        k7.sset(24 + 1 + i, 1, 12)
    for i in range(6):
        k7.sset(24 + 1, 1 + i, 12)

    # Map: ground row (bricks), row above = arrows with flags 0..7 repeating, hills of blocks
    for cy in range(MAP_H):
        for cx in range(MAP_W):
            k7.mset(cx, cy, 0)
            k7.mset_flags(cx, cy, 0)
    for cx in range(MAP_W):
        k7.mset(cx, MAP_H - 1, 1)
    for cx in range(MAP_W):
        k7.mset(cx, MAP_H - 2, 2)
        k7.mset_flags(cx, MAP_H - 2, cx % 8)
    for cx in range(0, MAP_W, 4):
        k7.mset(cx, MAP_H - 3, 3)
        k7.mset_flags(cx, MAP_H - 3, (cx // 4) % 8)
    for cx in range(MAP_W):
        if (cx // 2) % 5 == 0 and cx % 2 == 0:
            k7.mset(cx, MAP_H - 4, 1)
            k7.mset_flags(cx, MAP_H - 4, ROTATE)
    for cy in range(MAP_H - 5):
        for cx in range(MAP_W):
            if (cx + cy) % 7 == 0:
                k7.mset(cx, cy, 2)
                k7.mset_flags(cx, cy, (cx + cy) % 8)

def update():
    global cam_x
    if k7.btn(0):
        cam_x = max(0.0, cam_x - 3.0)
    if k7.btn(1):
        cam_x = min((MAP_W - 32) * CELL, cam_x + 3.0)

def draw():
    k7.cls(1)
    cell_x = int(cam_x) // CELL
    k7.map_draw(cell_x, 0, 0, 0, 33, MAP_H)
    k7.rect(0, 0, W - 1, H - 1, 6)
    k7.print("Tilemap flags demo", 60, 4, 7)
    k7.print("Left/Right = scroll map", 50, 232, 6)
    k7.print("Row: arrows 0-7 | corners | bricks", 20, 240, 5)
    k7.print("mget_flags(cx,cy)  mset_flags(cx,cy,f)  map_draw(...)", 4, 248, 11)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
