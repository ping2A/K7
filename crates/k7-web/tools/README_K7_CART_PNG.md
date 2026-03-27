# K7 cart PNG (PICO-8–style sharing)

[K7](https://github.com/ping2a/k7) can share a full game as a **normal PNG** you can post anywhere, similar in spirit to [PICO-8’s `.p8.png` cartridges](https://pico-8.fandom.com/wiki/P8PNGFileFormat).

## What’s inside

- **Label**: whatever the `k7canvas` shows when you export (like PICO-8’s cartridge picture).
- **Payload**: a PNG `tEXt` chunk, keyword **`k7cart`**, ASCII payload:
  - Same string as the editor’s URL share (`?g=…`):  
    `z` + URL-safe base64 (**raw deflate**, zlib *without* header — matches `CompressionStream('deflate')` in the browser)  
    or `j` + URL-safe base64 of UTF-8 JSON if smaller.

JSON keys mirror the web share state: `code`, optional `sounds`, `chains`, `audio_cart`, `map`, `sprites` (base64 blobs).

## Editor

- **Export cart PNG** — downloads `k7-cart.png`.
- **Import cart PNG** — restores editor + runtime state; click **Run** after.

**Note:** Some image hosts or editors **strip** ancillary PNG text chunks. If `k7cart` disappears, re-export from the editor or keep a lossless copy.

## CLI (stdlib only)

```bash
# Build cart from a state JSON (you can save one from the editor share workflow or hand-edit)
python3 crates/k7-web/tools/k7_cart_png.py pack --state mygame.json -o mygame.k7.png

# Optional: use your own label image
python3 crates/k7-web/tools/k7_cart_png.py pack --state mygame.json --base label.png -o mygame.k7.png

# Extract
python3 crates/k7-web/tools/k7_cart_png.py unpack mygame.k7.png --json restored.json --code restored.py
```

## Example sketch

Load **`K7 cart PNG (tools hint)`** in the editor example list (`k7_cart_tools.py`).
