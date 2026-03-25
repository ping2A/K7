//! Species and cell update logic. Port of PikuseruConsole/Sable species.rs (no_std, subset).

use crate::universe::{SandApi, Wind, EMPTY_WIND};
use crate::utils::{adjacency_left, adjacency_right, join_dy_dx, split_dy_dx};

#[repr(u8)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Species {
    Empty = 0,
    Wall = 1,
    Sand = 2,
    Water = 3,
    Gas = 4,
    Cloner = 5,
    Fire = 6,
    Wood = 7,
    Lava = 8,
    Ice = 9,
    Plant = 11,
    Acid = 12,
    Stone = 13,
    Dust = 14,
    Mite = 15,
    Oil = 16,
    Rocket = 17,
    Fungus = 18,
    Seed = 19,
}

impl From<u8> for Species {
    fn from(orig: u8) -> Self {
        match orig {
            0 => Species::Empty,
            1 => Species::Wall,
            2 => Species::Sand,
            3 => Species::Water,
            4 => Species::Gas,
            5 => Species::Cloner,
            6 => Species::Fire,
            7 => Species::Wood,
            8 => Species::Lava,
            9 => Species::Ice,
            11 => Species::Plant,
            12 => Species::Acid,
            13 => Species::Stone,
            14 => Species::Dust,
            15 => Species::Mite,
            16 => Species::Oil,
            17 => Species::Rocket,
            18 => Species::Fungus,
            19 => Species::Seed,
            _ => Species::Empty,
        }
    }
}

#[repr(C)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Cell {
    pub species: Species,
    pub ra: u8,
    pub rb: u8,
    pub clock: u8,
}

impl Cell {
    pub fn new(species: Species) -> Cell {
        extern "C" {
            fn frnd() -> f32;
            fn rnd(max: i32) -> i32;
        }
        Cell {
            species,
            ra: (100 + (unsafe { frnd() * 50.0 }) as u8).min(255),
            rb: 0,
            clock: 0,
        }
    }

    pub fn update(&self, api: SandApi) {
        self.species.update(*self, api);
    }
}

/// Entry point for the game tick loop. Updates one cell using the given API.
pub fn update_cell(cell: Cell, api: SandApi) {
    cell.species.update(cell, api);
}

pub const EMPTY_CELL: Cell = Cell {
    species: Species::Empty,
    ra: 0,
    rb: 0,
    clock: 0,
};

impl Species {
    pub fn update(&self, cell: Cell, api: SandApi) {
        match self {
            Species::Empty => {}
            Species::Wall => {}
            Species::Sand => update_sand(cell, api),
            Species::Water => update_water(cell, api),
            Species::Gas => update_gas(cell, api),
            Species::Stone => update_stone(cell, api),
            Species::Dust => update_dust(cell, api),
            Species::Fire => update_fire(cell, api),
            Species::Wood => update_wood(cell, api),
            Species::Lava => update_lava(cell, api),
            Species::Ice => update_ice(cell, api),
            Species::Cloner => update_cloner(cell, api),
            Species::Rocket => update_rocket(cell, api),
            Species::Plant => update_plant(cell, api),
            Species::Fungus => update_fungus(cell, api),
            Species::Seed => update_seed(cell, api),
            Species::Acid => update_acid(cell, api),
            Species::Mite => update_mite(cell, api),
            Species::Oil => update_oil(cell, api),
        }
    }
}

fn update_sand(cell: Cell, mut api: SandApi) {
    let dx = api.rand_dir_2();
    let nbr = api.get(0, 1);
    if nbr.species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(0, 1, cell);
    } else if api.get(dx, 1).species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(dx, 1, cell);
    } else if matches!(
        nbr.species,
        Species::Water | Species::Gas | Species::Oil | Species::Acid
    ) {
        api.set(0, 0, nbr);
        api.set(0, 1, cell);
    } else {
        api.set(0, 0, cell);
    }
}

fn update_dust(cell: Cell, mut api: SandApi) {
    let dx = api.rand_dir();
    let fluid = api.get_fluid();
    if fluid.pressure > 120 {
        api.set(
            0,
            0,
            Cell {
                species: Species::Fire,
                ra: (150 + cell.ra / 10).min(255),
                rb: 0,
                clock: 0,
            },
        );
        api.set_fluid(EMPTY_WIND);
        return;
    }
    let nbr = api.get(0, 1);
    if nbr.species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(0, 1, cell);
    } else if nbr.species == Species::Water {
        api.set(0, 0, nbr);
        api.set(0, 1, cell);
    } else if api.get(dx, 1).species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(dx, 1, cell);
    } else {
        api.set(0, 0, cell);
    }
}

