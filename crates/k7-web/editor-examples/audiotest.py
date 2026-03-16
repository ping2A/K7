# K7 Audio test — exercises all audio features for testing.
# Keys: Left/Right = slot, Z = play, X = layered, C = play music. In code: k7.master_volume(0.5), k7.mute_sfx(1), k7.mute_music(1).

import js
k7 = js.k7
CANVAS_ID = "k7canvas"
current = 0
LABELS = [
    "0 Layered (sine+tri+sq)",
    "1 Per-note volume @",
    "2 Per-note duration q/:2",
    "3 Arpeggio arp:maj",
    "4 Envelope pluck/pad",
    "5 Reverb/Echo/Chorus",
    "6 Lowpass/Highpass",
    "7 Distortion/Bitcrush",
    "8 Instrument piano:bright",
    "9 Instrument chip+pad",
    "10 Tremolo/Vibrato",
    "11 AutoPan",
    "12 Portamento",
    "13 Sidechain/EQ",
    "14 Full combo",
    "15 Instruments strings/brass",
]

def init():
    global current
    current = 0
    # 0: Layered waveform
    k7.set_sound(0, "c4:layer:sine:0.4,tri:0.3,sq:0.1|reverb:small")
    # 1: Per-note volume (@80 = 80%)
    k7.set_sound(1, "c4@100 e4@60 g4@80 c5@100")
    # 2: Per-note duration (short: q=quarter, h=half; numeric :2 = 2 beats)
    k7.set_sound(2, "cq4 eq4 g4:2 ch4")
    # 3: Arpeggio
    k7.set_sound(3, "c4|arp:maj")
    # 4: Envelope presets
    k7.set_sound(4, "c4|envelope:pluck e4|envelope:pad g4|envelope:organ")
    # 5: Reverb, Echo, Chorus
    k7.set_sound(5, "c4|reverb:hall e4|echo:short g4|chorus:thick")
    # 6: Lowpass / Highpass
    k7.set_sound(6, "c4|lp:warm e4|hp:bright g4|lp:dark")
    # 7: Distortion / Bitcrush
    k7.set_sound(7, "c4|dist:medium e4|bitcrush:nes g4|bitcrush:gameboy")
    # 8: Instrument (piano:bright = layer + hp + reverb)
    k7.set_sound(8, "c4:piano:bright e4:piano:bright g4:piano:bright")
    # 9: Instruments chip + pad
    k7.set_sound(9, "c4:chip:pulse e4:pad:warm g4:chip:triangle")
    # 10: Tremolo / Vibrato
    k7.set_sound(10, "c4|trem:5:0.5 e4|vib:5:0.02 g4|trem:8:0.6")
    # 11: AutoPan
    k7.set_sound(11, "c4 e4 g4 c5|autopan:1:0.7")
    # 12: Portamento (time_ms; target set at playback in full tracker)
    k7.set_sound(12, "c4|port:150 e4|port:100")
    # 13: Sidechain / EQ
    k7.set_sound(13, "c4|sidechain:subtle e4|eq:warm g4|eq:bright")
    # 14: Full combo (layered + reverb + envelope)
    k7.set_sound(14, "c4:layer:sine:0.5,tri:0.3|reverb:medium|envelope:pluck e4:layer:sq:0.5,tri:0.3|reverb:hall|envelope:pad")
    # 15: More instruments
    k7.set_sound(15, "c4:strings:ensemble e4:brass:section g4:organ:church")
    # Music track (play with C key)
    k7.set_music_track(0, "c4 e4 g4 c5 e4 g4 c5 e5")

def update():
    global current
    if k7.btnp(0):  # Left
        current = (current - 1) % 16
    if k7.btnp(1):  # Right
        current = (current + 1) % 16
    if k7.btnp(4):  # Z = play current
        k7.sfx(current)
    if k7.btnp(5):  # X = play layered (0)
        k7.sfx(0)
    if k7.btnp(6):  # C = play music track 0
        k7.play_music(0, 0)

def draw():
    k7.cls(0)
    k7.rectfill(0, 0, 255, 10, 1)
    k7.print("AUDIO TEST", 88, 2, 7)
    k7.print("<- -> slot  Z play  X layered  C music", 8, 18, 6)
    for i in range(16):
        y = 28 + i * 12
        col = 11 if i == current else 6
        k7.print(LABELS[i], 8, y, col)
    k7.print("master_volume(v) mute_sfx(1) mute_music(1)", 8, 218, 5)
    k7.draw_to_canvas(CANVAS_ID)

def game_loop():
    update()
    draw()

init()
js.game_loop_js = game_loop
