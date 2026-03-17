//! K7 web runtime: draw to canvas, play audio via Web Audio API, WebSocket multiplayer, load game WASM.

use std::cell::RefCell;
use std::rc::Rc;
use std::time::Duration;
use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast;
use k7::{self, AudioEngine, Map, Screen, Sprite, SCREEN_WIDTH, SCREEN_HEIGHT, SPRITE_COUNT, MAP_WIDTH, MAP_HEIGHT};
use k7::fonts;

/// Sample rate used for Rust-rendered audio (Web Audio API will resample if needed).
const AUDIO_SAMPLE_RATE: u32 = 44100;

#[wasm_bindgen(start)]
pub fn run() {
    log::info!("K7 web runtime");
}

#[wasm_bindgen]
pub struct K7Web {
    screen: Screen,
    demo_frame: u32,
    ws: Option<web_sys::WebSocket>,
    ws_inbox: Rc<RefCell<Vec<String>>>,
    #[allow(dead_code)]
    ws_closure: Option<Closure<dyn FnMut(web_sys::MessageEvent)>>,
    audio_engine: RefCell<AudioEngine>,
}

#[wasm_bindgen]
impl K7Web {
    #[wasm_bindgen(constructor)]
    pub fn new() -> Self {
        let mut screen = Screen::new(SCREEN_WIDTH, SCREEN_HEIGHT);
        while screen.sprites.len() < SPRITE_COUNT {
            screen.sprites.push(Sprite::new());
        }
        screen.cls(1);
        screen.print("K7", 20, 20, 7);
        Self {
            screen,
            demo_frame: 0,
            ws: None,
            ws_inbox: Rc::new(RefCell::new(Vec::new())),
            ws_closure: None,
            audio_engine: RefCell::new(AudioEngine::new(AUDIO_SAMPLE_RATE)),
        }
    }

    /// WebSocket: connect to URL (e.g. ws://localhost:8080 or wss://…).
    #[wasm_bindgen]
    pub fn ws_connect(&mut self, url: &str) -> Result<(), JsValue> {
        let ws = web_sys::WebSocket::new(url)?;
        let inbox = Rc::clone(&self.ws_inbox);
        let closure = Closure::new(move |ev: web_sys::MessageEvent| {
            if let Ok(js) = ev.data().dyn_into::<js_sys::JsString>() {
                if let Some(s) = js.as_string() {
                    let _ = inbox.borrow_mut().push(s);
                }
            }
        });
        ws.set_onmessage(Some(closure.as_ref().unchecked_ref()));
        self.ws_closure = Some(closure);
        self.ws = Some(ws);
        Ok(())
    }

    /// WebSocket: send a text message. No-op if not connected.
    #[wasm_bindgen]
    pub fn ws_send(&self, msg: &str) -> Result<(), JsValue> {
        if let Some(ref ws) = self.ws {
            if ws.ready_state() == web_sys::WebSocket::OPEN {
                ws.send_with_str(msg)?;
            }
        }
        Ok(())
    }

    /// WebSocket: take all received messages (empties the queue). Returns JS array of strings.
    #[wasm_bindgen]
    pub fn ws_take_messages(&self) -> js_sys::Array {
        let arr = js_sys::Array::new();
        let mut inbox = self.ws_inbox.borrow_mut();
        for s in inbox.drain(..) {
            arr.push(&JsValue::from(s));
        }
        arr
    }

    /// WebSocket: true if connected (ready state OPEN).
    #[wasm_bindgen]
    pub fn ws_connected(&self) -> bool {
        self.ws
            .as_ref()
            .map(|ws| ws.ready_state() == web_sys::WebSocket::OPEN)
            .unwrap_or(false)
    }

    /// Run one frame of the embedded default demo (uses gfx: cls, rect, circ, line, print).
    /// Call from a requestAnimationFrame loop together with draw_to_canvas.
    #[wasm_bindgen]
    pub fn tick_default_demo(&mut self) {
        let frame = self.demo_frame;
        self.demo_frame = frame.wrapping_add(1);
        let t = frame as f32 * 0.02;
        let screen = &mut self.screen;
        screen.cls(0);
        screen.color(7);
        screen.rect(8, 8, 247, 247, 7);
        screen.rectfill(16, 16, 240, 120, 2);
        screen.circfill(128, 128, 40, 8);
        screen.circ(128, 128, 50, 7);
        let cx = 128.0 + 60.0 * (t * 0.5).sin();
        let cy = 128.0 + 40.0 * (t * 0.3).cos();
        screen.circfill(cx as i32, cy as i32, 12, 11);
        screen.line(128, 128, cx as i32, cy as i32, 6);
        screen.print("K7 default demo", 80, 220, 7);
        screen.print(&format!("frame {}", frame), 80, 230, 6);
    }

