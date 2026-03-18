//! Wasmtime host: load game WASM and bind K7 API (display, audio, input, WebSocket).

use anyhow::Result;
use std::sync::{Arc, Mutex};
use std::str;
use wasmtime::*;
use k7::{Screen, AudioEngine};

/// Mouse state for WASM games (screen-space 0..width, 0..height).
pub struct MouseState {
    pub x: i32,
    pub y: i32,
    pub left: bool,
}

impl Default for MouseState {
    fn default() -> Self {
        Self { x: 0, y: 0, left: false }
    }
}

pub struct WasmContext {
    pub screen: Arc<Mutex<Screen>>,
    pub audio: Arc<Mutex<AudioEngine>>,
    pub ws_inbox: Arc<Mutex<Vec<String>>>,
    pub mouse: Arc<Mutex<MouseState>>,
}

pub struct WasmHost {
    engine: Engine,
    screen: Arc<Mutex<Screen>>,
    audio: Arc<Mutex<AudioEngine>>,
    ws_inbox: Arc<Mutex<Vec<String>>>,
    mouse: Arc<Mutex<MouseState>>,
    store: Option<Store<WasmContext>>,
    init_fn: Option<TypedFunc<(), ()>>,
    update_fn: Option<TypedFunc<(), ()>>,
    draw_fn: Option<TypedFunc<(), ()>>,
}

impl WasmHost {
    pub fn new(
        screen: Arc<Mutex<Screen>>,
        audio: Arc<Mutex<AudioEngine>>,
        ws_inbox: Arc<Mutex<Vec<String>>>,
        mouse: Arc<Mutex<MouseState>>,
    ) -> Self {
        Self {
            engine: Engine::default(),
            screen,
            audio,
            ws_inbox,
            mouse,
            store: None,
            init_fn: None,
            update_fn: None,
            draw_fn: None,
        }
    }

