//! Universe and SandApi for Sable. Pure Rust: uses rand instead of extern C.

use crate::species::{Cell, Species, EMPTY_CELL};
use rand::Rng;

pub const W: i32 = 128;
pub const H: i32 = 128;
pub const SIZE: usize = (W * H) as usize;

#[repr(C)]
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Wind {
    pub dx: u8,
    pub dy: u8,
    pub pressure: u8,
    pub density: u8,
}

pub struct Universe {
    pub cells: [Cell; SIZE],
    pub winds: [Wind; SIZE],
    pub burns: [Wind; SIZE],
    pub generation: u8,
}

pub struct SandApi<'a> {
    pub x: i32,
    pub y: i32,
    pub universe: &'a mut Universe,
}

fn rand_int(n: i32) -> i32 {
    if n <= 0 {
        return 0;
    }
    rand::thread_rng().gen_range(0..=n)
}

impl<'a> SandApi<'a> {
    pub fn get(&self, dx: i32, dy: i32) -> Cell {
        let nx = self.x + dx;
        let ny = self.y + dy;
        if nx < 0 || nx >= W || ny < 0 || ny >= H {
            return Cell {
                species: Species::Wall,
                ra: 0,
                rb: 0,
                clock: self.universe.generation,
            };
        }
        self.universe.get_cell(nx, ny)
    }

    pub fn set(&mut self, dx: i32, dy: i32, v: Cell) {
        let nx = self.x + dx;
        let ny = self.y + dy;
        if nx < 0 || nx >= W || ny < 0 || ny >= H {
            return;
        }
        let i = self.universe.get_index(nx, ny);
        self.universe.cells[i] = v;
        self.universe.cells[i].clock = self.universe.generation.wrapping_add(1);
    }

    pub fn get_fluid(&self) -> Wind {
        let idx = self.universe.get_index(self.x, self.y);
        self.universe.winds[idx]
    }

    pub fn set_fluid(&mut self, v: Wind) {
        let idx = self.universe.get_index(self.x, self.y);
        self.universe.burns[idx] = v;
    }

    pub fn rand_int(&self, n: i32) -> i32 {
        rand_int(n)
    }

    pub fn once_in(&self, n: i32) -> bool {
        rand_int(n) == 0
    }

    pub fn rand_dir(&self) -> i32 {
        let i = rand_int(1000);
        (i % 3) - 1
    }

    pub fn rand_dir_2(&self) -> i32 {
        if rand_int(1000) % 2 == 0 {
            -1
        } else {
            1
        }
    }

    pub fn rand_vec(&self) -> (i32, i32) {
        let i = rand_int(2000);
        match i % 9 {
            0 => (1, 1),
            1 => (1, 0),
            2 => (1, -1),
            3 => (0, -1),
            4 => (-1, -1),
            5 => (-1, 0),
            6 => (-1, 1),
            7 => (0, 1),
            _ => (0, 0),
        }
    }

    pub fn rand_vec_8(&self) -> (i32, i32) {
        let i = rand_int(8);
        match i {
            0 => (1, 1),
            1 => (1, 0),
            2 => (1, -1),
            3 => (0, -1),
            4 => (-1, -1),
            5 => (-1, 0),
            6 => (-1, 1),
            _ => (0, 1),
        }
    }
}

pub const EMPTY_WIND: Wind = Wind {
    dx: 0,
    dy: 0,
    pressure: 0,
    density: 0,
};

impl Universe {
    pub fn new() -> Self {
        Self {
            cells: [EMPTY_CELL; SIZE],
            winds: [EMPTY_WIND; SIZE],
            burns: [EMPTY_WIND; SIZE],
            generation: 0,
        }
    }

    pub fn get_index(&self, x: i32, y: i32) -> usize {
        (x * H + y) as usize
    }

    pub fn get_cell(&self, x: i32, y: i32) -> Cell {
        let i = self.get_index(x, y);
        self.cells[i]
    }

    pub fn prepare_tick(&mut self) {
        self.generation = self.generation.wrapping_add(1);
    }

    pub fn clear_burn(&mut self, x: i32, y: i32) {
        let idx = self.get_index(x, y);
        self.burns[idx] = EMPTY_WIND;
    }

    pub fn finish_tick(&mut self) {
        self.winds.copy_from_slice(&self.burns);
        self.generation = self.generation.wrapping_add(1);
    }

    pub fn reset(&mut self) {
        for i in 0..SIZE {
            self.cells[i] = EMPTY_CELL;
            self.winds[i] = EMPTY_WIND;
            self.burns[i] = EMPTY_WIND;
        }
    }

    pub fn paint(&mut self, x: i32, y: i32, size: i32, species: Species) {
        let radius = (size as f32) / 2.0;
        let floor = (radius + 1.0) as i32;
        let ceil = (radius + 1.5) as i32;
        for dx in -floor..ceil {
            for dy in -floor..ceil {
                if ((dx * dx + dy * dy) as f32) > radius * radius {
                    continue;
                }
                let px = x + dx;
                let py = y + dy;
                if px < 0 || px >= W || py < 0 || py >= H {
                    continue;
                }
                let c = self.get_cell(px, py);
                if c.species == Species::Empty || species == Species::Empty {
                    let ra = (60u8.saturating_add(size as u8))
                        .saturating_add((rand::random::<f32>() * 30.0) as u8)
                        .saturating_add((self.generation as i32 % 127 - 60).abs() as u8);
                    self.cells[self.get_index(px, py)] = Cell {
                        species,
                        ra,
                        rb: 0,
                        clock: self.generation,
                    };
                }
            }
        }
    }
}
