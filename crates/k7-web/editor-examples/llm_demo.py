# K7 LLM Chat — type in the demo, get replies on the canvas.
# 1) Start: cargo run -p k7-multiplayer-server (proxies to http://127.0.0.1:1234).
# 2) Run this demo; click the canvas, type your message, press Enter to send.

import js
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256

WS_URL = "ws://127.0.0.1:8081"

messages = []
display_lines = []
scroll = 0
frame = 0
status_msg = "Connecting..."
input_buf = ""
MAX_INPUT = 120
MAX_LINE_LEN = 52
LINE_H = 10
HEADER_H = 22
INPUT_H = 14
FOOTER_H = 0
VISIBLE_LINES = max(1, (H - HEADER_H - INPUT_H - 6) // LINE_H)


def wrap(txt, width=MAX_LINE_LEN):
    words = (txt or "").split()
    lines = []
    line = []
    n = 0
    for w in words:
        if n + len(w) + (1 if line else 0) > width:
            if line:
                lines.append(" ".join(line))
            line = [w]
            n = len(w)
        else:
            line.append(w)
            n += len(w) + (1 if len(line) > 1 else 0)
    if line:
        lines.append(" ".join(line))
    return lines


def build_display_lines():
    global display_lines
    display_lines = []
    for m in messages:
        role = m["role"]
        prefix = "You: " if role == "user" else "Assistant: "
        for i, line in enumerate(wrap(m["text"])):
            display_lines.append((role, (prefix if i == 0 else "    ") + line[:64]))


def init():
    global messages, display_lines, scroll, status_msg, input_buf, frame
    messages = []
    display_lines = []
    scroll = 0
    frame = 0
    input_buf = ""
    k7.text_input_mode(True)
    k7.llm_configure(None, None, None)
    try:
        k7.ws_connect(WS_URL)
        status_msg = "Type your message, Enter to send"
    except Exception:
        status_msg = "Start server: cargo run -p k7-multiplayer-server"


def update():
    global messages, display_lines, scroll, status_msg, input_buf
    k7.ws_take_messages()

    # Drain typed characters (K7 text input mode)
    for c in k7.take_key_queue():
        c = str(c)
        if c == "\n":
            msg = input_buf.strip()
            input_buf = ""
            if msg and k7.ws_connected():
                messages.append({"role": "user", "text": msg})
                k7.llm_send(msg)
                status_msg = "Waiting for reply..."
            elif msg:
                status_msg = "Not connected"
        elif c == "\b":
            input_buf = input_buf[:-1]
        elif len(input_buf) < MAX_INPUT and len(c) == 1:
            input_buf += c

    if k7.llm_pending():
        return

    err = k7.llm_take_error()
    if err:
        status_msg = "Error: " + err[:36]
        messages.append({"role": "assistant", "text": "[Error: " + err + "]"})
        return

    r = k7.llm_take_response()
    if r is not None:
        messages.append({"role": "assistant", "text": r})
        status_msg = "Type message, Enter to send"

    build_display_lines()

    if k7.btnp(2):
        scroll = max(0, scroll - 1)
    if k7.btnp(3):
        scroll = min(max(0, len(display_lines) - VISIBLE_LINES), scroll + 1)


def draw():
    global frame
    frame += 1
    k7.cls(0)
    k7.print("K7 LLM Chat", 80, 4, 11)
    k7.print(status_msg[:44], 4, 14, 6)

    # Chat area
    chat_y0 = HEADER_H
    chat_y1 = H - INPUT_H - 4
    k7.rect(2, chat_y0, W - 3, chat_y1, 5)
    k7.rectfill(4, chat_y0 + 2, W - 5, chat_y1 - 2, 0)

    start = scroll
    end = min(len(display_lines), start + VISIBLE_LINES)
    for i in range(start, end):
        j = i - start
        role, line = display_lines[i]
        col = 11 if role == "user" else 7
        k7.print(line, 6, chat_y0 + 4 + j * LINE_H, col)

    # Input line at bottom
    k7.rect(2, H - INPUT_H - 2, W - 3, H - 2, 5)
    k7.rectfill(4, H - INPUT_H, W - 5, H - 4, 0)
    prompt = "> " + input_buf
    if (frame // 30) % 2 == 0:
        prompt += "_"
    else:
        prompt += " "
    k7.print(prompt[:64], 6, H - INPUT_H + 2, 11)

    k7.print("Up/Down scroll", 4, H - 2, 5)
    k7.draw_to_canvas(CANVAS_ID)


def game_loop():
    update()
    draw()


init()
js.game_loop_js = game_loop
