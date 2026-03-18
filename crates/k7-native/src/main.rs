//! K7 native runner: window (pixels + winit), run game WASM (wasmtime), audio (cpal).

mod wasm_host;

use anyhow::Result;
use pixels::{Pixels, SurfaceTexture};
use winit::dpi::LogicalSize;
use winit::event::{Event, WindowEvent, MouseButton};
use winit::event_loop::EventLoop;
use winit::keyboard::{KeyCode, PhysicalKey};
use winit::window::WindowBuilder;
use k7::{Screen, AudioEngine, SCREEN_WIDTH, SCREEN_HEIGHT};
use wasm_host::MouseState;
use std::rc::Rc;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use cpal::traits::{DeviceTrait, HostTrait};

const SAMPLE_RATE: u32 = 44100;
/// Target game update rate (matches Pikuseru-style frame pacing): ~60 FPS.
const TARGET_FRAME_DURATION_MS: u64 = 1000 / 60;

fn main() -> Result<()> {
    env_logger::init();
    log::info!("K7 native starting");
    let event_loop = EventLoop::new()?;
    let window = Rc::new(
        WindowBuilder::new()
            .with_title("K7")
            .with_inner_size(LogicalSize::new(SCREEN_WIDTH as f64 * 2., SCREEN_HEIGHT as f64 * 2.))
            .with_resizable(true)
            .build(&event_loop)?,
    );
    let size = window.inner_size();
    log::info!("window inner_size (physical): {}x{}", size.width, size.height);
    let surface = SurfaceTexture::new(size.width, size.height, window.as_ref());
    let mut pixels = Pixels::new(SCREEN_WIDTH, SCREEN_HEIGHT, surface)?;

    let screen = Arc::new(Mutex::new(Screen::new(SCREEN_WIDTH, SCREEN_HEIGHT)));
    {
        let mut s = screen.lock().unwrap();
        s.cls(1);
        s.pset(10, 10, 8);
        s.print("K7", 20, 20, 7);
    }

    let audio = Arc::new(Mutex::new(AudioEngine::new(SAMPLE_RATE)));
    let audio_clone = audio.clone();
    let _stream = cpal::default_host()
        .default_output_device()
        .and_then(|d| {
            let config = cpal::StreamConfig {
                channels: 2,
                sample_rate: cpal::SampleRate(SAMPLE_RATE),
                buffer_size: cpal::BufferSize::Default,
            };
            d.build_output_stream(
                &config,
                move |data: &mut [f32], _: &cpal::OutputCallbackInfo| {
                    if let Ok(mut engine) = audio_clone.lock() {
                        engine.fill_buffer(data);
                    }
                },
                |e| log::error!("audio stream error: {}", e),
                None,
            )
            .ok()
        });

    let ws_inbox = Arc::new(Mutex::new(Vec::<String>::new()));
    let mouse_state = Arc::new(Mutex::new(MouseState::default()));
    let mut wasm_host = wasm_host::WasmHost::new(screen.clone(), audio.clone(), ws_inbox, mouse_state.clone());
    if let Some(wasm_path) = std::env::args().nth(1) {
        if let Ok(wasm_bytes) = std::fs::read(&wasm_path) {
            let _ = wasm_host.load(&wasm_bytes);
            if wasm_host.has_game() {
                let _ = wasm_host.call_init();
            }
        }
    }

    let mut show_fps = false;
    let mut last_frame = Instant::now();
    let mut last_update = Instant::now();
    let mut accumulator = Duration::ZERO;
    let mut last_surface_size: (u32, u32) = (size.width, size.height);
    let mut cursor_log_count: u32 = 0;

    if let Some(path) = std::env::args().nth(1) {
        log::info!("loaded WASM game: {}", path);
    }

    let window_for_redraw = window.clone();
    event_loop.run(move |event, target| {
        if let Event::WindowEvent { ref event, .. } = event {
            match event {
                WindowEvent::CloseRequested => {
                    log::info!("CloseRequested");
                    target.exit();
                }
                WindowEvent::ScaleFactorChanged { scale_factor: new_scale, .. } => {
                    log::info!("ScaleFactorChanged scale_factor={}", new_scale);
                }
                WindowEvent::Resized(new_size) => {
                    log::info!("Resized event: {}x{} (physical)", new_size.width, new_size.height);
                    if new_size.width > 0 && new_size.height > 0 {
                        if let Err(e) = pixels.resize_surface(new_size.width, new_size.height) {
                            log::error!("resize_surface failed: {}", e);
                        } else {
                            last_surface_size = (new_size.width, new_size.height);
                            log::info!("resize_surface ok, last_surface_size={}x{}", new_size.width, new_size.height);
                        }
                    }
                }
                WindowEvent::CursorMoved { position, .. } => {
                    let physical = (position.x as f32, position.y as f32);
                    let (px, py) = pixels
                        .window_pos_to_pixel(physical)
                        .unwrap_or_else(|pos| pixels.clamp_pixel_pos(pos));
                    let x = (px as i32).min(SCREEN_WIDTH as i32 - 1).max(0);
                    let y = (py as i32).min(SCREEN_HEIGHT as i32 - 1).max(0);
                    cursor_log_count = cursor_log_count.wrapping_add(1);
                    if cursor_log_count % 60 == 0 {
                        log::debug!("cursor physical=({:.0},{:.0}) -> pixel=({},{})", position.x, position.y, x, y);
                    }
                    if let Ok(mut m) = mouse_state.lock() {
                        m.x = x;
                        m.y = y;
                    }
                }
                WindowEvent::MouseInput { state, button: MouseButton::Left, .. } => {
                    log::debug!("MouseInput Left {}", if state.is_pressed() { "pressed" } else { "released" });
                    if let Ok(mut m) = mouse_state.lock() {
                        m.left = state.is_pressed();
                    }
                }
                WindowEvent::KeyboardInput { event: key_event, .. } => {
                    if key_event.state.is_pressed()
                        && key_event.physical_key == PhysicalKey::Code(KeyCode::F3)
                    {
                        show_fps = !show_fps;
                        log::info!("F3: show_fps={}", show_fps);
                    }
                }
                _ => {}
            }
        }
        if let Event::AboutToWait = event {
            window_for_redraw.request_redraw();
        }
        if let Event::WindowEvent { event: WindowEvent::RedrawRequested, .. } = event {
            // Sync surface size with window (in case Resized was missed or order differs)
            let current = window_for_redraw.inner_size();
            if current.width > 0 && current.height > 0 && (current.width != last_surface_size.0 || current.height != last_surface_size.1) {
                log::info!("RedrawRequested: syncing surface to window {}x{} (was {}x{})", current.width, current.height, last_surface_size.0, last_surface_size.1);
                if let Err(e) = pixels.resize_surface(current.width, current.height) {
                    log::error!("resize_surface in redraw failed: {}", e);
                } else {
                    last_surface_size = (current.width, current.height);
                }
            }

            let now = Instant::now();
            let delta = now.duration_since(last_update);
            last_update = now;
            accumulator = accumulator.saturating_add(delta);
            let target_dt = Duration::from_millis(TARGET_FRAME_DURATION_MS);
            while accumulator >= target_dt {
                accumulator = accumulator.saturating_sub(target_dt);
                if wasm_host.has_game() {
                    let _ = wasm_host.call_update();
                    let _ = wasm_host.call_draw();
                }
            }
            if show_fps {
                let elapsed = now.duration_since(last_frame).as_secs_f32();
                let fps = if elapsed > 0.0 { (1.0 / elapsed).round() as u32 } else { 0 };
                let fps_str = format!("{} FPS", fps);
                screen.lock().unwrap().print(&fps_str, 4, 4, 7);
            }
            last_frame = Instant::now();
            let frame = pixels.frame_mut();
            let buf = &screen.lock().unwrap().pixel_buffer;
            let len = frame.len().min(buf.len());
            frame[..len].copy_from_slice(&buf[..len]);
            if let Err(e) = pixels.render() {
                log::error!("render failed: {}", e);
            }
            window_for_redraw.request_redraw();
        }
    })?;
    Ok(())
}
