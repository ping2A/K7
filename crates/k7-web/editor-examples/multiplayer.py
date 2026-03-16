# K7 multiplayer: matchmaking + shared positions
# 1) Start server: cargo run -p k7-multiplayer-server
# 2) Select "Create room" or enter code and "Join room", then Run.
# Each client in the same room sends position and draws others.

import js
k7 = js.k7
CANVAS_ID = "k7canvas"
WS_URL = "ws://localhost:8081"

frame = 0
my_x = 128
my_y = 128
others = []
room_code = ""

def init():
    global frame, my_x, my_y, others, room_code
    frame = 0
    my_x = 128
    my_y = 128
    others = []
    room_code = ""
    try:
        k7.ws_connect(WS_URL)
        action = getattr(js.window, "_multiplayerAction", None) or "create"
        if action:
            k7.ws_send(str(action))
    except Exception as e:
        pass

def update():
    global frame, my_x, my_y, others, room_code
    frame += 1
    import math
    my_x = 128 + int(80 * math.sin(frame * 0.03))
    my_y = 128 + int(60 * math.cos(frame * 0.02))
    if k7.ws_connected():
        k7.ws_send(str(my_x) + "," + str(my_y))
        msgs = k7.ws_take_messages()
        others = []
        n = msgs.length
        for i in range(n):
            s = str(msgs[i])
            if s.startswith("created:"):
                room_code = s[8:].strip()
                el = js.document.getElementById("multiplayer-room-display")
                if el:
                    el.textContent = "Room: " + room_code
            elif s == "joined":
                el = js.document.getElementById("multiplayer-room-display")
                if el:
                    el.textContent = "Joined"
            elif s != "peer_joined":
                try:
                    parts = s.split(",")
                    if len(parts) >= 2:
                        others.append((int(parts[0]), int(parts[1])))
                except Exception:
                    pass

def draw():
    k7.cls(0)
    k7.rect(8, 8, 247, 247, 7)
    k7.circfill(my_x, my_y, 8, 11)
    k7.print("me", my_x - 6, my_y - 20, 11)
    for (ox, oy) in others:
        k7.circfill(ox, oy, 6, 8)
    k7.print("K7 multiplayer", 70, 4, 7)
    if room_code:
        k7.print("Room: " + room_code, 60, 220, 11)
    status = "connected" if k7.ws_connected() else "disconnected"
    k7.print(status + " peers:" + str(len(others)), 60, 232, 6)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
