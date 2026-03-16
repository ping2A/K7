#!/usr/bin/env python3
"""Extract example games from editor.html into editor-examples/*.py"""
import re
import os

NAMES = [
    "defaultGame", "defaultMouseGame", "defaultMultiplayerGame", "defaultPlasmaGame",
    "defaultFontsGame", "defaultRgbaGame", "defaultSkiGame", "defaultFlappyGame",
    "defaultFireworksGame", "defaultFlockGame", "defaultGhostmarkGame", "defaultSnakeGame",
    "defaultSpritesGame", "defaultMapScrollGame", "defaultPongGame", "defaultBreakoutGame",
    "defaultPlatformerGame", "defaultRaveTunnelGame", "defaultTrippyKaleidGame",
    "defaultHypnoSpiralGame", "defaultRasterBarsGame", "defaultScrollerGame",
    "defaultFireGame", "defaultAudioTestGame", "defaultSequencerGame", "defaultSableGame",
    "defaultDemoGame",
]
KEY_MAP = {
    "defaultGame": "default",
    "defaultMouseGame": "mouse",
    "defaultMultiplayerGame": "multiplayer",
    "defaultPlasmaGame": "plasma",
    "defaultFontsGame": "fonts",
    "defaultRgbaGame": "rgba",
    "defaultSkiGame": "ski",
    "defaultFlappyGame": "flappy",
    "defaultFireworksGame": "fireworks",
    "defaultFlockGame": "flock",
    "defaultGhostmarkGame": "ghostmark",
    "defaultSnakeGame": "snake",
    "defaultSpritesGame": "sprites",
    "defaultMapScrollGame": "mapscroll",
    "defaultPongGame": "pong",
    "defaultBreakoutGame": "breakout",
    "defaultPlatformerGame": "platformer",
    "defaultRaveTunnelGame": "ravetunnel",
    "defaultTrippyKaleidGame": "kaleidoscope",
    "defaultHypnoSpiralGame": "hypnospiral",
    "defaultRasterBarsGame": "rasterbars",
    "defaultScrollerGame": "scroller",
    "defaultFireGame": "fire",
    "defaultAudioTestGame": "audiotest",
    "defaultSequencerGame": "sequencer",
    "defaultSableGame": "sable",
    "defaultDemoGame": "showcase",
}

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base, "editor.html")
    out_dir = os.path.join(base, "editor-examples")
    os.makedirs(out_dir, exist_ok=True)

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    for name in NAMES:
        key = KEY_MAP[name]
        pattern = rf'const {re.escape(name)}\s*=\s*`((?:[^`\\]|\\.)*)`\s*;'
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            print(f"Skip {name} (not found)")
            continue
        code = m.group(1).replace("\\`", "`").replace("\\n", "\n")
        out_path = os.path.join(out_dir, f"{key}.py")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"Wrote {out_path}")
    print("Done.")

if __name__ == "__main__":
    main()
