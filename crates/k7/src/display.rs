//! Display: 256×256 pixel buffer, 8-bit palette + 32-bit RGBA API.

use crate::constants::PALETTE_SIZE;
use crate::palette::Palettes;
use crate::sprite::{Sprite, DynamicSprite};
use crate::map::{Map, FLAG_FLIP_X, FLAG_FLIP_Y, FLAG_ROTATE};
use crate::fonts::Font;

/// Screen buffer and drawing state.
/// Pixel buffer is stored as RGBA u8 (4 bytes per pixel) for easy use with pixels/GPU.
/// 8-bit drawing uses current palette to resolve to RGBA; pset_rgba writes directly.
pub struct Screen {
    pub width: u32,
    pub height: u32,
    /// RGBA buffer (width * height * 4)
    pub pixel_buffer: Vec<u8>,
    pub palettes: Palettes,
    pub current_palette: String,
    /// Resolved 16 colors from current palette (RGBA for fast lookup).
    palette_rgba: [u8; PALETTE_SIZE * 4],
    pub sprites: Vec<Sprite>,
    pub dynamic_sprites: Vec<DynamicSprite>,
    pub map: Map,
    /// Transparency: 0 = transparent when drawing sprites.
    pub transparency: [bool; 256],
    pub draw_color: u8,
    pub camera_x: i32,
    pub camera_y: i32,
    pub clip_left: i32,
    pub clip_top: i32,
    pub clip_right: i32,
    pub clip_bottom: i32,
    pub font: &'static Font,
}

impl Screen {
    pub fn new(width: u32, height: u32) -> Self {
        let size = (width * height * 4) as usize;
        let mut s = Self {
            width,
            height,
            pixel_buffer: vec![0; size],
            palettes: Palettes::new(),
            current_palette: "pico8".to_string(),
            palette_rgba: [0u8; PALETTE_SIZE * 4],
            sprites: Vec::new(),
            dynamic_sprites: Vec::new(),
            map: Map::new(),
            transparency: [false; 256],
            draw_color: 0,
            camera_x: 0,
            camera_y: 0,
            clip_left: 0,
            clip_top: 0,
            clip_right: width as i32,
            clip_bottom: height as i32,
            font: &crate::fonts::pico8::FONT,
        };
        s.transparency[0] = true;
        s.refresh_palette_rgba();
        s
    }

    fn refresh_palette_rgba(&mut self) {
        if let Some(pal) = self.palettes.get(&self.current_palette) {
            for i in 0..PALETTE_SIZE {
                let c = pal.get(i as u8);
                self.palette_rgba[i * 4] = c.r;
                self.palette_rgba[i * 4 + 1] = c.g;
                self.palette_rgba[i * 4 + 2] = c.b;
                self.palette_rgba[i * 4 + 3] = 255;
            }
        }
    }

    pub fn switch_palette(&mut self, name: &str) {
        if self.palettes.get(name).is_some() {
            self.current_palette = name.to_string();
            self.refresh_palette_rgba();
        }
    }

    pub fn set_palette_color(&mut self, index: u8, r: u8, g: u8, b: u8) {
        if let Some(pal) = self.palettes.get_mut(&self.current_palette) {
            pal.set(index, r, g, b);
            let i = index as usize % PALETTE_SIZE;
            self.palette_rgba[i * 4] = r;
            self.palette_rgba[i * 4 + 1] = g;
            self.palette_rgba[i * 4 + 2] = b;
            self.palette_rgba[i * 4 + 3] = 255;
        }
    }

    /// Swap two palette color entries (0..15). Useful for palette flash / swap effects.
    pub fn swap_palette_entries(&mut self, a: u8, b: u8) {
        if let Some(pal) = self.palettes.get_mut(&self.current_palette) {
            pal.swap(a, b);
            self.refresh_palette_rgba();
        }
    }

    fn in_clip(&self, x: i32, y: i32) -> bool {
        x >= self.clip_left && x < self.clip_right && y >= self.clip_top && y < self.clip_bottom
    }

    /// Resolve color: -1 means current draw_color.
    #[inline]
    fn find_color(&self, col: i32) -> u8 {
        if col >= 0 && col <= 255 {
            col as u8
        } else {
            self.draw_color
        }
    }

    /// Map RGBA to palette index (exact match or 0).
    fn rgba_to_palette_index(&self, r: u8, g: u8, b: u8) -> u8 {
        for i in 0..PALETTE_SIZE {
            if self.palette_rgba[i * 4] == r
                && self.palette_rgba[i * 4 + 1] == g
                && self.palette_rgba[i * 4 + 2] == b
            {
                return i as u8;
            }
        }
        0
    }

    fn buffer_index(&self, x: i32, y: i32) -> Option<usize> {
        if x < 0 || y < 0 || x >= self.width as i32 || y >= self.height as i32 {
            return None;
        }
        Some((y as u32 * self.width + x as u32) as usize * 4)
    }

    /// Clear screen with 8-bit color index.
    #[inline]
    pub fn cls(&mut self, col: u8) {
        let idx = col as usize % PALETTE_SIZE;
        let r = self.palette_rgba[idx * 4];
        let g = self.palette_rgba[idx * 4 + 1];
        let b = self.palette_rgba[idx * 4 + 2];
        let a = self.palette_rgba[idx * 4 + 3];
        let buf = &mut self.pixel_buffer[..];
        for chunk in buf.chunks_exact_mut(4) {
            chunk[0] = r;
            chunk[1] = g;
            chunk[2] = b;
            chunk[3] = a;
        }
    }

