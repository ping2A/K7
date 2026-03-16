//! Integration tests for the K7 public API.
//! Exercises full drawing and state flows without relying on internals.

use k7::{Screen, Sprite};
use k7::constants::{SCREEN_WIDTH, SCREEN_HEIGHT, SPRITE_COUNT};

fn screen_with_sprites() -> Screen {
    let mut s = Screen::new(SCREEN_WIDTH, SCREEN_HEIGHT);
    while s.sprites.len() < SPRITE_COUNT {
        s.sprites.push(Sprite::new());
    }
    s
}

#[test]
fn full_draw_sequence() {
    let mut s = screen_with_sprites();
    s.cls(0);
    s.color(1);
    s.pset(1, 1, -1);
    assert_eq!(s.pget(1, 1), 1);
    s.rectfill(10, 10, 50, 50, 2);
    s.rect(60, 60, 80, 80, 3);
    s.line(0, 100, 50, 100, 4);
    s.camera(0, 0);
    s.clip(-1, -1, -1, -1);
    assert_eq!(s.pget(30, 30), 2);
    assert_eq!(s.pget(70, 60), 3);
    assert_eq!(s.pget(25, 100), 4);
}

#[test]
fn map_and_map_draw_roundtrip() {
    let mut s = screen_with_sprites();
    for i in 0..16 {
        s.sprites[i].set(0, 0, i as u8);
    }
    s.cls(0);
    for y in 0..4i32 {
        for x in 0..4i32 {
            s.mset(x, y, (y * 4 + x) as u8);
        }
    }
    s.map_draw(0, 0, 0, 0, 4, 4);
    assert_eq!(s.pget(0, 0), 0);
    assert_eq!(s.pget(8, 0), 1);
    assert_eq!(s.pget(0, 8), 4);
}

#[test]
fn sprite_sheet_coords() {
    let mut s = screen_with_sprites();
    s.sset(0, 0, 1);
    s.sset(8, 0, 2);
    s.sset(0, 8, 3);
    assert_eq!(s.sget(0, 0), 1);
    assert_eq!(s.sget(8, 0), 2);
    assert_eq!(s.sget(0, 8), 3);
}