fn update_stone(cell: Cell, mut api: SandApi) {
    // Supported from directly above: don't fall
    let above = api.get(0, -1).species;
    if above == Species::Stone || above == Species::Wall {
        api.set(0, 0, cell);
        return;
    }
    // Arch: both diagonals above are stone — don't fall (and write so clock is updated)
    if api.get(-1, -1).species == Species::Stone && api.get(1, -1).species == Species::Stone {
        api.set(0, 0, cell);
        return;
    }
    let fluid = api.get_fluid();
    if fluid.pressure > 120 && api.rand_int(1) == 0 {
        api.set(
            0,
            0,
            Cell {
                species: Species::Sand,
                ra: cell.ra,
                rb: 0,
                clock: 0,
            },
        );
        return;
    }
    let nbr = api.get(0, 1);
    if nbr.species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(0, 1, cell);
    } else if matches!(
        nbr.species,
        Species::Water | Species::Gas | Species::Oil | Species::Acid
    ) {
        api.set(0, 0, nbr);
        api.set(0, 1, cell);
    } else {
        api.set(0, 0, cell);
    }
}

fn update_water(cell: Cell, mut api: SandApi) {
    let mut dx = api.rand_dir();
    let below = api.get(0, 1);
    let dx1 = api.get(dx, 1);
    if below.species == Species::Empty || below.species == Species::Oil {
        api.set(0, 0, below);
        let mut ra = cell.ra;
        if api.once_in(20) {
            ra = (100 + api.rand_int(50) as u8).min(255);
        }
        api.set(0, 1, Cell { ra, ..cell });
        return;
    }
    if dx1.species == Species::Empty || dx1.species == Species::Oil {
        api.set(0, 0, dx1);
        api.set(dx, 1, cell);
        return;
    }
    if api.get(-dx, 1).species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(-dx, 1, cell);
        return;
    }
    let left = cell.ra % 2 == 0;
    dx = if left { 1 } else { -1 };
    let dx0 = api.get(dx, 0);
    let dxd = api.get(dx * 2, 0);
    if dx0.species == Species::Empty && dxd.species == Species::Empty {
        api.set(0, 0, dxd);
        api.set(2 * dx, 0, Cell { rb: 6, ..cell });
    } else if dx0.species == Species::Empty || dx0.species == Species::Oil {
        api.set(0, 0, dx0);
        api.set(dx, 0, Cell { rb: 3, ..cell });
    } else if cell.rb == 0 && api.get(-dx, 0).species == Species::Empty {
        api.set(0, 0, Cell { ra: (cell.ra as i32 + dx) as u8, ..cell });
    } else if cell.rb > 0 {
        api.set(0, 0, Cell { rb: cell.rb - 1, ..cell });
    } else {
        api.set(0, 0, cell);
    }
}

fn update_gas(cell: Cell, mut api: SandApi) {
    let (dx, dy) = api.rand_vec_8();
    if cell.rb == 0 {
        api.set(0, 0, Cell { rb: 5, ..cell });
        return;
    }
    let nbr = api.get(dx, dy);
    if nbr.species == Species::Ice {
        api.set(0, 0, Cell { species: Species::Ice, clock: 0, ..cell });
    } else if nbr.species == Species::Empty {
        if cell.rb < 3 {
            api.set(0, 0, EMPTY_CELL);
            api.set(dx, dy, cell);
        } else {
            api.set(0, 0, Cell { rb: 1, ..cell });
            api.set(dx, dy, Cell { rb: cell.rb - 1, ..cell });
        }
    } else if (dx != 0 || dy != 0) && nbr.species == Species::Gas && nbr.rb < 4 {
        api.set(0, 0, EMPTY_CELL);
        api.set(dx, dy, Cell { rb: nbr.rb + cell.rb, ..cell });
    } else {
        api.set(0, 0, cell);
    }
}

fn update_fire(cell: Cell, mut api: SandApi) {
    let ra = cell.ra;
    let degraded = Cell {
        ra: ra.saturating_sub((2 + api.rand_dir() + 2) as u8),
        ..cell
    };
    let (dx, dy) = api.rand_vec();
    api.set_fluid(Wind { dx: 0, dy: 150, pressure: 1, density: 120 });
    if api.get(dx, dy).species == Species::Gas || api.get(dx, dy).species == Species::Dust {
        api.set(
            dx,
            dy,
            Cell {
                species: Species::Fire,
                ra: (150 + (dx + dy) * 10).clamp(0, 255) as u8,
                rb: 0,
                clock: 0,
            },
        );
    }
    if ra < 5 || api.get(dx, dy).species == Species::Water {
        api.set(0, 0, EMPTY_CELL);
    } else if api.get(dx, dy).species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(dx, dy, degraded);
    } else {
        api.set(0, 0, degraded);
    }
}