    /// Set pixel using 8-bit color index (current palette). Use -1 for current draw color.
    #[inline(always)]
    pub fn pset(&mut self, x: i32, y: i32, col: i32) {
        let c = self.find_color(col);
        self.pset_palette_index(x, y, c);
    }

    /// Set pixel using already-resolved palette index (no -1 handling). Used by line/hline/rectfill for speed.
    #[inline(always)]
    fn pset_palette_index(&mut self, x: i32, y: i32, col: u8) {
        let x = x + self.camera_x;
        let y = y + self.camera_y;
        if x < self.clip_left || x >= self.clip_right || y < self.clip_top || y >= self.clip_bottom {
            return;
        }
        if x >= 0 && y >= 0 && (x as u32) < self.width && (y as u32) < self.height {
            let i = (y as u32 * self.width + x as u32) as usize * 4;
            let idx = (col as usize) % PALETTE_SIZE;
            self.pixel_buffer[i] = self.palette_rgba[idx * 4];
            self.pixel_buffer[i + 1] = self.palette_rgba[idx * 4 + 1];
            self.pixel_buffer[i + 2] = self.palette_rgba[idx * 4 + 2];
            self.pixel_buffer[i + 3] = self.palette_rgba[idx * 4 + 3];
        }
    }

    /// Set pixel using 32-bit RGBA (for transparency and custom colors).
    pub fn pset_rgba(&mut self, x: i32, y: i32, r: u8, g: u8, b: u8, a: u8) {
        let x = x + self.camera_x;
        let y = y + self.camera_y;
        if !self.in_clip(x, y) {
            return;
        }
        if let Some(i) = self.buffer_index(x, y) {
            if a == 0 {
                return;
            }
            if a == 255 {
                self.pixel_buffer[i] = r;
                self.pixel_buffer[i + 1] = g;
                self.pixel_buffer[i + 2] = b;
                self.pixel_buffer[i + 3] = a;
            } else {
                let inv = (255 - a) as u32;
                self.pixel_buffer[i] = ((r as u32 * a as u32 + self.pixel_buffer[i] as u32 * inv) / 255) as u8;
                self.pixel_buffer[i + 1] = ((g as u32 * a as u32 + self.pixel_buffer[i + 1] as u32 * inv) / 255) as u8;
                self.pixel_buffer[i + 2] = ((b as u32 * a as u32 + self.pixel_buffer[i + 2] as u32 * inv) / 255) as u8;
                self.pixel_buffer[i + 3] = 255;
            }
        }
    }

    /// Draw a rectangle (filled) with 8-bit color.
    pub fn rectfill(&mut self, x0: i32, y0: i32, x1: i32, y1: i32, col: i32) {
        let (x0, x1) = (x0.min(x1), x0.max(x1));
        let (y0, y1) = (y0.min(y1), y0.max(y1));
        let c = self.find_color(col);
        let idx = (c as usize) % PALETTE_SIZE;
        let r = self.palette_rgba[idx * 4];
        let g = self.palette_rgba[idx * 4 + 1];
        let b = self.palette_rgba[idx * 4 + 2];
        let a = self.palette_rgba[idx * 4 + 3];
        let w_i = self.width as i32;
        let h_i = self.height as i32;
        for y in y0..=y1 {
            let y_scr = y + self.camera_y;
            if y_scr < self.clip_top || y_scr >= self.clip_bottom || y_scr < 0 || y_scr >= h_i {
                continue;
            }
            let row_start = (y_scr as u32 * self.width) as usize * 4;
            let x_start = (x0 + self.camera_x).max(self.clip_left).max(0);
            let x_end = (x1 + self.camera_x).min(self.clip_right - 1).min(w_i - 1);
            if x_start > x_end {
                continue;
            }
            let base = row_start + (x_start as usize) * 4;
            let count = (x_end - x_start + 1) as usize;
            let color = [r, g, b, a];
            for chunk in self.pixel_buffer[base..base + count * 4].chunks_exact_mut(4) {
                chunk.copy_from_slice(&color);
            }
        }
    }

    /// Fill rectangle with pre-resolved RGBA (world coords; camera applied inside). Used by spr for speed.
    #[inline(always)]
    fn fill_rect_rgba(&mut self, x0: i32, y0: i32, x1: i32, y1: i32, r: u8, g: u8, b: u8, a: u8) {
        let (x0, x1) = (x0.min(x1), x0.max(x1));
        let (y0, y1) = (y0.min(y1), y0.max(y1));
        let w_i = self.width as i32;
        let h_i = self.height as i32;
        let color = [r, g, b, a];
        for y in y0..=y1 {
            let y_scr = y + self.camera_y;
            if y_scr < self.clip_top || y_scr >= self.clip_bottom || y_scr < 0 || y_scr >= h_i {
                continue;
            }
            let row_start = (y_scr as u32 * self.width) as usize * 4;
            let x_start = (x0 + self.camera_x).max(self.clip_left).max(0);
            let x_end = (x1 + self.camera_x).min(self.clip_right - 1).min(w_i - 1);
            if x_start > x_end {
                continue;
            }
            let base = row_start + (x_start as usize) * 4;
            let count = (x_end - x_start + 1) as usize;
            for chunk in self.pixel_buffer[base..base + count * 4].chunks_exact_mut(4) {
                chunk.copy_from_slice(&color);
            }
        }
    }

