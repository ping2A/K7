# K7 Pong — arrows or W/S: left paddle. Z to serve.
# Right paddle is CPU; first to 5 wins.

import js
import random
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
PAD_W, PAD_H = 8, 32
BALL_R = 4
py1 = py2 = (H - PAD_H) // 2
px1, px2 = 24, W - 24 - PAD_W
bx, by = W // 2 - BALL_R, H // 2 - BALL_R
vx, vy = 0, 0
score1 = score2 = 0
serving = True

def init():
    global py1, py2, bx, by, vx, vy, score1, score2, serving
    py1 = py2 = (H - PAD_H) // 2
    bx, by = W // 2 - BALL_R, H // 2 - BALL_R
    vx, vy = 0, 0
    score1 = score2 = 0
    serving = True
    k7.set_sound(0, "c5")
    k7.set_sound(1, "e5")

def update():
    global py1, py2, bx, by, vx, vy, score1, score2, serving
    if k7.btn(2): py1 = max(0, py1 - 4)
    if k7.btn(3): py1 = min(H - PAD_H, py1 + 4)
    if serving:
        if k7.btnp(4):
            vx = 4 if random.random() > 0.5 else -4
            vy = random.uniform(-2, 2)
            serving = False
        return
    bx += vx
    by += vy
    if by <= 0 or by >= H - BALL_R * 2:
        vy = -vy
        by = max(0, min(H - BALL_R * 2, by))
    if bx <= px1 + PAD_W and by + BALL_R * 2 >= py1 and by <= py1 + PAD_H:
        vx = abs(vx)
        bx = px1 + PAD_W
        k7.sfx(0)
    if bx + BALL_R * 2 >= px2 and by + BALL_R * 2 >= py2 and by <= py2 + PAD_H:
        vx = -abs(vx)
        bx = px2 - BALL_R * 2
        k7.sfx(0)
    # CPU
    if py2 + PAD_H // 2 < by + BALL_R:
        py2 = min(H - PAD_H, py2 + 3)
    else:
        py2 = max(0, py2 - 3)
    if bx < 0:
        score2 += 1
        serving = True
        bx, by = W // 2 - BALL_R, H // 2 - BALL_R
        vx = vy = 0
        k7.sfx(1)
    if bx > W:
        score1 += 1
        serving = True
        bx, by = W // 2 - BALL_R, H // 2 - BALL_R
        vx = vy = 0
        k7.sfx(1)

def draw():
    k7.cls(0)
    k7.rect(0, 0, W - 1, H - 1, 7)
    k7.rectfill(px1, py1, px1 + PAD_W - 1, py1 + PAD_H - 1, 11)
    k7.rectfill(px2, py2, px2 + PAD_W - 1, py2 + PAD_H - 1, 8)
    k7.circfill(int(bx) + BALL_R, int(by) + BALL_R, BALL_R, 15)
    k7.print(str(score1), 80, 20, 7)
    k7.print(str(score2), 160, 20, 7)
    if serving:
        k7.print("Z to serve", 90, 120, 6)
    k7.print("pong", 110, 4, 7)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
