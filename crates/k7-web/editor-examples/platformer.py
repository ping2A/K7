# K7 Platformer — Arrows/WASD move, Z jump. Avoid enemies.
# Sprites: player idle/walk/jump, enemies. Reset bank loads this.

import js
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
CELL = 8
LW, LH = 64, 8
GRAVITY = 0.35
JUMP_VY = -5.5
MOVE_SPEED = 2
ENEMY_SPEED = 1.0
px, py = 0.0, 0.0
vx, vy = 0.0, 0.0
cam_x = 0
coins = 0
won = False
dead = False
anim_frame = 0
face_left = False
enemies = []

def put_sprite(n, grid):
    base_x = (n % 32) * 8
    base_y = (n // 32) * 8
    for dy in range(8):
        for dx in range(8):
            c = grid[dy][dx] if dy < len(grid) and dx < len(grid[dy]) else 0
            k7.sset(base_x + dx, base_y + dy, c)

PLAYER_IDLE, PLAYER_WALK1, PLAYER_WALK2, PLAYER_JUMP = 5, 6, 7, 8
ENEMY_SPRITE = 9
def init():
    global px, py, vx, vy, cam_x, coins, won, dead, anim_frame, face_left, enemies
    put_sprite(5, [
        [0,0,0,8,8,8,0,0],
        [0,0,8,8,8,8,8,0],
        [0,8,8,8,11,8,8,8],
        [0,8,8,8,8,8,8,0],
        [0,8,8,8,8,8,8,0],
        [0,0,8,8,8,8,0,0],
        [0,0,8,0,0,8,0,0],
        [0,0,8,0,0,8,0,0],
    ])
    put_sprite(6, [
        [0,0,0,8,8,8,0,0],
        [0,0,8,8,8,8,8,0],
        [0,8,8,8,11,8,8,8],
        [0,8,8,8,8,8,8,0],
        [0,0,8,8,8,8,8,0],
        [0,0,8,8,8,8,0,0],
        [0,8,0,0,0,0,8,0],
        [0,8,0,0,0,8,0,0],
    ])
    put_sprite(7, [
        [0,0,0,8,8,8,0,0],
        [0,0,8,8,8,8,8,0],
        [0,8,8,8,11,8,8,8],
        [0,8,8,8,8,8,8,0],
        [0,8,8,8,8,8,0,0],
        [0,8,8,8,8,0,0,0],
        [0,0,8,0,0,0,8,0],
        [0,0,8,0,0,8,0,0],
    ])
    put_sprite(8, [
        [0,0,0,8,8,8,0,0],
        [0,0,8,8,8,8,8,0],
        [0,8,8,8,11,8,8,8],
        [0,8,8,8,8,8,8,0],
        [0,8,8,8,8,8,8,0],
        [0,0,8,0,0,8,0,0],
        [0,0,0,8,8,0,0,0],
        [0,0,0,0,0,0,0,0],
    ])
    put_sprite(9, [
        [0,0,0,2,2,2,0,0],
        [0,0,2,8,8,2,0,0],
        [0,2,8,8,8,8,2,0],
        [0,2,8,8,8,8,2,0],
        [0,0,2,8,8,2,0,0],
        [0,0,0,2,2,0,0,0],
        [0,0,2,2,2,2,0,0],
        [0,0,2,0,0,2,0,0],
    ])
    put_sprite(1, [[6]*8 for _ in range(8)])
    put_sprite(2, [[5,5,7,5,5,7,5,5] for _ in range(8)])
    put_sprite(3, [
        [0,0,0,10,10,0,0,0],
        [0,0,10,10,10,10,0,0],
        [0,10,10,10,10,10,10,0],
        [0,10,10,10,10,10,10,0],
        [0,0,10,10,10,10,0,0],
        [0,0,0,10,10,0,0,0],
        [0]*8, [0]*8,
    ])
    put_sprite(4, [
        [0,0,0,9,9,0,0,0],
        [0,9,9,9,9,9,9,0],
        [0,9,9,9,9,9,9,0],
        [0,9,9,9,9,9,9,0],
        [0,9,9,9,9,9,9,0],
        [0,9,9,9,9,9,9,0],
        [0,9,9,9,9,9,9,0],
        [0,9,9,9,9,9,9,0],
    ])
    k7.set_sound(0, "c5 e5")
    k7.set_sound(1, "e5 g5 c6")
    k7.set_sound(2, "c5 e5 g5 c6")
    k7.set_sound(3, "a2 e2")
    for cy in range(LH):
        for cx in range(LW):
            k7.mset(cx, cy, 0)
    for cx in range(LW):
        k7.mset(cx, LH - 1, 1)
    for cx in range(4, 12):
        k7.mset(cx, LH - 3, 1)
    for cx in range(18, 28):
        k7.mset(cx, LH - 2, 2)
    for cx in range(35, 45):
        k7.mset(cx, LH - 4, 1)
    k7.mset(40, LH - 2, 3)
    k7.mset(42, LH - 2, 3)
    k7.mset(50, LH - 3, 3)
    k7.mset(55, LH - 2, 4)
    px, py = 24.0, (LH - 2) * CELL - 6
    vx, vy = 0.0, 0.0
    cam_x = 0
    coins = 0
    won = False
    dead = False
    anim_frame = 0
    face_left = False
    enemies = [
        {"x": 88.0, "y": (LH - 2) * CELL - 8, "vx": ENEMY_SPEED, "left": 80, "right": 120},
        {"x": 160.0, "y": (LH - 3) * CELL - 8, "vx": -ENEMY_SPEED, "left": 144, "right": 224},
        {"x": 280.0, "y": (LH - 4) * CELL - 8, "vx": ENEMY_SPEED, "left": 272, "right": 320},
    ]

def tile_at(cx, cy):
    if cx < 0 or cx >= LW or cy < 0 or cy >= LH:
        return 0
    return k7.mget(cx, cy)

def solid(cx, cy):
    return tile_at(cx, cy) in (1, 2)

def update():
    global px, py, vx, vy, cam_x, coins, won, dead, anim_frame, face_left, enemies
    if won or dead:
        if k7.btnp(4):
            init()
        return
    if k7.btn(0): vx = -MOVE_SPEED
    elif k7.btn(1): vx = MOVE_SPEED
    else: vx = 0
    if vx < 0: face_left = True
    elif vx > 0: face_left = False
    feet_cy = (int(py) + 8) // CELL
    on_ground = feet_cy < LH and (solid(int(px // CELL), feet_cy) or solid(int((px + 7) // CELL), feet_cy))
    if k7.btnp(2) or k7.btnp(4):
        if on_ground:
            vy = JUMP_VY
            k7.sfx(0)
    vy += GRAVITY
    px += vx
    left_cx = int(px // CELL)
    right_cx = int((px + 7) // CELL)
    if solid(left_cx, int(py // CELL)) or solid(left_cx, int((py + 7) // CELL)):
        px = (left_cx + 1) * CELL
        vx = 0
    if solid(right_cx, int(py // CELL)) or solid(right_cx, int((py + 7) // CELL)):
        px = right_cx * CELL - 8
        vx = 0
    py += vy
    cx0 = int(px // CELL)
    cx1 = int((px + 7) // CELL)
    cy0 = int(py // CELL)
    cy1 = int((py + 7) // CELL)
    for cx in range(cx0, cx1 + 1):
        for cy in range(cy0, cy1 + 1):
            t = tile_at(cx, cy)
            if t == 3:
                k7.mset(cx, cy, 0)
                coins += 1
                k7.sfx(1)
            if t == 4:
                won = True
                k7.sfx(2)
    feet_cy = (int(py) + 8) // CELL
    if feet_cy < LH and (solid(cx0, feet_cy) or solid(cx1, feet_cy)):
        py = feet_cy * CELL - 8
        vy = 0
    head_cy = (int(py) - 1) // CELL
    if head_cy >= 0 and (solid(cx0, head_cy) or solid(cx1, head_cy)):
        py = (head_cy + 1) * CELL
        vy = 0
    if py > LH * CELL:
        py = (LH - 2) * CELL - 6
        vy = 0
    anim_frame += 1
    for e in enemies:
        e["x"] += e["vx"]
        if e["x"] <= e["left"]:
            e["x"] = float(e["left"])
            e["vx"] = ENEMY_SPEED
        if e["x"] >= e["right"]:
            e["x"] = float(e["right"])
            e["vx"] = -ENEMY_SPEED
        ex, ey = int(e["x"]), int(e["y"])
        if ex + 8 > px and ex < px + 8 and ey + 8 > py and ey < py + 8:
            dead = True
            k7.sfx(3)
            k7.flash(8, 5)
    cam_x = max(0, min(int(px) - W // 2, LW * CELL - W))

def draw():
    k7.cls(0)
    k7.map_draw(cam_x // CELL, 0, 0, 0, 32, 32)
    for e in enemies:
        k7.spr(ENEMY_SPRITE, int(e["x"] - cam_x), int(e["y"]), 1, 1, 0, 0)
    if not dead:
        feet_cy = (int(py) + 8) // CELL
        on_ground = feet_cy < LH and (tile_at(int(px//CELL), feet_cy) in (1, 2) or tile_at(int((px+7)//CELL), feet_cy) in (1, 2))
        if not on_ground and vy != 0:
            s = PLAYER_JUMP
        elif vx != 0:
            s = PLAYER_WALK1 if (anim_frame // 8) % 2 == 0 else PLAYER_WALK2
        else:
            s = PLAYER_IDLE
        k7.spr(s, int(px - cam_x), int(py), 1, 1, 1 if face_left else 0, 0)
    k7.rect(0, 0, W - 1, H - 1, 6)
    k7.print("coins " + str(coins), 4, 4, 7)
    if won:
        k7.print("YOU WIN — Z to restart", 50, 120, 11)
    if dead:
        k7.print("DEAD — Z to restart", 60, 120, 8)
    k7.print("platformer", 4, 248, 6)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
