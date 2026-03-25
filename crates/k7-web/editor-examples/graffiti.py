# K7 Graffiti — “K7 - OPEN FANTASY CONSOLE” on a brick wall (BBC font = big tag).
# Spray build animation + techno party loop on channel 0.

import js
import math
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256

# Big tag: BBC glyphs (~8px wide); ADV spaces origins a bit wider for a slightly larger read.
FONT_TAG = "bbc"
ADV = 10
ROW_STEP = 14
Y_BLOCK = 40

LINE1 = "K7 - OPEN FANTASY"
LINE2 = "CONSOLE"
LINES = [LINE1, LINE2]

CHAR_TIME = 0.38
BUILD_DUR = 0.52
INTRO_PAUSE_AFTER_TAG = 0.9

# Star Wars–style crawl (full-width band; one pass synced to fast music, then demo restarts).
CRAWL_LINES = [
    "A long time ago in a",
    "console far, far away....",
    "",
    "It is a time of pixels.",
    "The K7 OPEN FANTASY",
    "CONSOLE unites Python,",
    "WASM, and chiptune sound",
    "in one tiny 256 square.",
    "",
    "Across browsers, dreamers",
    "paint walls, run sand,",
    "and chase high scores—",
    "no install required.",
    "",
    "This is not a trap.",
    "It is an invitation.",
    "Press Run. Make art.",
]
CRAWL_LINE_H = 10
CRAWL_GAP_BEFORE_REPEAT = 36
# Crawl viewport (above the floor strip at y≈158).
CRAWL_TOP = 4
CRAWL_BOTTOM = 154
# Crawl: scroll progress = music_step / CRAWL_STEPS_TOTAL; lower ms = quicker beat.
CRAWL_STEPS_TOTAL = 175
CRAWL_MUSIC_MS_NORMAL = 200
CRAWL_MUSIC_MS_FAST = 190

# Phase offsets so each silhouette moves out of sync across the screen.
DANCER_PHASES = [0.0, 1.1, 2.3, 0.5, 1.7, 2.9]

# Wall-clock sync: editor play_music uses k7.set_music_step_ms (default 200 ms per token).
MUSIC_STEP_MS = 200.0
MUSIC_START_MS = 0.0
PHASE = 0

# Eight poses per 2 s (8 × 250 ms): arms (L,R), legs (L,R), extra bob — crew hits same beat, mirrored per dancer.
# Values are “target” amplitudes scaled by ease inside each step.
DANCE_POSES = [
    (7, -7, 4, 4, 4),   # 0 downbeat: wide arms, jump prep
    (-5, 8, 5, 2, 2),   # 1 reach L / kick R
    (9, 9, 3, 3, 5),    # 2 hands high
    (4, -8, 2, 6, 3),   # 3 lean / stomp L
    (-6, -6, 6, 1, 5),  # 4 big kick R
    (8, -3, 3, 5, 3),   # 5 wave R
    (-7, 7, 4, 4, 2),   # 6 shuffle square
    (5, 5, 5, 5, 3),    # 7 bounce / pump
]

t = 0.0
paint_t = 0.0
DRIPS = []

