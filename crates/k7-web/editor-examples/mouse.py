# K7 Mouse API demo — move and click on the canvas.
# k7.mouse_x(), k7.mouse_y() (0–255), k7.mouse_btn(0)=left held, k7.mouse_btnp(0)=left just pressed.

import js
k7 = js.k7
CANVAS_ID = "k7canvas"

def init():
    pass

def update():
    pass

def draw():
    k7.cls(0)
    mx = k7.mouse_x()
    my = k7.mouse_y()
    lb = k7.mouse_btn(0)
    lbp = k7.mouse_btnp(0)
    k7.rect(0, 0, 255, 255, 7)
    k7.circfill(mx, my, 4, 11)
    k7.print("mouse_x=" + str(mx) + " mouse_y=" + str(my), 8, 8, 7)
    k7.print("btn(0)=" + str(lb) + " btnp(0)=" + str(lbp), 8, 18, 6)
    k7.print("move/click on canvas", 8, 238, 5)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
