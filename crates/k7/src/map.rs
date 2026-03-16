//! Map: 256×32 8-bit cells (sprite indices) + 8-bit flags per cell (flip/rotate).

use crate::constants::{MAP_WIDTH, MAP_HEIGHT};

/// Tile flags: bit0 = flip_x, bit1 = flip_y, bit2 = rotate 90° CW.
pub const FLAG_FLIP_X: u8 = 1;
pub const FLAG_FLIP_Y: u8 = 2;
pub const FLAG_ROTATE: u8 = 4;

#[derive(Clone, Debug)]
pub struct Map {
    pub cells: Vec<u8>,
    /// Per-cell flags (same length as cells). Bits: 1=flip_x, 2=flip_y, 4=rotate.
    pub flags: Vec<u8>,
    pub width: u32,
    pub height: u32,
}

impl Default for Map {
    fn default() -> Self {
        Self::new()
    }
}

impl Map {
    pub fn new() -> Self {
        let n = (MAP_WIDTH * MAP_HEIGHT) as usize;
        Self {
            cells: vec![0; n],
            flags: vec![0; n],
            width: MAP_WIDTH,
            height: MAP_HEIGHT,
        }
    }
    pub fn get(&self, x: i32, y: i32) -> u8 {
        if x < 0 || y < 0 || x >= self.width as i32 || y >= self.height as i32 {
            return 0;
        }
        let i = (y as u32 * self.width + x as u32) as usize;
        self.cells.get(i).copied().unwrap_or(0)
    }
    pub fn set(&mut self, x: i32, y: i32, cell: u8) {
        if x >= 0 && y >= 0 && x < self.width as i32 && y < self.height as i32 {
            let i = (y as u32 * self.width + x as u32) as usize;
            if i < self.cells.len() {
                self.cells[i] = cell & 0xFF;
            }
        }
    }
    pub fn get_flags(&self, x: i32, y: i32) -> u8 {
        if x < 0 || y < 0 || x >= self.width as i32 || y >= self.height as i32 {
            return 0;
        }
        let i = (y as u32 * self.width + x as u32) as usize;
        self.flags.get(i).copied().unwrap_or(0)
    }
    pub fn set_flags(&mut self, x: i32, y: i32, f: u8) {
        if x >= 0 && y >= 0 && x < self.width as i32 && y < self.height as i32 {
            let i = (y as u32 * self.width + x as u32) as usize;
            if i < self.flags.len() {
                self.flags[i] = f & 0xFF;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn map_new_has_correct_size() {
        let m = Map::new();
        assert_eq!(m.cells.len(), (MAP_WIDTH * MAP_HEIGHT) as usize);
        assert_eq!(m.width, MAP_WIDTH);
        assert_eq!(m.height, MAP_HEIGHT);
    }

    #[test]
    fn map_get_out_of_bounds_returns_zero() {
        let m = Map::new();
        assert_eq!(m.get(-1, 0), 0);
        assert_eq!(m.get(0, -1), 0);
        assert_eq!(m.get(MAP_WIDTH as i32, 0), 0);
        assert_eq!(m.get(0, MAP_HEIGHT as i32), 0);
        assert_eq!(m.get(1000, 1000), 0);
    }

    #[test]
    fn map_set_and_get_in_bounds() {
        let mut m = Map::new();
        m.set(0, 0, 1);
        m.set(255, 31, 255);
        m.set(100, 15, 42);
        assert_eq!(m.get(0, 0), 1);
        assert_eq!(m.get(255, 31), 255);
        assert_eq!(m.get(100, 15), 42);
    }

    #[test]
    fn map_set_out_of_bounds_ignored() {
        let mut m = Map::new();
        m.set(-1, 0, 1);
        m.set(0, -1, 1);
        m.set(256, 0, 1);
        m.set(0, 32, 1);
        assert_eq!(m.get(0, 0), 0);
    }

    #[test]
    fn map_cell_masked_to_8_bits() {
        let mut m = Map::new();
        m.set(0, 0, 0xFF);
        m.set(1, 0, 255);
        assert_eq!(m.get(0, 0), 255);
        assert_eq!(m.get(1, 0), 255);
    }

    #[test]
    fn map_row_major_indexing() {
        let mut m = Map::new();
        for y in 0..MAP_HEIGHT as i32 {
            for x in 0..MAP_WIDTH as i32 {
                m.set(x, y, (x + y * 2) as u8 & 0xFF);
            }
        }
        for y in 0..MAP_HEIGHT as i32 {
            for x in 0..MAP_WIDTH as i32 {
                assert_eq!(m.get(x, y), (x + y * 2) as u8 & 0xFF);
            }
        }
    }
}