    /// GFX API for Python/JS: clear screen with color index 0..15.
    #[wasm_bindgen]
    pub fn cls(&mut self, col: i32) {
        self.screen.cls(col as u8);
    }

    /// GFX: set pixel at (x,y) with palette color.
    #[wasm_bindgen]
    pub fn pset(&mut self, x: i32, y: i32, col: i32) {
        self.screen.pset(x, y, col);
    }

    /// GFX: set pixel with RGBA (0..255).
    #[wasm_bindgen]
    pub fn pset_rgba(&mut self, x: i32, y: i32, r: i32, g: i32, b: i32, a: i32) {
        self.screen.pset_rgba(x, y, r as u8, g as u8, b as u8, a as u8);
    }

    /// GFX: filled rectangle.
    #[wasm_bindgen]
    pub fn rectfill(&mut self, x0: i32, y0: i32, x1: i32, y1: i32, col: i32) {
        self.screen.rectfill(x0, y0, x1, y1, col);
    }

    /// GFX: filled rectangle with RGBA (0..255).
    #[wasm_bindgen]
    pub fn rectfill_rgba(&mut self, x0: i32, y0: i32, x1: i32, y1: i32, r: i32, g: i32, b: i32, a: i32) {
        self.screen.rectfill_rgba(x0, y0, x1, y1, r as u8, g as u8, b as u8, a as u8);
    }

    /// GFX: rectangle outline.
    #[wasm_bindgen]
    pub fn rect(&mut self, x0: i32, y0: i32, x1: i32, y1: i32, col: i32) {
        self.screen.rect(x0, y0, x1, y1, col);
    }

    /// GFX: circle outline.
    #[wasm_bindgen]
    pub fn circ(&mut self, x: i32, y: i32, r: i32, col: i32) {
        self.screen.circ(x, y, r, col);
    }

    /// GFX: filled circle.
    #[wasm_bindgen]
    pub fn circfill(&mut self, x: i32, y: i32, r: i32, col: i32) {
        self.screen.circfill(x, y, r, col);
    }

    /// GFX: line.
    #[wasm_bindgen]
    pub fn line(&mut self, x0: i32, y0: i32, x1: i32, y1: i32, col: i32) {
        self.screen.line(x0, y0, x1, y1, col);
    }

    /// GFX: print text at (x,y) with color.
    #[wasm_bindgen]
    pub fn print(&mut self, text: &str, x: i32, y: i32, col: i32) {
        self.screen.print(text, x, y, col);
    }

    /// GFX: print text at (x,y) with 32-bit RGBA (supports transparency).
    #[wasm_bindgen]
    pub fn print_rgba(&mut self, text: &str, x: i32, y: i32, r: i32, g: i32, b: i32, a: i32) {
        self.screen.print_rgba(text, x, y, r as u8, g as u8, b as u8, a as u8);
    }

    /// Set current font by name: "pico8", "bbc", "appleii", "cbmii", "trollmini".
    #[wasm_bindgen]
    pub fn set_font(&mut self, name: &str) -> bool {
        if let Some(font) = fonts::get_font(name) {
            self.screen.set_font(font);
            true
        } else {
            false
        }
    }

    /// GFX: set current draw color (used when col is -1).
    #[wasm_bindgen]
    pub fn color(&mut self, col: i32) {
        self.screen.color(col);
    }

    /// Palette: swap two color entries (0..15). Use for flash or swap effects.
    #[wasm_bindgen]
    pub fn palette_swap(&mut self, a: i32, b: i32) {
        let a = a as u8;
        let b = b as u8;
        if a <= 15 && b <= 15 {
            self.screen.swap_palette_entries(a, b);
        }
    }

    /// GFX: set camera offset.
    #[wasm_bindgen]
    pub fn camera(&mut self, x: i32, y: i32) {
        self.screen.camera(x, y);
    }

    /// Sprite: get palette index at sheet pixel (sx, sy). Sheet is 256×64 (32×8 sprites of 8×8).
    #[wasm_bindgen]
    pub fn sget(&self, sx: i32, sy: i32) -> u8 {
        self.screen.sget(sx, sy)
    }

    /// Sprite: set sheet pixel (sx, sy) to palette color.
    #[wasm_bindgen]
    pub fn sset(&mut self, sx: i32, sy: i32, col: i32) {
        self.screen.sset(sx, sy, col);
    }

    /// Sprite: draw sprite n at (x, y). w, h in sprite units (1 = 8px). flip_x, flip_y: 0 or 1. scale: 1 = 8px per tile, 2 = 16px, etc. (optional, default 1).
    #[wasm_bindgen]
    pub fn spr(&mut self, n: u32, x: i32, y: i32, w: i32, h: i32, flip_x: i32, flip_y: i32, scale: i32) {
        self.screen.spr(
            n,
            x,
            y,
            w.max(1),
            h.max(1),
            flip_x != 0,
            flip_y != 0,
            if scale >= 1 { scale } else { 1 },
        );
    }

