//! Sprites: 256× 8×8 bank + dynamic sprite API.

use crate::constants::SPRITE_SIZE;

/// Single 8×8 sprite: each byte is palette index (0..15).
#[derive(Clone, Debug)]
pub struct Sprite {
    pub data: [u8; (SPRITE_SIZE * SPRITE_SIZE) as usize],
}

impl Sprite {
    pub const fn new() -> Self {
        Self {
            data: [0u8; (SPRITE_SIZE * SPRITE_SIZE) as usize],
        }
    }
    pub fn from_slice(data: &[u8]) -> Self {
        let mut s = Self::new();
        let len = data.len().min(s.data.len());
        s.data[..len].copy_from_slice(&data[..len]);
        s
    }
    pub fn get(&self, x: u32, y: u32) -> u8 {
        if x < SPRITE_SIZE && y < SPRITE_SIZE {
            self.data[(y * SPRITE_SIZE + x) as usize]
        } else {
            0
        }
    }
    pub fn set(&mut self, x: u32, y: u32, c: u8) {
        if x < SPRITE_SIZE && y < SPRITE_SIZE {
            self.data[(y * SPRITE_SIZE + x) as usize] = c & 0x0F;
        }
    }
}

/// Dynamically created sprite (variable size stored in runtime).
#[derive(Clone, Debug)]
pub struct DynamicSprite {
    pub width: u32,
    pub height: u32,
    pub data: Vec<u8>,
}

impl DynamicSprite {
    pub fn new(width: u32, height: u32) -> Self {
        let size = (width * height) as usize;
        Self {
            width,
            height,
            data: vec![0; size],
        }
    }
    pub fn get(&self, x: u32, y: u32) -> u8 {
        if x < self.width && y < self.height {
            self.data[(y * self.width + x) as usize]
        } else {
            0
        }
    }
    pub fn set(&mut self, x: u32, y: u32, c: u8) {
        if x < self.width && y < self.height {
            self.data[(y * self.width + x) as usize] = c & 0x0F;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sprite_new_all_zeros() {
        let s = Sprite::new();
        for y in 0..SPRITE_SIZE {
            for x in 0..SPRITE_SIZE {
                assert_eq!(s.get(x, y), 0);
            }
        }
    }

    #[test]
    fn sprite_get_out_of_bounds_returns_zero() {
        let s = Sprite::new();
        assert_eq!(s.get(8, 0), 0);
        assert_eq!(s.get(0, 8), 0);
        assert_eq!(s.get(100, 100), 0);
    }

    #[test]
    fn sprite_set_and_get_in_bounds() {
        let mut s = Sprite::new();
        s.set(0, 0, 1);
        s.set(7, 7, 15);
        s.set(4, 4, 8);
        assert_eq!(s.get(0, 0), 1);
        assert_eq!(s.get(7, 7), 15);
        assert_eq!(s.get(4, 4), 8);
    }

    #[test]
    fn sprite_set_out_of_bounds_ignored() {
        let mut s = Sprite::new();
        s.set(8, 0, 1);
        s.set(0, 8, 1);
        assert_eq!(s.get(0, 0), 0);
    }

    #[test]
    fn sprite_masked_to_4_bits() {
        let mut s = Sprite::new();
        s.set(0, 0, 0xFF);
        s.set(1, 0, 31);
        assert_eq!(s.get(0, 0), 15);
        assert_eq!(s.get(1, 0), 15);
    }

    #[test]
    fn sprite_from_slice() {
        let data: Vec<u8> = (0..64).collect();
        let s = Sprite::from_slice(&data);
        for y in 0..SPRITE_SIZE {
            for x in 0..SPRITE_SIZE {
                assert_eq!(s.get(x, y), (y * SPRITE_SIZE + x) as u8);
            }
        }
    }

    #[test]
    fn dynamic_sprite_bounds() {
        let mut d = DynamicSprite::new(4, 4);
        d.set(0, 0, 1);
        d.set(3, 3, 15);
        assert_eq!(d.get(0, 0), 1);
        assert_eq!(d.get(3, 3), 15);
        assert_eq!(d.get(4, 0), 0);
        assert_eq!(d.get(0, 4), 0);
    }
}
