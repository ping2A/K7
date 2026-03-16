//! Predefined 16-color palettes (pico-8, commodore64, atari2600, etc.).

use std::collections::HashMap;
use crate::constants::PALETTE_SIZE;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Rgb {
    pub r: u8,
    pub g: u8,
    pub b: u8,
}

impl Rgb {
    pub const fn new(r: u8, g: u8, b: u8) -> Self {
        Self { r, g, b }
    }
}

/// Single 16-color palette.
#[derive(Debug, Clone)]
pub struct Palette {
    pub colors: [Rgb; PALETTE_SIZE],
}

impl Palette {
    pub fn get(&self, index: u8) -> Rgb {
        self.colors[index as usize % PALETTE_SIZE]
    }
    pub fn set(&mut self, index: u8, r: u8, g: u8, b: u8) {
        if (index as usize) < PALETTE_SIZE {
            self.colors[index as usize] = Rgb::new(r, g, b);
        }
    }
    /// Swap two palette entries by index (0..15).
    pub fn swap(&mut self, a: u8, b: u8) {
        let i = a as usize % PALETTE_SIZE;
        let j = b as usize % PALETTE_SIZE;
        if i != j {
            self.colors.swap(i, j);
        }
    }
}

/// Collection of named palettes.
#[derive(Debug)]
pub struct Palettes {
    pub palettes: HashMap<String, Palette>,
    pub list: Vec<String>,
}

impl Palettes {
    pub fn new() -> Self {
        let mut palettes = HashMap::new();
        let list = vec![
            "pico8".to_string(),
            "commodore64".to_string(),
            "atari2600".to_string(),
            "gameboy".to_string(),
            "cga".to_string(),
        ];
        palettes.insert("pico8".to_string(), pico8());
        palettes.insert("commodore64".to_string(), commodore64());
        palettes.insert("atari2600".to_string(), atari2600());
        palettes.insert("gameboy".to_string(), gameboy());
        palettes.insert("cga".to_string(), cga());
        Self { palettes, list }
    }
    pub fn get(&self, name: &str) -> Option<&Palette> {
        self.palettes.get(name)
    }
    pub fn get_mut(&mut self, name: &str) -> Option<&mut Palette> {
        self.palettes.get_mut(name)
    }
}

fn pico8() -> Palette {
    // Pico-8 default 16 colors (from pico-8.gpl)
    Palette {
        colors: [
            Rgb::new(0, 0, 0),       // 0 black
            Rgb::new(29, 43, 83),   // 1 dark_blue
            Rgb::new(126, 37, 83),  // 2 dark_purple
            Rgb::new(0, 135, 81),   // 3 dark_green
            Rgb::new(171, 82, 54),  // 4 brown
            Rgb::new(95, 87, 79),   // 5 dark_gray
            Rgb::new(194, 195, 199), // 6 light_gray
            Rgb::new(255, 241, 232), // 7 white
            Rgb::new(255, 0, 77),   // 8 red
            Rgb::new(255, 163, 0),  // 9 orange
            Rgb::new(255, 240, 36), // 10 yellow
            Rgb::new(0, 231, 86),   // 11 green
            Rgb::new(41, 173, 255), // 12 blue
            Rgb::new(131, 118, 156), // 13 indigo
            Rgb::new(255, 119, 168), // 14 pink
            Rgb::new(255, 204, 170), // 15 peach
        ],
    }
}

fn commodore64() -> Palette {
    // C64 16 colors
    Palette {
        colors: [
            Rgb::new(0, 0, 0),
            Rgb::new(255, 255, 255),
            Rgb::new(136, 57, 50),
            Rgb::new(103, 182, 189),
            Rgb::new(139, 63, 150),
            Rgb::new(85, 160, 73),
            Rgb::new(64, 49, 141),
            Rgb::new(191, 206, 114),
            Rgb::new(139, 84, 41),
            Rgb::new(87, 66, 0),
            Rgb::new(184, 105, 98),
            Rgb::new(80, 80, 80),
            Rgb::new(120, 120, 120),
            Rgb::new(148, 224, 137),
            Rgb::new(120, 105, 196),
            Rgb::new(159, 159, 159),
        ],
    }
}

fn atari2600() -> Palette {
    // Atari 2600 NTSC first 16
    Palette {
        colors: [
            Rgb::new(0, 0, 0),
            Rgb::new(68, 68, 0),
            Rgb::new(112, 40, 0),
            Rgb::new(132, 24, 0),
            Rgb::new(136, 0, 0),
            Rgb::new(120, 0, 92),
            Rgb::new(72, 0, 120),
            Rgb::new(20, 0, 132),
            Rgb::new(0, 0, 136),
            Rgb::new(0, 24, 124),
            Rgb::new(0, 44, 92),
            Rgb::new(0, 64, 44),
            Rgb::new(0, 60, 0),
            Rgb::new(20, 56, 0),
            Rgb::new(44, 48, 0),
            Rgb::new(68, 40, 0),
        ],
    }
}

fn gameboy() -> Palette {
    // Game Boy (DMG) classic 4-shade green; extended to 16 for K7 (repeated + grays).
    Palette {
        colors: [
            Rgb::new(15, 56, 15),   // darkest
            Rgb::new(48, 98, 48),
            Rgb::new(139, 172, 15),
            Rgb::new(155, 188, 15), // lightest green
            Rgb::new(15, 56, 15),
            Rgb::new(48, 98, 48),
            Rgb::new(139, 172, 15),
            Rgb::new(155, 188, 15),
            Rgb::new(80, 80, 80),
            Rgb::new(120, 120, 120),
            Rgb::new(160, 160, 160),
            Rgb::new(200, 200, 200),
            Rgb::new(15, 56, 15),
            Rgb::new(139, 172, 15),
            Rgb::new(200, 200, 200),
            Rgb::new(255, 255, 255),
        ],
    }
}

fn cga() -> Palette {
    // CGA 16-color palette (common “colorful” set).
    Palette {
        colors: [
            Rgb::new(0, 0, 0),
            Rgb::new(0, 0, 170),
            Rgb::new(0, 170, 0),
            Rgb::new(0, 170, 170),
            Rgb::new(170, 0, 0),
            Rgb::new(170, 0, 170),
            Rgb::new(170, 85, 0),
            Rgb::new(170, 170, 170),
            Rgb::new(85, 85, 85),
            Rgb::new(85, 85, 255),
            Rgb::new(85, 255, 85),
            Rgb::new(85, 255, 255),
            Rgb::new(255, 85, 85),
            Rgb::new(255, 85, 255),
            Rgb::new(255, 255, 85),
            Rgb::new(255, 255, 255),
        ],
    }
}
