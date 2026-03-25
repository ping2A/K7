//! Game state and main loop. Matches PikuseruConsole/Sable: species picker, paint, HSV colors, music.

use crate::species::{update_cell, Species};
use crate::universe::{SandApi, Universe, W, H};
use libm::{floorf, sinf};

const SCREEN_W: i32 = 256;
const SCREEN_H: i32 = 256;
const SIM_SCALE: i32 = 2;
const WIDGET_X: i32 = 240;
const WIDGET_SIZE: i32 = 8;
const BRUSH_SIZE: i32 = 10;

extern "C" {
    fn cls(col: i32);
    fn pset(x: i32, y: i32, col: i32);
    fn pset_rgba(x: i32, y: i32, r: i32, g: i32, b: i32, a: i32);
    fn rectfill(x0: i32, y0: i32, x1: i32, y1: i32, col: i32);
    fn rectfill_rgba(x0: i32, y0: i32, x1: i32, y1: i32, r: i32, g: i32, b: i32, a: i32);
    fn print(text_ptr: i32, len: i32, x: i32, y: i32, col: i32);
    fn mouse_x() -> i32;
    fn mouse_y() -> i32;
    fn mouse_left_state(button: i32) -> i32;
    fn set_music_track(id: u32, text_ptr: i32, len: i32);
    fn play_music(channel: u32, track_id: u32);
    fn frnd() -> f32;
    fn rnd(max: i32) -> i32;
}

fn rnd_range(lo: i32, hi: i32) -> i32 {
    if hi <= lo {
        return lo;
    }
    lo + (unsafe { rnd(hi - lo + 1) })
}

/// HSV to RGB (Sable-style), return (r,g,b) 0..255.
fn hsv_to_rgb(h: f32, s: f32, v: f32) -> (u8, u8, u8) {
    let (mut r, mut g, mut b) = (0.0f32, 0.0f32, 0.0f32);
    let i = floorf(h * 6.0) as i32;
    let f = h * 6.0 - i as f32;
    let p = v * (1.0 - s);
    let q = v * (1.0 - f * s);
    let t = v * (1.0 - (1.0 - f) * s);
    match i % 6 {
        0 => { r = v; g = t; b = p; }
        1 => { r = q; g = v; b = p; }
        2 => { r = p; g = v; b = t; }
        3 => { r = p; g = q; b = v; }
        4 => { r = t; g = p; b = v; }
        _ => { r = v; g = p; b = q; }
    }
    let clamp = |x: f32| (x.min(1.0).max(0.0) * 255.0) as u8;
    (clamp(r), clamp(g), clamp(b))
}

/// Species + ra/rb to RGB (port of Sable species_to_rgb).
fn species_to_rgb(species: Species, ra: u8, rb: u8) -> (u8, u8, u8) {
    let raf = ra as f32 / 255.0;
    let rbf = rb as f32 / 255.0;
    let mut hue = 0.0f32;
    let mut saturation = 0.6f32;
    let mut lightness = 0.3 + raf * 0.5;
    match species {
        Species::Empty => {
            hue = 0.10;
            saturation = 0.0;
            lightness = 0.18;
        }
        Species::Cloner => { hue = 0.9; saturation = 0.3; }
        Species::Acid => {
            hue = 0.18;
            saturation = 0.9;
            lightness = 0.8 + raf * 0.2;
        }
        Species::Dust => {
            hue = raf * 2.0;
            saturation = 0.4;
            lightness = 0.8;
        }
        Species::Fire => {
            hue = raf * 0.1;
            saturation = 0.7;
            lightness = 0.7 + raf * 0.3;
        }
        Species::Fungus => {
            hue = raf * 0.15 - 0.1;
            saturation = raf * 0.8 - 0.05;
            lightness = 1.5 - raf * 0.2;
        }
        Species::Gas => {
            hue = 0.0;
            lightness += 0.4;
            saturation = 0.2 + raf * 1.5;
        }
        Species::Ice => {
            hue = 0.6;
            saturation = 0.4;
            lightness = 0.7 + raf * 0.5;
        }
        Species::Lava => {
            hue = raf * 0.1;
            lightness = 0.7 + raf * 0.25;
        }
        Species::Mite => {
            hue = 0.8;
            saturation = 0.9;
            lightness = 0.8;
        }
        Species::Oil => {
            hue = raf * 5.0;
            saturation = 0.2;
            lightness = 0.3;
        }
        Species::Plant => { hue = 0.4; saturation = 0.4; }
        Species::Rocket => {
            hue = 0.0;
            saturation = 0.4 + rbf;
            lightness = 0.9;
        }
        Species::Sand => {
            hue = 0.1;
            saturation = 0.24;
            lightness = 0.87;
        }
        Species::Stone => {
            hue = 0.58 + raf * 0.5;
            saturation = 0.1;
        }
        Species::Seed => {
            hue = rbf * 2.0 * 0.5;
            saturation = 0.7 * (raf + 0.4) + rbf * 0.2;
            lightness = 0.9 * (raf + 0.9);
        }
        Species::Water => {
            hue = 0.6;
            lightness = 0.7 + raf * 0.25;
        }
        Species::Wood => {
            hue = raf * 0.1;
            saturation = 0.3;
            lightness = 0.3 + raf * 0.3;
        }
        Species::Wall => {
            hue = 0.12;
            saturation = 0.1;
            lightness = 0.25;
        }
    }
    if species != Species::Empty {
        lightness *= 0.975 + unsafe { frnd() };
    }
    let (r, g, b) = hsv_to_rgb(hue, saturation, lightness.min(1.0));
    (r, g, b)
}

