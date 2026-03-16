# K7 Scroller — demoscene-style scroller with rainbow and copper bars.
# Effect from: https://democyclopedia.wordpress.com/2016/02/23/s-for-scroller/

import js
import math
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
LINES = [
    "  *** K7 DEMOSCENE ***  INSPIRED BY ATARI ST EFFECTS  ",
    "  PLASMA * FIRE * TUNNELS * RASTERS * SCROLLER * GREETZ  ",
    "  PICO-8 STYLE EDITORS * PYODIDE * RUST * WASM  ",
]
scroll_x = 0.0
t = 0.0
last_beat = -1
CHARS_PER_LINE = 48
COLORS = [8, 9, 10, 11, 12, 13, 14, 15, 14, 13, 12, 11, 10, 9, 8]

def init():
    global scroll_x, t, last_beat
    scroll_x = 0.0
    t = 0.0
    last_beat = -1
    k7.set_sound(0, "a2:saw|reverb:small e2:saw|reverb:small")
    k7.set_sound(1, "e4:square|envelope:perc g4:square|envelope:perc")

def update():
    global scroll_x, t, last_beat
    t += 0.5
    scroll_x -= 1.2
    if scroll_x < -CHARS_PER_LINE * 8:
        scroll_x += CHARS_PER_LINE * 8
    beat = int(t) // 24
    if beat != last_beat:
        last_beat = beat
        k7.sfx(0)
    if int(t) % 12 == 0 and int(t) > 0:
        k7.sfx(1)

def draw():
    k7.cls(0)
    cx = 128
    k7.rect(0, 60, W - 1, 186, 6)
    k7.rectfill(2, 62, W - 3, 184, 0)
    for ly, line in enumerate(LINES):
        y = 78 + ly * 36
        k7.line(4, y - 2, W - 5, y - 2, 5)
        for i, c in enumerate(line[:CHARS_PER_LINE]):
            px = int(cx + (i * 8) + scroll_x)
            while px < -10:
                px += CHARS_PER_LINE * 8
            while px > W + 10:
                px -= CHARS_PER_LINE * 8
            if -8 < px < W:
                col = COLORS[(i + int(t * 0.5)) % len(COLORS)]
                k7.print(c, px, y, col)
    k7.rectfill(0, 0, W - 1, 24, 1)
    k7.print("K7 SCROLLER", 78, 8, 11)
    k7.print("DEMOSCENE EDITION", 68, 16, 9)
    k7.rectfill(0, H - 28, W - 1, H - 1, 1)
    k7.print("SPACE TO TEST SOUNDS", 52, H - 20, 6)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
