# Sable — falling sand (logic from https://github.com/PikuseruConsole/Sable). Uses k7.frame() clock.
# 64x60 sim, 4x draw for FPS. Palette at bottom; click/drag to paint. Up/Down = brush.

import js
import random
import math
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 64, 60
SIZE = W * H
EMPTY, WALL, SAND, WATER, GAS, CLONER, FIRE, WOOD, LAVA, ICE, _, PLANT, ACID, STONE, DUST, MITE, OIL, ROCKET, FUNGUS, SEED = range(20)
COLORS = [0, 5, 10, 12, 6, 13, 8, 4, 9, 14, 0, 3, 11, 5, 10, 15, 4, 8, 13, 3]
NAMES = "Empty Wall Sand Water Gas Cloner Fire Wood Lava Ice - Plant Acid Stone Dust Mite Oil Rocket Fungus Seed".split()
cells = bytearray(SIZE)
ra = bytearray(SIZE)
rb = bytearray(SIZE)
clock = [0] * SIZE
pressure = [0] * SIZE
current = SAND
brush = 2

def _i(x, y):
    if 0 <= x < W and 0 <= y < H: return x * H + y
    return -1

def _g(c, x, y):
    i = _i(x, y)
    return WALL if i < 0 else c[i]

def _s(c, x, y, v, ra_val=0, rb_val=0):
    i = _i(x, y)
    if i >= 0:
        c[i] = v
        ra[i] = ra_val & 255
        rb[i] = rb_val & 255
        clock[i] = generation

def _swap(c, x0, y0, x1, y1):
    i0, i1 = _i(x0,y0), _i(x1,y1)
    if i0 >= 0 and i1 >= 0:
        c[i0], c[i1] = c[i1], c[i0]
        ra[i0], ra[i1] = ra[i1], ra[i0]
        rb[i0], rb[i1] = rb[i1], rb[i0]
        clock[i0] = clock[i1] = generation

_HEAVY = (SAND, WATER, STONE, LAVA, DUST, ACID, OIL, WOOD, PLANT, FUNGUS, SEED, CLONER, WALL)