    /// Draw sprite n (0..255) at (x,y). w,h in sprite units (1 = 8px). flip_x, flip_y, rotate 90° CW. scale: 1 = 8px per tile, 2 = 16px, etc.
    pub fn spr(
        &mut self,
        n: u32,
        x: i32,
        y: i32,
        w: i32,
        h: i32,
        flip_x: bool,
        flip_y: bool,
        scale: i32,
    ) {
        self.spr_rot(n, x, y, w, h, flip_x, flip_y, false, scale);
    }

    /// Draw sprite with optional 90° CW rotate (e.g. for map tile flags).
    pub fn spr_rot(
        &mut self,
        n: u32,
        x: i32,
        y: i32,
        w: i32,
        h: i32,
        flip_x: bool,
        flip_y: bool,
        rotate: bool,
        scale: i32,
    ) {
        let w = w.max(1);
        let h = h.max(1);
        let scale = scale.max(1);
        for sy in 0..h {
            for sx in 0..w {
                let idx = n.saturating_add((sy * 32 + sx) as u32);
                if (idx as usize) >= self.sprites.len() {
                    continue;
                }
                let dx = x + sx * 8 * scale;
                let dy = y + sy * 8 * scale;
                let mut tile = [[0u8; 8]; 8];
                for (py, row) in tile.iter_mut().enumerate() {
                    for (px, cell) in row.iter_mut().enumerate() {
                        let (sx_px, sy_py) = if rotate { (py, 7 - px) } else { (px, py) };
                        let sx_px = if flip_x { 7 - sx_px } else { sx_px };
                        let sy_py = if flip_y { 7 - sy_py } else { sy_py };
                        *cell = self.sprites[idx as usize].get(sx_px as u32, sy_py as u32);
                    }
                }
                for (py, row) in tile.iter().enumerate() {
                    for (px, &c) in row.iter().enumerate() {
                        if self.transparency[c as usize] {
                            continue;
                        }
                        let idx = (c as usize) % PALETTE_SIZE;
                        let r = self.palette_rgba[idx * 4];
                        let g = self.palette_rgba[idx * 4 + 1];
                        let b = self.palette_rgba[idx * 4 + 2];
                        let a = self.palette_rgba[idx * 4 + 3];
                        let px_i = px as i32;
                        let py_i = py as i32;
                        let x0 = dx + px_i * scale;
                        let y0 = dy + py_i * scale;
                        self.fill_rect_rgba(x0, y0, x0 + scale - 1, y0 + scale - 1, r, g, b, a);
                    }
                }
            }
        }
    }

    /// Draw map layer: draw map cells as sprites (uses tile flags: flip_x, flip_y, rotate).
    pub fn map_draw(&mut self, cell_x: i32, cell_y: i32, sx: i32, sy: i32, w: i32, h: i32) {
        for cy in 0..h {
            for cx in 0..w {
                let mx = cell_x + cx;
                let my = cell_y + cy;
                let cell = self.map.get(mx, my);
                let f = self.map.get_flags(mx, my);
                let flip_x = (f & FLAG_FLIP_X) != 0;
                let flip_y = (f & FLAG_FLIP_Y) != 0;
                let rotate = (f & FLAG_ROTATE) != 0;
                let px = sx + cx * 8;
                let py = sy + cy * 8;
                self.spr_rot(cell as u32, px, py, 1, 1, flip_x, flip_y, rotate, 1);
            }
        }
    }

    /// Print text at (x,y) with 8-bit color. Uses current font (pico8: 3×7, bbc: 7×8, etc.; 95 glyphs).
    /// Each glyph row is one byte, MSB = left pixel.
    pub fn print(&mut self, text: &str, x: i32, y: i32, col: i32) {
        let f = self.font;
        let mut cx = x;
        let rows_per_glyph = f.glyph_height as usize;
        for ch in text.chars() {
            let idx = ch as usize;
            if idx >= 32 && idx < 127 {
                let g = idx - 32; // 0..94
                let glyph_start = g * rows_per_glyph;
                for dy in 0..f.glyph_height {
                    if glyph_start + dy as usize >= f.glyph_data.len() {
                        break;
                    }
                    let row_byte = f.glyph_data[glyph_start + dy as usize];
                    for dx in 0..f.glyph_width {
                        // pico8: 3 pixels per row in bits 7, 6, 5 (MSB = left)
                        let bit = 7 - dx;
                        if (row_byte >> bit) & 1 != 0 {
                            self.pset(cx + dx, y + dy, col);
                        }
                    }
                }
            }
            cx += f.advance_width;
        }
    }