# Techno party: long loop — several intros, dance variants, breakdown, alternate bass — less samey on repeat.
_TECHNO_INTRO = (
    "e2:saw|lowpass:dark e2:saw|lowpass:dark e3:square|envelope:perc|hp:bright e2:saw "
    "a1:square|envelope:perc e2:saw e2:saw e4:square|envelope:perc|hp:bright "
)
_TECHNO_INTRO_B = (
    "d2:saw|lowpass:dark d2:saw|lowpass:dark f3:square|envelope:perc|hp:bright d2:saw "
    "g1:square|envelope:perc d2:saw d2:saw a4:square|envelope:perc|hp:bright "
)
_TECHNO_INTRO_C = (
    "a2:saw|lowpass:dark a2:saw c3:square|envelope:perc|hp:bright a2:saw "
    "e1:square|envelope:perc a2:saw a2:saw g4:square|envelope:perc|hp:bright "
)
# Middle: driving 16ths — hats, kicks, snare, bass + leads (original + two reharm/variations).
_TECHNO_DANCE = (
    "f6:drums:hat e2:saw|lowpass:dark c5:drums:snare g5:square|envelope:perc|hp:bright "
    "f6:drums:hat d5:saw|lp:bright a1:square|envelope:perc b5:square|envelope:perc|hp:bright "
    "f6:drums:hat e2:saw|lowpass:dark g5:saw|lp:bright e4:square|envelope:perc|hp:bright "
    "f6:drums:hat c6:square|envelope:perc|hp:bright e2:saw|lowpass:dark d5:arp:trance "
    "g6:drums:hat b1:square|envelope:perc f5:lead:bright c5:drums:snare "
    "g6:drums:hat e2:saw|lowpass:dark a5:square|envelope:perc|hp:bright d4:pluck:bright "
)
_TECHNO_DANCE_B = (
    "f6:drums:hat d2:saw|lowpass:dark c5:drums:snare f5:square|envelope:perc|hp:bright "
    "f6:drums:hat e5:saw|lp:bright g1:square|envelope:perc c6:square|envelope:perc|hp:bright "
    "f6:drums:hat d2:saw|lowpass:dark a5:saw|lp:bright g4:square|envelope:perc|hp:bright "
    "f6:drums:hat b5:square|envelope:perc|hp:bright d2:saw|lowpass:dark e5:arp:trance "
    "g6:drums:hat a1:square|envelope:perc d5:lead:bright c5:drums:snare "
    "g6:drums:hat d2:saw|lowpass:dark b5:square|envelope:perc|hp:bright f4:pluck:bright "
)
_TECHNO_DANCE_C = (
    "g6:drums:hat a2:saw|lowpass:dark c5:drums:snare e5:square|envelope:perc|hp:bright "
    "g6:drums:hat d5:saw|lp:bright e1:square|envelope:perc a5:square|envelope:perc|hp:bright "
    "g6:drums:hat a2:saw|lowpass:dark f5:saw|lp:bright b4:square|envelope:perc|hp:bright "
    "g6:drums:hat g5:square|envelope:perc|hp:bright a2:saw|lowpass:dark c5:arp:trance "
    "f6:drums:hat d1:square|envelope:perc g5:lead:bright c5:drums:snare "
    "f6:drums:hat a2:saw|lowpass:dark c6:square|envelope:perc|hp:bright e4:pluck:bright "
)
# Sparse strip — breathing room before building again.
_TECHNO_BREAK = (
    "f6:drums:hat e2:saw|lowpass:dark - - "
    "f6:drums:hat a1:square|envelope:perc - e4:square|envelope:perc|hp:bright "
    "f6:drums:hat e2:saw|lowpass:dark - c5:drums:snare "
    "f6:drums:hat d2:saw|lowpass:dark - g5:square|envelope:perc|hp:bright "
    "g6:drums:hat b1:square|envelope:perc - c5:drums:snare "
    "g6:drums:hat e2:saw|lowpass:dark - a5:square|envelope:perc|hp:bright "
    "f6:drums:hat - e2:saw|lowpass:dark - "
    "f6:drums:hat - a1:square|envelope:perc e4:square|envelope:perc|hp:bright "
)
_TECHNO_OUTRO = (
    "e2:saw|lowpass:dark e2:saw e2:saw e4:square|envelope:perc|hp:bright "
    "a1:square|envelope:perc e2:saw e2:saw c4:square|envelope:perc|hp:bright "
    "e2:saw|lowpass:dark e2:saw e3:square|envelope:perc e2:saw|lowpass:dark "
    "b1:square|envelope:perc e2:saw e2:saw e5:square|envelope:perc|hp:bright "
)
_TECHNO_OUTRO_B = (
    "d2:saw|lowpass:dark d2:saw d2:saw f4:square|envelope:perc|hp:bright "
    "g1:square|envelope:perc d2:saw d2:saw a3:square|envelope:perc|hp:bright "
    "d2:saw|lowpass:dark d2:saw f3:square|envelope:perc d2:saw|lowpass:dark "
    "a1:square|envelope:perc d2:saw d2:saw d5:square|envelope:perc|hp:bright "
)
_TECHNO_INTRO_D = (
    "g2:saw|lowpass:dark g2:saw|lowpass:dark b3:square|envelope:perc|hp:bright g2:saw "
    "d1:square|envelope:perc g2:saw g2:saw b4:square|envelope:perc|hp:bright "
)
_TECHNO_INTRO_E = (
    "b1:square|envelope:perc b2:saw|lowpass:dark b2:saw d4:square|envelope:perc|hp:bright "
    "b1:square|envelope:perc b2:saw b2:saw f4:square|envelope:perc|hp:bright "
)
_TECHNO_INTRO_F = (
    "f2:saw|lowpass:dark f2:saw c3:square|envelope:perc|hp:bright f2:saw "
    "c1:square|envelope:perc f2:saw f2:saw a4:square|envelope:perc|hp:bright "
)
_TECHNO_DANCE_D = (
    "f6:drums:hat b2:saw|lowpass:dark c5:drums:snare d5:square|envelope:perc|hp:bright "
    "f6:drums:hat e5:saw|lp:bright e1:square|envelope:perc g5:square|envelope:perc|hp:bright "
    "f6:drums:hat b2:saw|lowpass:dark a5:saw|lp:bright c5:square|envelope:perc|hp:bright "
    "f6:drums:hat f5:square|envelope:perc|hp:bright b2:saw|lowpass:dark e5:arp:trance "
    "g6:drums:hat d1:square|envelope:perc c6:lead:bright c5:drums:snare "
    "g6:drums:hat b2:saw|lowpass:dark g5:square|envelope:perc|hp:bright a4:pluck:bright "
)
_TECHNO_DANCE_E = (
    "g6:drums:hat g2:saw|lowpass:dark c5:drums:snare b5:square|envelope:perc|hp:bright "
    "g6:drums:hat e5:saw|lp:bright d1:square|envelope:perc a5:square|envelope:perc|hp:bright "
    "g6:drums:hat g2:saw|lowpass:dark d5:saw|lp:bright e4:square|envelope:perc|hp:bright "
    "g6:drums:hat c6:square|envelope:perc|hp:bright g2:saw|lowpass:dark b4:arp:trance "
    "f6:drums:hat a1:square|envelope:perc f5:lead:bright c5:drums:snare "
    "f6:drums:hat g2:saw|lowpass:dark e6:square|envelope:perc|hp:bright d4:pluck:bright "
)
_TECHNO_DANCE_F = (
    "f6:drums:hat f2:saw|lowpass:dark c5:drums:snare g5:square|envelope:perc|hp:bright "
    "f6:drums:hat c5:saw|lp:bright g1:square|envelope:perc b5:square|envelope:perc|hp:bright "
    "f6:drums:hat f2:saw|lowpass:dark e5:saw|lp:bright d5:square|envelope:perc|hp:bright "
    "f6:drums:hat a5:square|envelope:perc|hp:bright f2:saw|lowpass:dark g5:arp:trance "
    "g6:drums:hat b1:square|envelope:perc e5:lead:bright c5:drums:snare "
    "g6:drums:hat f2:saw|lowpass:dark d6:square|envelope:perc|hp:bright a4:pluck:bright "
)
_TECHNO_DANCE_G = (
    "g6:drums:hat c3:saw|lowpass:dark c5:drums:snare e5:square|envelope:perc|hp:bright "
    "g6:drums:hat g5:saw|lp:bright g1:square|envelope:perc b5:square|envelope:perc|hp:bright "
    "g6:drums:hat c3:saw|lowpass:dark a5:saw|lp:bright d5:square|envelope:perc|hp:bright "
    "g6:drums:hat f5:square|envelope:perc|hp:bright c3:saw|lowpass:dark e5:arp:trance "
    "f6:drums:hat d1:square|envelope:perc g5:lead:bright c5:drums:snare "
    "f6:drums:hat c3:saw|lowpass:dark c6:square|envelope:perc|hp:bright f4:pluck:bright "
)
# Longer near-silent / hat-only strips.
_TECHNO_BREAK_B = (
    "g6:drums:hat - - - "
    "f6:drums:hat - e2:saw|lowpass:dark - "
    "g6:drums:hat - - c5:drums:snare "
    "f6:drums:hat - - - "
    "g6:drums:hat b1:square|envelope:perc - - "
    "f6:drums:hat - - e4:square|envelope:perc|hp:bright "
    "g6:drums:hat - d2:saw|lowpass:dark - "
    "f6:drums:hat - - - "
    "g6:drums:hat - - a1:square|envelope:perc "
    "f6:drums:hat c5:drums:snare - - "
)
_TECHNO_BREAK_C = (
    "f6:drums:hat a2:saw|lowpass:dark - - "
    "- f6:drums:hat - g2:saw|lowpass:dark "
    "- - f6:drums:hat c5:drums:snare "
    "e4:square|envelope:perc|hp:bright - - f6:drums:hat "
    "- d2:saw|lowpass:dark - g6:drums:hat "
    "- - - f6:drums:hat "
)
_TECHNO_OUTRO_C = (
    "a2:saw|lowpass:dark a2:saw a2:saw c5:square|envelope:perc|hp:bright "
    "e1:square|envelope:perc a2:saw a2:saw f4:square|envelope:perc|hp:bright "
    "a2:saw|lowpass:dark a2:saw b3:square|envelope:perc a2:saw|lowpass:dark "
    "g1:square|envelope:perc a2:saw a2:saw e5:square|envelope:perc|hp:bright "
)
_TECHNO_OUTRO_D = (
    "g2:saw|lowpass:dark g2:saw g2:saw b4:square|envelope:perc|hp:bright "
    "d1:square|envelope:perc g2:saw g2:saw d5:square|envelope:perc|hp:bright "
    "g2:saw|lowpass:dark g2:saw e4:square|envelope:perc g2:saw|lowpass:dark "
    "b1:square|envelope:perc g2:saw g2:saw g5:square|envelope:perc|hp:bright "
)


