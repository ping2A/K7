# K7 Breakout — Left/Right or A/D move paddle, Z or X to serve. Break all bricks!
# Special bricks (gold): drop power-ups. Catch them for a timed super power!

import js
import math
import random
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
PAD_W, PAD_H = 40, 8
BALL_R = 3
BRICK_W, BRICK_H = 16, 8
BRICK_COLS, BRICK_ROWS = 14, 5
TOP_MARGIN = 32
TRAIL_LEN = 8
PARTICLE_LIFE = 12
POWER_DROP_SPEED = 2
POWER_DURATION = 360
SPECIAL_BRICK_COL = 14
POWER_TYPES = ["wide", "slow", "extra_life"]

px = (W - PAD_W) // 2
py = H - 24
bx, by = 0, 0
bdx, bdy = 0, 0
bricks = []
score = 0
lives = 3
state = "serve"
ball_trail = []
particles = []
shake_frames = 0
falling_powers = []
active_power = None

def make_bricks():
    out = []
    for row in range(BRICK_ROWS):
        for col in range(BRICK_COLS):
            is_special = random.randint(0, 99) < 18
            power = random.choice(POWER_TYPES) if is_special else None
            out.append({
                "x": 4 + col * (BRICK_W + 2),
                "y": TOP_MARGIN + row * (BRICK_H + 2),
                "w": BRICK_W, "h": BRICK_H,
                "col": SPECIAL_BRICK_COL if is_special else (8 + (row % 3)),
                "special": is_special,
                "power": power
            })
    return out

def init():
    global px, py, bx, by, bdx, bdy, bricks, score, lives, state, ball_trail, particles, shake_frames, falling_powers, active_power
    px = (W - PAD_W) // 2
    py = H - 24
    bricks = make_bricks()
    ball_trail = []
    particles = []
    shake_frames = 0
    falling_powers = []
    active_power = None
    score = 0
    lives = 3
    state = "serve"
    k7.set_sound(0, "c5")
    k7.set_sound(1, "e5 g5")
    k7.set_sound(2, "c4")
    k7.set_sound(3, "c6 e6 g6")
    # Background music: simple arcade loop (bass + chords)
    k7.set_music_track(0, "c3 e3 g3 c4 e3 g3 c4 e4 g2 b2 d3 g3 b2 d3 g3 b3 c3 e3 g3 c4 e3 g3 c4 e4 a2 c3 e3 a3 c3 e3 a3 c4")
    k7.play_music(0, 0)

def spawn_particles(cx, cy, col):
    global particles
    n = 8
    for i in range(n):
        angle = (i / n) * 2 * math.pi + (k7.frame() * 0.1)
        speed = 1.5 + (i % 3)
        particles.append({
            "x": cx, "y": cy,
            "vx": math.cos(angle) * speed, "vy": math.sin(angle) * speed - 0.5,
            "life": PARTICLE_LIFE, "col": col
        })

def spawn_shiny_particles(cx, cy, count=6):
    """Sparkle effect for paddle/wall hits."""
    global particles
    for i in range(count):
        angle = (i / count) * 2 * math.pi + (k7.frame() * 0.2)
        speed = 1.0 + (i % 2)
        particles.append({
            "x": cx, "y": cy,
            "vx": math.cos(angle) * speed, "vy": math.sin(angle) * speed - 0.8,
            "life": 8, "col": 15 if (i % 2) == 0 else 11
        })

def serve_ball():
    global bx, by, bdx, bdy, ball_trail
    bx = px + effective_pad_w() // 2 - BALL_R
    by = py - BALL_R * 2 - 2
    bdx, bdy = 0, 0
    ball_trail = []

