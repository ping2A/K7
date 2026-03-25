# K7 Fonts demo — cycle through pico8, bbc, appleii, cbmii, trollmini.
# Usage: load in editor (Example: Fonts) or run with Pyodide.

import js
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
FONTS = ["pico8", "bbc", "appleii", "cbmii", "trollmini"]
idx = 0
t = 0


def init():
    global idx, t
    idx = 0
    t = 0


def update():
    global idx, t
    t += 0.5
    if int(t) % 120 == 0 and int(t) > 0:
        idx = (idx + 1) % len(FONTS)


def draw():
    k7.cls(0)
    k7.set_font(FONTS[idx])
    k7.rect(0, 0, W - 1, H - 1, 6)
    k7.rectfill(0, 0, W - 1, 22, 1)
    k7.print("K7 FONTS: " + FONTS[idx], 8, 4, 11)
    k7.print("pico8  bbc  appleii  cbmii  trollmini", 8, 14, 9)
    k7.print("The quick brown fox jumps over the lazy dog.", 8, 40, 7)
    k7.print("0123456789  !@#$%^&*()  ABCDEF  abcdef", 8, 56, 6)
    k7.print("Next font in " + str(max(0, 120 - int(t) % 120)) + " frames", 8, 200, 8)
    k7.draw_to_canvas(CANVAS_ID)


def game_loop():
    update()
    draw()


init()
js.game_loop_js = game_loop
