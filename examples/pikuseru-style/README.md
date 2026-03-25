# K7 examples (from Pikuseru)

These Python examples are adapted from [pikuseru-examples](https://github.com/PikuseruConsole/pikuseru-examples). They run in the K7 web Python editor (`crates/k7-web/editor.html`): use the **Example** dropdown and click Run.

- **plasma.py** – Plasma effect (from demos/plasma/plasma.pik). Uses sin/cos and rectfill for a full-screen effect.
- **fireworks.py** – Fireworks particles (from demos/fireworks). Gravity, respawn, pset.
- **flock.py** – Simple boids (from demos/flocking/flock.pik). No input; leader moves in a circle.
- **ghostmark.py** – **Benchmark**: 500 moving dots (bounce + gravity), each drawn with circfill. From ghostmark (original: http://tic.computer/play?cart=122). Use for comparing draw/update throughput across runtimes or devices.
