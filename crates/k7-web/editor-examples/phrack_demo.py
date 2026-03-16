# K7 Phrack-style demo — terminal/CRT aesthetic inspired by https://phrack.org/
# Green-on-black ASCII banner, scanlines, blinking cursor. Left/Right: palette.

import js
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256

# Condensed PHRACK-style ASCII banner (fits ~56 chars wide; backslashes escaped)
BANNER = [
    "    _____ ____ ____   _____   ___________  ___  ___",
    " ._\\__  \\   |   |__\\__  \\ _\\__  /\\  __//_\\  |/  /",
    " :   |/  >>  :   :  /  /./  /  |   |  /.  !/  /",
    " |   :  /     |  /   \\|  __  |   |   |  /   \\",
    " | ____/|  |  |  \\    \\   |  |__ :   |  \\    \\",
    " | |/// |____| _____\\  |\\___ | ://\\   !_____\\",
    " | :  /////|____|////\\\\____|////\\\\___/. \\\\__://///",
    " |___/ e-zine  /////:  //////|  ////   /////  //////",
    " ////       .    :     x0^67^aMi5H^iMP!",
]

PALETTES = ["gameboy", "pico8", "commodore64"]
palette_index = 0
cursor_blink = 0

def init():
    global palette_index, cursor_blink
    palette_index = 0
    cursor_blink = 0
    k7.switch_palette(PALETTES[0])
    k7.set_sound(0, "c3:square|envelope:perc e3:square g3:square")
    k7.set_sound(1, "a2:saw|reverb:small|lowpass:dark")
    # Techno background: driving saw bass + square stabs (16-step loop)
    k7.set_music_track(0, "e2:saw|lowpass:dark e2:saw e2:saw e4:square|envelope:perc|hp:bright a2:saw|lowpass:dark a2:saw a2:saw a3:square|envelope:perc e2:saw e2:saw e2:saw g4:square|envelope:perc|hp:bright b2:saw|lowpass:dark b2:saw b2:saw b3:square|envelope:perc e2:saw e2:saw e2:saw e4:square|envelope:perc a2:saw a2:saw a2:saw c4:square|envelope:perc e2:saw e2:saw e2:saw g4:square|envelope:perc b2:saw b2:saw b2:saw e4:square|envelope:perc")
    k7.play_music(0, 0)

def update():
    global cursor_blink, palette_index
    cursor_blink += 1
    if k7.btnp(4):
        k7.sfx(0)
    if k7.btnp(5):
        k7.sfx(1)
    if k7.btnp(0):
        palette_index = (palette_index - 1) % len(PALETTES)
        k7.switch_palette(PALETTES[palette_index])
        k7.sfx(0)
    if k7.btnp(1):
        palette_index = (palette_index + 1) % len(PALETTES)
        k7.switch_palette(PALETTES[palette_index])
        k7.sfx(0)

def draw():
    k7.cls(0)
    # CRT scanlines: alternate dark lines (before drawing text so text overwrites)
    if palette_index == 0:
        for y in range(0, H, 2):
            k7.rectfill(0, y, W - 1, y, 1)
    # Header
    k7.print(".:: PHRACK ::.", 72, 8, 11 if palette_index != 0 else 2)
    k7.print("CALL FOR PAPERS", 68, 16, 6 if palette_index != 0 else 1)
    # ASCII banner — terminal green (gameboy: 2=mid green; pico8: 11=green)
    banner_col = 2 if palette_index == 0 else 11
    title_col = 3 if palette_index == 0 else 7
    start_y = 32
    line_h = 10
    for i, line in enumerate(BANNER):
        # Trim to fit (advance 4px/char -> ~64 chars)
        s = line[:62] if len(line) > 62 else line
        x = max(0, (W - len(s) * 4) // 2)
        k7.print(s, x, start_y + i * line_h, banner_col)
    # Footer
    y_foot = start_y + len(BANNER) * line_h + 8
    k7.print("[ Skip To Site ]  [ Read CFP ]", 36, y_foot, 6 if palette_index != 0 else 1)
    k7.print("Z/X: palette  Left/Right: change", 24, y_foot + 12, 5)
    # Blinking cursor
    if (cursor_blink // 30) % 2 == 0:
        k7.rectfill(W // 2 - 4, H - 20, W // 2 + 4, H - 18, title_col)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
