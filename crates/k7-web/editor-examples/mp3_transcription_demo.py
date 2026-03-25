# Auto-transcribed from MP3 (pitch estimate — not a real MIDI import).
# Source file: ~/Downloads/2024021430.mp3 (~58s). Method: afconvert → WAV, librosa.pyin,
# steps quantized to ~16th note at detected ~117 BPM (k7.set_music_step_ms(128)).
#
# This is a *rough mono line*: chords and drums collapse to one pitch; expect errors.
# Re-run: scripts/mp3_to_k7_track.py (see repo scripts/; needs venv + librosa).
#
import js
k7 = js.k7
CANVAS_ID = "k7canvas"
W, H = 256, 256
MUSIC_STEP_MS = 128
MUSIC_START_MS = 0.0
frame = 0

TRACK = (
    "d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright "
    "d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright "
    "d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright - "
    "d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright f2:square|envelope:perc|hp:bright f2:square|envelope:perc|hp:bright f2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright "
    "d2:square|envelope:perc|hp:bright f2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright f2:square|envelope:perc|hp:bright - d2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright f2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright f2:square|envelope:perc|hp:bright f2:square|envelope:perc|hp:bright f2:square|envelope:perc|hp:bright f2:square|envelope:perc|hp:bright f2:square|envelope:perc|hp:bright f2:square|envelope:perc|hp:bright f2:square|envelope:perc|hp:bright "
    "f2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright a#2:square|envelope:perc|hp:bright a#2:square|envelope:perc|hp:bright "
    "a#2:square|envelope:perc|hp:bright a#2:square|envelope:perc|hp:bright a#2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright "
    "c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright "
    "c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright "
    "e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright "
    "e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright "
    "e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright "
    "e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright e2:square|envelope:perc|hp:bright d#2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - "
    "- c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright - - - c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "- c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright d#2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright "
    "c#2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright d#2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "- c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "- c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - - c2:square|envelope:perc|hp:bright - c#2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright - - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright d#2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "- - c2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c#2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright d#2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - "
    "c2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright - - - - - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright d2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright c2:square|envelope:perc|hp:bright "
    "c2:square|envelope:perc|hp:bright - c2:square|envelope:perc|hp:bright "
)

def init():
    global MUSIC_START_MS, frame
    frame = 0
    k7.switch_palette("pico8")
    if hasattr(k7, "set_music_step_ms"):
        k7.set_music_step_ms(int(MUSIC_STEP_MS))
    k7.set_music_track(0, TRACK)
    k7.play_music(0, 0)
    MUSIC_START_MS = float(js.Date.now())

def update():
    global frame, MUSIC_START_MS
    frame += 1
    if k7.btnp(4):
        k7.play_music(0, 0)
        MUSIC_START_MS = float(js.Date.now())

def draw():
    k7.cls(1)
    k7.print("MP3 -> K7 TRACK", 56, 20, 12)
    k7.print("2024021430.mp3", 52, 36, 11)
    k7.print("pyin ~117 bpm", 68, 52, 10)
    k7.print("Z: restart", 88, 200, 6)
    k7.draw_to_canvas(CANVAS_ID)


def game_loop():
    update()
    draw()


init()
js.game_loop_js = game_loop
