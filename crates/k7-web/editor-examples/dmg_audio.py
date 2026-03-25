# Game Boy–style DMG audio demo (8 phrases). Focus the canvas to hear.
# Left / Right: previous / next demo; the selected row plays immediately.
# Switching stops the previous clip (editor k7.sfx).
# Note ":N" = length in half-beats (0.5 s each at default), e.g. :4 = 2 s.

import js

k7 = js.k7
CANVAS_ID = "k7canvas"

W = "02468aceeca8642002468aceeca86420"
W_ALT = "fedcba9876543210fedcba9876543210"

# Current demo index 0..7, or -1 before first Left/Right.
_current = -1


def _load_wave_cart():
    try:
        k7.set_dmg_wave_cart_hexes([W, W_ALT])
    except Exception:
        pass


S0 = (
    "c4:dmgpulse1(2):4 d4:dmgpulse1(2):4 e4:dmgpulse1(2):4 f4:dmgpulse1(2):4 "
    "g4:dmgpulse1(2):4 a4:dmgpulse1(2):4 b4:dmgpulse1(2):4 c5:dmgpulse1(2):6"
)
S1 = (
    "c3:dmgpulse1(2,3,2,0):6 d3:dmgpulse1(2,3,2,0):6 e3:dmgpulse1(2,3,2,0):6 "
    "g3:dmgpulse1(2,2,3,0):8"
)
S2 = (
    "c4:dmgwavepreset(0):3 e4:dmgwavepreset(1):3 g4:dmgwavepreset(0):3 "
    f"b4:dmgwave({W},3):4 c5:dmgwave({W},1):4 e5:dmgwavepreset(1,2):6"
)
S3 = (
    "c5:dmgnoise15(4,4):3 e5:dmgnoise15(3,5):3 g5:dmgnoise15(4,6):3 "
    "c5:dmgnoise7(3,3):4 d5:dmgnoise15(2,4):4 e5:dmgnoise15(4,3):4 c5:dmgnoise15(5,4):6"
)
S4 = (
    "c4:dmgpulse2(2):4 d4:dmgpulse2(1):4 e4:dmgpulse2(2):4 f4:dmgpulse2(3):4 "
    "g4:dmgpulse2(2):4 a4:dmgpulse2(1):4 b4:dmgpulse2(3):4 c5:dmgpulse2(2):6"
)
S5 = (
    "c5:dmgnoise15(4,4):10|dmgenv:15:0:2 e5:dmgnoise15(3,5):10|dmgenv:12:0:2 "
    "g5:dmgnoise15(4,6):10|dmgenv:15:0:1 c5:dmgnoise7(3,3):12|dmgenv:15:0:3"
)
S6 = (
    "c4:dmgpulse2(2):1|dmglen:48:1 c4:dmgpulse2(2):1|dmglen:48:1 "
    "e4:dmgpulse2(1):1|dmglen:40:1 g4:dmgpulse2(2):1|dmglen:56:1 "
    "c5:dmgpulse2(2):2|dmglen:32:1"
)
S7 = (
    "c4:dmgpulse2(2):3|dmgpan:left e4:dmgpulse2(2):3|dmgpan:right "
    "g4:dmgpulse2(2):4 c4:dmgpulse2(1):2|dmgpan:left e4:dmgpulse2(1):2|dmgpan:right"
)

SOUNDS = [S0, S1, S2, S3, S4, S5, S6, S7]

DEMOS = [
    ("ch1 dmgpulse1", "square scale c4-c5 duty 2 no sweep"),
    ("ch1 + sweep", "pace/shift add freq then overflow mute"),
    ("ch3 wave ram", "cart preset 0/1 + inline nr32 levels"),
    ("ch4 noise", "15/7-bit lfsr nr43 div+shift"),
    ("ch2 dmgpulse2", "pulse no sweep same as gb ch2"),
    ("ch4 + dmgenv", "hw vol envelope 64hz steps"),
    ("ch2 + dmglen", "256hz length ctr shorter=higher load"),
    ("ch2 + dmgpan", "nr51 route left right then both"),
]


def init():
    _load_wave_cart()
    for i in range(len(SOUNDS)):
        k7.set_sound(i, SOUNDS[i])


def update():
    global _current
    if k7.btnp(0):
        _current = 7 if _current < 0 else (_current - 1) % 8
        k7.sfx(_current)
    if k7.btnp(1):
        _current = (_current + 1) % 8
        k7.sfx(_current)


def draw():
    k7.cls(1)
    k7.rectfill(0, 0, 255, 14, 2)
    k7.print("dmg demo", 4, 4, 7)
    k7.print("< > demo + play", 148, 4, 6)
    k7.print("< > = prev / next  (stops last)", 4, 14, 6)
    y0 = 24
    for i in range(8):
        title, ear = DEMOS[i]
        row = y0 + i * 20
        hi = _current == i
        c1 = 14 if hi else 11
        c2 = 14 if hi else 5
        k7.print(f"#{i} {title}", 4, row, c1)
        k7.print(ear, 10, row + 9, c2)
    if _current < 0:
        k7.print("press left or right", 4, 188, 6)
    k7.print("cart=2 waves dmgwavepreset(0)(1)", 4, 198, 5)
    k7.draw_to_canvas(CANVAS_ID)


def game_loop():
    update()
    draw()


init()
js.game_loop_js = game_loop
