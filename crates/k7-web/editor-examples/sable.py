# Sable — falling sand (logic from https://github.com/PikuseruConsole/Sable Rust src/species.rs).
# Rocket: samples neighbor then explodes into copies of that species. Mite: eats plant/wood/seed, loves dust, dies in fire/lava/water/oil.
# 80x79 sim, 3x draw (fills to palette). Palette at bottom; click/drag to paint. Up/Down = brush.

import js
import random
import math
k7 = js.k7
CANVAS_ID = "k7canvas"
PALETTE_H = 18
SCALE = 3
W = 80
H = (256 - PALETTE_H) // SCALE
SIZE = W * H
EMPTY, WALL, SAND, WATER, GAS, CLONER, FIRE, WOOD, LAVA, ICE, _, PLANT, ACID, STONE, DUST, MITE, OIL, ROCKET, FUNGUS, SEED = range(20)
NAMES = "Empty Wall Sand Water Gas Cloner Fire Wood Lava Ice - Plant Acid Stone Dust Mite Oil Rocket Fungus Seed".split()

# 32-bit RGB per species (r, g, b) 0..255. Index 10 unused.
SPECIES_RGB = [
    (45, 45, 55),      # Empty - dark
    (60, 60, 65),      # Wall - dark gray
    (218, 192, 130),   # Sand - tan
    (70, 130, 200),    # Water - blue
    (200, 220, 230),   # Gas - light blue-gray
    (220, 100, 220),   # Cloner - magenta
    (255, 140, 50),    # Fire - orange
    (120, 80, 50),     # Wood - brown
    (255, 90, 30),     # Lava - red-orange
    (180, 230, 255),   # Ice - cyan
    (45, 45, 55),      # (unused)
    (60, 180, 80),     # Plant - green
    (200, 255, 100),   # Acid - lime
    (140, 140, 150),   # Stone - gray
    (180, 170, 150),   # Dust - beige
    (180, 100, 200),   # Mite - purple
    (80, 55, 30),      # Oil - dark brown
    (255, 80, 60),     # Rocket - red
    (120, 80, 120),    # Fungus - purple-gray
    (200, 160, 100),   # Seed - tan
]