def launch_ball():
    global bdx, bdy
    bdx = 2 if (k7.frame() // 30) % 2 == 0 else -2
    bdy = -3

def add_shake(strength=4):
    global shake_frames
    shake_frames = max(shake_frames, strength)

def effective_pad_w():
    if active_power and active_power["type"] == "wide":
        return min(PAD_W * 2, W - 8)
    return PAD_W

def update():
    global px, bx, by, bdx, bdy, bricks, score, lives, state, ball_trail, particles, shake_frames, falling_powers, active_power
    f = k7.frame()
    if active_power and f >= active_power["until"]:
        active_power = None
    if state == "gameover":
        if k7.btnp(4) or k7.btnp(5):
            init()
        return
    if state == "serve":
        epw = effective_pad_w()
        if k7.btn(0): px = max(0, px - 6)
        if k7.btn(1): px = min(W - epw, px + 6)
        serve_ball()
        if k7.btnp(4) or k7.btnp(5):
            launch_ball()
            state = "play"
        return
    epw = effective_pad_w()
    px += 6 if k7.btn(1) else (-6 if k7.btn(0) else 0)
    px = max(0, min(W - epw, px))
    ball_trail.append((bx + BALL_R, by + BALL_R))
    if len(ball_trail) > TRAIL_LEN:
        ball_trail.pop(0)
    speed = 0.6 if (active_power and active_power["type"] == "slow") else 1.0
    bx += bdx * speed
    by += bdy * speed
    if bx <= 0:
        bdx = abs(bdx)
        bx = 0
        spawn_shiny_particles(BALL_R, by + BALL_R, 4)
        k7.sfx(0)
        add_shake(2)
    if bx >= W - BALL_R * 2:
        bdx = -abs(bdx)
        bx = W - BALL_R * 2
        spawn_shiny_particles(W - BALL_R, by + BALL_R, 4)
        k7.sfx(0)
        add_shake(2)
    if by <= 0:
        bdy = abs(bdy)
        by = 0
        spawn_shiny_particles(bx + BALL_R, BALL_R, 4)
        k7.sfx(0)
        add_shake(2)
    if by + BALL_R * 2 >= py and by <= py + PAD_H and bx + BALL_R * 2 >= px and bx <= px + epw:
        bdy = -abs(bdy)
        by = py - BALL_R * 2
        hit = (bx + BALL_R - (px + epw // 2)) / max(1, epw // 2)
        bdx = max(-4, min(4, bdx + hit * 2))
        spawn_shiny_particles(bx + BALL_R, py + PAD_H // 2, 8)
        k7.sfx(0)
        add_shake(3)
    if by > H:
        lives -= 1
        k7.sfx(2)
        k7.flash(8, 15)
        if lives <= 0:
            state = "gameover"
        else:
            state = "serve"
        return
    for b in bricks[:]:
        if bx + BALL_R * 2 >= b["x"] and bx <= b["x"] + b["w"] and by + BALL_R * 2 >= b["y"] and by <= b["y"] + b["h"]:
            cx = b["x"] + b["w"] // 2
            cy = b["y"] + b["h"] // 2
            spawn_particles(cx, cy, b["col"])
            spawn_shiny_particles(cx, cy, 4)
            if b.get("special") and b.get("power"):
                falling_powers.append({"x": cx - 4, "y": cy, "vy": POWER_DROP_SPEED, "power": b["power"]})
            bricks.remove(b)
            score += 15 if b.get("special") else 10
            ball_cx = bx + BALL_R
            ball_cy = by + BALL_R
            overlap_t = (ball_cy + BALL_R) - b["y"]
            overlap_b = (b["y"] + b["h"]) - (ball_cy - BALL_R)
            overlap_l = (ball_cx + BALL_R) - b["x"]
            overlap_r = (b["x"] + b["w"]) - (ball_cx - BALL_R)
            min_overlap = min(overlap_t, overlap_b, overlap_l, overlap_r)
            if min_overlap == overlap_t:
                bdy = -abs(bdy)
                by = b["y"] - BALL_R * 2 - 1
            elif min_overlap == overlap_b:
                bdy = abs(bdy)
                by = b["y"] + b["h"] + 1
            elif min_overlap == overlap_l:
                bdx = -abs(bdx)
                bx = b["x"] - BALL_R * 2 - 1
            else:
                bdx = abs(bdx)
                bx = b["x"] + b["w"] + 1
            k7.sfx(1)
            add_shake(4)
            break
    if len(bricks) == 0:
        state = "serve"
        lives += 1
        k7.sfx(3)
        k7.flash(11, 20)
        serve_ball()
        bricks = make_bricks()
        return
    for pw in falling_powers[:]:
        pw["y"] += pw["vy"]
        if pw["y"] > H:
            falling_powers.remove(pw)
            continue
        epw = effective_pad_w()
        if pw["y"] + 8 >= py and pw["y"] <= py + PAD_H and pw["x"] + 8 >= px and pw["x"] <= px + epw:
            if pw["power"] == "extra_life":
                lives += 1
            else:
                active_power = {"type": pw["power"], "until": k7.frame() + POWER_DURATION}
            falling_powers.remove(pw)
            k7.sfx(3)
            spawn_shiny_particles(pw["x"] + 4, pw["y"] + 4, 10)
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.12
        p["life"] -= 1
        if p["life"] <= 0:
            particles.remove(p)

def draw():
    global shake_frames
    k7.camera(0, 0)
    if shake_frames > 0:
        sx = (random.randint(0, 65535) % (shake_frames * 2)) - shake_frames
        sy = (random.randint(0, 32767) % (shake_frames * 2)) - shake_frames
        k7.camera(sx, sy)
    k7.cls(0)
    k7.rect(0, 0, W - 1, H - 1, 7)
    for b in bricks:
        k7.rectfill(b["x"], b["y"], b["x"] + b["w"] - 1, b["y"] + b["h"] - 1, b["col"])
    for pw in falling_powers:
        k7.rectfill(int(pw["x"]), int(pw["y"]), int(pw["x"]) + 7, int(pw["y"]) + 7, 11)
        k7.rect(int(pw["x"]), int(pw["y"]), int(pw["x"]) + 7, int(pw["y"]) + 7, 15)
    for i, (tx, ty) in enumerate(ball_trail):
        a = (i + 1) / (len(ball_trail) + 1)
        r = max(1, int(BALL_R * a * 0.6))
        c = 6 if a < 0.5 else 5
        k7.circfill(tx, ty, r, c)
    for p in particles:
        if p["life"] > 0:
            r = max(0, int(2 * p["life"] / PARTICLE_LIFE))
            if r > 0:
                k7.circfill(int(p["x"]), int(p["y"]), r, p["col"])
    epw = effective_pad_w()
    k7.rectfill(px, py, px + epw - 1, py + PAD_H - 1, 11)
    if active_power:
        k7.print(active_power["type"].upper() + "!", px + epw // 2 - 12, py - 10, 15)
    k7.circfill(int(bx) + BALL_R, int(by) + BALL_R, BALL_R, 15)
    k7.print("SCORE " + str(score), 4, 4, 7)
    k7.print("LIVES " + str(lives), W - 52, 4, 7)
    if state == "serve":
        k7.print("Z or X to serve", 72, 120, 6)
    if state == "gameover":
        k7.print("GAME OVER", 88, 110, 8)
        k7.print("Z or X to restart", 72, 128, 6)
    k7.camera(0, 0)
    if shake_frames > 0:
        shake_frames -= 1
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
