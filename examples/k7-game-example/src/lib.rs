//! K7 demoscene-style demo: plasma, scroller, chiptune.
//! Build: cargo build -p k7-game-example --target wasm32-unknown-unknown --release
//! Run: cargo run -p k7-native -- target/wasm32-unknown-unknown/release/k7_game_example.wasm

#![no_std]
#![allow(dead_code)]

use libm::{sinf, floorf};

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! {
    loop {}
}

extern "C" {
    fn mode_width() -> u32;
    fn mode_height() -> u32;
    fn cls(col: i32);
    fn pset(x: i32, y: i32, col: i32);
    fn pset_rgba(x: i32, y: i32, r: i32, g: i32, b: i32, a: i32);
    fn rectfill(x0: i32, y0: i32, x1: i32, y1: i32, col: i32);
    fn print(text_ptr: i32, len: i32, x: i32, y: i32, col: i32);
    fn rnd(max: i32) -> i32;
    fn frnd() -> f32;
    fn set_sound(id: u32, text_ptr: i32, len: i32);
    fn set_music_track(id: u32, text_ptr: i32, len: i32);
    fn play_sound(channel: u32, sound_id: u32);
    fn play_music(channel: u32, track_id: u32);
}

fn print_str(s: &[u8], x: i32, y: i32, col: i32) {
    unsafe { print(s.as_ptr() as i32, s.len() as i32, x, y, col); }
}

fn set_track(id: u32, s: &[u8]) {
    unsafe { set_music_track(id, s.as_ptr() as i32, s.len() as i32); }
}

const W: i32 = 256;
const H: i32 = 256;

static mut FRAME: u32 = 0;
static mut SCROLL_X: i32 = 0;

/// Map plasma value to palette index 0..15 (pico8).
#[inline(always)]
fn plasma_color(v: f32) -> i32 {
    let v = v - floorf(v / 16.0) * 16.0;
    (v as i32).abs() % 16
}

#[no_mangle]
pub extern "C" fn init() {
    unsafe {
        FRAME = 0;
        SCROLL_X = 0;
        set_track(0, b"c2 c2 e2 g2 c2 c2 a2 g2 f2 f2 d2 f2 e2 e2 c2 e2 c2 c2 e2 g2 g2 g2 e2 c2 a2 g2 f2 f2 d2 f2 e2 c2 c2 c2 ");
        set_track(1, b"c5 e5 g5 c6 g5 e5 c5 g4 e5 c5 g4 e4 c4 e4 g4 c5 e5 g5 c6 b5 g5 e5 c5 e5 c5 g4 e4 c4 e4 g4 c5 ");
        play_music(0, 0);
        play_music(1, 1);
    }
}

#[no_mangle]
pub extern "C" fn update() {
    unsafe {
        FRAME = FRAME.wrapping_add(1);
        SCROLL_X = (SCROLL_X - 2).rem_euclid(2048);
    }
}

#[no_mangle]
pub extern "C" fn draw() {
    unsafe {
        let t = FRAME as f32 * 0.04;
        cls(0);

        // Plasma
        for y in 0..H {
            for x in 0..W {
                let fx = x as f32 * 0.03;
                let fy = y as f32 * 0.03;
                let v = sinf(fx + t)
                    + sinf(fy + t * 0.7)
                    + sinf((x + y) as f32 * 0.02 + t * 0.5);
                let c = plasma_color(v * 2.0 + 4.0);
                pset(x, y, c);
            }
        }

        // Vignette / bands
        for x in 0..W {
            for y in 0..14 {
                pset_rgba(x, y, 0, 0, 0, 140);
            }
            for y in (H - 14)..H {
                pset_rgba(x, y, 0, 0, 0, 140);
            }
        }

        // Scroller: build visible slice into static buffer and print
        const MSG: &[u8] = b" * K7 DEMOSCENE * GREETZ TO THE SCENE * 256 BYTES * ";
        let msg_len = MSG.len() as i32;
        let char_w = 4;
        let offset = (SCROLL_X / char_w).rem_euclid(msg_len) as usize;
        static mut BUF: [u8; 64] = [32; 64];
        for i in 0..48 {
            BUF[i] = MSG[(offset + i) % MSG.len()];
        }
        BUF[48] = 0;
        print_str(&BUF[..48], 0, H - 11, 7);

        print_str(b"K7", W / 2 - 4, 4, 7);
        print_str(b"PLASMA", W / 2 - 12, 218, 6);
    }
}