    /// Map: get cell at (cx, cy). Map is 256×32 cells.
    #[wasm_bindgen]
    pub fn mget(&self, cx: i32, cy: i32) -> u8 {
        self.screen.mget(cx, cy)
    }

    /// Map: set cell (cx, cy) to value v (sprite index 0–255).
    #[wasm_bindgen]
    pub fn mset(&mut self, cx: i32, cy: i32, v: u8) {
        self.screen.mset(cx, cy, v);
    }

    /// Map: draw map as sprites (uses tile flags: flip_x, flip_y, rotate). cell_x, cell_y = start cell; sx, sy = pixel dest; w, h = cells to draw.
    #[wasm_bindgen]
    pub fn map_draw(&mut self, cell_x: i32, cell_y: i32, sx: i32, sy: i32, w: i32, h: i32) {
        self.screen.map_draw(cell_x, cell_y, sx, sy, w, h);
    }

    /// Map: get tile flags at (cx, cy). Bits: 1=flip_x, 2=flip_y, 4=rotate 90° CW.
    #[wasm_bindgen]
    pub fn mget_flags(&self, cx: i32, cy: i32) -> u8 {
        self.screen.mget_flags(cx, cy)
    }

    /// Map: set tile flags at (cx, cy). Bits: 1=flip_x, 2=flip_y, 4=rotate.
    #[wasm_bindgen]
    pub fn mset_flags(&mut self, cx: i32, cy: i32, f: u8) {
        self.screen.mset_flags(cx, cy, f);
    }

    /// Palette: switch to named palette (e.g. "pico8", "gameboy", "cga", "commodore64", "atari2600").
    #[wasm_bindgen]
    pub fn switch_palette(&mut self, name: &str) {
        self.screen.switch_palette(name);
    }

    /// Palette: list of built-in palette names. Returns JS array of strings.
    #[wasm_bindgen]
    pub fn palette_list(&self) -> js_sys::Array {
        let arr = js_sys::Array::new();
        for name in &self.screen.palettes.list {
            arr.push(&JsValue::from(name.as_str()));
        }
        arr
    }

    /// Get full sprite sheet as palette indices: 256×64 bytes (row-major). For editors.
    #[wasm_bindgen]
    pub fn get_sprite_sheet(&self) -> Vec<u8> {
        let mut out = vec![0u8; 256 * 64];
        for sy in 0..64i32 {
            for sx in 0..256i32 {
                out[(sy as usize * 256) + sx as usize] = self.screen.sget(sx, sy);
            }
        }
        out
    }

    /// Get full map as bytes: 256×32 (row-major). For editors.
    #[wasm_bindgen]
    pub fn get_map(&self) -> Vec<u8> {
        self.screen.map.cells.clone()
    }

    /// Set full map from bytes. 256×32 = cells only; 256×32×2 = cells then flags.
    #[wasm_bindgen]
    pub fn set_map(&mut self, data: &[u8]) -> Result<(), JsValue> {
        let need = (MAP_WIDTH * MAP_HEIGHT) as usize;
        if data.len() < need {
            return Err(JsValue::from("set_map: data too short"));
        }
        self.screen.map.cells[..need].copy_from_slice(&data[..need]);
        if data.len() >= need * 2 {
            self.screen.map.flags[..need].copy_from_slice(&data[need..need * 2]);
        }
        Ok(())
    }

    /// Get full map flags as bytes: 256×32 (row-major). For editors and share state.
    #[wasm_bindgen]
    pub fn get_map_flags(&self) -> Vec<u8> {
        self.screen.map.flags.clone()
    }

    /// Set full map flags from bytes (256×32 row-major).
    #[wasm_bindgen]
    pub fn set_map_flags(&mut self, data: &[u8]) -> Result<(), JsValue> {
        let need = (MAP_WIDTH * MAP_HEIGHT) as usize;
        if data.len() < need {
            return Err(JsValue::from("set_map_flags: data too short"));
        }
        self.screen.map.flags[..need].copy_from_slice(&data[..need]);
        Ok(())
    }

    /// Set full sprite sheet from bytes (256×64 row-major, palette indices). For loading shared game state.
    #[wasm_bindgen]
    pub fn set_sprite_sheet(&mut self, data: &[u8]) -> Result<(), JsValue> {
        let need = 256 * 64;
        if data.len() < need {
            return Err(JsValue::from("set_sprite_sheet: data too short"));
        }
        for sy in 0..64i32 {
            for sx in 0..256i32 {
                let i = (sy as usize * 256) + sx as usize;
                self.screen.sset(sx, sy, data[i] as i32);
            }
        }
        Ok(())
    }