    /// Print text at (x,y) with 32-bit RGBA color (supports transparency and custom colors).
    pub fn print_rgba(&mut self, text: &str, x: i32, y: i32, r: u8, g: u8, b: u8, a: u8) {
        let f = self.font;
        let mut cx = x;
        let rows_per_glyph = f.glyph_height as usize;
        for ch in text.chars() {
            let idx = ch as usize;
            if idx >= 32 && idx < 127 {
                let g_idx = idx - 32;
                let glyph_start = g_idx * rows_per_glyph;
                for dy in 0..f.glyph_height {
                    if glyph_start + dy as usize >= f.glyph_data.len() {
                        break;
                    }
                    let row_byte = f.glyph_data[glyph_start + dy as usize];
                    for dx in 0..f.glyph_width {
                        let bit = 7 - dx;
                        if (row_byte >> bit) & 1 != 0 {
                            self.pset_rgba(cx + dx, y + dy, r, g, b, a);
                        }
                    }
                }
            }
            cx += f.advance_width;
        }
    }

    /// Set current font (e.g. from crate::fonts::get_font("bbc")).
    pub fn set_font(&mut self, font: &'static Font) {
        self.font = font;
    }

    /// Set current draw color (used when col is -1 in drawing functions).
    pub fn color(&mut self, col: i32) {
        if col >= 0 && col <= 255 {
            self.draw_color = col as u8;
        }
    }

    /// Set camera offset (all drawing is offset by camera).
    pub fn camera(&mut self, x: i32, y: i32) {
        self.camera_x = x;
        self.camera_y = y;
    }

    /// Set clip rectangle to (x,y,w,h) intersected with screen. Pass -1,-1,-1,-1 to reset to full screen.
    pub fn clip(&mut self, x: i32, y: i32, w: i32, h: i32) {
        if x == -1 && y == -1 && w == -1 && h == -1 {
            self.clip_left = 0;
            self.clip_top = 0;
            self.clip_right = self.width as i32;
            self.clip_bottom = self.height as i32;
            return;
        }
        let w_i = self.width as i32;
        let h_i = self.height as i32;
        self.clip_left = x.max(0).min(w_i);
        self.clip_top = y.max(0).min(h_i);
        self.clip_right = (x + w).max(0).min(w_i);
        self.clip_bottom = (y + h).max(0).min(h_i);
    }

    /// Get palette index at screen position (after camera).
    pub fn pget(&self, x: i32, y: i32) -> u8 {
        let x = x + self.camera_x;
        let y = y + self.camera_y;
        if let Some(i) = self.buffer_index(x, y) {
            let r = self.pixel_buffer[i];
            let g = self.pixel_buffer[i + 1];
            let b = self.pixel_buffer[i + 2];
            return self.rgba_to_palette_index(r, g, b);
        }
        0
    }

    /// Draw line from (x0,y0) to (x1,y1). Bresenham.
    pub fn line(&mut self, x0: i32, y0: i32, x1: i32, y1: i32, col: i32) {
        let c = self.find_color(col);
        let (mut x0, mut y0) = (x0, y0);
        let dx = (x1 - x0).abs();
        let sx = if x0 < x1 { 1 } else { -1 };
        let dy = -((y1 - y0).abs());
        let sy: i32 = if y0 < y1 { 1 } else { -1 };
        let mut err = dx + dy;
        loop {
            self.pset_palette_index(x0, y0, c);
            if x0 == x1 && y0 == y1 {
                break;
            }
            let e2 = 2 * err;
            if e2 >= dy {
                err += dy;
                x0 += sx;
            }
            if e2 <= dx {
                err += dx;
                y0 += sy;
            }
        }
    }

    /// Draw horizontal line (fast path: one row fill).
    pub fn hline(&mut self, x1: i32, x2: i32, y: i32, col: i32) {
        let c = self.find_color(col);
        let idx = (c as usize) % PALETTE_SIZE;
        let r = self.palette_rgba[idx * 4];
        let g = self.palette_rgba[idx * 4 + 1];
        let b = self.palette_rgba[idx * 4 + 2];
        let a = self.palette_rgba[idx * 4 + 3];
        let x_min = x1.min(x2) + self.camera_x;
        let x_max = x1.max(x2) + self.camera_x;
        let y_scr = y + self.camera_y;
        if y_scr < self.clip_top || y_scr >= self.clip_bottom || y_scr < 0 || (y_scr as u32) >= self.height {
            return;
        }
        let x_start = x_min.max(self.clip_left).max(0);
        let x_end = x_max.min(self.clip_right - 1).min(self.width as i32 - 1);
        if x_start > x_end {
            return;
        }
        let row_start = (y_scr as u32 * self.width) as usize * 4;
        let base = row_start + (x_start as usize) * 4;
        let count = (x_end - x_start + 1) as usize;
        let color = [r, g, b, a];
        for chunk in self.pixel_buffer[base..base + count * 4].chunks_exact_mut(4) {
            chunk.copy_from_slice(&color);
        }
    }