fn update_lava(cell: Cell, mut api: SandApi) {
    api.set_fluid(Wind { dx: 0, dy: 10, pressure: 0, density: 60 });
    let (dx, dy) = api.rand_vec();
    if api.get(dx, dy).species == Species::Gas || api.get(dx, dy).species == Species::Dust {
        api.set(
            dx,
            dy,
            Cell {
                species: Species::Fire,
                ra: (150 + (dx + dy) * 10).clamp(0, 255) as u8,
                rb: 0,
                clock: 0,
            },
        );
    }
    let sample = api.get(dx, dy);
    if sample.species == Species::Water {
        api.set(
            0,
            0,
            Cell {
                species: Species::Stone,
                ra: (150 + (dx + dy) * 10).clamp(0, 255) as u8,
                rb: 0,
                clock: 0,
            },
        );
        api.set(dx, dy, EMPTY_CELL);
    } else if api.get(0, 1).species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(0, 1, cell);
    } else if api.get(dx, 1).species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(dx, 1, cell);
    } else if api.get(dx, 0).species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(dx, 0, cell);
    } else {
        api.set(0, 0, cell);
    }
}

fn update_wood(cell: Cell, mut api: SandApi) {
    let (dx, dy) = api.rand_vec();
    let nbr_species = api.get(dx, dy).species;
    if cell.rb == 0 && (nbr_species == Species::Fire || nbr_species == Species::Lava) {
        api.set(0, 0, Cell { rb: 90, ..cell });
    }
    if cell.rb > 1 {
        api.set(0, 0, Cell { rb: cell.rb - 1, ..cell });
        if cell.rb % 4 == 0 && nbr_species == Species::Empty {
            api.set(
                dx,
                dy,
                Cell {
                    species: Species::Fire,
                    ra: (30 + api.rand_int(60) as u8).min(255),
                    rb: 0,
                    clock: 0,
                },
            );
        }
        if nbr_species == Species::Water {
            api.set(0, 0, Cell { ra: 50, rb: 0, ..cell });
        }
    } else if cell.rb == 1 {
        api.set(0, 0, EMPTY_CELL);
    }
}

fn update_ice(cell: Cell, mut api: SandApi) {
    let (dx, dy) = api.rand_vec();
    let fluid = api.get_fluid();
    if fluid.pressure > 120 && api.rand_int(1) == 0 {
        api.set(0, 0, Cell { species: Species::Water, ..cell });
        return;
    }
    let nbr_species = api.get(dx, dy).species;
    if nbr_species == Species::Fire || nbr_species == Species::Lava {
        api.set(0, 0, Cell { species: Species::Water, ..cell });
    } else if nbr_species == Species::Water && api.rand_int(100) < 7 {
        api.set(dx, dy, Cell { species: Species::Ice, ..cell });
    }
}

fn update_cloner(cell: Cell, mut api: SandApi) {
    let mut clone_species = Species::from(cell.rb);
    let g = api.universe.generation;
    for dx in [-1, 0, 1] {
        for dy in [-1, 0, 1] {
            if cell.rb == 0 {
                let nbr_species = api.get(dx, dy).species;
                if nbr_species != Species::Empty
                    && nbr_species != Species::Cloner
                    && nbr_species != Species::Wall
                {
                    clone_species = nbr_species;
                    api.set(0, 0, Cell { rb: clone_species as u8, ra: 200, ..cell });
                    return;
                }
            } else if api.rand_int(100) > 90 && api.get(dx, dy).species == Species::Empty {
                let ra = (80 + api.rand_int(30) as u8 + (g as i32 % 127 - 60).abs() as u8).min(255);
                api.set(dx, dy, Cell::new(clone_species));
                api.set(dx, dy, Cell { species: clone_species, ra, rb: 0, clock: 0 });
                return;
            }
        }
    }
}

