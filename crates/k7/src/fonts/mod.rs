//! Predefined fonts: pico8, bbc, appleii, cbmii, trollmini.

pub mod pico8;
pub mod bbc;
pub mod appleii;
pub mod cbmii;
pub mod trollmini;

#[derive(Debug)]
pub struct Font {
    pub glyph_width: i32,
    pub glyph_height: i32,
    pub left_bearing: i32,
    pub top_bearing: i32,
    pub advance_width: i32,
    pub line_height: i32,
    pub glyph_data: &'static [u8],
    pub name: &'static str,
}

/// Font registry: pico8, bbc, appleii, cbmii, trollmini. Default = pico8.
pub fn get_font(name: &str) -> Option<&'static Font> {
    match name {
        "pico8" | "pico-8" => Some(&pico8::FONT),
        "bbc" => Some(&bbc::FONT),
        "appleii" | "apple_ii" => Some(&appleii::FONT),
        "cbmii" | "cbm_ii" => Some(&cbmii::FONT),
        "trollmini" => Some(&trollmini::FONT),
        _ => None,
    }
}
