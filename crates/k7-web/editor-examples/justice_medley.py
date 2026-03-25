# Justice medley → K7 music-track notation (one token per step).
#
# Transcription from tutorial-style breakdown (letters = pitch; * = sharp), “all in octaves”
# on piano → here the upper octave is written as d4… stabs; LH line uses d3 / g#3 bass.
# https://www.youtube.com/watch?v=Cbu9QmEgQZA
#
# Also: MuseScore piano sketch https://musescore.com/user/31708009/scores/7578644
#
# INTRO: (D-F-D-E-D-F-D) x3, then G-A-A# - A#-C-C# - G
# VERSE: DDDED DDDFD D  — every 4 bars → DDDED DDDED, bridge G-A-A# … A, then back to verse
# MELODY: RH D-FF-DDE-FF-DD ; LH D - G# - DD
# OUTRO: DDEDAFD (loop)

import js
import math

k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256

MUSIC_STEP_MS = 178.0
MUSIC_START_MS = 0.0
SECTION_BOUNDS = []
TOTAL_STEPS = 0
t = 0.0

_SQ = "square|envelope:perc|hp:bright"
_BS = "saw|lowpass:dark"


def _sq(pitch):
    return "%s:%s" % (pitch, _SQ)


def _bs(pitch):
    return "%s:%s" % (pitch, _BS)


def _tok(s):
    return " ".join(s.split())


def build_track(sections):
    """sections: list of (display_name, token_chunk_str) → flat track + step ranges for UI."""
    global SECTION_BOUNDS, TOTAL_STEPS
    bounds = []
    parts = []
    acc = 0
    for name, chunk in sections:
        tokens = _tok(chunk).split()
        n = len(tokens)
        bounds.append((acc, acc + n, name))
        acc += n
        parts.extend(tokens)
    SECTION_BOUNDS = bounds
    TOTAL_STEPS = len(parts)
    return " ".join(parts)


# --- INTRO: D-F-D-E-D-F-D x3, then G-A-A# - A#-C-C# - G ---
_DFDE_LINE = " ".join(
    [_sq("d4"), _sq("f4"), _sq("d4"), _sq("e4"), _sq("d4"), _sq("f4"), _sq("d4")]
)
_INTRO_HEAD = " ".join([_DFDE_LINE, _DFDE_LINE, _DFDE_LINE])
_INTRO_TAIL = " ".join(
    [
        _sq("g4"),
        _sq("a4"),
        _sq("a#4"),
        "-",
        _sq("a#4"),
        _sq("c5"),
        _sq("c#5"),
        "-",
        _sq("g4"),
    ]
)
_INTRO_FULL = _INTRO_HEAD + " " + _INTRO_TAIL

# --- VERSE cell: DDDED + DDDFD + D ---
_DDDED = " ".join([_sq("d4"), _sq("d4"), _sq("d4"), _sq("e4"), _sq("d4")])
_DDDFD = " ".join([_sq("d4"), _sq("d4"), _sq("d4"), _sq("f4"), _sq("d4")])
_VERSE_BAR = " ".join([_DDDED, _DDDFD, _sq("d4")])

# Four verse bars, then bridge: DDDED DDDED + G-A-A# - A#-C-C# - A, then two verse bars again
_VERSE_X4 = " ".join([_VERSE_BAR] * 4)
_BRIDGE_DOUBLE = " ".join([_DDDED, _DDDED])
_BRIDGE_TAIL = " ".join(
    [
        _sq("g4"),
        _sq("a4"),
        _sq("a#4"),
        "-",
        _sq("a#4"),
        _sq("c5"),
        _sq("c#5"),
        "-",
        _sq("a4"),
    ]
)
_BRIDGE_FULL = " ".join([_BRIDGE_DOUBLE, _BRIDGE_TAIL])
_VERSE_RETURN = " ".join([_VERSE_BAR] * 2)

# --- MELODY: RH then LH (mono tracker; piano plays both hands together) ---
_MELODY_RH = " ".join(
    [
        _sq("d4"),
        _sq("f4"),
        _sq("f4"),
        _sq("d4"),
        _sq("d4"),
        _sq("e4"),
        _sq("f4"),
        _sq("f4"),
        _sq("d4"),
        _sq("d4"),
    ]
)
_MELODY_LH = " ".join([_bs("d3"), "-", _bs("g#3"), "-", _bs("d3"), _bs("d3")])