def _strip_track(s):
    return " ".join(s.replace("  ", " ").split())


_TECHNO_CORE = _strip_track(_TECHNO_INTRO + _TECHNO_DANCE + _TECHNO_OUTRO)
_TECHNO_BRIDGE = _strip_track(
    _TECHNO_INTRO_B + _TECHNO_DANCE_B + _TECHNO_OUTRO_B + _TECHNO_BREAK + _TECHNO_INTRO_C + _TECHNO_DANCE_C + _TECHNO_OUTRO
)
_TECHNO_MIDDLE = _strip_track(
    _TECHNO_INTRO_D + _TECHNO_DANCE_D + _TECHNO_OUTRO
    + _TECHNO_BREAK_B
    + _TECHNO_INTRO_E + _TECHNO_DANCE_E + _TECHNO_OUTRO_B
    + _TECHNO_DANCE_F + _TECHNO_OUTRO_C
    + _TECHNO_INTRO_F + _TECHNO_DANCE_G + _TECHNO_OUTRO_D
    + _TECHNO_BREAK_C
    + _TECHNO_INTRO + _TECHNO_DANCE_B + _TECHNO_OUTRO_B
    + _TECHNO_INTRO_C + _TECHNO_DANCE + _TECHNO_OUTRO
)
# Very long loop: core → repeats & bridges → extended middle (many keys / grooves) → mirror back.
_TECHNO = _strip_track(
    _TECHNO_CORE + " "
    + _TECHNO_DANCE + " " + _TECHNO_OUTRO + " "
    + _TECHNO_BRIDGE + " "
    + _TECHNO_DANCE_B + " " + _TECHNO_OUTRO_B + " "
    + _TECHNO_MIDDLE + " "
    + _TECHNO_BRIDGE + " "
    + _TECHNO_DANCE_C + " " + _TECHNO_OUTRO + " "
    + _TECHNO_INTRO_B + _TECHNO_DANCE + " " + _TECHNO_OUTRO_B
)


