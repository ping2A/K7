//! K7 native runner: window (pixels + winit), run game WASM (wasmtime), audio (cpal).

mod wasm_host;

use anyhow::Result;
use pixels::{Pixels, SurfaceTexture};
use winit::dpi::LogicalSize;
use winit::event::{Event, WindowEvent};
use winit::event_loop::EventLoop;
use winit::keyboard::{KeyCode, PhysicalKey};
use winit::window::WindowBuilder;
use k7::{Screen, AudioEngine, SCREEN_WIDTH, SCREEN_HEIGHT};
use std::sync::{Arc, Mutex};
use std::time::Instant;
use cpal::traits::{DeviceTrait, HostTrait};

const SAMPLE_RATE: u32 = 44100;

fn main() -> Result<()> {
    env_logger::init();
    let event_loop = EventLoop::new()?;
    let window = WindowBuilder::new()
        .with_title("K7")
        .with_inner_size(LogicalSize::new(SCREEN_WIDTH as f64 * 2., SCREEN_HEIGHT as f64 * 2.))
        .with_resizable(true)
        .build(&event_loop)?;

    let size = window.inner_size();
    let surface = SurfaceTexture::new(size.width, size.height, &window);
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
    let mut wasm_host = wasm_host::WasmHost::new(screen.clone(), audio.clone(), ws_inbox);
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

    event_loop.run(move |event, target| {
        if let Event::WindowEvent { ref event, .. } = event {
            match event {
                WindowEvent::CloseRequested => target.exit(),
                WindowEvent::Resized(new_size) => {
                    if let Err(e) = pixels.resize_surface(new_size.width, new_size.height) {
                        log::error!("resize surface: {}", e);
                    }
                }
                WindowEvent::KeyboardInput { event: key_event, .. } => {
                    if key_event.state.is_pressed()
                        && key_event.physical_key == PhysicalKey::Code(KeyCode::KeyF)
                    {
                        show_fps = !show_fps;
                    }
                }
                _ => {}
            }
        }
        if let Event::AboutToWait = event {
            if wasm_host.has_game() {
                let _ = wasm_host.call_update();
                let _ = wasm_host.call_draw();
            }
            if show_fps {
                let now = Instant::now();
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
                log::error!("render: {}", e);
            }
        }
    })?;
    Ok(())
}