# --- OUTRO: DDEDAFD x many ---
_OUTRO_CELL = " ".join(
    [_sq("d4"), _sq("d4"), _sq("e4"), _sq("d4"), _sq("a4"), _sq("f4"), _sq("d4")]
)
_OUTRO = " ".join([_OUTRO_CELL] * 18)

_MEDLEY_PARTS = [
    ("INTRO", _INTRO_FULL),
    ("VERSE x4", _VERSE_X4),
    ("BRIDGE", _BRIDGE_FULL),
    ("VERSE x2", _VERSE_RETURN),
    ("MELODY RH", _MELODY_RH),
    ("MELODY LH", _MELODY_LH),
    ("MELODY RH", _MELODY_RH),
    ("OUTRO", _OUTRO),
]

MEDLEY = build_track(_MEDLEY_PARTS)


def music_step_index():
    if MUSIC_START_MS <= 0 or TOTAL_STEPS <= 0:
        return 0
    return int((float(js.Date.now()) - MUSIC_START_MS) / max(1.0, MUSIC_STEP_MS))


def music_step_ease():
    if MUSIC_START_MS <= 0:
        return 0.0
    frac = ((float(js.Date.now()) - MUSIC_START_MS) / max(1.0, MUSIC_STEP_MS)) % 1.0
    return 0.5 - 0.5 * math.cos(frac * math.pi)


def current_section_name():
    if not SECTION_BOUNDS or TOTAL_STEPS <= 0:
        return "—"
    step = music_step_index() % TOTAL_STEPS
    for lo, hi, name in SECTION_BOUNDS:
        if lo <= step < hi:
            return name
    return SECTION_BOUNDS[-1][2]


def init():
    global MUSIC_START_MS, t
    t = 0.0
    k7.switch_palette("pico8")
    k7.set_music_step_ms(int(MUSIC_STEP_MS))
    k7.set_music_track(0, MEDLEY)
    k7.play_music(0, 0)
    MUSIC_START_MS = float(js.Date.now())


def update():
    global t, MUSIC_START_MS
    t += 0.035
    if k7.btnp(4):
        k7.play_music(0, 0)
        MUSIC_START_MS = float(js.Date.now())


def draw():
    k7.cls(1)
    step = music_step_index() % max(1, TOTAL_STEPS)
    ease = music_step_ease()

    for y in range(0, H, 4):
        a = int(18 * (1.0 - abs(y - H // 2) / (H * 0.6)))
        if a > 0:
            k7.rectfill_rgba(0, y, W - 1, y, 20, 10, 40, min(90, a))

    k7.set_font("pico8")
    k7.print("JUSTICE MEDLEY", 76, 14, 10)
    k7.print("YT TRANSCRIPTION", 72, 26, 9)
    sec = current_section_name()
    k7.print("NOW:", 12, 52, 6)
    k7.print(sec[:28], 12, 64, 11)

    cx = W // 2
    cy = 108
    s = int(10 + 8 * ease)
    k7.rectfill_rgba(cx - s // 2, cy - 2, cx + s // 2, cy + 2, 255, 210, 90, 240)
    k7.rectfill_rgba(cx - 2, cy - s // 2, cx + 2, cy + s // 2, 255, 210, 90, 240)

    bar_w = 10
    gap = 6
    base_x = (W - (6 * bar_w + 5 * gap)) // 2
    for i in range(6):
        h = int(12 + 22 * (0.5 + 0.5 * math.sin(t * 3.0 + i * 0.9)) * (0.6 + 0.4 * ease))
        x0 = base_x + i * (bar_w + gap)
        y0 = H - 36 - h
        k7.rectfill_rgba(x0, y0, x0 + bar_w - 1, H - 36, 180, 80, 220, 220)

    k7.print("STEP %d / %d" % (step, max(1, TOTAL_STEPS) - 1), 68, H - 24, 5)
    k7.print("Z: RESTART TRACK", 72, H - 14, 6)
    k7.draw_to_canvas(CANVAS_ID)


def game_loop():
    update()
    draw()


init()
js.game_loop_js = game_loop
