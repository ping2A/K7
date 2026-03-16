//! K7 fantasy console core.
//!
//! - Display: 256×256 default, 8-bit palette (16 colors) + 32-bit RGBA API
//! - Sprites: 256× 8×8 bank + dynamic API
//! - Map: 256×32 8-bit cells
//! - Audio: 4 channels, 64 definable sounds, 8 music tracks
//! - Fonts: predefined (pico8, bbc, trollmini, etc.)

pub mod constants;
pub mod palette;
pub mod display;
pub mod sprite;
pub mod map;
pub mod fonts;
pub mod audio;
pub mod cartridge;

pub use constants::*;
pub use palette::{Palette, Palettes, Rgb};
pub use display::Screen;
pub use sprite::{Sprite, DynamicSprite};
pub use map::{Map, FLAG_FLIP_X, FLAG_FLIP_Y, FLAG_ROTATE};
pub use fonts::Font;
pub use audio::{AudioEngine, SoundId, MusicId};
pub use cartridge::Cartridge;
