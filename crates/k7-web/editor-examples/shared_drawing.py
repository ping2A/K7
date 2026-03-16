# K7 Shared drawing — everyone in the same room draws on the same canvas.
# 1) Start server: cargo run -p k7-multiplayer-server
# 2) Create room or Join with code, then Run. Draw with mouse; click palette bar to pick color. C = clear (broadcast to all).

import js
k7 = js.k7
CANVAS_ID = "k7canvas"
WS_URL = "ws://localhost:8081"
W, H = 256, 256
PALETTE_Y = 248

room_code = ""
room_ready = False
join_sent = False
current_color = 7
last_sent_x = -1
last_sent_y = -1

def init():
    global room_code, room_ready, join_sent, last_sent_x, last_sent_y
    room_code = ""
    room_ready = False
    join_sent = False
    last_sent_x = -1
    last_sent_y = -1
    k7.cls(0)
    try:
        k7.ws_connect(WS_URL)
    except Exception:
        pass

def process_messages():
    global room_code, room_ready, join_sent
    if not k7.ws_connected():
        return
    msgs = k7.ws_take_messages()
    for i in range(msgs.length):
        s = str(msgs[i])
        if s.startswith("created:"):
            room_code = s[8:].strip()
            room_ready = True
            el = js.document.getElementById("multiplayer-room-display")
            if el:
                el.textContent = "Room: " + room_code
        elif s == "joined":
            room_ready = True
            el = js.document.getElementById("multiplayer-room-display")
            if el:
                el.textContent = "Joined"
        elif s == "error:send_create_or_join":
            join_sent = False
        elif s == "c":
            k7.cls(0)
        elif s.startswith("d,"):
            parts = s.split(",")
            if len(parts) >= 4:
                try:
                    x = int(parts[1])
                    y = int(parts[2])
                    c = int(parts[3])
                    if 0 <= x < W and 0 <= y < PALETTE_Y and 0 <= c <= 15:
                        k7.pset(x, y, c)
                except ValueError:
                    pass

def update():
    global room_code, join_sent, current_color, last_sent_x, last_sent_y
    # Send create/join only once the WebSocket is connected so it's always the first message
    if k7.ws_connected() and not join_sent:
        action = getattr(js.window, "_multiplayerAction", None) or "create"
        if action:
            k7.ws_send(str(action))
            join_sent = True
    mx = k7.mouse_x()
    my = k7.mouse_y()
    process_messages()
    if my >= PALETTE_Y:
        if k7.mouse_btnp(0):
            current_color = max(0, min(15, mx // 16))
        return
    if k7.mouse_btn(0) and 0 <= mx < W and 0 <= my < PALETTE_Y:
        k7.pset(mx, my, current_color)
        if room_ready and (mx != last_sent_x or my != last_sent_y) and k7.ws_connected():
            k7.ws_send("d," + str(mx) + "," + str(my) + "," + str(current_color))
            last_sent_x = mx
            last_sent_y = my
    else:
        last_sent_x = -1
        last_sent_y = -1
    if k7.btnp(6):
        k7.cls(0)
        if room_ready and k7.ws_connected():
            k7.ws_send("c")

def draw():
    for i in range(16):
        x0 = i * 16
        k7.rectfill(x0, PALETTE_Y, x0 + 15, H - 1, i)
        if i == current_color:
            k7.rect(x0, PALETTE_Y, x0 + 15, H - 1, 15)
    k7.rect(0, 0, W - 1, PALETTE_Y - 1, 7)
    k7.print("Shared drawing", 70, 4, 7)
    if room_code:
        k7.print("Room: " + room_code, 40, 232, 11)
    status = "connected" if k7.ws_connected() else "disconnected"
    if not room_ready and k7.ws_connected():
        status = "waiting for room..."
    k7.print(status + "  color:" + str(current_color), 20, 240, 6)
    k7.print("C = clear", 100, 220, 5)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