fn update_rocket(cell: Cell, mut api: SandApi) {
    if cell.rb == 0 {
        api.set(0, 0, Cell { ra: 0, rb: 100, ..cell });
        return;
    }
    let clone_species = if cell.rb != 100 {
        Species::from(cell.rb)
    } else {
        Species::Sand
    };
    let (sx, sy) = api.rand_vec_8();
    let sample = api.get(sx, sy);
    if cell.rb == 100
        && sample.species != Species::Empty
        && sample.species != Species::Rocket
        && sample.species != Species::Wall
        && sample.species != Species::Cloner
    {
        api.set(0, 0, Cell { ra: 1, rb: sample.species as u8, ..cell });
        return;
    }
    let ra = cell.ra;
    if ra == 0 {
        let dx = api.rand_dir_2();
        let nbr = api.get(0, 1);
        if nbr.species == Species::Empty {
            api.set(0, 0, EMPTY_CELL);
            api.set(0, 1, cell);
        } else if api.get(dx, 1).species == Species::Empty {
            api.set(0, 0, EMPTY_CELL);
            api.set(dx, 1, cell);
        } else if matches!(nbr.species, Species::Water | Species::Gas | Species::Oil | Species::Acid) {
            api.set(0, 0, nbr);
            api.set(0, 1, cell);
        } else {
            api.set(0, 0, cell);
        }
    } else if ra == 1 {
        api.set(0, 0, Cell { ra: 2, ..cell });
    } else if ra == 2 {
        let (mut dx, mut dy) = api.rand_vec_8();
        if api.get(dx, dy).species != Species::Empty {
            dx = -dx;
            dy = -dy;
        }
        api.set(0, 0, Cell { ra: 100 + join_dy_dx(dx, dy), ..cell });
    } else if ra >= 100 {
        let (dx, dy) = split_dy_dx(ra - 100);
        let nbr = api.get(dx, dy * 2);
        if nbr.species == Species::Empty
            || nbr.species == Species::Fire
            || nbr.species == Species::Rocket
        {
            api.set(0, 0, Cell::new(clone_species));
            api.set(0, dy, Cell::new(clone_species));
            let (ndx, ndy) = match api.rand_int(100) % 5 {
                0 => adjacency_left((dx, dy)),
                1 => adjacency_right((dx, dy)),
                _ => (dx, dy),
            };
            api.set(
                dx,
                dy * 2,
                Cell { ra: 100 + join_dy_dx(ndx, ndy), ..cell },
            );
        } else {
            api.set(0, 0, EMPTY_CELL);
        }
    }
}

fn update_plant(cell: Cell, mut api: SandApi) {
    let (dx, dy) = api.rand_vec();
    let nbr_species = api.get(dx, dy).species;
    if cell.rb == 0 && (nbr_species == Species::Fire || nbr_species == Species::Lava) {
        api.set(0, 0, Cell { rb: 20, ..cell });
    }
    if nbr_species == Species::Wood {
        let (dx2, dy2) = api.rand_vec_8();
        if api.get(dx2, dy2).species == Species::Empty {
            let drift = (api.rand_int(100) % 15) - 7;
            api.set(
                dx2,
                dy2,
                Cell {
                    species: Species::Plant,
                    ra: (cell.ra as i32 + drift).clamp(0, 255) as u8,
                    rb: 0,
                    clock: 0,
                },
            );
        }
    }
    if cell.rb > 1 {
        api.set(0, 0, Cell { rb: cell.rb - 1, ..cell });
    } else if cell.rb == 1 {
        api.set(0, 0, EMPTY_CELL);
    }
}

fn update_fungus(cell: Cell, mut api: SandApi) {
    let (dx, dy) = api.rand_vec();
    let nbr_species = api.get(dx, dy).species;
    if cell.rb == 0 && (nbr_species == Species::Fire || nbr_species == Species::Lava) {
        api.set(0, 0, Cell { rb: 10, ..cell });
    }
    if nbr_species != Species::Empty && nbr_species != Species::Fungus && nbr_species != Species::Fire && nbr_species != Species::Ice {
        let (dx2, dy2) = api.rand_vec_8();
        if api.get(dx2, dy2).species == Species::Empty {
            let drift = (api.rand_int(100) % 15) as i32 - 7;
            api.set(
                dx2,
                dy2,
                Cell {
                    species: Species::Fungus,
                    ra: (cell.ra as i32 + drift).clamp(0, 255) as u8,
                    rb: 0,
                    clock: 0,
                },
            );
        }
    }
    if cell.rb > 1 {
        api.set(0, 0, Cell { rb: cell.rb - 1, ..cell });
    } else if cell.rb == 1 {
        api.set(0, 0, EMPTY_CELL);
    }
}