    /// Draw vertical line (fast path: one column fill).
    pub fn vline(&mut self, x: i32, y1: i32, y2: i32, col: i32) {
        let c = self.find_color(col);
        let idx = (c as usize) % PALETTE_SIZE;
        let r = self.palette_rgba[idx * 4];
        let g = self.palette_rgba[idx * 4 + 1];
        let b = self.palette_rgba[idx * 4 + 2];
        let a = self.palette_rgba[idx * 4 + 3];
        let x_scr = x + self.camera_x;
        let y_min = y1.min(y2) + self.camera_y;
        let y_max = y1.max(y2) + self.camera_y;
        if x_scr < self.clip_left || x_scr >= self.clip_right || x_scr < 0 || (x_scr as u32) >= self.width {
            return;
        }
        let y_start = y_min.max(self.clip_top).max(0);
        let y_end = y_max.min(self.clip_bottom - 1).min(self.height as i32 - 1);
        if y_start > y_end {
            return;
        }
        let col_off = (x_scr as u32 * 4) as usize;
        let color = [r, g, b, a];
        for y in y_start..=y_end {
            let base = (y as u32 * self.width * 4) as usize + col_off;
            self.pixel_buffer[base..base + 4].copy_from_slice(&color);
        }
    }

    /// Draw rectangle outline.
    pub fn rect(&mut self, x0: i32, y0: i32, x1: i32, y1: i32, col: i32) {
        let (x_min, x_max) = (x0.min(x1), x0.max(x1));
        let (y_min, y_max) = (y0.min(y1), y0.max(y1));
        self.hline(x_min, x_max, y_min, col);
        self.hline(x_min, x_max, y_max, col);
        if y_max - y_min > 1 {
            self.vline(x_min, y_min + 1, y_max - 1, col);
            self.vline(x_max, y_min + 1, y_max - 1, col);
        }
    }

    /// Draw square outline (side length h).
    pub fn square(&mut self, x0: i32, y0: i32, h: i32, col: i32) {
        self.rect(x0, y0, x0 + h, y0 + h, col);
    }

    /// Draw filled square.
    pub fn squarefill(&mut self, x0: i32, y0: i32, h: i32, col: i32) {
        self.rectfill(x0, y0, x0 + h, y0 + h, col);
    }

    /// Draw circle outline.
    pub fn circ(&mut self, x: i32, y: i32, r: i32, col: i32) {
        self.ellipse(x, y, r, r, col);
    }

    /// Draw filled circle.
    pub fn circfill(&mut self, x: i32, y: i32, r: i32, col: i32) {
        self.ellipsefill(x, y, r, r, col);
    }

    /// Draw ellipse outline (center x,y; radii rx, ry). SDL2 gfx-style.
    pub fn ellipse(&mut self, x: i32, y: i32, rx: i32, ry: i32, col: i32) {
        if rx <= 0 || ry <= 0 {
            return;
        }
        let col = self.find_color(col);
        let mut h: i32;
        let mut i: i32;
        let mut j: i32;
        let mut k: i32;
        let mut ok: i32 = 0xFFFF;
        let mut oj: i32 = 0xFFFF;
        let mut oh: i32 = 0xFFFF;
        let mut oi: i32 = 0xFFFF;
        let mut ix: i32;
        let mut iy: i32;
        let mut xmi: i32;
        let mut xpi: i32;
        let mut xmj: i32;
        let mut xpj: i32;
        let mut ymi: i32;
        let mut ypi: i32;
        let mut xmk: i32;
        let mut xpk: i32;
        let mut ymh: i32;
        let mut yph: i32;
        let mut ymj: i32;
        let mut ypj: i32;
        let mut xmh: i32;
        let mut xph: i32;
        let mut ymk: i32;
        let mut ypk: i32;
        if rx > ry {
            ix = 0;
            iy = rx * 64;
            h = (ix + 32) >> 6;
            i = (iy + 32) >> 6;
            while i > h {
                h = (ix + 32) >> 6;
                i = (iy + 32) >> 6;
                j = (h * ry) / rx;
                k = (i * ry) / rx;
                if ((ok != k) && (oj != k)) || ((oj != j) && (ok != j)) || (k != j) {
                    xph = x + h;
                    xmh = x - h;
                    if k > 0 {
                        ypk = y + k;
                        ymk = y - k;
                        self.pset(xmh, ypk, col as i32);
                        self.pset(xph, ypk, col as i32);
                        self.pset(xmh, ymk, col as i32);
                        self.pset(xph, ymk, col as i32);
                    } else {
                        self.pset(xmh, y, col as i32);
                        self.pset(xph, y, col as i32);
                    }
                    ok = k;
                    xpi = x + i;
                    xmi = x - i;
                    if j > 0 {
                        ypj = y + j;
                        ymj = y - j;
                        self.pset(xmi, ypj, col as i32);
                        self.pset(xpi, ypj, col as i32);
                        self.pset(xmi, ymj, col as i32);
                        self.pset(xpi, ymj, col as i32);
                    } else {
                        self.pset(xmi, y, col as i32);
                        self.pset(xpi, y, col as i32);
                    }
                    oj = j;
                }
                ix += iy / rx;
                iy -= ix / rx;
            }
        } else {
            ix = 0;
            iy = ry * 64;
            h = (ix + 32) >> 6;
            i = (iy + 32) >> 6;
            while i > h {
                h = (ix + 32) >> 6;
                i = (iy + 32) >> 6;
                j = (h * rx) / ry;
                k = (i * rx) / ry;
                if ((oi != i) && (oh != i)) || ((oh != h) && (oi != h) && (i != h)) {
                    xmj = x - j;
                    xpj = x + j;
                    if i > 0 {
                        ypi = y + i;
                        ymi = y - i;
                        self.pset(xmj, ypi, col as i32);
                        self.pset(xpj, ypi, col as i32);
                        self.pset(xmj, ymi, col as i32);
                        self.pset(xpj, ymi, col as i32);
                    } else {
                        self.pset(xmj, y, col as i32);
                        self.pset(xpj, y, col as i32);
                    }
                    oi = i;
                    xmk = x - k;
                    xpk = x + k;
                    if h > 0 {
                        yph = y + h;
                        ymh = y - h;
                        self.pset(xmk, yph, col as i32);
                        self.pset(xpk, yph, col as i32);
                        self.pset(xmk, ymh, col as i32);
                        self.pset(xpk, ymh, col as i32);
                    } else {
                        self.pset(xmk, y, col as i32);
                        self.pset(xpk, y, col as i32);
                    }
                    oh = h;
                }
                ix += iy / ry;
                iy -= ix / ry;
            }
        }
    }