def char_build(phase_t, char_index, char_time, build_dur):
    start = char_index * char_time
    return max(0.0, min(1.0, (phase_t - start) / build_dur))


def num_tag_chars():
    return sum(len(s) for s in LINES)


def tag_intro_duration():
    n = num_tag_chars()
    if n <= 0:
        return 0.0
    return (n - 1) * CHAR_TIME + BUILD_DUR + INTRO_PAUSE_AFTER_TAG


def init():
    global t, paint_t, DRIPS, MUSIC_START_MS, PHASE, MUSIC_STEP_MS
    t = 0.0
    paint_t = 0.0
    DRIPS = []
    PHASE = 0
    MUSIC_STEP_MS = float(CRAWL_MUSIC_MS_NORMAL)
    k7.set_music_step_ms(CRAWL_MUSIC_MS_NORMAL)
    y0 = Y_BLOCK
    for row, line in enumerate(LINES):
        cx = W // 2 - (len(line) * ADV) // 2
        base_y = y0 + row * ROW_STEP
        span = len(line) * ADV + 20
        for i in range(12 + row * 4):
            u = (i * 41 + row * 7) % max(1, span)
            x = cx - 10 + u
            y_start = base_y + 11 + (i * 3) % 6
            ln = 14 + (i * 11) % 24
            hue = (i * 0.37 + row * 0.2) % 1.0
            r = int(160 + 95 * math.sin(hue * 6.28))
            g = int(50 + 110 * math.sin(hue * 6.28 + 2.0))
            b = int(180 + 75 * math.sin(hue * 6.28 + 4.0))
            DRIPS.append((x, y_start, ln, r, g, b))

    k7.set_music_track(0, _TECHNO)
    k7.play_music(0, 0)
    MUSIC_START_MS = float(js.Date.now())


