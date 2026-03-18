//! K7 native runtime as a library: run WASM games or native games that implement [NativeGame].

mod wasm_host;

pub use wasm_host::MouseState;

use anyhow::Result;
use cpal::traits::{DeviceTrait, HostTrait};
use k7::{AudioEngine, Screen, SCREEN_HEIGHT, SCREEN_WIDTH};
use pixels::{Pixels, SurfaceTexture};
use std::rc::Rc;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use winit::dpi::LogicalSize;
use winit::event::{Event, MouseButton, WindowEvent};
use winit::event_loop::EventLoop;
use winit::keyboard::{KeyCode, PhysicalKey};
use winit::window::WindowBuilder;

const SAMPLE_RATE: u32 = 44100;
const TARGET_FRAME_DURATION_MS: u64 = 1000 / 60;

/// Trait for pure-Rust games run by the K7 native runtime (no WASM).
/// Implement this and call [run_native] to use the same window, audio, and input as WASM games.
pub trait NativeGame {
    /// Initialize game state using the K7 screen and audio (e.g. set music, draw once).
    fn init(screen: &mut Screen, audio: &mut AudioEngine) -> Self
    where
        Self: Sized;

    /// Update game logic once per tick. Mouse coordinates are in screen space (0..width, 0..height).
    fn update(&mut self, screen: &mut Screen, mouse_x: i32, mouse_y: i32, mouse_left: bool);

    /// Draw the current frame to the screen.
    fn draw(&self, screen: &mut Screen);
}

/// Run the K7 native runtime with a pure-Rust game. Creates window, audio, and event loop;
/// each frame calls [NativeGame::update] and [NativeGame::draw]. F3 toggles FPS.
pub fn run_native<G: NativeGame>(title: &str) -> Result<()> {
    env_logger::init();
    log::info!("K7 native running: {}", title);

    let event_loop = EventLoop::new()?;
    let window = Rc::new(
        WindowBuilder::new()
            .with_title(title)
            .with_inner_size(LogicalSize::new(
                SCREEN_WIDTH as f64 * 2.,
                SCREEN_HEIGHT as f64 * 2.,
            ))
            .with_resizable(true)
            .build(&event_loop)?,
    );
    let size = window.inner_size();
    let surface = SurfaceTexture::new(size.width, size.height, window.as_ref());
    let mut pixels = Pixels::new(SCREEN_WIDTH, SCREEN_HEIGHT, surface)?;

    let screen = Arc::new(Mutex::new(Screen::new(SCREEN_WIDTH, SCREEN_HEIGHT)));
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

    let mouse_state = Arc::new(Mutex::new(MouseState::default()));
    let mut game = {
        let mut s = screen.lock().unwrap();
        let mut a = audio.lock().unwrap();
        G::init(&mut s, &mut a)
    };

    let mut show_fps = false;
    let mut last_frame = Instant::now();
    let mut last_update = Instant::now();
    let mut accumulator = Duration::ZERO;
    let mut last_surface_size: (u32, u32) = (size.width, size.height);

    let window_redraw = window.clone();
    event_loop.run(move |event, target| {
        if let Event::WindowEvent { ref event, .. } = event {
            match event {
                WindowEvent::CloseRequested => target.exit(),
                WindowEvent::Resized(new_size) => {
                    if new_size.width > 0 && new_size.height > 0 {
                        let _ = pixels.resize_surface(new_size.width, new_size.height);
                        last_surface_size = (new_size.width, new_size.height);
                    }
                }
                WindowEvent::CursorMoved { position, .. } => {
                    let physical = (position.x as f32, position.y as f32);
                    let (px, py) = pixels
                        .window_pos_to_pixel(physical)
                        .unwrap_or_else(|pos| pixels.clamp_pixel_pos(pos));
                    let x = (px as i32).clamp(0, SCREEN_WIDTH as i32 - 1);
                    let y = (py as i32).clamp(0, SCREEN_HEIGHT as i32 - 1);
                    if let Ok(mut m) = mouse_state.lock() {
                        m.x = x;
                        m.y = y;
                    }
                }
                WindowEvent::MouseInput {
                    state,
                    button: MouseButton::Left,
                    ..
                } => {
                    if let Ok(mut m) = mouse_state.lock() {
                        m.left = state.is_pressed();
                    }
                }
                WindowEvent::KeyboardInput { event: key_event, .. } => {
                    if key_event.state.is_pressed()
                        && key_event.physical_key == PhysicalKey::Code(KeyCode::F3)
                    {
                        show_fps = !show_fps;
                    }
                }
                _ => {}
            }
        }
        if let Event::AboutToWait = event {
            window_redraw.request_redraw();
        }
        if let Event::WindowEvent {
            event: WindowEvent::RedrawRequested,
            ..
        } = event
        {
            let current = window_redraw.inner_size();
            if current.width > 0
                && current.height > 0
                && (current.width != last_surface_size.0 || current.height != last_surface_size.1)
            {
                let _ = pixels.resize_surface(current.width, current.height);
                last_surface_size = (current.width, current.height);
            }

            let now = Instant::now();
            let delta = now.duration_since(last_update);
            last_update = now;
            accumulator = accumulator.saturating_add(delta);
            let target_dt = Duration::from_millis(TARGET_FRAME_DURATION_MS);
            while accumulator >= target_dt {
                accumulator = accumulator.saturating_sub(target_dt);
                let (mx, my, left) = {
                    let m = mouse_state.lock().unwrap();
                    (m.x, m.y, m.left)
                };
                if let Ok(mut s) = screen.lock() {
                    game.update(&mut s, mx, my, left);
                    game.draw(&mut s);
                }
            }
            if show_fps {
                let elapsed = now.duration_since(last_frame).as_secs_f32();
                let fps = if elapsed > 0.0 {
                    (1.0 / elapsed).round() as u32
                } else {
                    0
                };
                let fps_str = format!("{} FPS", fps);
                if let Ok(mut s) = screen.lock() {
                    s.print(&fps_str, 4, 4, 7);
                }
            }
            last_frame = Instant::now();
            let frame = pixels.frame_mut();
            if let Ok(s) = screen.lock() {
                let buf = &s.pixel_buffer;
                let len = frame.len().min(buf.len());
                frame[..len].copy_from_slice(&buf[..len]);
            }
            if let Err(e) = pixels.render() {
                log::error!("render failed: {}", e);
            }
            window_redraw.request_redraw();
        }
    })?;
    Ok(())
}
