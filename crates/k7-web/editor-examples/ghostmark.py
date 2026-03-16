# K7 Ghostmark benchmark (from pikuseru-examples/ghostmark)
# Original: http://tic.computer/play?cart=122 — 500 moving dots, bounce + gravity.
# Z = fewer dots, X = more dots.

import js
import random
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
MIN_DOTS = 10
MAX_DOTS = 2000
DOT_STEP = 50

class Item:
    def __init__(self):
        self.x = random.uniform(10, W - 10)
        self.y = random.uniform(10, H - 10)
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)
        self.color = random.randint(0, 15)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < 0 or self.x >= W:
            self.vx = -self.vx
        if self.y >= H:
            self.y = H - 1
            self.vy = -(random.randint(0, 100) / 25.0)
        self.vy += 0.05

    def draw(self):
        k7.circfill(int(self.x), int(self.y), 2, self.color)

Items = []

def init():
    global Items
    Items = []
    for _ in range(500):
        Items.append(Item())

def update():
    global Items
    # Z = fewer dots, X = more dots
    if k7.btnp(4):  # Z
        n = max(MIN_DOTS, len(Items) - DOT_STEP)
        if n < len(Items):
            Items[:] = Items[:n]
    if k7.btnp(5):  # X
        n = min(MAX_DOTS, len(Items) + DOT_STEP)
        for _ in range(n - len(Items)):
            Items.append(Item())
    for item in Items:
        item.update()

def draw():
    k7.cls(0)
    for item in Items:
        item.draw()
    k7.print("dots: " + str(len(Items)), W - 70, 0, 7)
    k7.print("ghostmark  Z fewer X more", 4, 248, 6)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
