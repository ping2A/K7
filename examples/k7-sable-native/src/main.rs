//! Sable falling-sand game: pure Rust, no WASM. Uses k7-native as the runtime.

mod game;
mod species;
mod universe;
mod utils;

use anyhow::Result;
use game::MyGame;
use k7_native;

fn main() -> Result<()> {
    k7_native::run_native::<MyGame>("Sable (native)")
}