def tick():
    global generation
    generation = k7.frame()
    c, rnd, clk, pr, ra_arr, rb_arr = cells, random.randint, clock, pressure, ra, rb
    if (generation & 1) == 0:
        for x in range(W):
            p = 0
            for y in range(H):
                i = x * H + y
                pr[i] = p
                if c[i] in _HEAVY:
                    p = min(255, p + 1)
    x_order = range(W) if (generation & 1) == 0 else range(W - 1, -1, -1)
    for x in x_order:
        for y in range(H):
            i = x * H + y
            if clk[i] == generation:
                continue
            s = c[i]
            if s in (EMPTY, WALL):
                continue
            dx2 = 1 if rnd(0, 1) else -1
            dx = rnd(0, 2) - 1
            dxr, dyr = rnd(0, 2) - 1, rnd(0, 2) - 1
            below = c[i + 1] if (y + 1) < H else WALL
            if s == SAND:
                if below == EMPTY: _swap(c, x, y, x, y + 1)
                elif _g(c, x + dx2, y + 1) == EMPTY: _swap(c, x, y, x + dx2, y + 1)
                elif below in (WATER, GAS, OIL, ACID): _swap(c, x, y, x, y + 1)
            elif s == WATER:
                if below == EMPTY or below == OIL:
                    new_ra = ra_arr[i]
                    if rnd(0, 19) == 0: new_ra = 100 + rnd(0, 49)
                    _s(c, x, y, below, 0, 0)
                    _s(c, x, y + 1, WATER, new_ra, rb_arr[i])
                elif _g(c, x + dx, y + 1) == EMPTY or _g(c, x + dx, y + 1) == OIL:
                    _s(c, x, y, _g(c, x + dx, y + 1), 0, 0)
                    _s(c, x + dx, y + 1, WATER, ra_arr[i], rb_arr[i])
                elif _g(c, x - dx, y + 1) == EMPTY:
                    _s(c, x, y, EMPTY, 0, 0)
                    _s(c, x - dx, y + 1, WATER, ra_arr[i], rb_arr[i])
                else:
                    left = (ra_arr[i] % 2) == 0
                    d = 1 if left else -1
                    dx0 = _g(c, x + d, y)
                    dxd = _g(c, x + 2*d, y)
                    if dx0 == EMPTY and dxd == EMPTY:
                        _s(c, x, y, dxd, 0, 0)
                        _s(c, x + 2*d, y, WATER, ra_arr[i], 6)
                    elif dx0 == EMPTY or dx0 == OIL:
                        _s(c, x, y, dx0, 0, 0)
                        _s(c, x + d, y, WATER, ra_arr[i], 3)
                    elif rb_arr[i] == 0 and _g(c, x - d, y) == EMPTY:
                        _s(c, x, y, WATER, (ra_arr[i] + d) & 255, rb_arr[i])
                    elif rb_arr[i] > 0:
                        _s(c, x, y, WATER, ra_arr[i], max(0, rb_arr[i] - 1))
            elif s == OIL:
                rb_val = rb_arr[i]
                nbr = _g(c, x + dxr, y + dyr)
                if rb_val == 0 and (nbr == FIRE or nbr == LAVA or (nbr == OIL and 1 < rb[_i(x+dxr,y+dyr)] < 20)):
                    _s(c, x, y, OIL, ra_arr[i], 50)
                    rb_val = 50
                if rb_val > 1:
                    _s(c, x, y, OIL, ra_arr[i], rb_val - 1)
                if rb_val % 4 != 0 and nbr == EMPTY and rnd(0, 99) > 90:
                    _s(c, x + dxr, y + dyr, FIRE, 20 + rnd(0, 29), 0)
                if nbr == WATER:
                    _s(c, x, y, OIL, 50, 0)
                elif below == EMPTY:
                    _swap(c, x, y, x, y + 1)
                elif _g(c, x + dx, y + 1) == EMPTY: _swap(c, x, y, x + dx, y + 1)
                elif _g(c, x - dx, y + 1) == EMPTY: _swap(c, x, y, x - dx, y + 1)
                elif _g(c, x + dx, y) == EMPTY: _s(c, x, y, EMPTY, 0, 0); _s(c, x + dx, y, OIL, ra_arr[i], rb_arr[i])
                elif _g(c, x - dx, y) == EMPTY: _s(c, x, y, EMPTY, 0, 0); _s(c, x - dx, y, OIL, ra_arr[i], rb_arr[i])
                elif rb_val == 1:
                    _s(c, x, y, EMPTY, 0, 0)
            elif s == ACID:
                ra_val = ra_arr[i]
                deg = (ra_val - 60) & 255
                degraded = EMPTY if deg < 80 else ACID
                if degraded == ACID: deg = ra_val - 60
                if below == EMPTY: _swap(c, x, y, x, y + 1)
                elif _g(c, x + dx, y) == EMPTY: _s(c, x, y, EMPTY, 0, 0); _s(c, x + dx, y, ACID, ra_arr[i], rb_arr[i])
                elif _g(c, x - dx, y) == EMPTY: _s(c, x, y, EMPTY, 0, 0); _s(c, x - dx, y, ACID, ra_arr[i], rb_arr[i])
                else:
                    n = _g(c, x, y + 1)
                    if n != WALL and n != ACID: _s(c, x, y, EMPTY, 0, 0); _s(c, x, y + 1, degraded, deg, 0)
                    elif _g(c, x + dx, y) != WALL and _g(c, x + dx, y) != ACID: _s(c, x, y, EMPTY, 0, 0); _s(c, x + dx, y, degraded, deg, 0)
                    elif _g(c, x - dx, y) != WALL and _g(c, x - dx, y) != ACID: _s(c, x, y, EMPTY, 0, 0); _s(c, x - dx, y, degraded, deg, 0)
                    elif _g(c, x, y - 1) not in (WALL, ACID, EMPTY): _s(c, x, y, EMPTY, 0, 0); _s(c, x, y - 1, degraded, deg, 0)
                    else: _s(c, x, y, ACID, ra_arr[i], rb_arr[i])
            elif s == LAVA:
                if _g(c, x + dxr, y + dyr) in (GAS, DUST) and rnd(0, 99) < 25:
                    _s(c, x + dxr, y + dyr, FIRE, 150 + (dxr + dyr) * 10, 0)
                if below == WATER:
                    _s(c, x, y, STONE, 0, 0)
                    _s(c, x, y + 1, EMPTY, 0, 0)
                elif below == EMPTY: _swap(c, x, y, x, y + 1)
                elif _g(c, x + dx2, y + 1) == EMPTY: _swap(c, x, y, x + dx2, y + 1)
                elif _g(c, x + dx2, y) == EMPTY: _s(c, x, y, EMPTY, 0, 0); _s(c, x + dx2, y, LAVA, ra_arr[i], rb_arr[i])
                else: _s(c, x, y, LAVA, ra_arr[i], rb_arr[i])
            elif s == FIRE:
                ra_val = ra_arr[i]
                dec = 2 + (rnd(0, 2) - 1)
                new_ra = max(0, ra_val - dec)
                if _g(c, x + dxr, y + dyr) in (GAS, DUST) and rnd(0, 99) < 25:
                    _s(c, x + dxr, y + dyr, FIRE, 150 + (dxr + dyr) * 10, 0)
                if new_ra < 5 or _g(c, x + dxr, y + dyr) == WATER:
                    _s(c, x, y, EMPTY, 0, 0)
                elif _g(c, x + dxr, y + dyr) == EMPTY:
                    _s(c, x, y, EMPTY, 0, 0)
                    _s(c, x + dxr, y + dyr, FIRE, new_ra, 0)
                else:
                    _s(c, x, y, FIRE, new_ra, 0)
            elif s == GAS:
                if rb_arr[i] == 0: _s(c, x, y, GAS, ra_arr[i], 5)
                nbr = _g(c, x + dxr, y + dyr)
                if nbr == ICE:
                    _s(c, x, y, ICE, ra_arr[i], rb_arr[i])
                elif nbr == EMPTY:
                    if rb_arr[i] < 3: _s(c, x, y, EMPTY, 0, 0); _s(c, x + dxr, y + dyr, GAS, ra_arr[i], rb_arr[i])
                    else: _s(c, x, y, GAS, ra_arr[i], 1); _s(c, x + dxr, y + dyr, GAS, ra_arr[i], (rb_arr[i] - 1) & 255)
                elif (dxr != 0 or dyr != 0) and nbr == GAS and rb[_i(x+dxr,y+dyr)] < 4:
                    _s(c, x, y, EMPTY, 0, 0)
                    _s(c, x + dxr, y + dyr, GAS, ra_arr[i], (rb[_i(x+dxr,y+dyr)] + rb_arr[i]) & 255)
            elif s == DUST:
                if pr[i] > 120:
                    _s(c, x, y, FIRE, 150 + (ra_arr[i] // 10), 0)
                elif below == EMPTY: _swap(c, x, y, x, y + 1)
                elif below == WATER: _s(c, x, y, WATER, 0, 0); _s(c, x, y + 1, DUST, ra_arr[i], rb_arr[i])
                elif _g(c, x + dx, y + 1) == EMPTY: _swap(c, x, y, x + dx, y + 1)
                else: _s(c, x, y, DUST, ra_arr[i], rb_arr[i])
            elif s == STONE:
                if pr[i] > 120 and rnd(0, 1) == 0:
                    _s(c, x, y, SAND, ra_arr[i], 0)
                elif _g(c, x - 1, y - 1) == STONE and _g(c, x + 1, y - 1) == STONE:
                    pass
                elif below == EMPTY: _swap(c, x, y, x, y + 1)
                elif below in (WATER, GAS, OIL, ACID): _swap(c, x, y, x, y + 1)
                else: _s(c, x, y, STONE, ra_arr[i], rb_arr[i])
            elif s == WOOD:
                rb_val = rb_arr[i]
                nbr = _g(c, x + dxr, y + dyr)
                if rb_val == 0 and nbr in (FIRE, LAVA) and rnd(0, 299) < 200:
                    _s(c, x, y, WOOD, ra_arr[i], 90)
                elif rb_val > 1:
                    _s(c, x, y, WOOD, ra_arr[i], rb_val - 1)
                elif rb_val % 4 == 0 and nbr == EMPTY and rnd(0, 99) < 25:
                    _s(c, x + dxr, y + dyr, FIRE, 30 + rnd(0, 59), 0)
                elif nbr == WATER:
                    _s(c, x, y, WOOD, 50, 0)
                elif rb_val == 1:
                    _s(c, x, y, EMPTY, 0, 0)
                else: _s(c, x, y, WOOD, ra_arr[i], rb_arr[i])
            elif s == ICE:
                if pr[i] > 120 and rnd(0, 1) == 0:
                    _s(c, x, y, WATER, ra_arr[i], rb_arr[i])
                else:
                    nbr = _g(c, x + dxr, y + dyr)
                    if nbr in (FIRE, LAVA):
                        _s(c, x, y, WATER, ra_arr[i], rb_arr[i])
                    elif nbr == WATER and rnd(0, 99) < 7:
                        _s(c, x + dxr, y + dyr, ICE, ra_arr[i], rb_arr[i])
                    else: _s(c, x, y, ICE, ra_arr[i], rb_arr[i])
            elif s == SEED:
                rb_val = rb_arr[i]
                nbr = _g(c, x + dxr, y + dyr)
                if nbr in (FIRE, LAVA):
                    _s(c, x, y, FIRE, 5, 0)
                elif rb_val == 0:
                    below_d = _g(c, x + dx2, y + 1)
                    if below_d in (SAND, PLANT, FUNGUS) and rnd(0, 99) < 50:
                        _s(c, x, y, SEED, ra_arr[i], rnd(1, 253))
                    elif below == EMPTY: _swap(c, x, y, x, y + 1)
                    elif _g(c, x + dx2, y + 1) == EMPTY: _swap(c, x, y, x + dx2, y + 1)
                    elif below in (WATER, GAS, OIL, ACID): _swap(c, x, y, x, y + 1)
                    else: _s(c, x, y, SEED, ra_arr[i], rb_arr[i])
                elif nbr == WATER:
                    _s(c, x, y, SEED, ra_arr[i], rb_arr[i])
                else: _s(c, x, y, SEED, ra_arr[i], rb_arr[i])
            elif s == PLANT:
                rb_val = rb_arr[i]
                nbr = _g(c, x + dxr, y + dyr)
                if rb_val == 0 and nbr in (FIRE, LAVA): _s(c, x, y, PLANT, ra_arr[i], 20)
                elif nbr == WOOD and _g(c, x + dxr, y + dyr) == EMPTY and rnd(0, 99) < 20: _s(c, x + dxr, y + dyr, PLANT, (ra_arr[i] + (rnd(0, 99) % 15 - 7)) & 255, 0)
                elif rb_val > 1: _s(c, x, y, PLANT, ra_arr[i], rb_val - 1)
                elif nbr == EMPTY and rnd(0, 99) < 20: _s(c, x + dxr, y + dyr, FIRE, 20 + rnd(0, 29), 0)
                elif nbr == WATER: _s(c, x, y, PLANT, 50, 0)
                elif rb_val == 1: _s(c, x, y, EMPTY, 0, 0)
                else: _s(c, x, y, PLANT, ra_arr[i], rb_arr[i])
            elif s == FUNGUS:
                rb_val = rb_arr[i]
                nbr = _g(c, x + dxr, y + dyr)
                if rb_val == 0 and nbr in (FIRE, LAVA): _s(c, x, y, FUNGUS, ra_arr[i], 10)
                if nbr != EMPTY and nbr != FUNGUS and nbr not in (FIRE, ICE) and _g(c, x + dxr, y + dyr) == EMPTY and rnd(0, 99) < 20:
                    _s(c, x + dxr, y + dyr, FUNGUS, (ra_arr[i] + (rnd(0, 99) % 15 - 7)) & 255, 0)
                if rb_val > 1: _s(c, x, y, FUNGUS, ra_arr[i], rb_val - 1)
                elif nbr == EMPTY and rnd(0, 99) < 20: _s(c, x + dxr, y + dyr, FIRE, 10 + rnd(0, 9), 0)
                else: _s(c, x, y, FUNGUS, ra_arr[i], rb_arr[i])
            elif s == CLONER:
                clone_species = rb_arr[i]
                if clone_species == 0:
                    for dxx in (-1, 0, 1):
                        for dyy in (-1, 0, 1):
                            n = _g(c, x + dxx, y + dyy)
                            if n not in (EMPTY, CLONER, WALL):
                                _s(c, x, y, CLONER, 200, n)
                                clone_species = n
                                break
                        if clone_species != 0: break
                if clone_species != 0 and rnd(0, 99) > 90:
                    for dxx in (-1, 0, 1):
                        for dyy in (-1, 0, 1):
                            if _g(c, x + dxx, y + dyy) == EMPTY:
                                _s(c, x + dxx, y + dyy, clone_species, 80 + rnd(0, 29), 0)
                                break
                        else: continue
                        break
            else:
                _s(c, x, y, s, ra_arr[i], rb_arr[i])

def init():
    global cells, ra, rb, clock, pressure
    cells = bytearray(SIZE)
    ra = bytearray(SIZE)
    rb = bytearray(SIZE)
    clock = [0] * SIZE
    pressure = [0] * SIZE
    for x in range(3, W - 3, 4):
        y = int(8 + 3 * math.sin(x / 10))
        if 0 <= y < H: _s(cells, x, y, SAND)
    for x in range(20, W - 3, 28):
        y = int(H // 2 + 10 * math.sin(x / 10))
        if 0 <= y < H: _s(cells, x, y, SEED)

def update():
    global current, brush
    mx, my = k7.mouse_x(), k7.mouse_y()
    sx, sy = mx // 4, my // 4
    if sy >= H:
        if k7.mouse_btnp(0): current = min(mx // 16, 18)
    elif k7.mouse_btn(0) and 0 <= sx < W and 0 <= sy < H:
        for dy in range(-brush, brush + 1):
            for dx in range(-brush, brush + 1):
                if dx*dx + dy*dy <= brush*brush: _s(cells, sx + dx, sy + dy, current)
    if k7.btnp(2): brush = min(5, brush + 1)
    if k7.btnp(3): brush = max(0, brush - 1)
    tick()

def draw():
    k7.cls(0)
    c = cells
    scale = 4
    for y in range(H):
        for x in range(W):
            v = c[x * H + y]
            col = COLORS[v] if v < len(COLORS) else 7
            k7.rectfill(x*scale, y*scale, x*scale+scale-1, y*scale+scale-1, col)
    for i in range(19):
        k7.rectfill(i*16, 240, i*16+15, 255, COLORS[i] if i < len(COLORS) else 7)
        if i == current: k7.rect(i*16, 240, i*16+15, 255, 7)
    k7.print(NAMES[current][:6], 0, 248, 0)
    k7.print("Up/Dn brush", 160, 248, 6)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

generation = 0
init()
js.game_loop_js = game_loop
