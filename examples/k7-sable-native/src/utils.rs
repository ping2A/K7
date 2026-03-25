//! Direction helpers for Rocket etc. (from PikuseruConsole/Sable)

pub fn adjacency_right(dir: (i32, i32)) -> (i32, i32) {
    match dir {
        (0, 1) => (1, 1),
        (1, 1) => (1, 0),
        (1, 0) => (1, -1),
        (1, -1) => (0, -1),
        (0, -1) => (-1, -1),
        (-1, -1) => (-1, 0),
        (-1, 0) => (-1, 1),
        (-1, 1) => (0, 1),
        _ => (0, 0),
    }
}

pub fn adjacency_left(dir: (i32, i32)) -> (i32, i32) {
    match dir {
        (0, 1) => (-1, 1),
        (1, 1) => (0, 1),
        (1, 0) => (1, 1),
        (1, -1) => (1, 0),
        (0, -1) => (1, -1),
        (-1, -1) => (0, -1),
        (-1, 0) => (-1, -1),
        (-1, 1) => (-1, 0),
        _ => (0, 0),
    }
}

pub fn join_dy_dx(dx: i32, dy: i32) -> u8 {
    (((dx + 1) * 3) + (dy + 1)) as u8
}

pub fn split_dy_dx(s: u8) -> (i32, i32) {
    let s = s as i32;
    let dx = (s / 3) - 1;
    let dy = (s % 3) - 1;
    (dx, dy)
}
