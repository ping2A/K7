# K7 Ghostmark benchmark (from pikuseru-examples/ghostmark)
# Original: http://tic.computer/play?cart=122
# 500 moving dots (bounce + gravity). Use for benchmarking draw/update throughput.
# In K7 we draw each as circfill (no spr); press X in original adds 500 more (no input in web yet).

import js
import random
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256

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
    for item in Items:
        item.update()

def draw():
    k7.cls(0)
    for item in Items:
        item.draw()
    k7.print("dots: " + str(len(Items)), W - 70, 0, 7)
    k7.print("ghostmark benchmark", 4, 248, 6)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
