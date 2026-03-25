# K7 Map scroll — draws the map with map_draw.
# Edit the map in the Map tab; this demo scrolls the camera.

import js
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
cam_x = 0.0
MAP_CW, MAP_CH = 256, 32
CELL = 8

def paint_tile_sprites():
    # Sprite 0 is invisible in map_draw (transparent); use 1 = ground, 2 = accent.
    for x in range(8):
        for y in range(8):
            k7.sset(x, y, 0)
            if y >= 4:
                k7.sset(x, y, 11)
            elif y == 3:
                k7.sset(x, y, 3)
    for ox in range(8):
        for oy in range(8):
            sx, sy = 8 + ox, oy
            c = 9 if (ox + oy) % 2 == 0 else 10
            if 1 < ox < 6 and 1 < oy < 6:
                k7.sset(sx, sy, c)
            else:
                k7.sset(sx, sy, 0)


def init():
    global cam_x
    cam_x = 0.0
    paint_tile_sprites()
    for cx in range(MAP_CW):
        if k7.mget(cx, MAP_CH - 1) == 0:
            k7.mset(cx, MAP_CH - 1, 1)
        if cx % 4 == 0 and k7.mget(cx, MAP_CH - 2) == 0:
            k7.mset(cx, MAP_CH - 2, 2)

def update():
    global cam_x
    cam_x += 0.4
    if cam_x >= (MAP_CW - 32) * CELL:
        cam_x = 0.0

def draw():
    k7.cls(0)
    cell_x = int(cam_x) // CELL
    k7.map_draw(cell_x, 0, 0, 0, 32, 32)
    k7.rect(0, 0, W - 1, H - 1, 6)
    k7.print("map scroll — edit Map tab", 30, 4, 7)
    k7.print("map_draw(cx,cy,sx,sy,w,h)", 20, 244, 6)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