    fn bind_api(linker: &mut Linker<WasmContext>) -> Result<()> {
        linker.func_wrap("env", "mode_width", |caller: Caller<'_, WasmContext>| {
            caller.data().screen.lock().unwrap().width as u32
        })?;
        linker.func_wrap("env", "mode_height", |caller: Caller<'_, WasmContext>| {
            caller.data().screen.lock().unwrap().height as u32
        })?;
        linker.func_wrap("env", "cls", |caller: Caller<'_, WasmContext>, col: i32| {
            caller.data().screen.lock().unwrap().cls(col as u8);
        })?;
        linker.func_wrap("env", "pset", |caller: Caller<'_, WasmContext>, x: i32, y: i32, col: i32| {
            caller.data().screen.lock().unwrap().pset(x, y, col);
        })?;
        linker.func_wrap("env", "pset_rgba", |caller: Caller<'_, WasmContext>, x: i32, y: i32, r: i32, g: i32, b: i32, a: i32| {
            caller.data().screen.lock().unwrap().pset_rgba(x, y, r as u8, g as u8, b as u8, a as u8);
        })?;
        linker.func_wrap("env", "rectfill", |caller: Caller<'_, WasmContext>, x0: i32, y0: i32, x1: i32, y1: i32, col: i32| {
            caller.data().screen.lock().unwrap().rectfill(x0, y0, x1, y1, col);
        })?;
        linker.func_wrap("env", "rectfill_rgba", |caller: Caller<'_, WasmContext>, x0: i32, y0: i32, x1: i32, y1: i32, r: i32, g: i32, b: i32, a: i32| {
            caller.data().screen.lock().unwrap().rectfill_rgba(x0, y0, x1, y1, r as u8, g as u8, b as u8, a as u8);
        })?;
        linker.func_wrap("env", "spr", |caller: Caller<'_, WasmContext>, n: u32, x: i32, y: i32, w: i32, h: i32, flip_x: i32, flip_y: i32| {
            caller.data().screen.lock().unwrap().spr(n, x, y, w, h, flip_x != 0, flip_y != 0, 1);
        })?;
        linker.func_wrap("env", "print", |mut caller: Caller<'_, WasmContext>, text_ptr: i32, len: i32, x: i32, y: i32, col: i32| {
            if let Some(wasmtime::Extern::Memory(mem)) = caller.get_export("memory") {
                let data = mem.data(&caller);
                let start = text_ptr as u32 as usize;
                let end = (start + len as u32 as usize).min(data.len());
                if start < data.len() {
                    let text = str::from_utf8(&data[start..end]).unwrap_or("");
                    caller.data().screen.lock().unwrap().print(text, x, y, col);
                }
            }
        })?;
        linker.func_wrap("env", "rnd", |_caller: Caller<'_, WasmContext>, max: i32| -> i32 {
            if max <= 0 { 0 } else { (rand::random::<f32>() * max as f32) as i32 }
        })?;
        linker.func_wrap("env", "frnd", |_caller: Caller<'_, WasmContext>| -> f32 {
            rand::random()
        })?;
        linker.func_wrap("env", "mouse_x", |caller: Caller<'_, WasmContext>| -> i32 {
            caller.data().mouse.lock().map(|m| m.x).unwrap_or(0)
        })?;
        linker.func_wrap("env", "mouse_y", |caller: Caller<'_, WasmContext>| -> i32 {
            caller.data().mouse.lock().map(|m| m.y).unwrap_or(0)
        })?;
        linker.func_wrap("env", "mouse_left_state", |caller: Caller<'_, WasmContext>, _button: i32| -> i32 {
            caller.data().mouse.lock().map(|m| m.left as i32).unwrap_or(0)
        })?;
        linker.func_wrap("env", "play_sound", |caller: Caller<'_, WasmContext>, channel: u32, sound_id: u32| {
            let _ = caller.data().audio.lock().map(|mut a| a.play_sound(channel as u8, sound_id as u8));
        })?;
        linker.func_wrap("env", "play_music", |caller: Caller<'_, WasmContext>, channel: u32, track_id: u32| {
            let _ = caller.data().audio.lock().map(|mut a| a.play_music(channel as u8, track_id as u8));
        })?;
        linker.func_wrap("env", "set_sound", |mut caller: Caller<'_, WasmContext>, id: u32, text_ptr: i32, len: i32| {
            if let Some(wasmtime::Extern::Memory(mem)) = caller.get_export("memory") {
                let data = mem.data(&caller);
                let start = text_ptr as u32 as usize;
                let end = (start + len as u32 as usize).min(data.len());
                if start < data.len() {
                    if let Ok(s) = str::from_utf8(&data[start..end]) {
                        let _ = caller.data().audio.lock().map(|mut a| a.set_sound(id as u8, s.to_string()));
                    }
                }
            }
        })?;
        linker.func_wrap("env", "set_music_track", |mut caller: Caller<'_, WasmContext>, id: u32, text_ptr: i32, len: i32| {
            if let Some(wasmtime::Extern::Memory(mem)) = caller.get_export("memory") {
                let data = mem.data(&caller);
                let start = text_ptr as u32 as usize;
                let end = (start + len as u32 as usize).min(data.len());
                if start < data.len() {
                    if let Ok(s) = str::from_utf8(&data[start..end]) {
                        let _ = caller.data().audio.lock().map(|mut a| a.set_music_track(id as u8, s.to_string()));
                    }
                }
            }
        })?;
        // WebSocket multiplayer (stub on native: connect/send no-op; inbox empty until real impl)
        linker.func_wrap("env", "k7_ws_connect", |mut caller: Caller<'_, WasmContext>, text_ptr: i32, len: i32| {
            if let Some(wasmtime::Extern::Memory(mem)) = caller.get_export("memory") {
                let data = mem.data(&caller);
                let start = text_ptr as u32 as usize;
                let end = (start + len as u32 as usize).min(data.len());
                if start < data.len() {
                    if let Ok(url) = str::from_utf8(&data[start..end]) {
                        log::info!("k7_ws_connect (native stub): {}", url);
                        // TODO: spawn WebSocket client thread, push received to ws_inbox
                    }
                }
            }
        })?;
        linker.func_wrap("env", "k7_ws_send", |mut caller: Caller<'_, WasmContext>, text_ptr: i32, len: i32| {
            if let Some(wasmtime::Extern::Memory(mem)) = caller.get_export("memory") {
                let data = mem.data(&caller);
                let start = text_ptr as u32 as usize;
                let end = (start + len as u32 as usize).min(data.len());
                if start < data.len() {
                    if let Ok(_msg) = str::from_utf8(&data[start..end]) {
                        // TODO: send via WebSocket
                    }
                }
            }
        })?;
        linker.func_wrap("env", "k7_ws_has_message", |caller: Caller<'_, WasmContext>| -> i32 {
            caller.data().ws_inbox.lock().map(|q| !q.is_empty()).unwrap_or(false) as i32
        })?;
        linker.func_wrap("env", "k7_ws_next_message", |mut caller: Caller<'_, WasmContext>, buf_ptr: i32, max_len: i32| -> i32 {
            let msg = {
                let mut inbox = match caller.data().ws_inbox.lock() {
                    Ok(i) => i,
                    Err(_) => return -1,
                };
                match inbox.pop() {
                    Some(m) => m,
                    None => return -1,
                }
            };
            if let Some(wasmtime::Extern::Memory(mem)) = caller.get_export("memory") {
                let data = mem.data_mut(&mut caller);
                let start = buf_ptr as u32 as usize;
                let max = max_len as u32 as usize;
                let bytes = msg.as_bytes();
                let copy_len = bytes.len().min(max);
                if start + copy_len <= data.len() {
                    data[start..start + copy_len].copy_from_slice(&bytes[..copy_len]);
                    return copy_len as i32;
                }
            }
            -1
        })?;
        Ok(())
    }

    pub fn load(&mut self, wasm_bytes: &[u8]) -> Result<()> {
        self.store = Some(Store::new(&self.engine, WasmContext {
            screen: self.screen.clone(),
            audio: self.audio.clone(),
            ws_inbox: self.ws_inbox.clone(),
            mouse: self.mouse.clone(),
        }));
        let mut linker = Linker::new(&self.engine);
        Self::bind_api(&mut linker)?;
        let module = Module::new(&self.engine, wasm_bytes)?;
        let instance = linker.instantiate(self.store.as_mut().unwrap(), &module)?;
        let store = self.store.as_mut().unwrap();
        self.init_fn = instance.get_typed_func(&mut *store, "init").ok();
        self.update_fn = instance.get_typed_func(&mut *store, "update").ok();
        self.draw_fn = instance.get_typed_func(&mut *store, "draw").ok();
        Ok(())
    }

    pub fn call_init(&mut self) -> Result<()> {
        if let Some(ref f) = self.init_fn {
            f.call(self.store.as_mut().unwrap(), ())?;
        }
        Ok(())
    }

    pub fn call_update(&mut self) -> Result<()> {
        if let Some(ref f) = self.update_fn {
            f.call(self.store.as_mut().unwrap(), ())?;
        }
        Ok(())
    }

    pub fn call_draw(&mut self) -> Result<()> {
        if let Some(ref f) = self.draw_fn {
            f.call(self.store.as_mut().unwrap(), ())?;
        }
        Ok(())
    }

    pub fn has_game(&self) -> bool {
        self.draw_fn.is_some()
    }
}