fn update_seed(cell: Cell, mut api: SandApi) {
    let (dx, dy) = api.rand_vec();
    let nbr_species = api.get(dx, dy).species;
    if nbr_species == Species::Fire || nbr_species == Species::Lava {
        api.set(0, 0, Cell { species: Species::Fire, ra: 5, rb: 0, clock: 0 });
        return;
    }
    if cell.rb == 0 {
        let dxf = api.rand_dir_2();
        let below = api.get(dxf, 1).species;
        if matches!(below, Species::Sand | Species::Plant | Species::Fungus) {
            api.set(0, 0, Cell { rb: (api.rand_int(253) + 1) as u8, ..cell });
            return;
        }
        let nbr = api.get(0, 1);
        if nbr.species == Species::Empty {
            api.set(0, 0, EMPTY_CELL);
            api.set(0, 1, cell);
        } else if api.get(dxf, 1).species == Species::Empty {
            api.set(0, 0, EMPTY_CELL);
            api.set(dxf, 1, cell);
        } else if matches!(nbr.species, Species::Water | Species::Gas | Species::Oil | Species::Acid) {
            api.set(0, 0, nbr);
            api.set(0, 1, cell);
        } else {
            api.set(0, 0, cell);
        }
    } else if nbr_species == Species::Water {
        api.set(dx, dy, Cell::new(Species::Seed));
    }
}

fn update_acid(cell: Cell, mut api: SandApi) {
    let dx = api.rand_dir_2();
    let mut degraded = cell;
    degraded.ra = cell.ra.saturating_sub(60);
    if degraded.ra < 80 {
        degraded = EMPTY_CELL;
    }
    if api.get(0, 1).species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(0, 1, cell);
    } else if api.get(dx, 0).species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(dx, 0, cell);
    } else if api.get(-dx, 0).species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(-dx, 0, cell);
    } else {
        let below = api.get(0, 1);
        let side = api.get(dx, 0);
        if below.species != Species::Wall && below.species != Species::Acid {
            api.set(0, 0, EMPTY_CELL);
            api.set(0, 1, degraded);
        } else if side.species != Species::Wall && side.species != Species::Acid {
            api.set(0, 0, EMPTY_CELL);
            api.set(dx, 0, degraded);
        } else {
            api.set(0, 0, cell);
        }
    }
}

fn update_mite(cell: Cell, mut api: SandApi) {
    let dx = if cell.ra < 20 { (cell.ra as i32) - 1 } else { 0 };
    let mut dy = 1;
    let mut mite = cell;
    if cell.rb > 10 {
        mite.rb = mite.rb.saturating_sub(1);
        dy = -1;
    } else if cell.rb > 1 {
        mite.rb = mite.rb.saturating_sub(1);
    }
    let nbr = api.get(dx, dy);
    let sx = (api.rand_int(100) % 3) - 1;
    let sy = (api.rand_int(1000) % 3) - 1;
    let sample = api.get(sx, sy).species;
    if matches!(sample, Species::Fire | Species::Lava | Species::Water | Species::Oil) {
        api.set(0, 0, EMPTY_CELL);
        return;
    }
    if (matches!(sample, Species::Plant | Species::Wood | Species::Seed)) && api.rand_int(1000) > 800 {
        api.set(0, 0, EMPTY_CELL);
        api.set(sx, sy, cell);
        return;
    }
    if sample == Species::Dust && api.rand_int(1000) > 200 {
        api.set(sx, sy, cell);
    }
    if nbr.species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(dx, dy, mite);
    } else {
        api.set(0, 0, mite);
    }
}

fn update_oil(cell: Cell, mut api: SandApi) {
    let (dx, _dy) = api.rand_vec();
    let nbr = api.get(dx, 0);
    let mut new_cell = cell;
    if cell.rb == 0
        && (nbr.species == Species::Fire
            || nbr.species == Species::Lava
            || (nbr.species == Species::Oil && nbr.rb > 1 && nbr.rb < 20))
    {
        new_cell = Cell { rb: 50, ..cell };
    }
    if cell.rb > 1 {
        new_cell = Cell { rb: cell.rb - 1, ..cell };
        if cell.rb % 4 != 0 && nbr.species == Species::Empty {
            api.set(
                dx,
                0,
                Cell {
                    species: Species::Fire,
                    ra: (20 + api.rand_int(30) as u8).min(255),
                    rb: 0,
                    clock: 0,
                },
            );
        }
        if nbr.species == Species::Water {
            new_cell = Cell { ra: 50, rb: 0, ..cell };
        }
    } else if cell.rb == 1 {
        api.set(0, 0, EMPTY_CELL);
        return;
    }
    if api.get(0, 1).species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(0, 1, new_cell);
    } else if api.get(dx, 1).species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(dx, 1, new_cell);
    } else if api.get(-dx, 1).species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(-dx, 1, new_cell);
    } else if api.get(dx, 0).species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(dx, 0, new_cell);
    } else if api.get(-dx, 0).species == Species::Empty {
        api.set(0, 0, EMPTY_CELL);
        api.set(-dx, 0, new_cell);
    } else {
        api.set(0, 0, new_cell);
    }
}
