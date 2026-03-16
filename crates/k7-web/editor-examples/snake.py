# K7 Snake — arrows to move, eat the apple.
# Edit sprites in the Sprites tab for a custom head/apple (sprite 0 and 1).

import js
import random
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
CELL = 8
GW, GH = W // CELL, H // CELL
TICK_INTERVAL = 12
snake = []
dir_x, dir_y = 1, 0
food_x, food_y = 0, 0
score = 0
dead = False
tick = 0
melody_beat = 0
melody_tick = 0
MELODY_BEAT_INTERVAL = 25
MELODY_NOTES = [2, 3, 4, 3, 2, 3, 4, 5, 4, 3, 2, 3, 2, 2, 2, 2]

def place_food():
    global food_x, food_y
    while True:
        food_x = random.randint(0, GW - 1)
        food_y = random.randint(0, GH - 1)
        if (food_x, food_y) not in snake:
            break

def init():
    global snake, dir_x, dir_y, score, dead, tick, melody_beat, melody_tick
    snake = [(GW // 2, GH // 2)]
    dir_x, dir_y = 1, 0
    score = 0
    dead = False
    tick = 0
    melody_beat = 0
    melody_tick = 0
    place_food()
    k7.set_sound(0, "e5 g5 b5 e6")
    k7.set_sound(1, "c4 e4 g4 c5 b4 g4")
    k7.set_sound(2, "c4")
    k7.set_sound(3, "e4")
    k7.set_sound(4, "g4")
    k7.set_sound(5, "c5")
    k7.set_sound(6, "e5")
    k7.set_sound(7, "g5")

def update():
    global snake, score, dead, dir_x, dir_y, tick, melody_beat, melody_tick
    if dead:
        if k7.btnp(4):
            init()
        return
    melody_tick += 1
    if melody_tick % MELODY_BEAT_INTERVAL == 1:
        melody_beat += 1
        k7.sfx(MELODY_NOTES[melody_beat % len(MELODY_NOTES)])
    tick += 1
    if k7.btnp(0) and dir_x != 1:  dir_x, dir_y = -1, 0
    if k7.btnp(1) and dir_x != -1: dir_x, dir_y = 1, 0
    if k7.btnp(2) and dir_y != 1:  dir_x, dir_y = 0, -1
    if k7.btnp(3) and dir_y != -1: dir_x, dir_y = 0, 1
    if tick < TICK_INTERVAL:
        return
    tick = 0
    head = (snake[0][0] + dir_x, snake[0][1] + dir_y)
    if head[0] < 0 or head[0] >= GW or head[1] < 0 or head[1] >= GH or head in snake:
        dead = True
        k7.sfx(1)
        return
    snake.insert(0, head)
    if head == (food_x, food_y):
        score += 1
        k7.sfx(0)
        place_food()
    else:
        snake.pop()

def draw():
    k7.cls(0)
    k7.rect(0, 0, W - 1, H - 1, 7)
    for i, (gx, gy) in enumerate(snake):
        col = 11 if i == 0 else 3
        k7.rectfill(gx * CELL + 1, gy * CELL + 1, (gx + 1) * CELL - 1, (gy + 1) * CELL - 1, col)
    k7.rectfill(food_x * CELL + 2, food_y * CELL + 2, (food_x + 1) * CELL - 2, (food_y + 1) * CELL - 2, 8)
    k7.print("score " + str(score), 4, 4, 7)
    if dead:
        k7.print("GAME OVER — Z to restart", 40, 120, 8)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