def species_rgba(species, ra_val=0):
    if species >= len(SPECIES_RGB):
        return 180, 180, 180, 255
    r, g, b = SPECIES_RGB[species]
    if species == FIRE and ra_val > 0:
        r = min(255, r + ra_val // 3)
        g = min(255, g + ra_val // 4)
    elif species == WATER and ra_val > 0:
        b = min(255, b + ra_val // 2)
    elif species == LAVA and ra_val > 0:
        r = min(255, r + ra_val // 4)
    return r, g, b, 255
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

# 8 directions (no center). For Gas, Rocket, etc.
_DIRS_8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

def _rand_vec_8(rnd):
    dx, dy = _DIRS_8[rnd(0, 7)]
    return dx, dy

def _join_dy_dx(dx, dy):
    return ((dx + 1) * 3 + (dy + 1)) & 255

def _split_dy_dx(s):
    s = int(s) % 9
    dx = (s // 3) - 1
    dy = (s % 3) - 1
    return dx, dy

def _adjacency_left(dx, dy):
    # rotate direction 45° left
    t = {(0, 1): (-1, 1), (1, 1): (0, 1), (1, 0): (1, 1), (1, -1): (1, 0), (0, -1): (1, -1),
         (-1, -1): (0, -1), (-1, 0): (-1, -1), (-1, 1): (-1, 0)}
    return t.get((dx, dy), (dx, dy))

def _adjacency_right(dx, dy):
    t = {(0, 1): (1, 1), (1, 1): (1, 0), (1, 0): (1, -1), (1, -1): (0, -1), (0, -1): (-1, -1),
         (-1, -1): (-1, 0), (-1, 0): (-1, 1), (-1, 1): (0, 1)}
    return t.get((dx, dy), (dx, dy))

TICKS_PER_FRAME_MAX = 3

def _count_active():
    n = 0
    c = cells
    for i in range(SIZE):
        if c[i] not in (EMPTY, WALL):
            n += 1
    return n

def tick(gen=None):
    global generation
    generation = int(gen) if gen is not None else k7.frame()
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
                if rb_arr[i] == 0:
                    _s(c, x, y, GAS, ra_arr[i], 5)
                    continue
                dxr, dyr = _rand_vec_8(rnd)
                nbr = _g(c, x + dxr, y + dyr)
                if nbr == ICE:
                    _s(c, x, y, ICE, ra_arr[i], rb_arr[i])
                elif nbr == EMPTY:
                    if rb_arr[i] < 3:
                        _s(c, x, y, EMPTY, 0, 0)
                        _s(c, x + dxr, y + dyr, GAS, ra_arr[i], rb_arr[i])
                    else:
                        _s(c, x, y, GAS, ra_arr[i], 1)
                        _s(c, x + dxr, y + dyr, GAS, ra_arr[i], (rb_arr[i] - 1) & 255)
                elif nbr == GAS:
                    j = _i(x + dxr, y + dyr)
                    if j >= 0 and rb[j] < 4:
                        _s(c, x, y, EMPTY, 0, 0)
                        _s(c, x + dxr, y + dyr, GAS, ra_arr[i], (rb[j] + rb_arr[i]) & 255)
                else:
                    _s(c, x, y, GAS, ra_arr[i], rb_arr[i])
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
                elif nbr == WOOD and rnd(0, 99) < 20:
                    dxr2, dyr2 = _rand_vec_8(rnd)
                    if _g(c, x + dxr2, y + dyr2) == EMPTY:
                        drift = (rnd(0, 99) % 15) - 7
                        _s(c, x + dxr2, y + dyr2, PLANT, (ra_arr[i] + drift) & 255, 0)
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
            elif s == ROCKET:
                # Original: sample neighbor for species, then ra=0 fall, ra=1->2, ra=2 pick dir and set ra=100+join, ra>=100 move 2 steps and spawn 2 clones
                rra, rrb = ra_arr[i], rb_arr[i]
                if rrb == 0:
                    _s(c, x, y, ROCKET, rra, 100)
                    continue
                clone_species = rrb if rrb != 100 else SAND
                if rrb == 100:
                    sx, sy = _rand_vec_8(rnd)
                    sample = _g(c, x + sx, y + sy)
                    if sample not in (EMPTY, ROCKET, WALL, CLONER):
                        _s(c, x, y, ROCKET, 1, sample)
                        clone_species = sample
                    else:
                        _s(c, x, y, ROCKET, rra, rrb)
                    continue
                if rra == 0:
                    if below == EMPTY:
                        _swap(c, x, y, x, y + 1)
                    elif _g(c, x + dx2, y + 1) == EMPTY:
                        _swap(c, x, y, x + dx2, y + 1)
                    elif below in (WATER, GAS, OIL, ACID):
                        _swap(c, x, y, x, y + 1)
                    else:
                        _s(c, x, y, ROCKET, rra, rrb)
                elif rra == 1:
                    _s(c, x, y, ROCKET, 2, rrb)
                elif rra == 2:
                    dxr2, dyr2 = _rand_vec_8(rnd)
                    nbr = _g(c, x + dxr2, y + dyr2)
                    if nbr != EMPTY:
                        dxr2, dyr2 = -dxr2, -dyr2
                    enc = _join_dy_dx(dxr2, dyr2)
                    _s(c, x, y, ROCKET, 100 + enc, rrb)
                elif rra >= 100:
                    dxr2, dyr2 = _split_dy_dx(rra - 100)
                    if dxr2 == 0 and dyr2 == 0:
                        dxr2, dyr2 = 0, 1
                    tx2, ty2 = x + dxr2, y + dyr2 * 2
                    nbr2 = _g(c, tx2, ty2)
                    if nbr2 in (EMPTY, FIRE, ROCKET):
                        _s(c, x, y, clone_species, 80 + rnd(0, 29), 0)
                        _s(c, x, y + dyr2, clone_species, 80 + rnd(0, 29), 0)
                        ndx, ndy = dxr2, dyr2
                        if rnd(0, 99) % 5 == 0:
                            ndx, ndy = _adjacency_left(dxr2, dyr2)
                        elif rnd(0, 99) % 5 == 1:
                            ndx, ndy = _adjacency_right(dxr2, dyr2)
                        _s(c, tx2, ty2, ROCKET, 100 + _join_dy_dx(ndx, ndy), rrb)
                    else:
                        _s(c, x, y, EMPTY, 0, 0)
                else:
                    _s(c, x, y, ROCKET, rra, rrb)
            elif s == MITE:
                # Original: eats plant/wood/seed (move there), loves dust (80% duplicate to dust cell), dies in fire/lava/water/oil, slides on ice
                dxm = rnd(-1, 1)
                dym = rnd(-1, 1)
                if dxm == 0 and dym == 0:
                    dym = 1
                sx, sy = x + (rnd(0, 2) - 1), y + (rnd(0, 2) - 1)
                sample = _g(c, sx, sy)
                nbr = _g(c, x + dxm, y + dym)
                if sample in (FIRE, LAVA, WATER, OIL):
                    _s(c, x, y, EMPTY, 0, 0)
                elif sample in (PLANT, WOOD, SEED) and rnd(0, 999) > 200:
                    _s(c, x, y, EMPTY, 0, 0)
                    _s(c, sx, sy, MITE, ra_arr[i], rb_arr[i])
                elif sample == DUST and rnd(0, 999) > 200:
                    _s(c, sx, sy, MITE, ra_arr[i], rb_arr[i])
                elif nbr == EMPTY:
                    _swap(c, x, y, x + dxm, y + dym)
                elif _g(c, x, y + 1) == ICE and _g(c, x + dxm, y) == EMPTY:
                    _s(c, x, y, EMPTY, 0, 0)
                    _s(c, x + dxm, y, MITE, ra_arr[i], rb_arr[i])
                else:
                    _s(c, x, y, MITE, ra_arr[i], rb_arr[i])
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

PALETTE_Y0 = 256 - PALETTE_H

def update():
    global current, brush
    mx, my = k7.mouse_x(), k7.mouse_y()
    sx, sy = mx // SCALE, my // SCALE
    if my >= PALETTE_Y0:
        if k7.mouse_btnp(0): current = min(mx // 13, 18)
    elif k7.mouse_btn(0) and 0 <= sx < W and 0 <= sy < H:
        for dy in range(-brush, brush + 1):
            for dx in range(-brush, brush + 1):
                if dx*dx + dy*dy <= brush*brush:
                    if current == ROCKET:
                        _s(cells, sx + dx, sy + dy, current, 0, 100)
                    else:
                        _s(cells, sx + dx, sy + dy, current)
    if k7.btnp(2): brush = min(5, brush + 1)
    if k7.btnp(3): brush = max(0, brush - 1)
    n_active = _count_active()
    if n_active > 120:
        n_ticks = 1
    elif n_active > 50:
        n_ticks = 2
    else:
        n_ticks = TICKS_PER_FRAME_MAX
    f = k7.frame()
    for step in range(n_ticks):
        tick(f * TICKS_PER_FRAME_MAX + step)

def draw():
    k7.cls(0)
    c, ra_arr = cells, ra
    for y in range(H):
        for x in range(W):
            i = x * H + y
            v = c[i]
            r, g, b, a = species_rgba(v, ra_arr[i] if v < len(SPECIES_RGB) else 0)
            k7.rectfill_rgba(x*SCALE, y*SCALE, x*SCALE+SCALE-1, y*SCALE+SCALE-1, r, g, b, a)
    slot_w = 13
    for i in range(19):
        x0 = i * slot_w
        r, g, b, a = species_rgba(i)
        k7.rectfill_rgba(x0, PALETTE_Y0, x0 + slot_w - 1, PALETTE_Y0 + PALETTE_H - 1, r, g, b, a)
        if i == current:
            k7.rect(x0, PALETTE_Y0, x0 + slot_w - 1, PALETTE_Y0 + PALETTE_H - 1, 8)
    k7.print_rgba(NAMES[current][:6], 0, PALETTE_Y0 + 2, 255, 80, 80, 255)
    k7.print_rgba("Up/Dn brush", 200, PALETTE_Y0 + 2, 180, 180, 180, 255)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

generation = 0
init()
js.game_loop_js = game_loop