    /// Draw filled ellipse.
    pub fn ellipsefill(&mut self, x: i32, y: i32, rx: i32, ry: i32, col: i32) {
        if rx <= 0 || ry <= 0 {
            return;
        }
        let col = self.find_color(col);
        let mut h: i32;
        let mut i: i32;
        let mut j: i32;
        let mut k: i32;
        let mut ok: i32 = 0xFFFF;
        let mut oj: i32 = 0xFFFF;
        let mut oh: i32 = 0xFFFF;
        let mut oi: i32 = 0xFFFF;
        let mut ix: i32;
        let mut iy: i32;
        let mut xmi: i32;
        let mut xpi: i32;
        let mut xmj: i32;
        let mut xpj: i32;
        let mut xmh: i32;
        let mut xph: i32;
        let mut xmk: i32;
        let mut xpk: i32;
        if rx > ry {
            ix = 0;
            iy = rx * 64;
            h = (ix + 32) >> 6;
            i = (iy + 32) >> 6;
            while i > h {
                h = (ix + 32) >> 6;
                i = (iy + 32) >> 6;
                j = (h * ry) / rx;
                k = (i * ry) / rx;
                if (ok != k) && (oj != k) {
                    xph = x + h;
                    xmh = x - h;
                    if k > 0 {
                        self.hline(xmh, xph, y + k, col as i32);
                        self.hline(xmh, xph, y - k, col as i32);
                    } else {
                        self.hline(xmh, xph, y, col as i32);
                    }
                    ok = k;
                }
                if (oj != j) && (ok != j) && (k != j) {
                    xmi = x - i;
                    xpi = x + i;
                    if j > 0 {
                        self.hline(xmi, xpi, y + j, col as i32);
                        self.hline(xmi, xpi, y - j, col as i32);
                    } else {
                        self.hline(xmi, xpi, y, col as i32);
                    }
                    oj = j;
                }
                ix += iy / rx;
                iy -= ix / rx;
            }
        } else {
            ix = 0;
            iy = ry * 64;
            h = (ix + 32) >> 6;
            i = (iy + 32) >> 6;
            while i > h {
                h = (ix + 32) >> 6;
                i = (iy + 32) >> 6;
                j = (h * rx) / ry;
                k = (i * rx) / ry;
                if (oi != i) && (oh != i) {
                    xmj = x - j;
                    xpj = x + j;
                    if i > 0 {
                        self.hline(xmj, xpj, y + i, col as i32);
                        self.hline(xmj, xpj, y - i, col as i32);
                    } else {
                        self.hline(xmj, xpj, y, col as i32);
                    }
                    oi = i;
                }
                if (oh != h) && (oi != h) && (i != h) {
                    xmk = x - k;
                    xpk = x + k;
                    if h > 0 {
                        self.hline(xmk, xpk, y + h, col as i32);
                        self.hline(xmk, xpk, y - h, col as i32);
                    } else {
                        self.hline(xmk, xpk, y, col as i32);
                    }
                    oh = h;
                }
                ix += iy / ry;
                iy -= ix / ry;
            }
        }
    }

    /// Draw triangle outline.
    pub fn trigon(&mut self, x1: i32, y1: i32, x2: i32, y2: i32, x3: i32, y3: i32, col: i32) {
        self.line(x1, y1, x2, y2, col);
        self.line(x2, y2, x3, y3, col);
        self.line(x3, y3, x1, y1, col);
    }

    /// Draw polygon outline (line between consecutive points and close with first).
    pub fn polygon(&mut self, vx: &[i32], vy: &[i32], col: i32) {
        if vx.len() < 3 || vy.len() < 3 || vx.len() != vy.len() {
            return;
        }
        let n = vx.len();
        for i in 0..n - 1 {
            self.line(vx[i], vy[i], vx[i + 1], vy[i + 1], col);
        }
        self.line(vx[n - 1], vy[n - 1], vx[0], vy[0], col);
    }

    /// Get sprite pixel at sheet coordinates (pixels). Sprite sheet is 32 sprites per row.
    pub fn sget(&self, x: i32, y: i32) -> u8 {
        if x < 0 || y < 0 {
            return 0;
        }
        let sx = (x / 8) as u32;
        let sy = (y / 8) as u32;
        let idx = sx + 32 * sy;
        if (idx as usize) >= self.sprites.len() {
            return 0;
        }
        self.sprites[idx as usize].get((x % 8) as u32, (y % 8) as u32)
    }

