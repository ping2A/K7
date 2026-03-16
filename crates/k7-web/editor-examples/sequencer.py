# K7 Sequencer — Sequence8-style step sequencer (idea from billiam.itch.io/sequence8, Pikuseru sound demo).
# 16 steps x 10 notes. Arrows = move cursor, Z or click = toggle cell. Playhead auto-advances.

import js
k7 = js.k7
CANVAS_ID = "k7canvas"
STEPS, ROWS = 16, 10
CELL_W, CELL_H = 16, 16
GRID_W = STEPS * CELL_W
GRID_H = ROWS * CELL_H
grid = [[0] * ROWS for _ in range(STEPS)]
playhead = 0
cursor_x, cursor_y = 0, 0
timer = 0
# One note per row (e2 up to a#3), pluck envelope
NOTES = ["e2", "f#2", "g#2", "a#2", "c3", "d3", "e3", "f#3", "g#3", "a#3"]

def init():
    global grid, playhead, cursor_x, cursor_y, timer
    grid = [[0] * ROWS for _ in range(STEPS)]
    playhead = 0
    cursor_x, cursor_y = 0, 0
    timer = 0
    for i in range(ROWS):
        k7.set_sound(i, NOTES[i] + "|envelope:pluck")

def update():
    global playhead, timer, grid, cursor_x, cursor_y
    if k7.btnp(0): cursor_x = (cursor_x - 1) % STEPS
    if k7.btnp(1): cursor_x = (cursor_x + 1) % STEPS
    if k7.btnp(2): cursor_y = (cursor_y - 1) % ROWS
    if k7.btnp(3): cursor_y = (cursor_y + 1) % ROWS
    if k7.btnp(4):
        grid[cursor_x][cursor_y] = 1 - grid[cursor_x][cursor_y]
    if k7.mouse_btnp(0):
        gx = k7.mouse_x() // CELL_W
        gy = k7.mouse_y() // CELL_H
        if 0 <= gx < STEPS and 0 <= gy < ROWS:
            grid[gx][gy] = 1 - grid[gx][gy]
    timer += 1
    if timer % 8 == 1:
        playhead = (playhead + 1) % STEPS
        for y in range(ROWS):
            if grid[playhead][y]:
                k7.sfx(y)

def draw():
    k7.cls(0)
    for x in range(STEPS):
        for y in range(ROWS):
            px, py = x * CELL_W, y * CELL_H
            on = grid[x][y]
            is_playhead = (x == playhead)
            is_cursor = (x == cursor_x and y == cursor_y)
            if on:
                k7.rectfill(px + 1, py + 1, px + CELL_W - 2, py + CELL_H - 2, 11)
            else:
                k7.rectfill(px + 1, py + 1, px + CELL_W - 2, py + CELL_H - 2, 6)
            if is_playhead:
                k7.rect(px, py, px + CELL_W - 1, py + CELL_H - 1, 7)
            if is_cursor:
                k7.rect(px + 2, py + 2, px + CELL_W - 3, py + CELL_H - 3, 15)
    k7.rectfill(0, GRID_H, 255, 255, 0)
    k7.print("SEQUENCER", 88, GRID_H + 4, 7)
    k7.print("arrows/click move  Z toggle", 48, GRID_H + 18, 6)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