def start_crawl_phase():
    global PHASE, MUSIC_START_MS, MUSIC_STEP_MS
    PHASE = 1
    MUSIC_STEP_MS = float(CRAWL_MUSIC_MS_FAST)
    k7.set_music_step_ms(CRAWL_MUSIC_MS_FAST)
    k7.play_music(0, 0)
    MUSIC_START_MS = float(js.Date.now())


def restart_demo():
    init()


def music_step_index():
    """Which music-step slice we’re in (locks dance poses to the music grid)."""
    if MUSIC_START_MS <= 0:
        return 0
    return int((float(js.Date.now()) - MUSIC_START_MS) / max(1.0, MUSIC_STEP_MS))


def music_step_ease():
    """0→1 within the current 250 ms step (smooth hit on the beat)."""
    if MUSIC_START_MS <= 0:
        return 0.0
    frac = ((float(js.Date.now()) - MUSIC_START_MS) / max(1.0, MUSIC_STEP_MS)) % 1.0
    return 0.5 - 0.5 * math.cos(frac * math.pi)


def update():
    global t, paint_t
    t += 0.035
    paint_t += 0.035
    if PHASE == 0:
        if paint_t >= tag_intro_duration():
            start_crawl_phase()
    elif PHASE == 1:
        if music_step_index() >= CRAWL_STEPS_TOTAL:
            restart_demo()