const N_WIDGETS: usize = 18;
const WIDGET_SPECIES: [Species; N_WIDGETS] = [
    Species::Water,
    Species::Fire,
    Species::Lava,
    Species::Seed,
    Species::Sand,
    Species::Plant,
    Species::Rocket,
    Species::Oil,
    Species::Acid,
    Species::Stone,
    Species::Wood,
    Species::Mite,
    Species::Gas,
    Species::Ice,
    Species::Cloner,
    Species::Dust,
    Species::Fungus,
    Species::Empty,
];

fn widget_species_color(s: Species) -> i32 {
    use Species::*;
    match s {
        Empty => 0,
        Wall => 1,
        Sand => 2,
        Water => 3,
        Gas => 4,
        Cloner => 5,
        Fire => 6,
        Wood => 7,
        Lava => 8,
        Ice => 9,
        Plant => 11,
        Acid => 12,
        Stone => 13,
        Dust => 14,
        Mite => 15,
        Oil => 16,
        Rocket => 17,
        Fungus => 18,
        Seed => 19,
    }
}

fn species_name(s: Species) -> &'static [u8] {
    use Species::*;
    match s {
        Empty => b"Empty",
        Wall => b"Wall",
        Sand => b"Sand",
        Water => b"Water",
        Gas => b"Gas",
        Cloner => b"Cloner",
        Fire => b"Fire",
        Wood => b"Wood",
        Lava => b"Lava",
        Ice => b"Ice",
        Plant => b"Plant",
        Acid => b"Acid",
        Stone => b"Stone",
        Dust => b"Dust",
        Mite => b"Mite",
        Oil => b"Oil",
        Rocket => b"Rocket",
        Fungus => b"Fungus",
        Seed => b"Seed",
    }
}

pub struct MyGame {
    pub universe: Universe,
    current_species: Species,
    prev_left: bool,
}

impl MyGame {
    pub fn init() -> Self {
        // Calm melodic background: simple tune with soft pad (h = half note = 1s)
        const TRACK: &[u8] = b"ch3:pad:warm eh3:pad:warm gh3:pad:warm ch4:pad:warm gh3:pad:warm eh3:pad:warm ch3:pad:warm eh3:pad:warm gh3:pad:warm ch4:pad:warm ah3:pad:warm gh3:pad:warm eh3:pad:warm gh3:pad:warm ch3:pad:warm ";
        unsafe {
            set_music_track(0, TRACK.as_ptr() as i32, TRACK.len() as i32);
            play_music(0, 0);
        }
        let mut universe = Universe::new();
        // Bottom wall
        for x in 0..W {
            universe.paint(x, H - 1, 1, Species::Wall);
        }
        // Sable-style: sin-wave sand at bottom
        let mut x = 5;
        while x <= W - 5 {
            let y = H - 40 + (5.0 * sinf(x as f32 / 20.0)) as i32;
            let size = (unsafe { frnd() } * 6.0) as i32 + 10;
            universe.paint(x, y, size, Species::Sand);
            x += 10;
        }
        // Sin-wave seeds in middle
        let mut x = 40;
        while x <= W - 5 {
            let y = H / 2 + (20.0 * sinf(x as f32 / 20.0)) as i32;
            universe.paint(x, y, 6, Species::Seed);
            x += 50 + rnd_range(0, 10);
        }
        Self {
            universe,
            current_species: Species::Sand,
            prev_left: false,
        }
    }

