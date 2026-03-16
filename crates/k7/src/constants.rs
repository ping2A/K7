//! K7 fantasy console constants.

/// Default display width in pixels.
pub const SCREEN_WIDTH: u32 = 256;
/// Default display height in pixels.
pub const SCREEN_HEIGHT: u32 = 256;
/// Number of palette colors (8-bit index 0..15).
pub const PALETTE_SIZE: usize = 16;
/// Sprite size in pixels.
pub const SPRITE_SIZE: u32 = 8;
/// Number of sprites in the cartridge bank.
pub const SPRITE_COUNT: usize = 256;
/// Map width in cells.
pub const MAP_WIDTH: u32 = 256;
/// Map height in cells.
pub const MAP_HEIGHT: u32 = 32;
/// Number of audio channels.
pub const AUDIO_CHANNELS: usize = 4;
/// Number of definable sounds.
pub const SOUND_COUNT: usize = 64;
/// Number of music tracks.
pub const MUSIC_TRACK_COUNT: usize = 8;
