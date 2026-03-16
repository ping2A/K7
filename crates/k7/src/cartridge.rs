//! Cartridge format: sprites (256×8×8), map (256×32), sounds, music.

use crate::sprite::Sprite;
use crate::map::Map;
use crate::constants::{SPRITE_COUNT, MAP_WIDTH, MAP_HEIGHT, SOUND_COUNT, MUSIC_TRACK_COUNT};

/// Cartridge data loaded from a game (file or embedded).
pub struct Cartridge {
    pub sprites: Vec<Sprite>,
    pub map: Map,
    pub sounds: [Option<String>; SOUND_COUNT],
    pub music_tracks: [Option<String>; MUSIC_TRACK_COUNT],
}

impl Default for Cartridge {
    fn default() -> Self {
        Self::new()
    }
}

impl Cartridge {
    pub fn new() -> Self {
        Self {
            sprites: (0..SPRITE_COUNT).map(|_| Sprite::new()).collect(),
            map: Map::new(),
            sounds: std::array::from_fn(|_| None),
            music_tracks: std::array::from_fn(|_| None),
        }
    }

    pub fn load_sprites(&mut self, data: &[u8]) {
        let mut off = 0;
        self.sprites.clear();
        for _ in 0..SPRITE_COUNT {
            let mut sprite = Sprite::new();
            let end = (off + 64).min(data.len());
            let len = end - off;
            if len > 0 {
                sprite.data[..len].copy_from_slice(&data[off..end]);
            }
            self.sprites.push(sprite);
            off += 64;
            if off >= data.len() {
                break;
            }
        }
        while self.sprites.len() < SPRITE_COUNT {
            self.sprites.push(Sprite::new());
        }
    }

    pub fn load_map(&mut self, data: &[u8]) {
        let size = (MAP_WIDTH * MAP_HEIGHT) as usize;
        let len = data.len().min(size);
        self.map.cells[..len].copy_from_slice(&data[..len]);
    }
}