    /// Set sprite pixel at sheet coordinates.
    pub fn sset(&mut self, x: i32, y: i32, col: i32) {
        if x < 0 || y < 0 {
            return;
        }
        let sx = (x / 8) as u32;
        let sy = (y / 8) as u32;
        let idx = sx + 32 * sy;
        if (idx as usize) < self.sprites.len() {
            let c = self.find_color(col);
            self.sprites[idx as usize].set((x % 8) as u32, (y % 8) as u32, c);
        }
    }

    /// Get map cell at (x, y) in cell coordinates.
    pub fn mget(&self, x: i32, y: i32) -> u8 {
        self.map.get(x, y)
    }

    /// Set map cell at (x, y).
    pub fn mset(&mut self, x: i32, y: i32, v: u8) {
        self.map.set(x, y, v);
    }

    /// Get map tile flags at (x, y). Bits: 1=flip_x, 2=flip_y, 4=rotate 90° CW.
    pub fn mget_flags(&self, x: i32, y: i32) -> u8 {
        self.map.get_flags(x, y)
    }

    /// Set map tile flags at (x, y). Bits: 1=flip_x, 2=flip_y, 4=rotate.
    pub fn mset_flags(&mut self, x: i32, y: i32, f: u8) {
        self.map.set_flags(x, y, f);
    }

    /// Resize internal buffer (e.g. for customizable screen size). Keeps aspect or stretches.
    pub fn resize(&mut self, width: u32, height: u32) {
        self.width = width;
        self.height = height;
        self.clip_right = width as i32;
        self.clip_bottom = height as i32;
        self.pixel_buffer.resize((width * height * 4) as usize, 0);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::{SCREEN_WIDTH, SCREEN_HEIGHT, SPRITE_COUNT};
    use crate::sprite::Sprite;

    fn screen_with_sprites() -> Screen {
        let mut s = Screen::new(SCREEN_WIDTH, SCREEN_HEIGHT);
        while s.sprites.len() < SPRITE_COUNT {
            s.sprites.push(Sprite::new());
        }
        s
    }

    #[test]
    fn screen_cls_fills_with_color() {
        let mut s = screen_with_sprites();
        s.cls(5);
        assert_eq!(s.pget(0, 0), 5);
        assert_eq!(s.pget(100, 100), 5);
        assert_eq!(s.pget(255, 255), 5);
    }

    #[test]
    fn screen_pset_pget() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.pset(10, 20, 3);
        assert_eq!(s.pget(10, 20), 3);
        s.pset(0, 0, 15);
        assert_eq!(s.pget(0, 0), 15);
    }

    #[test]
    fn screen_pset_out_of_bounds_no_panic() {
        let mut s = screen_with_sprites();
        s.pset(-1, 0, 1);
        s.pset(0, -1, 1);
        s.pset(256, 0, 1);
        s.pset(0, 256, 1);
    }