    pub fn update(&mut self) {
        let left = unsafe { mouse_left_state(0) } != 0;
        let click = left && !self.prev_left;
        let mx = unsafe { mouse_x() };
        let my = unsafe { mouse_y() };
        if left {
            if mx >= WIDGET_X {
                if click {
                    let cell_y = my / WIDGET_SIZE;
                    if cell_y < N_WIDGETS as i32 {
                        self.current_species = WIDGET_SPECIES[cell_y as usize];
                    } else if cell_y >= 18 && cell_y <= 22 {
                        self.universe.reset();
                        for x in 0..W {
                            self.universe.paint(x, H - 1, 1, Species::Wall);
                        }
                    }
                }
            } else {
                let sim_x = mx / SIM_SCALE;
                let sim_y = my / SIM_SCALE;
                if sim_x >= 0 && sim_x < W && sim_y >= 0 && sim_y < H {
                    self.universe.paint(sim_x, sim_y, BRUSH_SIZE, self.current_species);
                }
            }
        }
        self.prev_left = left;
        self.universe.prepare_tick();
        // Row-by-row bottom-to-top so stone arch support (diagonals at y-1) see unmodified state
        for y in (0..H).rev() {
            for x in 0..W {
                let scanx = if self.universe.generation % 2 == 0 {
                    W - 1 - x
                } else {
                    x
                };
                self.universe.clear_burn(scanx, y);
                let cell = self.universe.get_cell(scanx, y);
                if cell.clock.wrapping_sub(self.universe.generation) != 1 {
                    let api = SandApi {
                        x: scanx,
                        y,
                        universe: &mut self.universe,
                    };
                    update_cell(cell, api);
                }
            }
        }
        self.universe.finish_tick();
    }

    pub fn draw(&self) {
        unsafe {
            cls(0);
            let w = W;
            let h = H;
            rectfill(0, 0, w * SIM_SCALE - 1, h * SIM_SCALE - 1, 0);
            for x in 0..w {
                for y in 0..h {
                    let c = self.universe.get_cell(x, y);
                    if c.species == Species::Empty {
                        continue;
                    }
                    let (r, g, b) = species_to_rgb(c.species, c.ra, c.rb);
                    let sx = x * SIM_SCALE;
                    let sy = y * SIM_SCALE;
                    rectfill_rgba(sx, sy, sx + SIM_SCALE - 1, sy + SIM_SCALE - 1, r as i32, g as i32, b as i32, 255);
                }
            }
            for (i, &sp) in WIDGET_SPECIES.iter().enumerate() {
                let wy = (i as i32) * WIDGET_SIZE;
                let col = widget_species_color(sp);
                rectfill(WIDGET_X, wy, WIDGET_X + WIDGET_SIZE - 1, wy + WIDGET_SIZE - 1, col);
                if sp == self.current_species {
                    rectfill(WIDGET_X, wy, WIDGET_X + WIDGET_SIZE - 1, wy, 7);
                    rectfill(WIDGET_X, wy + WIDGET_SIZE - 1, WIDGET_X + WIDGET_SIZE - 1, wy + WIDGET_SIZE - 1, 7);
                    rectfill(WIDGET_X, wy, WIDGET_X, wy + WIDGET_SIZE - 1, 7);
                    rectfill(WIDGET_X + WIDGET_SIZE - 1, wy, WIDGET_X + WIDGET_SIZE - 1, wy + WIDGET_SIZE - 1, 7);
                }
            }
            rectfill(WIDGET_X, 18 * WIDGET_SIZE, WIDGET_X + WIDGET_SIZE - 1, 18 * WIDGET_SIZE + WIDGET_SIZE - 1, 8);
            print(b"CLR\0".as_ptr() as i32, 3, WIDGET_X - 20, 18 * WIDGET_SIZE + 1, 7);
            print(b"Sable\0".as_ptr() as i32, 5, SCREEN_W / 2 - 12, 2, 7);
            let name = species_name(self.current_species);
            print(name.as_ptr() as i32, name.len() as i32, 2, 10, 7);
        }
    }
}