    /// Reset sprite bank to 256 empty 8×8 sprites. Call when loading a new game.
    #[wasm_bindgen]
    pub fn reset_sprite_bank(&mut self) {
        self.screen.sprites.clear();
        while self.screen.sprites.len() < SPRITE_COUNT {
            self.screen.sprites.push(Sprite::new());
        }
    }

    /// Reset map to zeros. Call when loading a new game.
    #[wasm_bindgen]
    pub fn reset_map(&mut self) {
        self.screen.map = Map::new();
    }

    /// Reset all VM state for a new game: palette pico8, camera, clip, draw color, cls, map, sprites.
    /// Call once before running new game code (e.g. when user clicks Run or loads another example).
    #[wasm_bindgen]
    pub fn reset_game_state(&mut self) {
        self.screen.switch_palette("pico8");
        self.screen.camera(0, 0);
        self.screen.clip(-1, -1, -1, -1);
        self.screen.color(0);
        self.screen.cls(0);
        self.screen.map = Map::new();
        self.screen.sprites.clear();
        while self.screen.sprites.len() < SPRITE_COUNT {
            self.screen.sprites.push(Sprite::new());
        }
    }

    /// Copy RGBA pixel data into the screen at (x, y). data length must be at least w*h*4.
    #[wasm_bindgen]
    pub fn copy_from_u8(&mut self, x: i32, y: i32, w: i32, h: i32, data: &[u8]) -> Result<(), JsValue> {
        let sw = self.screen.width as i32;
        let sh = self.screen.height as i32;
        let need = (w * h * 4) as usize;
        if data.len() < need {
            return Err(JsValue::from("data too short"));
        }
        let x0 = x.max(0).min(sw);
        let y0 = y.max(0).min(sh);
        let x1 = (x + w).max(0).min(sw);
        let y1 = (y + h).max(0).min(sh);
        let cw = (x1 - x0) as usize;
        let ch = (y1 - y0) as usize;
        if cw == 0 || ch == 0 {
            return Ok(());
        }
        let src_row_bytes = (w * 4) as usize;
        let src_col_off = ((x0 - x) * 4) as usize;
        let buf = &mut self.screen.pixel_buffer[..];
        for row in 0..ch {
            let src_row = (y0 - y) as usize + row;
            let src_off = src_row * src_row_bytes + src_col_off;
            let dy = y0 + row as i32;
            let dst_off = (dy as u32 * self.screen.width + x0 as u32) as usize * 4;
            let len = cw * 4;
            if dst_off + len <= buf.len() && src_off + len <= data.len() {
                buf[dst_off..dst_off + len].copy_from_slice(&data[src_off..src_off + len]);
            }
        }
        Ok(())
    }

    /// Expand instrument token (e.g. "c4:piano:bright" -> "c4:layer:...|reverb:small"). Core sound notation.
    #[wasm_bindgen]
    pub fn expand_sound_token(&self, token: &str) -> String {
        k7::audio::expand_sound_token(token)
    }

    /// Render a sound notation string to mono float samples using the Rust parser and synth.
    /// Returns a Float32Array of samples at 44100 Hz. Use with get_audio_sample_rate() to create an AudioBuffer.
    #[wasm_bindgen]
    pub fn render_sound(&self, notation: &str) -> js_sys::Float32Array {
        let engine = self.audio_engine.borrow();
        let default_duration = Duration::from_millis(100);
        let samples = engine.render_sound_to_buffer(notation.trim(), default_duration, 0.7);
        js_sys::Float32Array::from(samples.as_slice())
    }

    /// Sample rate used by render_sound (44100).
    #[wasm_bindgen]
    pub fn get_audio_sample_rate(&self) -> u32 {
        AUDIO_SAMPLE_RATE
    }

    /// Draw current frame to canvas (call each frame).
    #[wasm_bindgen]
    pub fn draw_to_canvas(&self, canvas_id: &str) -> Result<(), JsValue> {
        let window = web_sys::window().ok_or("no window")?;
        let document = window.document().ok_or("no document")?;
        let canvas = document
            .get_element_by_id(canvas_id)
            .ok_or("canvas not found")?
            .dyn_into::<web_sys::HtmlCanvasElement>()?;
        let ctx = canvas
            .get_context("2d")?
            .ok_or("no context")?
            .dyn_into::<web_sys::CanvasRenderingContext2d>()?;
        let buf = self.screen.pixel_buffer.as_slice();
        let len = (SCREEN_WIDTH * SCREEN_HEIGHT * 4) as usize;
        let buf = if buf.len() >= len { &buf[..len] } else { buf };
        let image_data = web_sys::ImageData::new_with_u8_clamped_array_and_sh(
            wasm_bindgen::Clamped(buf),
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )?;
        ctx.put_image_data(&image_data, 0.0, 0.0)?;
        Ok(())
    }
}
