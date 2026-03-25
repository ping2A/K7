# Duck forest — K7 port of Pikuseru duck.pik (Python half + __gfx__ ideas):
# https://github.com/PikuseruConsole/pikuseru-examples/blob/main/games/duck.pik
# Player duck = circfill stack like _draw() in cartridge; terrain logic matches set_trees/set_bounds/…
#
# Top-down world + perspective stacks: trees (line trunk + layered foliage), bushes,
# optional building stacks, clouds, blob collision, camera follow. Procedural infinite
# terrain (noise biomes). You play as a duck (sprite body + head). Music is an original
# chiptune loop (not MP3 pitch-tracking).

import js
import math
import random

k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256

CELL_SIZE = 16
# Reference size for duck.pik spawn scaling only (map is procedural / unbounded).
SPAWN_REF_CELLS = 48
CELL_FILL = max(5, (W + CELL_SIZE - 1) // CELL_SIZE + 2)
SEED = random.random()

# Perspective (scaled from duck.pik)
PERSPECTIVE_OFFSET_X = 32
PERSPECTIVE_OFFSET_Y = 40

frame = 0
time_s = 0.0


def flr(x):
    return int(math.floor(x))


def mid(a, b, c):
    return max(a, min(b, c))


def lerp(a, b, t):
    return a + t * (b - a)


def ease(t):
    if t >= 0.5:
        return (t - 1) * (2 * t - 2) * (2 * t - 2) + 1
    return 4 * t * t * t


def frange(start, stop, step):
    if step == 0:
        return []
    n = int(round(abs((stop - start) / step) + 0.5001))
    if (stop - start) / step < 0:
        step = -step
    return [start + i * step for i in range(n)]


def myrange(r):
    return random.randint(flr(r[0]), flr(r[1]))


def myrange_f(r):
    return random.uniform(r[0], r[1])


class Vec2(object):
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def len2(self):
        return self.x * self.x + self.y * self.y

    def len(self):
        return math.sqrt(self.len2())

    def _add(self, b):
        self.x += b.x
        self.y += b.y

    def _mul(self, s):
        self.x *= s
        self.y *= s

    def sub(self, b):
        return Vec2(self.x - b.x, self.y - b.y)

    def add(self, b):
        return Vec2(self.x + b.x, self.y + b.y)

    def mul(self, s):
        return Vec2(self.x * s, self.y * s)

    def lerp(self, b, t):
        return Vec2(lerp(self.x, b.x, t), lerp(self.y, b.y, t))

    def div(self, s):
        if s != 0:
            return Vec2(self.x / s, self.y / s)
        return Vec2(0, 0)


# duck.pik: SHADOW_OFFSET = Vec2(2, 3).normalize().mul(0.2) — same for player + cloud shadows
_spn = math.hypot(2, 3)
SHADOW_OFFSET = Vec2(2 / _spn * 0.2, 3 / _spn * 0.2)
PERSPECTIVE_OFFSET = Vec2(PERSPECTIVE_OFFSET_X, PERSPECTIVE_OFFSET_Y)
WORLD_PX_W = float(SPAWN_REF_CELLS * CELL_SIZE)


def local_noise(nx, ny, nz=0.0, freq=10, zoom=300.0):
    # duck.pik: return noise((freq*nx)/zoom, (freq*ny)/zoom, nz) / 2.0 + 1.0  (stub was `return 1`)
    u = (freq * nx) / zoom + nz * 0.017
    v = (freq * ny) / zoom + nz * 0.023
    h = math.sin(u * 12.9898 + math.sin(v * 4.1415) * 3.1)
    h *= math.cos(v * 78.233 + math.sin(u * 2.718) * 1.7)
    h += math.sin((u + v) * 6.283 + nz) * 0.35
    # Keep >0: pico-8 index 0 paints as black — reads as “empty void” for ground tiles.
    # duck.pik stub used `return 1` → always bright biomes; match that intent.
    return max(0.55, min(1.5, h * 0.5 + 1.0))


def biome_at_cell(x, y):
    """Procedural biome for any integer world cell (infinite map)."""
    n = local_noise(x, y, SEED * 6.2831853) / 0.06666666666666667
    return max(1, min(15, flr(n)))


def cell_rng_seed(x, y):
    return (int(x) * 73856093 + int(y) * 19349663 + int(SEED * (1 << 30))) & 0xFFFFFFFFFFFFFFFF


class Biome(object):
    def __init__(self, colour, tree_range, bush_p, transition, footprints, foot_sfx):
        self.colour = colour
        self.tree_range = tree_range
        self.bush_props = bush_p
        self.transition = transition
        self.footprints = footprints
        self.foot_sfx = foot_sfx
        self.building_freq = 0.0


class Biomes(object):
    def __init__(self):
        self.biomes = {}
        for i in range(16):
            self.biomes[i] = Biome(i, [0, 0], [0, 0, [0, 0, 0, 0]], False, True, 3)
        self.biomes[3].transition = True
        self.biomes[3].tree_range = [0.25, 0.3]
        self.biomes[3].bush_props = [0.5, 0.5, [8, 12, 13, 10]]
        self.biomes[4].transition = True
        self.biomes[7].transition = True
        self.biomes[7].tree_range = [0.0, 0.1]
        self.biomes[10].transition = True
        self.biomes[10].building_freq = 0.8
        self.biomes[11].transition = True
        self.biomes[11].tree_range = [0.1, 0.3]
        self.biomes[11].bush_props = [0.5, 0.8, [8, 12, 13, 10]]
        self.biomes[14].transition = True
        self.biomes[15].transition = True
        self.biomes[15].tree_range = [0, 0.2]
        self.biomes[15].building_freq = 0.01


class Building(object):
    def __init__(self, w, h, pos, height, color):
        self.w = w
        self.h = h
        self.pos = pos
        self.height = height
        self.color = color
        self.s = Vec2(0, 0)


class Bush(object):
    def __init__(self, p, r, height, colour, bloom):
        self.pos = p
        self.r = r
        self.height = height
        self.colour = colour
        self.bloom = bloom
        self.s = Vec2(p.x, p.y)


class Tree(object):
    def __init__(self, pos, height, girth, leaves):
        self.pos = pos
        self.height = height
        self.girth = girth
        self.leaves = leaves
        self.s = Vec2(pos.x, pos.y)


class Cell(object):
    def __init__(self, color):
        self.x = 0
        self.y = 0
        self.color = color
        self.seed = 0.0
        self.edges = {
            -1: {-1: 1, 0: 1, 1: 1},
            0: {-1: 1, 0: 1, 1: 1},
            1: {-1: 1, 0: 1, 1: 1},
        }
        self.trees = []
        self.bushes = []
        self.building = None
        self.init = False


class Blobs(object):
    def __init__(self):
        self.blobs = {}

    def len(self):
        return len(self.blobs)

    def add_blob(self, p, r):
        key = "%d-%d-%d" % (flr(p.x), flr(p.y), flr(r * 10))
        if key not in self.blobs:
            self.blobs[key] = [p, r * r, False]

    def update(self, player):
        for blob in self.blobs.values():
            d = player.pos.sub(blob[0])
            l2 = d.len2()
            if l2 < blob[1] + player.r2:
                blob[2] = True
                ln = math.sqrt(max(l2, 0.0001))
                dv = d.div(ln)
                player.v._add(dv)
            else:
                blob[2] = False


class Configuration(object):
    def __init__(self, biomes, blobs):
        self.biomes = biomes
        self.blobs = blobs
        self.trees_height_range = [6, 14]
        self.trees_girth_range = [2, 5]
        self.trees_gap = 8
        self.bushes_height_range = [0.5, 1.2]
        self.bushes_cluster_range = [2, 4]
        self.bushes_radius_range = [1, 2.5]
        self.buildings_height_range = [8, 20]
        self.buildings_w_range = [4, 8]
        self.buildings_h_range = [4, 8]
        self.buildings_colours = [8, 9, 6]
        self.cell_fill = CELL_FILL
        self.cell_size = CELL_SIZE
        self.shadow_offset = SHADOW_OFFSET
        self.perspective_offset = PERSPECTIVE_OFFSET


class Buildings(object):
    def __init__(self, config):
        self.config = config
        self.cell_size = config.cell_size

    def update(self, x, y, cell, cam, cells, blobs):
        building = cell.building
        if not building:
            return
        cellp = Vec2(
            cam.pos.x % self.cell_size - x * self.cell_size,
            cam.pos.y % self.cell_size - y * self.cell_size,
        )
        building.s = building.pos.sub(cellp.add(self.config.perspective_offset))
        s1 = max(building.w, building.h)
        s2 = min(building.w, building.h)
        for i in frange(-s1 + s2 / 2, s1 - s2 / 2, s2):
            p1 = Vec2((cells.pos.x + x) * self.cell_size, (cells.pos.y + y) * self.cell_size).add(building.pos)
            if s1 == building.w:
                p1.x += i
            else:
                p1.y += i
            blobs.add_blob(p1, s2)
            p2 = Vec2((cells.pos.x + x) * self.cell_size, (cells.pos.y + y) * self.cell_size).add(building.pos)
            if s1 == building.w:
                p2.x += s1 - s2 / 2
            else:
                p2.y += s1 - s2 / 2
            if p2.sub(p1).len() > 2:
                blobs.add_blob(p2, s2)

    def draw(self, a, b, cell, cam, shadow):
        building = cell.building
        if not building:
            return
        k7.camera(-flr(cam.c.x - a * self.cell_size), -flr(cam.c.y - b * self.cell_size))
        if shadow:
            for i in frange(0, building.height / 2, 2):
                t = Vec2(building.s.x, building.s.y)
                t._mul(i * 0.015)
                t._add(building.pos)
                k7.rectfill(
                    flr(t.x - building.w),
                    flr(t.y - building.h),
                    flr(t.x + building.w),
                    flr(t.y + building.h),
                    5,
                )
        else:
            for i in frange(building.height / 2, building.height - 1, 2):
                t = Vec2(building.s.x, building.s.y)
                t._mul(i * 0.015)
                t._add(building.pos)
                k7.rectfill(
                    flr(t.x - building.w),
                    flr(t.y - building.h),
                    flr(t.x + building.w),
                    flr(t.y + building.h),
                    5,
                )
            s = building.s.mul(building.height * 0.015)
            s._add(building.pos)
            k7.rectfill(
                flr(s.x - building.w),
                flr(s.y - building.h),
                flr(s.x + building.w),
                flr(s.y + building.h),
                building.color,
            )


class Bushes(object):
    def __init__(self, config):
        self.config = config
        self.cell_size = config.cell_size

    def update(self, x, y, cell, cam, cells, blobs):
        cellp = Vec2(
            cam.pos.x % self.cell_size - x * self.cell_size,
            cam.pos.y % self.cell_size - y * self.cell_size,
        )
        for bush in cell.bushes:
            bush.s = bush.pos.sub(cellp.add(self.config.perspective_offset))
            bush.s = bush.s.mul(bush.height * 0.015)
            bush.s._add(bush.pos)

    def draw(self, a, b, cell, cam, shadow):
        if not cell.bushes:
            return
        k7.camera(-flr(cam.c.x - a * self.cell_size), -flr(cam.c.y - b * self.cell_size))
        if shadow:
            for bush in cell.bushes:
                k7.circfill(
                    flr(bush.pos.x + self.config.shadow_offset.x * bush.height),
                    flr(bush.pos.y + self.config.shadow_offset.y * bush.height),
                    flr(bush.r),
                    5,
                )
        else:
            for bush in cell.bushes:
                k7.circfill(flr(bush.s.x), flr(bush.s.y), flr(bush.r), 3)
            for bush in cell.bushes:
                if bush.bloom:
                    p = bush.s.add(bush.bloom)
                    k7.pset(flr(p.x), flr(p.y), bush.colour)


class Trees(object):
    def __init__(self, config):
        self.config = config
        self.cell_size = config.cell_size

    def update(self, x, y, cell, cam, cells, blobs):
        cellp = Vec2(
            cam.pos.x % self.cell_size - x * self.cell_size,
            cam.pos.y % self.cell_size - y * self.cell_size,
        )
        for tree in cell.trees:
            tree.s = tree.pos.sub(cellp.add(self.config.perspective_offset))
            tree.s._mul(tree.height * 0.015)
            tree.s._add(tree.pos)
            leaves_0 = tree.pos.lerp(tree.s, 0.5)
            leaves_1 = tree.pos.lerp(tree.s, 0.75)
            leaves_2 = tree.s
            tree.leaves[0] = [leaves_0.x, leaves_0.y]
            tree.leaves[1] = [leaves_1.x, leaves_1.y]
            tree.leaves[2] = [leaves_2.x, leaves_2.y]
            blobs.add_blob(
                Vec2((cells.pos.x + x) * self.cell_size, (cells.pos.y + y) * self.cell_size).add(tree.pos),
                tree.girth,
            )

    def draw(self, a, b, cell, cam, shadow):
        k7.camera(-flr(cam.c.x - a * self.cell_size), -flr(cam.c.y - b * self.cell_size))
        if not cell.trees:
            return
        if shadow:
            for tree in cell.trees:
                k7.circfill(
                    flr(tree.pos.x + self.config.shadow_offset.x * tree.height / 2),
                    flr(tree.pos.y + self.config.shadow_offset.y * tree.height / 2),
                    flr(tree.girth),
                    5,
                )
        else:
            for tree in cell.trees:
                for ox in range(-1, 2):
                    for oy in range(-1, 2):
                        if abs(ox) + abs(oy) != 2:
                            k7.line(
                                flr(tree.pos.x + ox),
                                flr(tree.pos.y + oy),
                                flr(tree.s.x),
                                flr(tree.s.y),
                                4,
                            )
            ccols = [[3, 1.0], [11, 0.7], [7, 0.4]]
            for i in range(3):
                for tree in cell.trees:
                    k7.circfill(
                        flr(tree.leaves[i][0]),
                        flr(tree.leaves[i][1]),
                        flr(tree.girth * ccols[i][1]),
                        ccols[i][0],
                    )


class Cells(object):
    def __init__(self, x, y, config, biomes):
        self.pos = Vec2(x, y)
        self.config = config
        self.biomes = biomes
        self.cell_fill = config.cell_fill
        self.cell_size = config.cell_size
        self.cells = [None] * (self.cell_fill * self.cell_fill)
        self._cache = {}
        self.set_cells()

    def set_pos(self, pos):
        if self.pos.x != pos.x or self.pos.y != pos.y:
            self.pos.x = pos.x
            self.pos.y = pos.y
            self.set_cells()

    def get(self, x, y):
        # Avoid clearing mid-frame: duplicate Cell objects broke terrain init (black world).
        if len(self._cache) > 5000:
            self._cache = {}
        key = "%d-%d" % (x, y)
        if key in self._cache:
            return self._cache[key]
        cell = Cell(1)
        self._cache[key] = cell
        return cell

    def get_current(self, a, b):
        return self.cells[a * self.cell_fill + b]

    def set_bounds(self, x, y, cell):
        cell.color = biome_at_cell(x, y)
        random.seed(cell_rng_seed(x, y))
        for u in range(-1, 2):
            for v in range(-1, 2):
                e = biome_at_cell(x + u, y + v)
                if e == 14:
                    e = 3
                cell.edges[u][v] = e or 1

    def set_trees(self, cell, biome):
        tree_freq = ease(myrange_f(biome.tree_range))
        if cell.color == 14:
            cell.color = 3
            height = myrange(self.config.trees_height_range)
            girth = min(self.cell_size, self.cell_size) * 2 / 5
            p = Vec2(self.cell_size / 2, self.cell_size / 2)
            leaves = [[0, 0], [0, 0], [0, 0]]
            cell.trees.append(Tree(p, height, girth, leaves))
        else:
            for tx in range(0, self.cell_size - self.config.trees_gap, self.config.trees_gap):
                for ty in range(0, self.cell_size - self.config.trees_gap, self.config.trees_gap):
                    if random.random() < tree_freq:
                        height = myrange(self.config.trees_height_range)
                        girth = myrange(self.config.trees_girth_range)
                        px = tx + random.random() * self.config.trees_gap
                        py = ty + random.random() * self.config.trees_gap
                        px = mid(girth, px, self.cell_size - girth)
                        py = mid(girth, py, self.cell_size - girth)
                        leaves = [[0, 0], [0, 0], [0, 0]]
                        cell.trees.append(Tree(Vec2(px, py), height, girth, leaves))

    def set_bushes(self, cell, biome):
        if random.random() < biome.bush_props[0]:
            bx = random.random() * self.cell_size
            by = random.random() * self.cell_size
            r_add = 0.0
            bloom_colours = biome.bush_props[2]
            colour = bloom_colours[flr(random.random() * len(bloom_colours)) % len(bloom_colours)]
            for _ in range(myrange(self.config.bushes_cluster_range)):
                r = myrange_f(self.config.bushes_radius_range)
                height = myrange_f(self.config.bushes_height_range)
                p = Vec2(
                    bx + myrange_f([1, (r + r_add)]) - myrange_f([1, (r + r_add) / 2]),
                    by + myrange_f([1, (r + r_add)]) - myrange_f([1, (r + r_add) / 2]),
                )
                bloom = None
                if random.random() < biome.bush_props[1]:
                    ang = random.random() * 6.28
                    r_add = random.random() * (r / 2.0) + r / 4.0
                    bloom = Vec2(r * math.cos(ang), r * math.sin(ang))
                cell.bushes.append(Bush(p, r, height, colour, bloom))

    def set_buildings(self, cell, biome):
        if (len(cell.trees) + len(cell.bushes) == 0) and random.random() < biome.building_freq:
            cell.building = Building(
                myrange(self.config.buildings_w_range),
                myrange(self.config.buildings_h_range),
                Vec2(self.cell_size / 2, self.cell_size / 2),
                myrange(self.config.buildings_height_range),
                self.config.buildings_colours[flr(random.random() * 16) % len(self.config.buildings_colours)],
            )

    def set_cells(self):
        for a in range(self.cell_fill):
            for b in range(self.cell_fill):
                x = flr(a + self.pos.x)
                y = flr(b + self.pos.y)
                cell = self.get(x, y)
                self.cells[a * self.cell_fill + b] = cell
                if cell.init:
                    continue
                cell.x = x
                cell.y = y
                cell.init = True
                self.set_bounds(x, y, cell)
                biome = self.biomes.biomes.get(cell.color, self.biomes.biomes[1])
                self.set_trees(cell, biome)
                self.set_bushes(cell, biome)
                self.set_buildings(cell, biome)


class Player(object):
    def __init__(self, vec2):
        self.pos = vec2
        self.v = Vec2(0, 0)
        # Slower than duck.pik for a large world; tweak speed / max_speed together.
        self.speed = Vec2(0.32, 0.32)
        self.max_speed = 1.35
        self.cur_speed = 0.0
        self.damping = 0.82
        # Heading for head/body stack: screen +x right, +y down (atan2(dy, dx)).
        self.a = -math.pi / 2
        self.r = 4.0
        self.r2 = self.r * self.r
        self.height = 4.0
        self.c = [4, 10, 3]

    def update(self):
        v_dif = Vec2(0, 0)
        if k7.btn(0):
            v_dif.x -= self.speed.x
        if k7.btn(1):
            v_dif.x += self.speed.x
        if k7.btn(2):
            v_dif.y -= self.speed.y
        if k7.btn(3):
            v_dif.y += self.speed.y
        if abs(v_dif.x) + abs(v_dif.y) > 0.01:
            self.v._add(v_dif)
            self.a = math.atan2(v_dif.y, v_dif.x)
        if k7.btnp(0):
            k7.sfx(8)
        if k7.btnp(1):
            k7.sfx(9)
        if k7.btnp(2):
            k7.sfx(10)
        if k7.btnp(3):
            k7.sfx(11)
        self.v._mul(self.damping)
        if abs(self.v.x) < 0.01:
            self.v.x = 0
        if abs(self.v.y) < 0.01:
            self.v.y = 0
        self.cur_speed = self.v.len()
        if self.cur_speed > self.max_speed:
            self.v._mul(self.max_speed / self.cur_speed)
            self.cur_speed = self.max_speed
        self.pos._add(self.v)

    def draw_shadow(self):
        o = SHADOW_OFFSET.mul(self.height)
        k7.circfill(flr(self.pos.x + o.x), flr(self.pos.y + o.y), flr(self.r), 5)

    def draw(self):
        # duck.pik Player.draw(): body + head circles + eye pset (procedural duck)
        s = self.cur_speed / self.max_speed * self.r / 5 + 0.5
        p1 = Vec2(self.pos.x, self.pos.y)
        p2 = Vec2(
            p1.x + self.height * math.cos(self.a) * s,
            p1.y + self.height * math.sin(self.a) * s,
        )
        k7.circfill(flr(p1.x), flr(p1.y), flr(self.r * 3 / 4), self.c[0])
        k7.circfill(flr(p2.x), flr(p2.y), flr(self.r / 2), self.c[1])
        p2 = p1.lerp(p2, 0.75)
        k7.circfill(flr(p2.x), flr(p2.y), flr(self.r / 2), self.c[2])
        p2 = p1.lerp(p2, 0.5)
        k7.pset(flr(p2.x), flr(p2.y), 0)


class Camera(object):
    def __init__(self, vec2):
        self.pos = vec2
        self.c = Vec2(self.pos.x % CELL_SIZE, self.pos.y % CELL_SIZE)
        self.offset = Vec2(W / 2, H / 2)
        # duck.pik: sway [0.15,0.15,50,50], pikuseru_time → time_s
        self.sway = [0.15, 0.15, 50.0, 50.0]
        self.pos_o = Vec2(self.pos.x, self.pos.y)
        self.v = Vec2(0, 0)

    def update(self, p_p, p_v):
        # duck.pik: offset = p_v.mul(-15).add(Vec2(64,64)) — scale lead for 256px view
        lead = -15.0 * (W / 128.0)
        self.offset = p_v.mul(lead).add(Vec2(W / 2, H / 2))
        self.pos_o = Vec2(self.pos.x, self.pos.y)
        sway = Vec2(
            self.sway[0] * math.cos(time_s / self.sway[2] * 6.2831853),
            self.sway[1] * math.sin(time_s / self.sway[3] * 6.2831853),
        )
        target = p_p.sub(self.offset)
        self.pos = self.pos.lerp(target, 0.1).add(sway)
        self.v = self.pos.sub(self.pos_o)
        self.c.x = self.pos.x % CELL_SIZE
        self.c.y = self.pos.y % CELL_SIZE


class Cloud(object):
    __slots__ = ("p", "s", "ps", "r", "height")

    def __init__(self, x, y, r, height):
        self.p = Vec2(x, y)
        self.s = Vec2(x, y)
        self.ps = Vec2(x, y)
        self.r = r
        self.height = height


class Clouds(object):
    def __init__(self):
        # duck.pik: count 20–40, radius 5–15, cluster 5–7, height 45–50 (scaled for 256 view)
        self.radius_max = 12.0
        self.size = W
        self.height_mult = 0.015
        self.clouds = []
        n = random.randint(18, 34)
        for _ in range(n):
            x = random.random() * self.size * 2
            y = random.random() * self.size * 2
            r = 0.0
            for _ in range(random.randint(5, 7)):
                c_r = random.uniform(3, self.radius_max)
                c_p = [
                    x + random.uniform(1, (c_r + r) / 2) - random.uniform(1, (c_r + r) / 2),
                    y + random.uniform(1, (c_r + r) / 2) - random.uniform(1, (c_r + r) / 2),
                ]
                if random.random() > 0.5:
                    x, y, r = c_p[0], c_p[1], c_r
                self.clouds.append(
                    Cloud(c_p[0], c_p[1], c_r, random.uniform(22.0, 28.0))
                )

    def update(self, cam):
        rm = self.radius_max
        for cloud in self.clouds:
            # duck.pik: cloud.p.x += 0.1 - cam.v.x
            cloud.p.x += 0.1 - cam.v.x
            cloud.p.y += 0.1 - cam.v.y
            if cloud.p.x > self.size + rm:
                cloud.p.x -= self.size * 2 + rm
            elif cloud.p.x < -self.size - rm:
                cloud.p.x += self.size * 2 + rm
            if cloud.p.y > self.size + rm:
                cloud.p.y -= self.size * 2 + rm
            elif cloud.p.y < -self.size - rm:
                cloud.p.y += self.size * 2 + rm
            cloud.s = cloud.p.sub(PERSPECTIVE_OFFSET)
            cloud.s._mul(cloud.height * self.height_mult)
            cloud.s._add(cloud.p)
            cloud.ps = cloud.p.add(SHADOW_OFFSET.mul(cloud.height))

    def draw_shadow(self):
        for cloud in self.clouds:
            k7.circfill(flr(cloud.ps.x), flr(cloud.ps.y), flr(cloud.r), 5)

    def draw(self):
        for cloud in self.clouds:
            k7.circfill(flr(cloud.s.x), flr(cloud.s.y), flr(cloud.r), 7)


# Original forest BGM: layered pads + light percussion (not MP3-derived).
_FOREST_BGM = (
    "c3:saw|lowpass:dark g2:saw|lowpass:dark e3:triangle c4:square|envelope:perc|hp:bright "
    "c3:saw|lowpass:dark a2:saw|lowpass:dark f3:triangle e4:square|envelope:perc|hp:bright "
    "d3:saw|lowpass:dark b2:saw|lowpass:dark g3:triangle d4:square|envelope:perc|hp:bright "
    "c3:saw|lowpass:dark g2:saw|lowpass:dark e3:triangle g4:square|envelope:perc|hp:bright "
    "f6:drums:hat c3:saw|lowpass:dark g3:triangle a3:square|envelope:perc|hp:bright "
    "f6:drums:hat d3:saw|lowpass:dark f3:triangle c5:square|envelope:perc|hp:bright "
    "g6:drums:hat e3:saw|lowpass:dark c4:triangle e4:square|envelope:perc|hp:bright "
    "f6:drums:hat c3:saw|lowpass:dark g3:triangle g4:square|envelope:perc|hp:bright "
    "c5:pluck:bright g2:saw|lowpass:dark e3:triangle c4:square|envelope:perc|hp:bright "
    "e5:pluck:bright a2:saw|lowpass:dark f3:triangle a4:square|envelope:perc|hp:bright "
    "g5:pluck:bright b2:saw|lowpass:dark g3:triangle e5:square|envelope:perc|hp:bright "
    "c5:pluck:bright c3:saw|lowpass:dark e4:triangle g4:square|envelope:perc|hp:bright "
    "f6:drums:hat c3:saw|lowpass:dark g2:saw|lowpass:dark e3:triangle c4:square|envelope:perc|hp:bright "
    "c5:drums:snare d3:saw|lowpass:dark a2:saw|lowpass:dark f3:triangle d4:square|envelope:perc|hp:bright "
    "f6:drums:hat e3:saw|lowpass:dark b2:saw|lowpass:dark g3:triangle e4:square|envelope:perc|hp:bright "
    "g6:drums:hat c3:saw|lowpass:dark g2:saw|lowpass:dark c4:triangle g4:square|envelope:perc|hp:bright "
).replace("  ", " ").strip()

B = Biomes()
BLOBS = Blobs()
CONFIG = Configuration(B, BLOBS)
def _duck_pik_spawn_and_camera():
    # duck.pik: P = Player(Vec2(82,16).mul(32)); P.pos.y -= 128
    #          CAM = Camera(P.pos.sub(Vec2(64, 64+128)))
    ow = 128 * 32
    px = 82 * 32
    py = 16 * 32 - 128
    p = Vec2(px / ow * WORLD_PX_W, py / ow * WORLD_PX_W)
    cam_dx = 64 / ow * WORLD_PX_W
    cam_dy = (64 + 128) / ow * WORLD_PX_W
    return p, Vec2(p.x - cam_dx, p.y - cam_dy)


_spawn, _cam0 = _duck_pik_spawn_and_camera()
P = Player(_spawn)
CAM = Camera(_cam0)
CLOUDS = Clouds()
TREES = Trees(CONFIG)
BUSHES = Bushes(CONFIG)
BUILDINGS = Buildings(CONFIG)
CELLS = Cells(flr(CAM.pos.x / CELL_SIZE), flr(CAM.pos.y / CELL_SIZE), CONFIG, B)


def draw_background():
    k7.camera(-flr(CAM.pos.x), -flr(CAM.pos.y))
    for a in range(CELL_FILL):
        for b in range(CELL_FILL):
            x = (CELLS.pos.x + a) * CELL_SIZE
            y = (CELLS.pos.y + b) * CELL_SIZE
            cell = CELLS.get_current(a, b)
            c = cell.color if cell and cell.color else 11
            k7.rectfill(x, y, x + CELL_SIZE, y + CELL_SIZE, c)


def draw_world_shadows():
    for a in range(CELL_FILL):
        for b in range(CELL_FILL):
            cell = CELLS.get_current(a, b)
            TREES.draw(a, b, cell, CAM, True)
            BUSHES.draw(a, b, cell, CAM, True)
            BUILDINGS.draw(a, b, cell, CAM, True)


def draw_world_solids():
    for a in range(CELL_FILL):
        for b in range(CELL_FILL):
            cell = CELLS.get_current(a, b)
            TREES.draw(a, b, cell, CAM, False)
            BUSHES.draw(a, b, cell, CAM, False)
            BUILDINGS.draw(a, b, cell, CAM, False)


def draw_player_world():
    k7.camera(-flr(CAM.pos.x), -flr(CAM.pos.y))
    P.draw_shadow()
    P.draw()


def draw_clouds_world(shadow):
    k7.camera(-flr(CAM.pos.x), -flr(CAM.pos.y))
    if shadow:
        CLOUDS.draw_shadow()
    else:
        CLOUDS.draw()


def init():
    global frame, time_s, PERSPECTIVE_OFFSET
    frame = 0
    time_s = 0.0
    k7.switch_palette("pico8")
    if hasattr(k7, "set_music_step_ms"):
        k7.set_music_step_ms(210)
    k7.set_music_track(0, _FOREST_BGM)
    k7.play_music(0, 0)
    # SFX slots 8–11: arrow quacks (avoid 0–7 common editor slots).
    k7.set_sound(8, "a3:triangle|envelope:perc|hp:bright")
    k7.set_sound(9, "c4:triangle|envelope:perc|hp:bright")
    k7.set_sound(10, "e3:triangle|envelope:perc|hp:bright")
    k7.set_sound(11, "g3:triangle|envelope:perc|hp:bright")


def update():
    global frame, time_s, PERSPECTIVE_OFFSET
    frame += 1
    time_s += 0.035
    P.update()
    # duck.pik: Vec2(64+sin(t/9)*4, 80+sin(t/11)*4) — base halved for our PERSPECTIVE_OFFSET_X/Y
    po = Vec2(
        PERSPECTIVE_OFFSET_X + math.sin(time_s / 9.0) * 2,
        PERSPECTIVE_OFFSET_Y + math.sin(time_s / 11.0) * 2,
    )
    PERSPECTIVE_OFFSET = po
    CONFIG.perspective_offset = po
    CAM.update(P.pos, P.v)
    CELLS.set_pos(Vec2(flr(CAM.pos.x / CELL_SIZE), flr(CAM.pos.y / CELL_SIZE)))
    BLOBS.blobs = {}
    for x in range(CELL_FILL):
        for y in range(CELL_FILL):
            cell = CELLS.get_current(x, y)
            TREES.update(x, y, cell, CAM, CELLS, BLOBS)
            BUSHES.update(x, y, cell, CAM, CELLS, BLOBS)
            BUILDINGS.update(x, y, cell, CAM, CELLS, BLOBS)
    CLOUDS.update(CAM)
    BLOBS.update(P)


def draw():
    k7.cls(0)
    k7.camera(0, 0)
    draw_background()
    draw_world_shadows()
    draw_clouds_world(True)
    draw_world_solids()
    draw_player_world()
    draw_clouds_world(False)
    k7.camera(0, 0)
    k7.set_font("pico8")
    k7.print("duck forest (duck.pik)", 4, 4, 7)
    k7.print("arrows move", 4, 14, 6)
    k7.print("blobs:%d" % BLOBS.len(), 4, H - 12, 5)
    k7.draw_to_canvas(CANVAS_ID)


def game_loop():
    update()
    draw()


init()
js.game_loop_js = game_loop
