#!/usr/bin/env python3
"""Remove inline example games from editor.html and add lazy-load logic."""
import os

base = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(base, "editor.html")

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Keep lines 1-826 (0-indexed: 0..825), then insert new block, then lines 3663+ (index 3662+)
before = lines[:826]
after = lines[3662:]

new_block = '''    const EXAMPLE_PATHS = {
      default: 'editor-examples/default.py',
      showcase: 'editor-examples/showcase.py',
      mouse: 'editor-examples/mouse.py',
      multiplayer: 'editor-examples/multiplayer.py',
      plasma: 'editor-examples/plasma.py',
      fonts: 'editor-examples/fonts.py',
      rgba: 'editor-examples/rgba.py',
      ski: 'editor-examples/ski.py',
      flappy: 'editor-examples/flappy.py',
      fireworks: 'editor-examples/fireworks.py',
      flock: 'editor-examples/flock.py',
      ghostmark: 'editor-examples/ghostmark.py',
      snake: 'editor-examples/snake.py',
      sprites: 'editor-examples/sprites.py',
      mapscroll: 'editor-examples/mapscroll.py',
      pong: 'editor-examples/pong.py',
      breakout: 'editor-examples/breakout.py',
      platformer: 'editor-examples/platformer.py',
      ravetunnel: 'editor-examples/ravetunnel.py',
      kaleidoscope: 'editor-examples/kaleidoscope.py',
      hypnospiral: 'editor-examples/hypnospiral.py',
      rasterbars: 'editor-examples/rasterbars.py',
      scroller: 'editor-examples/scroller.py',
      phrack_demo: 'editor-examples/phrack_demo.py',
      fire: 'editor-examples/fire.py',
      audiotest: 'editor-examples/audiotest.py',
      llm_demo: 'editor-examples/llm_demo.py',
      sequencer: 'editor-examples/sequencer.py',
      sable: 'editor-examples/sable.py',
    };

    async function loadExample(key) {
      const path = EXAMPLE_PATHS[key];
      if (!path) return;
      status('Loading example…');
      try {
        const res = await fetch(path);
        if (!res.ok) throw new Error(res.status);
        const code = await res.text();
        if (codeEditor && codeEditor.setValue) codeEditor.setValue(code, -1);
        else {
          const fb = document.getElementById('code-fallback');
          if (fb) fb.value = code;
        }
        status('');
      } catch (e) {
        status('Failed to load example. Serve editor from a server (e.g. cargo run -p k7-web).');
        console.warn('loadExample', key, e);
      }
    }

'''

out = before + [new_block] + after
with open(path, "w", encoding="utf-8") as f:
    f.writelines(out)
print("Patched editor.html: removed inline examples, added EXAMPLE_PATHS and loadExample.")