    #[test]
    fn screen_color_minus_one_uses_draw_color() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.color(7);
        s.pset(5, 5, -1);
        assert_eq!(s.pget(5, 5), 7);
    }

    #[test]
    fn screen_rectfill() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.rectfill(10, 10, 30, 25, 4);
        assert_eq!(s.pget(10, 10), 4);
        assert_eq!(s.pget(30, 25), 4);
        assert_eq!(s.pget(20, 17), 4);
        assert_eq!(s.pget(9, 10), 0);
        assert_eq!(s.pget(31, 25), 0);
    }

    #[test]
    fn screen_rectfill_swapped_coords() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.rectfill(30, 25, 10, 10, 2);
        assert_eq!(s.pget(10, 10), 2);
        assert_eq!(s.pget(30, 25), 2);
    }

    #[test]
    fn screen_rect_outline() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.rect(5, 5, 15, 12, 1);
        assert_eq!(s.pget(5, 5), 1);
        assert_eq!(s.pget(15, 5), 1);
        assert_eq!(s.pget(5, 12), 1);
        assert_eq!(s.pget(15, 12), 1);
        assert_eq!(s.pget(5, 8), 1);
        assert_eq!(s.pget(15, 8), 1);
        assert_eq!(s.pget(10, 8), 0);
        assert_eq!(s.pget(10, 10), 0);
    }

    #[test]
    fn screen_line() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.line(0, 0, 10, 0, 1);
        for x in 0..=10 {
            assert_eq!(s.pget(x, 0), 1, "hline at x={}", x);
        }
        s.cls(0);
        s.line(5, 5, 5, 15, 2);
        for y in 5..=15 {
            assert_eq!(s.pget(5, y), 2, "vline at y={}", y);
        }
    }

    #[test]
    fn screen_camera_offset() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.camera(10, 20);
        s.pset(0, 0, 1);
        assert_eq!(s.pget(0, 0), 1);
        s.camera(0, 0);
    }

    #[test]
    fn screen_clip() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.clip(10, 10, 20, 20);
        s.pset(5, 5, 1);
        s.pset(15, 15, 1);
        assert_eq!(s.pget(5, 5), 0);
        assert_eq!(s.pget(15, 15), 1);
        s.clip(-1, -1, -1, -1);
        s.pset(5, 5, 2);
        assert_eq!(s.pget(5, 5), 2);
    }

    #[test]
    fn screen_circfill_center() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.circfill(20, 20, 5, 3);
        assert_eq!(s.pget(20, 20), 3);
        assert_eq!(s.pget(25, 20), 3);
        assert_eq!(s.pget(15, 20), 3);
    }

    #[test]
    fn screen_sget_sset() {
        let mut s = screen_with_sprites();
        s.sset(0, 0, 5);
        assert_eq!(s.sget(0, 0), 5);
        s.sset(7, 7, 15);
        assert_eq!(s.sget(7, 7), 15);
        s.sset(8, 0, 1);
        assert_eq!(s.sget(8, 0), 1);
    }

    #[test]
    fn screen_sget_out_of_bounds_returns_zero() {
        let s = screen_with_sprites();
        assert_eq!(s.sget(-1, 0), 0);
        assert_eq!(s.sget(0, -1), 0);
    }

    #[test]
    fn screen_spr_draws_non_transparent() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.sprites[0].set(0, 0, 1);
        s.sprites[0].set(1, 0, 2);
        s.spr(0, 0, 0, 1, 1, false, false, 1);
        assert_eq!(s.pget(0, 0), 1);
        assert_eq!(s.pget(1, 0), 2);
    }

    #[test]
    fn screen_spr_transparent_skipped() {
        let mut s = screen_with_sprites();
        s.cls(3);
        s.sprites[0].set(0, 0, 0);
        s.sprites[0].set(1, 0, 1);
        s.spr(0, 0, 0, 1, 1, false, false, 1);
        assert_eq!(s.pget(0, 0), 3);
        assert_eq!(s.pget(1, 0), 1);
    }

    #[test]
    fn screen_mget_mset() {
        let mut s = screen_with_sprites();
        assert_eq!(s.mget(0, 0), 0);
        s.mset(0, 0, 10);
        s.mset(100, 5, 255);
        assert_eq!(s.mget(0, 0), 10);
        assert_eq!(s.mget(100, 5), 255);
    }

    #[test]
    fn screen_map_draw_uses_cells() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.sprites[1].set(0, 0, 7);
        s.mset(0, 0, 1);
        s.map_draw(0, 0, 0, 0, 1, 1);
        assert_eq!(s.pget(0, 0), 7);
    }

    #[test]
    fn screen_swap_palette_entries() {
        let mut s = screen_with_sprites();
        s.cls(1);
        assert_eq!(s.pget(0, 0), 1);
        s.swap_palette_entries(0, 1);
        s.cls(1);
        assert_eq!(s.pget(0, 0), 1);
        s.cls(0);
        assert_eq!(s.pget(0, 0), 0);
    }

    #[test]
    fn screen_print_places_pixels() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.print("A", 0, 0, 1);
        assert_eq!(s.pget(0, 0), 1);
    }

    #[test]
    fn screen_circ_zero_radius_no_panic() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.circ(10, 10, 0, 1);
        s.circfill(20, 20, 0, 1);
        assert_eq!(s.pget(10, 10), 0);
        assert_eq!(s.pget(20, 20), 0);
    }

    #[test]
    fn screen_rectfill_zero_size_no_panic() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.rectfill(10, 10, 10, 10, 1);
        assert_eq!(s.pget(10, 10), 1);
    }

    #[test]
    fn screen_spr_flip_x() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.sprites[0].set(0, 0, 1);
        s.sprites[0].set(7, 0, 2);
        s.spr(0, 0, 0, 1, 1, true, false, 1);
        assert_eq!(s.pget(0, 0), 2);
        assert_eq!(s.pget(7, 0), 1);
    }

    #[test]
    fn screen_spr_flip_y() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.sprites[0].set(0, 0, 1);
        s.sprites[0].set(0, 7, 2);
        s.spr(0, 0, 0, 1, 1, false, true, 1);
        assert_eq!(s.pget(0, 0), 2);
        assert_eq!(s.pget(0, 7), 1);
    }

    #[test]
    fn screen_map_draw_out_of_range_cell_uses_zero() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.map_draw(-1, -1, 0, 0, 2, 2);
        s.map_draw(255, 31, 0, 0, 1, 1);
        assert_eq!(s.pget(0, 0), 0);
    }

    #[test]
    fn screen_resize() {
        let mut s = screen_with_sprites();
        s.resize(64, 64);
        assert_eq!(s.width, 64);
        assert_eq!(s.height, 64);
        assert_eq!(s.pixel_buffer.len(), 64 * 64 * 4);
        s.cls(2);
        assert_eq!(s.pget(0, 0), 2);
    }

    #[test]
    fn screen_hline() {
        let mut s = screen_with_sprites();
        s.cls(0);
        s.hline(5, 15, 10, 1);
        for x in 5..=15 {
            assert_eq!(s.pget(x, 10), 1);
        }
        assert_eq!(s.pget(4, 10), 0);
        assert_eq!(s.pget(16, 10), 0);
    }

    #[test]
    fn screen_pget_out_of_bounds_returns_zero() {
        let s = screen_with_sprites();
        assert_eq!(s.pget(-1, 0), 0);
        assert_eq!(s.pget(0, -1), 0);
        assert_eq!(s.pget(256, 0), 0);
        assert_eq!(s.pget(0, 256), 0);
    }
}
