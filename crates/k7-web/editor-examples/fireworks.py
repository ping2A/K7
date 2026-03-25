# K7 Fireworks (from pikuseru-examples/demos/fireworks)
# By saccharine; particles + gravity + respawn.

import js
import math
import random
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
fireworks = []

def create_particle(x, y, color, speed, direction):
    return {"x": x, "y": y, "color": color, "dx": math.cos(direction) * speed, "dy": math.sin(direction) * speed}

def init():
    global fireworks
    fireworks = []
    k7.set_sound(0, "f3:noise|envelope:perc|lowpass:dark|reverb:small c5:triangle|envelope:perc|hp:bright")
    k7.set_sound(1, "d4:noise|envelope:perc g4:square|envelope:perc")
    for _ in range(5):
        particles = []
        for _ in range(120):
            particles.append(create_particle(0, H - 1, 0, 100, 0.75))
        fireworks.append(particles)

def update():
    global fireworks
    for particles in fireworks:
        for p in particles[:]:
            p["dy"] += 0.3
            p["x"] += p["dx"]
            p["y"] += p["dy"]
            if p["y"] > H - 1:
                particles.remove(p)
        if len(particles) < 20:
            x = random.randint(32, 32 + 64)
            y = random.randint(10, 60)
            c = random.randint(1, 15)
            k7.sfx(random.randint(0, 1))
            for _ in range(120):
                particles.append(create_particle(x, y, c, random.uniform(1, 5), random.uniform(0, 2 * math.pi)))

def draw():
    k7.cls(0)
    for particles in fireworks:
        for p in particles:
            x, y = int(p["x"]), int(p["y"])
            if 0 <= x < W and 0 <= y < H:
                k7.pset(x, y, p["color"])
    k7.print("fireworks", 4, 4, 7)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
