# K7 Showcase — 90s demoscene. Logo from logo.png into sprite sheet only (map bank not used).
# Copper, plasma, scroller, fire, tunnel. k7.apply_logo_from_preload() loads logo into sprites.

import js
import math
import random
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
SCENE_DURATION = 480
SCENE_NAMES = ("INTRO", "COPPER", "PLASMA", "MAP", "SCROLLER", "FIRE", "TUNNEL", "CREDITS", "STARFIELD", "RASTER", "HYPNO", "ZOOM")
N_SCENES = 12
LOGOW, LOGOH = 24, 8
LOGO_BASE = 1
scroll_x = 0.0
t = 0.0
heat = []
user_scene = None
scene_start_frame = 0
stars = []
master_vol = 0.7
FW, FH = 48, 48
FIRE_COLORS = (0, 4, 8, 9, 10, 11, 15, 7)
FIRE_THRESHOLDS = (0.02, 0.10, 0.22, 0.40, 0.58, 0.75, 0.90, 1.01)
logo_from_preload = False
LOGO_FALLBACK = [
    [0,0,1,1,0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,1,1,1,1,2,2,2,2,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]
CREDITS = [
    "  *** K7 ***  FANTASY CONSOLE IN THE BROWSER  ",
    "  GFX * SOUND * MAP * SPRITES * INPUT * PYTHON  ",
    "  PICO-8 STYLE * PYODIDE * RUST * WASM  ",
    "  GREETZ TO THE DEMOSCENE * 90S FOREVER  ",
]

def heat_to_color(v):
    if v <= 0: return 0
    for i in range(len(FIRE_THRESHOLDS)):
        if v < FIRE_THRESHOLDS[i]: return FIRE_COLORS[i]
    return FIRE_COLORS[-1]

def init_logo():
    global logo_from_preload
    logo_from_preload = k7.apply_logo_from_preload()
    if logo_from_preload:
        return
    for sy in range(8):
        for sx in range(8):
            k7.sset(8 + sx, sy, 11)
            k7.sset(16 + sx, sy, 9)
            k7.sset(0 + sx, sy, 0)

def init_map_logo():
    """Fill map region (0,0)-(LOGOW, LOGOH). Cell 0 = background; logo uses sprites LOGO_BASE+."""
    for cy in range(LOGOH):
        for cx in range(LOGOW):
            if logo_from_preload:
                n = LOGO_BASE + (cy * LOGOW + cx)
            else:
                v = LOGO_FALLBACK[cy][cx] if cy < len(LOGO_FALLBACK) and cx < len(LOGO_FALLBACK[0]) else 0
                n = (LOGO_BASE + v) if v else 0
            k7.mset(cx, cy, n)

def init():
    global scroll_x, t, heat, stars, user_scene, scene_start_frame, master_vol
    scroll_x = 0.0
    t = 0.0
    user_scene = None
    scene_start_frame = 0
    master_vol = 0.7
    heat = [[0.0] * FW for _ in range(FH)]
    stars = [(random.randint(0, W - 1), random.randint(0, H - 1), random.random() * 2 + 0.5) for _ in range(80)]
    init_logo()
    init_map_logo()
    k7.set_sound(0, "c2:square|envelope:perc")
    k7.set_sound(1, "e5:square|envelope:perc|hp:bright")
    k7.set_sound(2, "c4:saw|reverb:small e4:saw g4:saw")
    k7.set_sound(3, "a2:saw|reverb:large|lowpass:dark")
    k7.set_sound(4, "e4:sine|reverb:hall g4:sine b4:sine")
    k7.set_sound(5, "c3:square e3:square g3:square c4:square")
    k7.set_sound(6, "a3:triangle|reverb:small c4:triangle e4:triangle")
    k7.set_sound(7, "f4:noise|envelope:perc|hp:bright")
    k7.set_sound(8, "d5:sine|tremolo:2:0.15")
    k7.set_music_track(0, "c3 e3 g3 c4 e3 g3 c4 e4")
    k7.master_volume(master_vol)

def scene_index():
    global user_scene
    frame = k7.frame()
    if user_scene is not None:
        return user_scene
    return (frame // SCENE_DURATION) % N_SCENES

def scene_local_frame():
    frame = k7.frame()
    if user_scene is not None:
        return frame - scene_start_frame
    return frame % SCENE_DURATION

def handle_scene_keys():
    """Z/X or Left/Right: prev/next scene. C/V: volume down/up."""
    global user_scene, scene_start_frame, master_vol
    frame = k7.frame()
    cur = scene_index()
    if k7.btnp(0) or k7.btnp(4):
        user_scene = (cur - 1) % N_SCENES
        scene_start_frame = frame
    if k7.btnp(1) or k7.btnp(5):
        user_scene = (cur + 1) % N_SCENES
        scene_start_frame = frame
    if k7.btnp(6):
        master_vol = max(0.0, master_vol - 0.1)
        k7.master_volume(master_vol)
    if k7.btnp(7):
        master_vol = min(1.0, master_vol + 0.1)
        k7.master_volume(master_vol)

def draw_scene_indicator():
    """Draw scene number, key hint, and volume at bottom."""
    sc = scene_index()
    k7.print(str(sc + 1) + "/" + str(N_SCENES), W - 28, 4, 6)
    k7.print("Z X scene  C V vol", 4, H - 10, 5)
    vol_pct = int(master_vol * 100)
    k7.print(str(vol_pct) + "%", W - 20, H - 10, 6)

def apply_scene_transition():
    """Short flash at the start of each scene for a clean cut."""
    f = scene_local_frame()
    if f < 4:
        k7.flash(9, 2)

def update():
    global scroll_x, t, heat, stars
    handle_scene_keys()
    t += 0.5
    scroll_x -= 1.5
    if scroll_x < -48 * 8:
        scroll_x += 48 * 8
    frame = k7.frame()
    sc = scene_index()
    if frame <= 0:
        pass
    else:
        if frame % 32 == 1:
            k7.sfx(0)
        if frame % 16 == 1:
            k7.sfx(1)
        if frame % 128 == 1:
            k7.sfx(2)
        if frame % 256 == 1:
            k7.sfx(4)
        if frame % 64 == 1:
            k7.sfx(6)
        if sc == 0 and frame % 60 == 5:
            k7.sfx(8)
        if sc == 2 and frame % 90 == 10:
            k7.sfx(6)
        if sc == 5 and frame % 8 == 2:
            k7.sfx(7)
        if sc == 6 and frame % 40 == 5:
            k7.sfx(3)
        if sc == 8 and frame % 24 == 3:
            k7.sfx(1)
        if sc == 9 and frame % 8 == 1:
            k7.sfx(0)
        if sc == 10 and frame % 8 == 2:
            k7.sfx(2)
    if sc == 5:
        for x in range(FW):
            c = 1.0 - 0.4 * abs(x - FW//2) / (FW//2)
            heat[FH-1][x] = min(1.0, heat[FH-1][x] + random.uniform(0.5, 1.0) * c)
            if random.random() < 0.6:
                heat[FH-1][x] = min(1.0, heat[FH-1][x] + 0.4)
        for x in range(FW):
            heat[FH-2][x] = min(1.0, heat[FH-2][x] + 0.12 * heat[FH-1][x])
        for y in range(FH-2, -1, -1):
            for x in range(FW):
                xl, xr = (x-1) % FW, (x+1) % FW
                s = heat[y+1][x] + heat[y+1][xl] + heat[y+1][xr]
                up = max(0, (s/3.0)*0.28 - 0.008)
                heat[y][x] = max(0, min(1.0, up + random.uniform(-0.01, 0.015)))
    if sc == 8:
        for i in range(len(stars)):
            x, y, spd = stars[i]
            y -= spd * 3
            if y < 0:
                y = H + random.randint(0, 20)
                x = random.randint(0, W - 1)
                spd = random.random() * 2 + 0.5
            stars[i] = (x, y, spd)

def logo_tile(cy, cx):
    if logo_from_preload:
        return LOGO_BASE + (cy * LOGOW + cx)
    v = LOGO_FALLBACK[cy][cx] if cy < len(LOGO_FALLBACK) and cx < len(LOGO_FALLBACK[0]) else 0
    return LOGO_BASE + v

def draw_logo(sx, sy, cols, rows):
    for cy in range(rows):
        for cx in range(cols):
            n = logo_tile(cy, cx)
            k7.spr(n, sx + cx * 8, sy + cy * 8, 1, 1, 0, 0)

def draw_logo_wave(sx, sy, cols, rows, amp, phase):
    for cy in range(rows):
        offset_x = int(amp * math.sin(phase + cy * 0.5))
        for cx in range(cols):
            n = logo_tile(cy, cx)
            k7.spr(n, sx + cx * 8 + offset_x, sy + cy * 8, 1, 1, 0, 0)

def draw_logo_scaled(sx, sy, cols, rows, scale):
    cell = 8 * scale
    for cy in range(rows):
        for cx in range(cols):
            n = logo_tile(cy, cx)
            k7.spr(n, sx + cx * cell, sy + cy * cell, scale, scale, 0, 0)

def draw_logo_bounce(sx, sy, cols, rows, bounce):
    for cy in range(rows):
        for cx in range(cols):
            n = logo_tile(cy, cx)
            k7.spr(n, sx + cx * 8, sy + cy * 8 + bounce, 1, 1, 0, 0)

def draw_border():
    k7.rect(0, 0, W-1, H-1, 6)
    k7.rect(2, 2, W-3, H-3, 5)

def draw_raster_background():
    phase = t * 2
    amp = 12
    for y in range(H):
        i = (y + int(phase * 4)) % 24
        col = (i % 12) + 2
        if col == 0: col = 8
        offset = int(amp * math.sin(y * 0.06 + t * 2.5))
        x1, x2 = max(0, 0 + offset), min(W, W + offset)
        k7.line(x1, y, x2, y, col)

def scene0_logo_reveal():
    k7.cls(0)
    draw_raster_background()
    f = k7.frame() % SCENE_DURATION
    if f < 6:
        k7.flash(11, 4)
    reveal = min(LOGOW, 3 + (f * 26) // 85)
    logo_sx = 128 - (LOGOW * 4)
    logo_sy = 96
    k7.camera(0, 0)
    draw_logo(logo_sx, logo_sy, reveal, LOGOH)
    k7.rectfill(0, 0, W-1, 18, 0)
    k7.print("K7 INTRO", 92, 4, 15)
    k7.print("LOGO FROM SPRITES", 72, 12, 9)
    draw_border()
    draw_scene_indicator()
    k7.draw_to_canvas(CANVAS_ID)

def scene1_logo_copper():
    k7.cls(0)
    draw_raster_background()
    wobble_x = int(4 * math.sin(t * 0.8))
    wobble_y = int(3 * math.sin(t * 0.6 + 1))
    k7.camera(wobble_x, wobble_y)
    logo_sx = 128 - (LOGOW * 4)
    logo_sy = 96
    draw_logo_wave(logo_sx, logo_sy, LOGOW, LOGOH, 6, t * 1.2)
    f = k7.frame()
    if f % 48 == 1:
        k7.palette_swap(11, 9)
    elif f % 48 == 2:
        k7.palette_swap(11, 9)
    k7.camera(0, 0)
    for bar in range(0, 22, 4):
        c = (bar + int(t * 8)) % 14 + 1
        if c == 0: c = 8
        k7.rectfill(0, bar, W - 1, bar + 2, c)
    for bar in range(H - 22, H, 4):
        c = (bar + int(t * 8)) % 14 + 1
        if c == 0: c = 8
        k7.rectfill(0, bar, W - 1, min(bar + 2, H - 1), c)
    k7.rectfill(0, 0, W-1, 18, 0)
    k7.print("COPPER + LOGO WAVE", 56, 4, 15)
    k7.print("PALETTE SWAP ON BEAT", 60, 12, 9)
    draw_border()
    draw_scene_indicator()
    k7.draw_to_canvas(CANVAS_ID)

def scene2_logo_plasma():
    k7.cls(0)
    cell = 4
    for py in range(0, H, cell):
        for px in range(0, W, cell):
            v = math.sin(px * 0.03 + t * 0.8) + math.sin(py * 0.03 + t * 0.6)
            v += math.sin((px + py) * 0.02 + t * 1.2) * 0.6
            v += math.sin(math.sqrt(px*px + py*py) * 0.04 + t * 0.5) * 0.4
            col = (int(v * 3 + t * 2.5) % 14) + 1
            if col == 0: col = 8
            k7.rectfill(px, py, min(px + cell - 1, W - 1), min(py + cell - 1, H - 1), col)
    k7.camera(0, 0)
    bounce = int(8 * math.sin(t * 0.7))
    logo_sx = 128 - (LOGOW * 4)
    logo_sy = 92
    draw_logo_bounce(logo_sx, logo_sy, LOGOW, LOGOH, bounce)
    k7.rect(8, 8, W - 9, H - 9, (int(t) % 8) + 8)
    k7.rect(12, 12, W - 13, H - 13, (int(t * 2) % 6) + 2)
    k7.rectfill(0, 0, W-1, 18, 0)
    k7.print("PLASMA + LOGO BOUNCE", 64, 4, 15)
    draw_border()
    draw_scene_indicator()
    k7.draw_to_canvas(CANVAS_ID)

def scene3_logo_zoom():
    k7.cls(0)
    draw_raster_background()
    k7.camera(0, 0)
    center_cols, center_rows = 12, 4
    logo_w = center_cols * 16
    logo_h = center_rows * 16
    logo_sx = 128 - logo_w // 2
    logo_sy = 128 - logo_h // 2
    off_x = (LOGOW - center_cols) // 2
    off_y = (LOGOH - center_rows) // 2
    for cy in range(center_rows):
        for cx in range(center_cols):
            n = logo_tile(off_y + cy, off_x + cx)
            k7.spr(n, logo_sx + cx * 16, logo_sy + cy * 16, 2, 2, 0, 0)
    k7.rectfill(0, 0, W-1, 22, 0)
    k7.print("LOGO 2X SCALE (spr w,h)", 48, 4, 15)
    k7.print("CENTER CROP", 92, 12, 9)
    draw_border()
    k7.draw_to_canvas(CANVAS_ID)

def scene3_raster_only():
    """Scene 3: logo drawn via map_draw (map cell 0 = bg; logo sprites 1+)."""
    k7.cls(0)
    draw_raster_background()
    k7.camera(0, 0)
    logo_sx = 128 - (LOGOW * 4)
    logo_sy = 96
    k7.map_draw(0, 0, logo_sx, logo_sy, LOGOW, LOGOH)
    f = k7.frame()
    if f % 32 == 1:
        k7.palette_swap(11, 9)
    elif f % 32 == 2:
        k7.palette_swap(11, 9)
    for y in range(0, H, 4):
        if (y + int(t)) % 8 == 0:
            k7.rectfill(0, y, W - 1, y + 1, 0)
    k7.rectfill(0, 0, W-1, 18, 0)
    k7.print("LOGO VIA MAP (map_draw)", 56, 4, 15)
    k7.print("Cell 0 = bg, sprites 1+", 56, 12, 9)
    draw_border()
    draw_scene_indicator()
    k7.draw_to_canvas(CANVAS_ID)

def scene4_scroller():
    k7.cls(0)
    k7.rect(0, 50, W-1, 200, 6)
    k7.rect(2, 52, W-3, 198, 5)
    k7.rectfill(4, 54, W-5, 196, 0)
    cx = 128
    COLORS = [8, 9, 10, 11, 12, 13, 14, 15, 14, 13, 12, 11, 10, 9, 8]
    for ly, line in enumerate(CREDITS):
        y = 66 + ly * 34
        k7.line(6, y - 2, W-7, y - 2, 5)
        for i, c in enumerate(line[:48]):
            px = int(cx + (i * 8) + scroll_x)
            while px < -10: px += 48 * 8
            while px > W + 10: px -= 48 * 8
            if -8 < px < W:
                col = COLORS[(i + int(t * 0.5)) % len(COLORS)]
                k7.print(c, px, y, col)
    logo_sx = 128 - (LOGOW * 4)
    draw_logo_wave(logo_sx, 6, LOGOW, LOGOH, 4, t * 0.6)
    k7.rectfill(0, 0, W-1, 22, 1)
    k7.print("SCROLLER + LOGO", 72, 6, 11)
    k7.rectfill(0, H-26, W-1, H-1, 1)
    k7.print("K7 SHOWCASE", 76, H-18, 6)
    draw_border()
    draw_scene_indicator()
    k7.draw_to_canvas(CANVAS_ID)

def scene5_fire():
    k7.cls(0)
    cell = 5
    for y in range(FH):
        for x in range(FW):
            c = heat_to_color(heat[y][x])
            if c > 0:
                k7.rectfill(x*cell, y*cell, x*cell+cell-1, y*cell+cell-1, c)
    if k7.frame() % 16 == 0:
        k7.flash(8, 1)
    k7.rectfill(0, 0, W-1, 18, 0)
    k7.print("FIRE", 108, 2, 10)
    draw_border()
    draw_scene_indicator()
    k7.draw_to_canvas(CANVAS_ID)

def scene6_tunnel():
    k7.cls(0)
    cx, cy = 128, 128
    pulse = 0.78 + 0.22 * math.sin(t * 0.5)
    for ring in range(20, 0, -1):
        r = ring * 11 * pulse
        if r < 2: continue
        angle_off = t * 2.2 + ring * 0.32
        col = (int(t * 2) + ring * 2) % 16
        if col == 0: col = 8
        n = 32
        for i in range(n):
            a1 = (i / n) * 2 * math.pi + angle_off
            a2 = ((i + 1) / n) * 2 * math.pi + angle_off
            x1 = cx + r * math.cos(a1)
            y1 = cy + r * math.sin(a1)
            x2 = cx + r * math.cos(a2)
            y2 = cy + r * math.sin(a2)
            k7.line(int(x1), int(y1), int(x2), int(y2), col)
    k7.circfill(cx, cy, 6, 0)
    k7.circfill(cx, cy, 4, 15)
    k7.circfill(cx, cy, 2, 7)
    logo_sx = 128 - (LOGOW * 4)
    draw_logo_bounce(logo_sx, 200, LOGOW, LOGOH, int(4 * math.sin(t * 0.5)))
    k7.rectfill(0, 0, W-1, 16, 0)
    k7.print("TUNNEL + LOGO", 72, 2, 11)
    draw_border()
    draw_scene_indicator()
    k7.draw_to_canvas(CANVAS_ID)

def scene7_credits():
    k7.cls(0)
    f = k7.frame() % 120
    if f < 8:
        k7.flash(9, 4)
    k7.rectfill(0, 0, W-1, 42, 1)
    k7.rectfill(0, H-48, W-1, H-1, 1)
    logo_sx = 128 - (LOGOW * 4)
    draw_logo_wave(logo_sx, 52, LOGOW, LOGOH, 4, t * 0.8)
    k7.print("MADE WITH K7", 68, 14, 11)
    k7.print("GFX  SOUND  MAP  SPRITES  INPUT", 32, 102, 7)
    k7.print("PALETTE  FLASH  FRAME CLOCK", 48, 120, 6)
    k7.print("PYTHON + PYODIDE + RUST + WASM", 24, 150, 5)
    k7.print("EDITOR  SHARE URL  OPEN SOURCE", 28, 170, 9)
    k7.print("LOAD DEMO FROM INDEX", 56, 220, 10)
    draw_border()
    draw_scene_indicator()
    k7.draw_to_canvas(CANVAS_ID)

def scene8_starfield():
    k7.cls(0)
    for (x, y, spd) in stars:
        brightness = min(15, int(spd * 5) + 8)
        k7.pset(int(x), int(y), brightness)
        if brightness >= 12:
            k7.pset(int(x) + 1, int(y), 6)
            k7.pset(int(x), int(y) + 1, 6)
    logo_sx = 128 - (LOGOW * 4)
    draw_logo_wave(logo_sx, 200, LOGOW, LOGOH, 3, t * 0.4)
    k7.rectfill(0, 0, W-1, 18, 0)
    k7.print("STARFIELD", 88, 4, 15)
    draw_border()
    draw_scene_indicator()
    k7.draw_to_canvas(CANVAS_ID)

def scene9_raster_bars():
    k7.cls(0)
    phase = t * 2
    amp = 14
    for y in range(H):
        i = (y + int(phase * 4)) % 32
        col = (i % 14) + 1
        if col == 0: col = 8
        offset = int(amp * math.sin(y * 0.08 + t * 3))
        x1 = max(0, 0 + offset)
        x2 = min(W, W + offset)
        k7.line(x1, y, x2, y, col)
    k7.rectfill(0, 0, W-1, 18, 0)
    k7.print("RASTER BARS", 72, 4, 15)
    logo_sx = 128 - (LOGOW * 4)
    draw_logo_bounce(logo_sx, 200, LOGOW, LOGOH, int(5 * math.sin(t * 0.5)))
    draw_border()
    draw_scene_indicator()
    k7.draw_to_canvas(CANVAS_ID)

def scene10_hypnospiral():
    k7.cls(0)
    cx, cy = 128, 128
    spin = t * 3
    for i in range(100):
        angle = (i / 100) * 4 * math.pi + spin
        r = 20 + (i / 100) * 100
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        col = (i + int(t * 8)) % 16
        if col == 0: col = 9
        k7.circfill(int(x), int(y), 3, col)
    for i in range(0, 100, 3):
        angle = (i / 100) * 4 * math.pi + spin + math.pi
        r = 20 + (i / 100) * 100
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        col = (i + int(t * 8) + 8) % 16
        if col == 0: col = 2
        k7.circfill(int(x), int(y), 2, col)
    k7.circfill(cx, cy, 14, int(t * 2) % 16)
    logo_sx = 128 - (LOGOW * 4)
    draw_logo_wave(logo_sx, 8, LOGOW, LOGOH, 3, t * 0.6)
    k7.rectfill(0, 0, W-1, 18, 0)
    k7.print("HYPNOSPIRAL", 72, 4, 15)
    draw_border()
    draw_scene_indicator()
    k7.draw_to_canvas(CANVAS_ID)

def scene11_logo_zoom():
    k7.cls(0)
    draw_raster_background()
    k7.camera(0, 0)
    center_cols, center_rows = 12, 4
    off_x = (LOGOW - center_cols) // 2
    off_y = (LOGOH - center_rows) // 2
    scale = 2 if math.sin(t * 0.3) > 0 else 1
    cell = 8 * scale
    logo_w = center_cols * cell
    logo_h = center_rows * cell
    logo_sx = 128 - logo_w // 2
    logo_sy = 128 - logo_h // 2
    for cy in range(center_rows):
        for cx in range(center_cols):
            n = logo_tile(off_y + cy, off_x + cx)
            k7.spr(n, logo_sx + cx * cell, logo_sy + cy * cell, 1, 1, 0, 0, scale)
    k7.rectfill(0, 0, W-1, 22, 0)
    k7.print("LOGO ZOOM (spr scale)", 56, 4, 15)
    k7.print("PULSE", 108, 12, 9)
    draw_border()
    draw_scene_indicator()
    k7.draw_to_canvas(CANVAS_ID)

def draw():
    apply_scene_transition()
    sc = scene_index()
    if sc == 0: scene0_logo_reveal()
    elif sc == 1: scene1_logo_copper()
    elif sc == 2: scene2_logo_plasma()
    elif sc == 3: scene3_raster_only()
    elif sc == 4: scene4_scroller()
    elif sc == 5: scene5_fire()
    elif sc == 6: scene6_tunnel()
    elif sc == 7: scene7_credits()
    elif sc == 8: scene8_starfield()
    elif sc == 9: scene9_raster_bars()
    elif sc == 10: scene10_hypnospiral()
    else: scene11_logo_zoom()

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