def draw_bricks():
    """Running-bond brick with mortar, per-brick colour noise, edge light/shade, light weathering."""
    gap = 2
    BW, BH = 20, 11
    mr, mg, mb = 32, 29, 26
    k7.cls(1)
    k7.rectfill_rgba(0, 0, W - 1, H - 1, mr, mg, mb, 255)

    row = 0
    y = 0
    while y <= H - 4:
        stagger = ((BW + gap) // 2) if (row % 2) else 0
        x = -stagger
        col = 0
        while x < W + BW:
            bx = x
            x0 = max(0, bx)
            x1 = min(bx + BW - gap - 1, W - 1)
            y0b = y
            y1b = min(y + BH - gap - 1, H - 1)
            if x1 > x0 and y1b > y0b:
                seed = abs((row * 97 + col * 53 + row * col * 5) % 997)
                r = 96 + seed % 58
                g = 42 + (seed // 3) % 34
                b = 26 + (seed // 7) % 40
                if seed % 13 < 2:
                    r = min(255, r + 22)
                    g = min(255, g + 8)
                elif seed % 17 < 2:
                    r = max(72, r - 28)
                    g = max(30, g - 12)
                    b = max(14, b - 10)
                k7.rectfill_rgba(x0, y0b, x1, y1b, r, g, b, 255)
                k7.rectfill_rgba(
                    x0, y0b, x1, min(y0b + 1, y1b),
                    min(255, r + 32), min(255, g + 14), min(255, b + 10), 140,
                )
                k7.rectfill_rgba(
                    x0, max(y0b, y1b - 1), x1, y1b,
                    max(0, r - 38), max(0, g - 20), max(0, b - 18), 110,
                )
                if seed % 9 == 0:
                    k7.rectfill_rgba(x0 + 2, y0b + 3, x0 + 5, y0b + 5, 48, 40, 32, 70)
                if seed % 11 == 0:
                    k7.pset_rgba(x1 - 2, y0b + 4, 70, 62, 52, 90)
            x += BW + gap
            col += 1
        y += BH + gap
        row += 1

    for i in range(22):
        sx = (i * 41 + 19) % (W - 6)
        sy = (i * 37 + 5) % (H - 6)
        k7.rectfill_rgba(sx, sy, sx + 4, sy + 2, 55, 62, 48, 28)
    for y in range(0, H, 4):
        a = int(22 * (abs(y - H // 2) / (H * 0.55)))
        if a > 0:
            k7.rectfill_rgba(0, y, 5, y + 2, 0, 0, 0, min(200, a))
            k7.rectfill_rgba(W - 6, y, W - 1, y + 2, 0, 0, 0, min(200, a))


def spray_burst(px, py, intensity, br, bg, bb, seed):
    if intensity <= 0.001:
        return
    n = int(32 + 48 * intensity)
    for i in range(n):
        ang = (seed * 1.1 + i * 0.89 + t * 2.0) % 6.28
        dist = (i % 9) * (0.45 + 0.55 * intensity) + math.sin(i * 0.7) * 2.5
        dx = int(math.cos(ang) * dist + math.sin(t * 5 + i) * 1.8)
        dy = int(math.sin(ang) * dist * 0.75 + math.cos(t * 4 + i) * 1.2)
        x, y = px + dx, py + dy
        if 0 <= x < W and 0 <= y < H:
            a = int((45 + 100 * intensity) * (0.5 + 0.5 * math.sin(i * 0.3 + t)))
            k7.pset_rgba(
                x, y,
                max(0, min(255, br + i % 5 - 2)),
                max(0, min(255, bg + i % 4 - 2)),
                max(0, min(255, bb + i % 5 - 2)),
                min(255, int(a * intensity)),
            )


def draw_graffiti_char(ch, bx, by, gidx, strength):
    """Large BBC glyphs: fat outline + fill + chrome (strength = spray progress)."""
    if strength <= 0.0:
        return
    hue = (t * 0.12 + gidx * 0.19) % 1.0
    fr = int(118 + 127 * math.sin(hue * 6.28))
    fg = int(118 + 127 * math.sin(hue * 6.28 + 2.09))
    fb = int(118 + 127 * math.sin(hue * 6.28 + 4.18))

    mist = max(0.0, 1.0 - strength / 0.35) if strength < 0.35 else 0.0
    if mist > 0:
        spray_burst(bx + ADV // 2, by + 6, mist, fr, fg, fb, gidx * 17)

    outline_alpha = int(255 * max(0.0, min(1.0, (strength - 0.12) / 0.55)))
    fill_alpha = int(255 * max(0.0, min(1.0, (strength - 0.38) / 0.62)))
    hi_alpha = int(200 * max(0.0, min(1.0, (strength - 0.72) / 0.28)))

    if outline_alpha > 0:
        outline = (18, 12, 28)
        for oy in range(-6, 7):
            for ox in range(-6, 7):
                if ox * ox + oy * oy > 30:
                    continue
                k7.print_rgba(
                    ch, bx + ox, by + oy,
                    outline[0], outline[1], outline[2],
                    min(255, outline_alpha),
                )

    if fill_alpha > 30:
        k7.print_rgba(ch, bx + 6, by + 8, 35, 18, 45, min(220, fill_alpha - 20))
        k7.print_rgba(ch, bx, by, fr, fg, fb, fill_alpha)

    if hi_alpha > 0:
        k7.print_rgba(ch, bx - 3, by - 3, 255, 255, 255, hi_alpha)


def draw_drips(strength_gate):
    if strength_gate < 0.92:
        return
    wet = (strength_gate - 0.92) / 0.08
    for x, y0, ln, r, g, b in DRIPS:
        for k in range(ln):
            yy = y0 + k
            if yy >= H:
                break
            fade = (1.0 - k / max(1.0, float(ln))) ** 1.4
            a = int(220 * fade * fade * wet)
            wobble = int(1.2 * math.sin(t * 3.2 + k * 0.35 + x * 0.1))
            k7.pset_rgba(x + wobble, yy, r, g, b, min(255, a))


def nozzle(px, py):
    k7.rectfill_rgba(px - 2, py - 2, px + 2, py + 2, 255, 250, 220, 160)
    k7.pset_rgba(px + 3, py, 210, 210, 220, 140)


def draw_star_wars_crawl():
    """Full-width crawl during PHASE 1; scroll driven by music steps (same clock as dancers)."""
    if PHASE != 1:
        return
    k7.set_font("pico8")
    n = len(CRAWL_LINES)
    total_h = float(n * CRAWL_LINE_H + CRAWL_GAP_BEFORE_REPEAT)
    prog = min(1.0, float(music_step_index()) / float(max(1, CRAWL_STEPS_TOTAL)))
    scroll = prog * total_h

    margin = 2
    k7.rectfill_rgba(margin, CRAWL_TOP - 2, W - 1 - margin, CRAWL_BOTTOM + 2, 8, 6, 14, 215)
    band = max(8, (CRAWL_BOTTOM - CRAWL_TOP) // 5)
    for yy in range(CRAWL_TOP, min(CRAWL_TOP + band, CRAWL_BOTTOM)):
        a = int(100 * (yy - CRAWL_TOP) / max(1, band))
        k7.rectfill_rgba(margin, yy, W - 1 - margin, yy, 0, 0, 0, min(120, a))
    for yy in range(max(CRAWL_TOP, CRAWL_BOTTOM - band), CRAWL_BOTTOM + 1):
        a = int(85 * (CRAWL_BOTTOM - yy) / max(1, band))
        k7.rectfill_rgba(margin, yy, W - 1 - margin, yy, 0, 0, 0, min(100, a))

    gold_r, gold_g, gold_b = 255, 210, 96
    shadow = (40, 28, 10)

    for i in range(n):
        line = CRAWL_LINES[i]
        y = int(CRAWL_BOTTOM - scroll + i * CRAWL_LINE_H)
        if y < CRAWL_TOP - CRAWL_LINE_H or y > CRAWL_BOTTOM + 2:
            continue
        if not line.strip():
            continue
        adv = 4
        x = max(margin, W // 2 - (len(line) * adv) // 2)
        k7.print_rgba(line, x + 1, y + 1, shadow[0], shadow[1], shadow[2], 200)
        k7.print_rgba(line, x, y, gold_r, gold_g, gold_b, 255)


def draw_dancing_crowd():
    """Neon silhouettes roam the frame; limb poses follow music steps (tempo matches current phase)."""
    step = music_step_index()
    ease = music_step_ease()
    m = step % len(DANCE_POSES)
    al0, ar0, ll0, lr0, bob0 = DANCE_POSES[m]

    for idx, ph in enumerate(DANCER_PHASES):
        u = t * (0.52 + idx * 0.062) + ph
        v = t * (0.44 + idx * 0.051) + ph * 2.17
        cx = int(W / 2 + (W / 2 - 22) * math.sin(u))
        foot_y = int(158 + (H - 24 - 158) * (0.5 + 0.5 * math.sin(v * 0.88 + ph)))
        cx += int(14 * math.sin(v * 1.1 + idx))
        foot_y += int(6 * math.sin(u * 1.4))
        cx = max(18, min(W - 18, cx))
        foot_y = max(92, min(H - 6, foot_y))

        wiggle = 0.35 + 0.65 * ease
        al, ar = al0 * wiggle, ar0 * wiggle
        ll, lr = ll0 * wiggle, lr0 * wiggle
        if idx % 2 == 1:
            al, ar = -ar, -al
            ll, lr = lr, ll
        micro = 1.2 * math.sin(t * 14.0 + ph * 3.0)
        arm_l = int(al + micro)
        arm_r = int(ar - micro * 0.8)
        leg_l = int(ll + math.sin(t * 13.0 + ph) * 1.5)
        leg_r = int(lr - math.sin(t * 13.0 + ph) * 1.5)
        bob = int(bob0 * ease + 1.5 * math.sin(t * 16.0 + ph))
        hip_sway = int(3.0 * math.sin(t * 9.0 + ph) + (m % 3) * ease)

        foot_y += bob
        foot_y = max(92, min(H - 6, foot_y))
        hue = (idx * 0.17 + t * 0.08) % 1.0
        br = int(120 + 100 * math.sin(hue * 6.28))
        bg = int(120 + 100 * math.sin(hue * 6.28 + 2.09))
        bb = int(200 + 55 * math.sin(hue * 6.28 + 4.18))

        lx0 = cx - 5 + hip_sway + leg_l
        k7.rectfill_rgba(lx0, foot_y - 5, lx0 + 3, foot_y, br, bg, bb, 255)
        rx0 = cx + 2 + hip_sway - leg_r
        k7.rectfill_rgba(rx0, foot_y - 5, rx0 + 3, foot_y, br, bg, bb, 255)

        k7.rectfill_rgba(
            cx - 4 + hip_sway, foot_y - 16,
            cx + 4 + hip_sway, foot_y - 5,
            max(40, br - 30), max(40, bg - 30), max(60, bb - 20), 255,
        )

        k7.rectfill_rgba(
            cx - 10 + hip_sway + arm_l, foot_y - 15,
            cx - 4 + hip_sway + arm_l, foot_y - 9,
            min(255, br + 40), min(255, bg + 50), 255, 240,
        )
        k7.rectfill_rgba(
            cx + 4 + hip_sway + arm_r, foot_y - 15,
            cx + 10 + hip_sway + arm_r, foot_y - 9,
            min(255, br + 40), min(255, bg + 50), 255, 240,
        )

        hx = cx + hip_sway
        k7.rectfill_rgba(hx - 3, foot_y - 22, hx + 3, foot_y - 16, 255, 230, 210, 255)


def draw():
    draw_bricks()
    if PHASE == 1:
        draw_star_wars_crawl()

    k7.set_font(FONT_TAG)

    num_chars = num_tag_chars()
    phase_t = paint_t if PHASE == 0 else 1e9

    y_block = Y_BLOCK
    char_index = 0
    current_nx = W // 2
    current_ny = y_block + 7
    spray_active = False

    for row, line in enumerate(LINES):
        cx = W // 2 - (len(line) * ADV) // 2
        by = y_block + row * ROW_STEP + int(1.0 * math.sin(t * 1.4 + row))
        for i, ch in enumerate(line):
            bx = cx + i * ADV
            st = char_build(phase_t, char_index, CHAR_TIME, BUILD_DUR)
            draw_graffiti_char(ch, bx, by, char_index + row * 32, st)
            if 0.06 < st < 0.97:
                spray_active = True
                jitter_x = math.sin(t * 11 + char_index) * 2.0
                jitter_y = math.cos(t * 9 + char_index * 0.7) * 1.3
                current_nx = int(bx + ADV // 2 + jitter_x)
                current_ny = int(by + 6 + jitter_y)
            char_index += 1

    if PHASE == 0:
        done_chars = 0.0
        for c in range(num_chars):
            done_chars += char_build(phase_t, c, CHAR_TIME, BUILD_DUR)
        strength_gate = done_chars / max(1.0, float(num_chars))
    else:
        strength_gate = 1.0

    draw_drips(strength_gate)

    if spray_active:
        nozzle(current_nx, current_ny)

    k7.set_font("pico8")

    k7.rectfill_rgba(0, 158, W - 1, 166, 38, 36, 42, 210)
    k7.rectfill_rgba(0, 166, W - 1, H - 1, 28, 28, 32, 255)

    draw_dancing_crowd()

    k7.draw_to_canvas(CANVAS_ID)


def game_loop():
    update()
    draw()


init()
js.game_loop_js = game_loop
