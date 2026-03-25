//! Sable falling-sand game for K7 native. Rust port of https://github.com/PikuseruConsole/Sable
//!
//! Build: cargo build -p k7-sable --target wasm32-unknown-unknown --release
//! Run:   cargo run -p k7-native -- target/wasm32-unknown-unknown/release/k7_sable.wasm

#![no_std]
#![allow(dead_code)]

mod game;
mod species;
mod universe;
mod utils;

use core::mem::MaybeUninit;
use game::MyGame;

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! {
    loop {}
}

static mut GAME: MaybeUninit<MyGame> = MaybeUninit::uninit();

#[no_mangle]
pub extern "C" fn init() {
    unsafe {
        GAME.write(MyGame::init());
    }
}

#[no_mangle]
pub extern "C" fn update() {
    unsafe {
        GAME.assume_init_mut().update();
    }
}

#[no_mangle]
pub extern "C" fn draw() {
    unsafe {
        GAME.assume_init_mut().draw();
    }
}
