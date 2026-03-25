//! Parse melody notation with waveform and effects (from survie tracker).
//! Format: "c4 d4 e4" or "c4:sine|reverb:small d4:tri|lp:warm"
//! Instruments: "c4:piano:bright" expands to waveform+effects (survie-style).
//! DMG-style: `dmgwave(32 hex nibbles)`, `dmgnoise15`, `dmgnoise7`, `dmgnoise15(d,shift)`,
//! `dmgpulse1(duty)` or `dmgpulse1(duty,pace,shift,subtract)`.

use std::time::Duration;

use super::dmg;

/// Instrument presets: category:preset -> expansion (Survie-style, 34 categories, 110+ presets).
fn get_instrument_expansion(category: &str, preset: &str) -> Option<&'static str> {
    let c = category.to_lowercase();
    let p = preset.to_lowercase();
    match c.as_str() {
        "piano" => match p.as_str() {
            "bright" => Some("layer:sine:0.4,tri:0.3,sq:0.1|hp:bright|reverb:small"),
            "dark" => Some("layer:sine:0.5,tri:0.3|lp:warm|reverb:medium"),
            "electric" => Some("layer:sine:0.6,sq:0.2|chorus:subtle|reverb:small"),
            _ => None,
        },
        "guitar" => match p.as_str() {
            "acoustic" => Some("tri|hp:thin|chorus:subtle|reverb:small"),
            "electric" | "clean" => Some("tri|chorus:subtle|reverb:small"),
            "distorted" => Some("saw|dist:hard|lp:warm|reverb:medium"),
            _ => None,
        },
        "bass" => match p.as_str() {
            "soft" | "acoustic" => Some("tri|lp:warm|comp:bass"),
            "punch" | "electric" => Some("saw|lp:warm|comp:bass|dist:soft"),
            "synth" => Some("saw|lp:dark|comp:bass|dist:medium"),
            "slap" => Some("tri|hp:thin|comp:drum|dist:soft"),
            _ => None,
        },
        "lead" => match p.as_str() {
            "pulse" | "square" => Some("sq|vib:5:0.02|comp:medium|reverb:small"),
            "saw" | "bright" => Some("saw|lp:bright|vib:5:0.02|comp:medium|reverb:small"),
            "sine" => Some("sine|reverb:small"),
            _ => None,
        },
        "pad" => match p.as_str() {
            "strings" => Some("sine|envelope:pad|reverb:large"),
            "organ" => Some("sine|envelope:organ|reverb:medium"),
            "warm" => Some("layer:sine:0.5,tri:0.3|chorus:thick|reverb:hall"),
            "space" => Some("layer:sine:0.4,tri:0.3|chorus:thick|reverb:cathedral"),
            "dark" => Some("layer:tri:0.5,sine:0.3|lp:dark|reverb:hall"),
            _ => None,
        },
        "drums" => match p.as_str() {
            "kick" => Some("sine|envelope:perc"),
            "snare" | "hihat" => Some("noise|envelope:perc|hp:bright"),
            "hat" => Some("noise|envelope:perc|hp:bright"),
            "tom" => Some("noise|lp:warm|comp:drum"),
            _ => None,
        },
        "strings" => match p.as_str() {
            "violin" => Some("layer:sine:0.5,tri:0.3|vib:5:0.015|reverb:hall"),
            "cello" => Some("layer:tri:0.6,sine:0.3|lp:warm|vib:4:0.01|reverb:hall"),
            "ensemble" => Some("layer:sine:0.4,tri:0.3|chorus:thick|reverb:hall"),
            _ => None,
        },
        "organ" => match p.as_str() {
            "church" => Some("layer:sine:0.4,sq:0.3,tri:0.2|reverb:cathedral"),
            "hammond" => Some("layer:sine:0.5,sq:0.3|vib:6:0.015|chorus:thick"),
            "rock" => Some("sq|dist:medium|vib:5:0.02|reverb:medium"),
            _ => None,
        },
        "brass" => match p.as_str() {
            "trumpet" => Some("layer:sq:0.5,saw:0.3|hp:bright|reverb:medium"),
            "horn" => Some("layer:sine:0.5,sq:0.2|lp:warm|reverb:hall"),
            "section" => Some("layer:sine:0.4,sq:0.3,tri:0.2|chorus:subtle|reverb:hall"),
            _ => None,
        },
        "woodwinds" => match p.as_str() {
            "flute" => Some("sine|vib:5:0.015|reverb:hall"),
            "sax" => Some("layer:sq:0.5,tri:0.3|vib:5:0.02|reverb:medium"),
            "clarinet" => Some("layer:sq:0.6,tri:0.2|vib:4:0.01|reverb:hall"),
            _ => None,
        },
        "arp" => match p.as_str() {
            "8bit" => Some("sq|bitcrush:nes|trem:16:0.5|reverb:small"),
            "trance" => Some("saw|lp:bright|trem:8:0.6|chorus:subtle|reverb:medium"),
            "ambient" => Some("layer:sine:0.5,tri:0.3|trem:2:0.4|chorus:thick|reverb:hall"),
            _ => None,
        },
        "pluck" => match p.as_str() {
            "soft" => Some("sine|envelope:pluck|reverb:small"),
            "bright" | "synth" => Some("saw|hp:bright|dist:soft|reverb:small"),
            "harp" => Some("layer:sine:0.6,tri:0.3|hp:thin|reverb:hall"),
            "bass" => Some("tri|lp:warm|dist:soft|comp:bass"),
            _ => None,
        },
        "bells" => match p.as_str() {
            "tubular" => Some("layer:sine:0.7,tri:0.2|hp:bright|reverb:cathedral"),
            "church" => Some("layer:sine:0.6,tri:0.3|reverb:cathedral"),
            "xylophone" => Some("layer:sine:0.6,sq:0.2|hp:bright|reverb:small"),
            "glockenspiel" => Some("sine|hp:bright|chorus:subtle|reverb:hall"),
            _ => None,
        },
        "asian" => match p.as_str() {
            "shamisen" => Some("tri|hp:thin|reverb:small"),
            "koto" => Some("layer:tri:0.5,sine:0.3|hp:thin|reverb:medium"),
            "erhu" => Some("layer:sine:0.5,tri:0.3|vib:6:0.025|reverb:hall"),
            "gamelan" => Some("layer:sine:0.4,sq:0.3,tri:0.2|hp:bright|reverb:hall"),
            _ => None,
        },
        "mideast" => match p.as_str() {
            "oud" => Some("tri|chorus:subtle|reverb:medium"),
            "sitar" => Some("layer:tri:0.5,sq:0.3|vib:7:0.03|reverb:hall"),
            "ney" => Some("sine|vib:5:0.02|reverb:large"),
            "duduk" => Some("layer:sine:0.6,tri:0.3|lp:warm|vib:3:0.015|reverb:hall"),
            _ => None,
        },
        "latin" => match p.as_str() {
            "marimba" => Some("layer:sine:0.6,tri:0.3|reverb:medium"),
            "steel" => Some("layer:sine:0.5,tri:0.3,sq:0.1|chorus:subtle|reverb:small"),
            "accordion" => Some("layer:sq:0.5,tri:0.3|vib:4:0.02|chorus:subtle|reverb:small"),
            "nylon" => Some("tri|chorus:subtle|reverb:small"),
            _ => None,
        },
        "perc" => match p.as_str() {
            "tambourine" => Some("pink|hp:bright|trem:10:0.5"),
            "shaker" => Some("pink|hp:bright|trem:15:0.6"),
            "cowbell" => Some("sq|hp:bright|dist:medium"),
            "conga" => Some("noise|lp:warm|comp:drum"),
            "bongo" => Some("noise|comp:drum"),
            "clap" => Some("pink|hp:bright|reverb:small"),
            _ => None,
        },
        "edrums" => match p.as_str() {
            "808" => Some("sine|comp:limiter|dist:soft"),
            "909" => Some("noise|hp:bright|comp:drum|dist:medium"),
            "trap" => Some("noise|lp:dark|comp:limiter|dist:hard"),
            "dnb" => Some("noise|hp:bright|comp:drum|dist:hard|reverb:small"),
            _ => None,
        },
        "chip" => match p.as_str() {
            "pulse" => Some("sq|bitcrush:nes"),
            "tri" | "triangle" => Some("tri|bitcrush:nes"),
            "noise" => Some("noise|bitcrush:nes|hp:bright"),
            "c64" => Some("pwm:0.25|bitcrush:6|vib:6:0.02"),
            "gameboy" | "gb" => Some("sq|bitcrush:gameboy"),
            _ => None,
        },
        "vintage" => match p.as_str() {
            "musicbox" => Some("layer:sine:0.7,tri:0.2|reverb:small"),
            "celesta" => Some("layer:sine:0.7,tri:0.2|hp:bright|reverb:hall"),
            "harpsichord" => Some("tri|hp:bright|reverb:small"),
            "mellotron" => Some("layer:sine:0.5,tri:0.4|chorus:thick|reverb:hall"),
            _ => None,
        },
        "impact" => match p.as_str() {
            "cinematic" => Some("noise|lp:dark|comp:limiter|dist:hard|reverb:hall"),
            "hit" => Some("noise|lp:warm|comp:limiter|dist:medium"),
            "boom" => Some("noise|lp:dark|comp:limiter|reverb:large"),
            "stab" => Some("noise|hp:bright|comp:drum|dist:hard"),
            _ => None,
        },
        "riser" => match p.as_str() {
            "tension" => Some("pink|lp:warm|trem:1:0.3|reverb:large"),
            "epic" => Some("layer:pink:0.5,saw:0.3|lp:warm|reverb:cathedral"),
            "sweep" => Some("pink|hp:thin|chorus:thick|reverb:hall"),
            _ => None,
        },
        "whoosh" => match p.as_str() {
            "fast" => Some("pink|hp:bright|reverb:medium"),
            "slow" => Some("pink|lp:warm|chorus:thick|reverb:large"),
            "reverse" => Some("pink|hp:thin|reverb:hall"),
            _ => None,
        },
        "banjo" => match p.as_str() {
            "bluegrass" => Some("tri|hp:thin|chorus:subtle|reverb:small"),
            "clawhammer" => Some("tri|hp:bright|reverb:small"),
            _ => None,
        },
        "mandolin" => match p.as_str() {
            "folk" => Some("layer:tri:0.5,sine:0.3|hp:thin|chorus:subtle|reverb:small"),
            "tremolo" => Some("layer:tri:0.5,sine:0.3|trem:12:0.7|reverb:small"),
            _ => None,
        },
        "accordion" => match p.as_str() {
            "folk" => Some("layer:sq:0.5,tri:0.3|vib:4:0.02|reverb:small"),
            "tango" => Some("layer:sq:0.5,tri:0.3|vib:5:0.025|chorus:subtle|reverb:medium"),
            _ => None,
        },
        "harmonica" => match p.as_str() {
            "blues" => Some("layer:sq:0.5,tri:0.3|vib:4:0.02|reverb:medium"),
            "folk" => Some("layer:sq:0.5,sine:0.3|vib:3:0.015|reverb:small"),
            _ => None,
        },
        "timpani" => match p.as_str() {
            "orchestral" => Some("noise|lp:dark|comp:drum|reverb:hall"),
            "roll" => Some("noise|lp:dark|trem:8:0.6|comp:drum|reverb:hall"),
            _ => None,
        },
        "harp" => match p.as_str() {
            "orchestral" => Some("layer:sine:0.6,tri:0.3|hp:thin|chorus:subtle|reverb:hall"),
            "celtic" => Some("layer:sine:0.6,tri:0.3|hp:thin|reverb:medium"),
            _ => None,
        },
        "choir" => match p.as_str() {
            "epic" => Some("layer:sine:0.5,tri:0.3|chorus:thick|comp:vocal|reverb:cathedral"),
            "oohs" | "aahs" | "latin" => Some("layer:sine:0.6,tri:0.2|chorus:thick|reverb:cathedral"),
            _ => None,
        },
        "drone" => match p.as_str() {
            "dark" => Some("layer:sine:0.4,tri:0.3|lp:dark|reverb:cathedral"),
            "space" => Some("layer:sine:0.4,tri:0.3|chorus:thick|reverb:cathedral"),
            "warm" => Some("layer:sine:0.5,tri:0.3|lp:warm|chorus:thick|reverb:hall"),
            _ => None,
        },
        "texture" => match p.as_str() {
            "granular" => Some("pink|lp:warm|trem:3:0.5|chorus:thick|reverb:hall"),
            "shimmer" => Some("layer:sine:0.4,tri:0.3|chorus:thick|reverb:cathedral"),
            "noise" => Some("pink|lp:warm|chorus:thick|reverb:large"),
            _ => None,
        },
        "retro" => match p.as_str() {
            "powerup" => Some("sq|bitcrush:nes"),
            "coin" => Some("sine|bitcrush:nes|reverb:small"),
            "jump" => Some("tri|bitcrush:nes"),
            "death" => Some("sq|bitcrush:nes|dist:soft"),
            _ => None,
        },
        "scifi" => match p.as_str() {
            "laser" => Some("sq|chorus:subtle|reverb:small"),
            "computer" => Some("sq|bitcrush:8"),
            "alien" => Some("layer:sine:0.5,sq:0.3|vib:7:0.05|chorus:thick|reverb:large"),
            "warp" => Some("pink|lp:warm|chorus:thick|reverb:cathedral"),
            _ => None,
        },
        _ => None,
    }
}

/// Expand a single sound token: "c4:piano:bright" -> "c4:layer:sine:0.4,...|hp:bright|reverb:small".
/// If the token is not an instrument (note:category:preset), returns it unchanged.
pub fn expand_sound_token(token: &str) -> String {
    let token = token.trim();
    if token.is_empty() {
        return token.to_string();
    }
    let pipe_split: Vec<&str> = token.splitn(2, '|').collect();
    let note_part = pipe_split[0];
    let effects_suffix = pipe_split
        .get(1)
        .map(|s| format!("|{}", s))
        .unwrap_or_default();
    let note_colon: Vec<&str> = note_part.split(':').collect();
    if note_colon.len() >= 3 {
        let note_str = note_colon[0].trim();
        let category = note_colon[1];
        let preset = note_colon[2];
        if let Some(exp) = get_instrument_expansion(category, preset) {
            return format!("{}:{}", note_str, exp) + &effects_suffix;
        }
    }
    token.to_string() + &effects_suffix
}

/// Base waveform for layering (no Layered variant).
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum WaveformBase {
    Sine,
    Square,
    Triangle,
    Sawtooth,
    Pwm(f32),
    Noise,
    PinkNoise,
}

impl WaveformBase {
    pub fn from_str(s: &str) -> Option<Self> {
        let s = s.to_lowercase();
        if s.starts_with("pwm") {
            let parts: Vec<&str> = s.split(':').collect();
            let w: f32 = parts.get(1).and_then(|p| p.parse().ok()).unwrap_or(0.5);
            return Some(WaveformBase::Pwm(w.clamp(0.1, 0.9)));
        }
        match s.as_str() {
            "sine" | "sin" | "tone" => Some(WaveformBase::Sine),
            "square" | "sq" | "beep" => Some(WaveformBase::Square),
            "triangle" | "tri" => Some(WaveformBase::Triangle),
            "sawtooth" | "saw" => Some(WaveformBase::Sawtooth),
            "noise" | "white" => Some(WaveformBase::Noise),
            "pink" | "pinknoise" | "pink_noise" => Some(WaveformBase::PinkNoise),
            _ => None,
        }
    }
}

/// Waveform for a note (single or layered).
#[derive(Debug, Clone, PartialEq)]
pub enum Waveform {
    Sine,
    Square,
    Triangle,
    Sawtooth,
    Pwm(f32),
    Noise,
    PinkNoise,
    /// Game Boy CH3: 16 bytes wave RAM; `output_shift` NR32 0–3 (0=mute, 1=100%, 2=50%, 3=25%).
    DmgWave {
        ram: [u8; 16],
        output_shift: u8,
    },
    /// CH3 wave from `AudioEngine` cart entry (set via host `set_dmg_wave_cart_hexes`).
    DmgWaveCart {
        index: usize,
        output_shift: u8,
    },
    /// CH4 LFSR; `nr43` None = pick divider/shift from note frequency; `seven_bit` = NR43 bit 3.
    DmgNoise {
        nr43: Option<u8>,
        seven_bit: bool,
    },
    /// CH1 pulse + sweep (`subtract` = NR10 direction bit: subtraction vs addition).
    DmgPulse1 {
        duty: u8,
        sweep_pace: u8,
        sweep_shift: u8,
        sweep_subtract: bool,
    },
    /// CH2-style pulse (no sweep).
    DmgPulse2 {
        duty: u8,
    },
    Layered(Vec<(WaveformBase, f32)>),
}

fn strip_paren_content<'a>(prefix: &'a str, s: &'a str) -> Option<&'a str> {
    let rest = s.strip_prefix(prefix)?;
    let end = rest.rfind(')')?;
    Some(&rest[..end])
}

/// `dmgwave(HEX)` or `dmgwave(HEX,level)` with level 0–3 (NR32).
fn parse_dmgwave_ram_and_level(inner: &str) -> Option<([u8; 16], u8)> {
    let inner = inner.trim();
    if let Some((hex, lvl_s)) = inner.rsplit_once(',') {
        if let Ok(lvl) = lvl_s.trim().parse::<u8>() {
            if lvl <= 3 {
                if let Some(ram) = dmg::parse_wave_hex32(hex.trim()) {
                    return Some((ram, lvl));
                }
            }
        }
    }
    dmg::parse_wave_hex32(inner).map(|ram| (ram, 1))
}

impl Waveform {
    pub fn from_str(s: &str) -> Option<Self> {
        let s = s.to_lowercase();
        if let Some(inner) = strip_paren_content("dmgwave(", &s) {
            if let Some((ram, output_shift)) = parse_dmgwave_ram_and_level(inner) {
                return Some(Waveform::DmgWave {
                    ram,
                    output_shift,
                });
            }
            return None;
        }
        if let Some(inner) = strip_paren_content("dmgwavepreset(", &s) {
            let parts: Vec<&str> = inner.split(',').map(str::trim).collect();
            let idx = parts.first()?.parse::<usize>().ok()?;
            let output_shift = parts
                .get(1)
                .and_then(|x| x.parse::<u8>().ok())
                .unwrap_or(1)
                .min(3);
            return Some(Waveform::DmgWaveCart {
                index: idx,
                output_shift,
            });
        }
        if let Some(inner) = strip_paren_content("dmgpulse1(", &s) {
            let parts: Vec<u8> = inner
                .split(',')
                .filter_map(|p| p.trim().parse::<u8>().ok())
                .collect();
            let duty = *parts.first()?;
            let sweep_pace = parts.get(1).copied().unwrap_or(0).min(7);
            let sweep_shift = parts.get(2).copied().unwrap_or(0).min(7);
            let sweep_subtract = parts.get(3).copied().unwrap_or(0) != 0;
            return Some(Waveform::DmgPulse1 {
                duty: duty.min(3),
                sweep_pace,
                sweep_shift,
                sweep_subtract,
            });
        }
        if let Some(inner) = strip_paren_content("dmgpulse2(", &s) {
            let duty = inner
                .split(',')
                .next()?
                .trim()
                .parse::<u8>()
                .ok()?
                .min(3);
            return Some(Waveform::DmgPulse2 { duty });
        }
        if let Some(inner) = strip_paren_content("dmgnoise15(", &s) {
            let parts: Vec<u8> = inner
                .split(',')
                .filter_map(|p| p.trim().parse::<u8>().ok())
                .collect();
            let div = *parts.first()?;
            let shift = *parts.get(1)?;
            let nr43 = dmg::pack_nr43(div.min(7), shift.min(13), false);
            return Some(Waveform::DmgNoise {
                nr43: Some(nr43),
                seven_bit: false,
            });
        }
        if let Some(inner) = strip_paren_content("dmgnoise7(", &s) {
            let parts: Vec<u8> = inner
                .split(',')
                .filter_map(|p| p.trim().parse::<u8>().ok())
                .collect();
            let div = *parts.first()?;
            let shift = *parts.get(1)?;
            let nr43 = dmg::pack_nr43(div.min(7), shift.min(13), true);
            return Some(Waveform::DmgNoise {
                nr43: Some(nr43),
                seven_bit: true,
            });
        }
        match s.as_str() {
            "dmgnoise15" => {
                return Some(Waveform::DmgNoise {
                    nr43: None,
                    seven_bit: false,
                });
            }
            "dmgnoise7" => {
                return Some(Waveform::DmgNoise {
                    nr43: None,
                    seven_bit: true,
                });
            }
            _ => {}
        }
        if s.starts_with("pwm") && !s.starts_with("layer") {
            let parts: Vec<&str> = s.split(':').collect();
            let w: f32 = parts.get(1).and_then(|p| p.parse().ok()).unwrap_or(0.5);
            return Some(Waveform::Pwm(w.clamp(0.1, 0.9)));
        }
        if s.starts_with("layer") {
            let parts: Vec<&str> = s.split(':').collect();
            if parts.len() > 1 {
                let rest = parts[1..].join(":");
                let mut layers = Vec::new();
                for spec in rest.split(',') {
                    let spec_parts: Vec<&str> = spec.split(':').collect();
                    if spec_parts.len() >= 2 {
                        if let Some(base) = WaveformBase::from_str(spec_parts[0]) {
                            if let Ok(blend) = spec_parts[1].parse::<f32>() {
                                layers.push((base, blend.clamp(0.0, 1.0)));
                            }
                        }
                    }
                }
                if !layers.is_empty() {
                    return Some(Waveform::Layered(layers));
                }
            }
        }
        match s.as_str() {
            "sine" | "sin" | "tone" => Some(Waveform::Sine),
            "square" | "sq" | "beep" => Some(Waveform::Square),
            "triangle" | "tri" => Some(Waveform::Triangle),
            "sawtooth" | "saw" => Some(Waveform::Sawtooth),
            "noise" | "white" => Some(Waveform::Noise),
            "pink" | "pinknoise" | "pink_noise" => Some(Waveform::PinkNoise),
            _ => None,
        }
    }
}

impl Default for Waveform {
    fn default() -> Self {
        Waveform::Triangle
    }
}

/// Effect with parameters (subset from survie for K7 synth).
#[derive(Debug, Clone, PartialEq)]
pub enum Effect {
    Tremolo { rate: f32, depth: f32 },
    Vibrato { rate: f32, depth: f32 },
    Echo { delay_ms: f32, feedback: f32, mix: f32 },
    Reverb { room_size: f32, damping: f32, mix: f32 },
    Chorus { rate: f32, depth: f32, mix: f32 },
    Lowpass { cutoff: f32, resonance: f32 },
    Highpass { cutoff: f32, resonance: f32 },
    Distortion { amount: f32 },
    Bitcrush { bits: f32, rate_factor: f32 },
    Compressor {
        threshold: f32,
        ratio: f32,
        attack_ms: f32,
        release_ms: f32,
        makeup_gain: f32,
    },
    Delay { delay_ms: f32, feedback: f32, mix: f32 },
    Phaser { rate: f32, depth: f32, feedback: f32, mix: f32 },
    Flanger { rate: f32, depth: f32, feedback: f32, mix: f32 },
    RingMod { carrier_freq: f32, mix: f32 },
    Limiter { threshold: f32, release_ms: f32 },
    Envelope { attack: f32, decay: f32, sustain: f32, release: f32 },
    Arpeggio { intervals: Vec<i32>, rate_hz: f32 },
    Portamento { target_freq: f32, time_ms: f32 },
    AutoPan { rate: f32, depth: f32 },
    Sidechain { threshold: f32, ratio: f32, attack_ms: f32, release_ms: f32 },
    Eq { low_gain: f32, mid_gain: f32, high_gain: f32 },
    /// DMG NRx2-style envelope: `pace` 0 = hold `initial`; else step every `pace` ticks at 64 Hz.
    DmgGbEnvelope {
        initial: u8,
        increasing: bool,
        pace: u8,
    },
    /// DMG length: 256 Hz countdown; `load` 0–63 (higher = shorter); `enabled` uses hardware length.
    DmgLength {
        load: u8,
        enabled: bool,
    },
    /// DMG-style stereo into host mixer (`left`/`right` enable).
    DmgPan {
        left: bool,
        right: bool,
    },
    /// CH3 NR32 output level override (0–3).
    DmgWaveOut {
        shift: u8,
    },
}

impl Effect {
    pub fn from_str(s: &str) -> Option<Self> {
        let parts: Vec<&str> = s.split(':').collect();
        if parts.is_empty() {
            return None;
        }
        let name = parts[0].to_lowercase();
        let p = |i: usize, d: f32| -> f32 {
            parts.get(i).and_then(|x| x.parse().ok()).unwrap_or(d)
        };
        match name.as_str() {
            "tremolo" | "trem" | "am" => Some(Effect::Tremolo { rate: p(1, 5.0), depth: p(2, 0.5) }),
            "vibrato" | "vib" | "fm" => Some(Effect::Vibrato { rate: p(1, 5.0), depth: p(2, 0.02) }),
            "echo" | "delay" | "dly" => {
                if let Some(pr) = parts.get(1) {
                    match pr.to_lowercase().as_str() {
                        "short" => return Some(Effect::Echo { delay_ms: 150.0, feedback: 0.3, mix: 0.4 }),
                        "medium" | "med" => return Some(Effect::Echo { delay_ms: 300.0, feedback: 0.4, mix: 0.5 }),
                        "long" => return Some(Effect::Echo { delay_ms: 500.0, feedback: 0.5, mix: 0.6 }),
                        "small" => return Some(Effect::Echo { delay_ms: 200.0, feedback: 0.3, mix: 0.4 }),
                        _ => {}
                    }
                }
                Some(Effect::Echo {
                    delay_ms: p(1, 300.0),
                    feedback: p(2, 0.4),
                    mix: p(3, 0.5),
                })
            }
            "reverb" | "rev" | "room" => {
                if let Some(pr) = parts.get(1) {
                    match pr.to_lowercase().as_str() {
                        "small" => return Some(Effect::Reverb { room_size: 0.3, damping: 0.4, mix: 0.3 }),
                        "medium" | "med" => return Some(Effect::Reverb { room_size: 0.5, damping: 0.3, mix: 0.4 }),
                        "large" => return Some(Effect::Reverb { room_size: 0.7, damping: 0.3, mix: 0.5 }),
                        "hall" => return Some(Effect::Reverb { room_size: 0.9, damping: 0.2, mix: 0.6 }),
                        "cathedral" | "church" => return Some(Effect::Reverb { room_size: 0.95, damping: 0.2, mix: 0.7 }),
                        _ => {}
                    }
                }
                Some(Effect::Reverb {
                    room_size: p(1, 0.7),
                    damping: p(2, 0.3),
                    mix: p(3, 0.5),
                })
            }
            "chorus" | "cho" => {
                if let Some(pr) = parts.get(1) {
                    match pr.to_lowercase().as_str() {
                        "subtle" => return Some(Effect::Chorus { rate: 1.0, depth: 5.0, mix: 0.3 }),
                        "thick" => return Some(Effect::Chorus { rate: 2.0, depth: 15.0, mix: 0.6 }),
                        _ => {}
                    }
                }
                Some(Effect::Chorus { rate: p(1, 1.5), depth: p(2, 10.0), mix: p(3, 0.5) })
            }
            "lowpass" | "lp" | "lpf" => {
                if let Some(pr) = parts.get(1) {
                    match pr.to_lowercase().as_str() {
                        "dark" => return Some(Effect::Lowpass { cutoff: 300.0, resonance: 0.4 }),
                        "warm" => return Some(Effect::Lowpass { cutoff: 800.0, resonance: 0.3 }),
                        _ => {}
                    }
                }
                Some(Effect::Lowpass { cutoff: p(1, 1000.0), resonance: p(2, 0.3) })
            }
            "highpass" | "hp" | "hpf" => {
                if let Some(pr) = parts.get(1) {
                    match pr.to_lowercase().as_str() {
                        "thin" => return Some(Effect::Highpass { cutoff: 800.0, resonance: 0.2 }),
                        "bright" => return Some(Effect::Highpass { cutoff: 300.0, resonance: 0.3 }),
                        _ => {}
                    }
                }
                Some(Effect::Highpass { cutoff: p(1, 200.0), resonance: p(2, 0.3) })
            }
            "distortion" | "dist" => {
                if let Some(pr) = parts.get(1) {
                    match pr.to_lowercase().as_str() {
                        "soft" => return Some(Effect::Distortion { amount: 0.3 }),
                        "medium" | "med" => return Some(Effect::Distortion { amount: 0.5 }),
                        "hard" => return Some(Effect::Distortion { amount: 0.7 }),
                        _ => {}
                    }
                }
                Some(Effect::Distortion { amount: p(1, 0.5) })
            }
            "bitcrush" | "crush" | "lofi" => {
                if let Some(pr) = parts.get(1) {
                    match pr.to_lowercase().as_str() {
                        "nes" | "8bit" => return Some(Effect::Bitcrush { bits: 6.0, rate_factor: 0.6 }),
                        "gameboy" | "gb" => return Some(Effect::Bitcrush { bits: 4.0, rate_factor: 0.5 }),
                        _ => {}
                    }
                }
                Some(Effect::Bitcrush { bits: p(1, 6.0), rate_factor: p(2, 0.5) })
            }
            "compressor" | "comp" => {
                if let Some(pr) = parts.get(1) {
                    let (th, ratio, atk, rel, makeup) = match pr.to_lowercase().as_str() {
                        "subtle" | "soft" => (-24.0, 2.0, 15.0, 150.0, 3.0),
                        "medium" | "normal" => (-20.0, 4.0, 10.0, 100.0, 6.0),
                        "heavy" | "hard" => (-16.0, 8.0, 5.0, 50.0, 10.0),
                        "limiter" | "limit" => (-6.0, 20.0, 1.0, 50.0, 3.0),
                        "vocal" | "voice" => (-18.0, 3.5, 8.0, 120.0, 5.0),
                        "drum" | "drums" => (-12.0, 6.0, 3.0, 80.0, 8.0),
                        "bass" | "sub" => (-18.0, 5.0, 15.0, 150.0, 6.0),
                        _ => (p(1, -20.0), p(2, 4.0), p(3, 10.0), p(4, 100.0), p(5, 0.0)),
                    };
                    return Some(Effect::Compressor {
                        threshold: th,
                        ratio,
                        attack_ms: atk,
                        release_ms: rel,
                        makeup_gain: makeup,
                    });
                }
                Some(Effect::Compressor {
                    threshold: p(1, -20.0),
                    ratio: p(2, 4.0),
                    attack_ms: p(3, 10.0),
                    release_ms: p(4, 100.0),
                    makeup_gain: p(5, 0.0),
                })
            }
            "phaser" | "phs" => Some(Effect::Phaser {
                rate: p(1, 0.5),
                depth: p(2, 0.7),
                feedback: p(3, 0.5),
                mix: p(4, 0.5),
            }),
            "flanger" | "fla" => Some(Effect::Flanger {
                rate: p(1, 0.5),
                depth: p(2, 5.0),
                feedback: p(3, 0.6),
                mix: p(4, 0.5),
            }),
            "ringmod" | "ring" | "rm" => Some(Effect::RingMod { carrier_freq: p(1, 200.0), mix: p(2, 0.5) }),
            "limiter" | "lim" => Some(Effect::Limiter { threshold: p(1, -0.5), release_ms: p(2, 50.0) }),
            "envelope" | "env" | "adsr" => {
                if let Some(pr) = parts.get(1) {
                    match pr.to_lowercase().as_str() {
                        "pluck" => return Some(Effect::Envelope { attack: 0.001, decay: 0.05, sustain: 0.0, release: 0.1 }),
                        "pad" => return Some(Effect::Envelope { attack: 0.5, decay: 0.2, sustain: 0.8, release: 1.0 }),
                        "organ" => return Some(Effect::Envelope { attack: 0.001, decay: 0.0, sustain: 1.0, release: 0.05 }),
                        "brass" => return Some(Effect::Envelope { attack: 0.1, decay: 0.2, sustain: 0.8, release: 0.3 }),
                        "strings" => return Some(Effect::Envelope { attack: 0.3, decay: 0.2, sustain: 0.7, release: 0.5 }),
                        "piano" => return Some(Effect::Envelope { attack: 0.01, decay: 0.3, sustain: 0.5, release: 0.4 }),
                        "perc" | "percussion" => return Some(Effect::Envelope { attack: 0.001, decay: 0.1, sustain: 0.0, release: 0.05 }),
                        "gate" | "gated" => return Some(Effect::Envelope { attack: 0.001, decay: 0.0, sustain: 1.0, release: 0.001 }),
                        _ => {}
                    }
                }
                Some(Effect::Envelope {
                    attack: p(1, 0.01),
                    decay: p(2, 0.1),
                    sustain: p(3, 0.7),
                    release: p(4, 0.2),
                })
            }
            "arpeggio" | "arp" | "chord" => {
                if let Some(pr) = parts.get(1) {
                    let intervals: Vec<i32> = match pr.to_lowercase().as_str() {
                        "maj" | "major" => vec![0, 4, 7],
                        "min" | "minor" => vec![0, 3, 7],
                        "dim" | "diminished" => vec![0, 3, 6],
                        "aug" | "augmented" => vec![0, 4, 8],
                        "maj7" | "major7" => vec![0, 4, 7, 11],
                        "min7" | "minor7" => vec![0, 3, 7, 10],
                        "dom7" | "dominant7" => vec![0, 4, 7, 10],
                        "sus2" => vec![0, 2, 7],
                        "sus4" => vec![0, 5, 7],
                        "power" => vec![0, 7],
                        "octave" | "oct" => vec![0, 12],
                        "fifth" | "5th" => vec![0, 7, 12],
                        _ => pr.split(',').filter_map(|x| x.trim().parse().ok()).collect(),
                    };
                    if !intervals.is_empty() {
                        return Some(Effect::Arpeggio { intervals, rate_hz: p(2, 16.0) });
                    }
                }
                Some(Effect::Arpeggio { intervals: vec![0, 4, 7], rate_hz: 16.0 })
            }
            "portamento" | "port" | "slide" | "glide" => {
                Some(Effect::Portamento { target_freq: 0.0, time_ms: p(1, 100.0) })
            }
            "autopan" | "pan" | "apan" => {
                if let Some(pr) = parts.get(1) {
                    match pr.to_lowercase().as_str() {
                        "slow" | "gentle" => return Some(Effect::AutoPan { rate: 0.5, depth: 0.6 }),
                        "fast" | "quick" => return Some(Effect::AutoPan { rate: 2.0, depth: 0.8 }),
                        "wide" => return Some(Effect::AutoPan { rate: 1.0, depth: 0.9 }),
                        "narrow" => return Some(Effect::AutoPan { rate: 1.0, depth: 0.4 }),
                        _ => {}
                    }
                }
                Some(Effect::AutoPan { rate: p(1, 1.0), depth: p(2, 0.7) })
            }
            "sidechain" | "duck" | "sc" => {
                if let Some(pr) = parts.get(1) {
                    match pr.to_lowercase().as_str() {
                        "pumping" | "edm" => return Some(Effect::Sidechain { threshold: -24.0, ratio: 10.0, attack_ms: 5.0, release_ms: 150.0 }),
                        "subtle" | "light" => return Some(Effect::Sidechain { threshold: -30.0, ratio: 5.0, attack_ms: 10.0, release_ms: 200.0 }),
                        "extreme" | "heavy" => return Some(Effect::Sidechain { threshold: -18.0, ratio: 20.0, attack_ms: 3.0, release_ms: 100.0 }),
                        _ => {}
                    }
                }
                Some(Effect::Sidechain { threshold: p(1, -20.0), ratio: p(2, 10.0), attack_ms: p(3, 5.0), release_ms: p(4, 150.0) })
            }
            "eq" | "equalizer" | "tone" => {
                if let Some(pr) = parts.get(1) {
                    match pr.to_lowercase().as_str() {
                        "bright" => return Some(Effect::Eq { low_gain: -2.0, mid_gain: 1.0, high_gain: 4.0 }),
                        "warm" => return Some(Effect::Eq { low_gain: 3.0, mid_gain: 1.0, high_gain: -2.0 }),
                        "smiley" => return Some(Effect::Eq { low_gain: 4.0, mid_gain: -2.0, high_gain: 4.0 }),
                        "bass_boost" | "bass" => return Some(Effect::Eq { low_gain: 6.0, mid_gain: 0.0, high_gain: 0.0 }),
                        "treble_boost" | "treble" => return Some(Effect::Eq { low_gain: 0.0, mid_gain: 0.0, high_gain: 6.0 }),
                        _ => {}
                    }
                }
                Some(Effect::Eq { low_gain: p(1, 0.0), mid_gain: p(2, 0.0), high_gain: p(3, 0.0) })
            }
            "dmgenv" | "dmg_gb_env" => {
                let initial = parts
                    .get(1)
                    .and_then(|x| x.parse::<u8>().ok())
                    .unwrap_or(15)
                    .min(15);
                let increasing = parts.get(2).and_then(|x| x.parse::<u8>().ok()).unwrap_or(0) != 0;
                let pace = parts
                    .get(3)
                    .and_then(|x| x.parse::<u8>().ok())
                    .unwrap_or(0)
                    .min(7);
                Some(Effect::DmgGbEnvelope {
                    initial,
                    increasing,
                    pace,
                })
            }
            "dmglen" | "dmg_length" => {
                let load = parts
                    .get(1)
                    .and_then(|x| x.parse::<u8>().ok())
                    .unwrap_or(0)
                    .min(63);
                let enabled = parts.get(2).and_then(|x| x.parse::<u8>().ok()).unwrap_or(1) != 0;
                Some(Effect::DmgLength { load, enabled })
            }
            "dmgpan" => {
                let m = parts
                    .get(1)
                    .map(|x| x.to_lowercase())
                    .unwrap_or_default();
                let (left, right) = match m.as_str() {
                    "left" | "l" => (true, false),
                    "right" | "r" => (false, true),
                    "off" | "mute" | "none" => (false, false),
                    _ => (true, true),
                };
                Some(Effect::DmgPan { left, right })
            }
            "dmgout" | "dmgwaveout" => {
                let shift = parts
                    .get(1)
                    .and_then(|x| x.parse::<u8>().ok())
                    .unwrap_or(1)
                    .min(3);
                Some(Effect::DmgWaveOut { shift })
            }
            _ => None,
        }
    }
}

#[derive(Clone)]
pub struct NoteEvent {
    pub frequency: f32,
    pub duration: Duration,
    pub volume: f32,
    pub waveform: Waveform,
    pub effects: Vec<Effect>,
}

impl NoteEvent {
    pub fn frequency(&self) -> f32 {
        self.frequency
    }
}

fn parse_note_to_freq(s: &str) -> f32 {
    let s = s.to_lowercase();
    let mut chars = s.chars().peekable();
    let note = chars.next().unwrap_or('c');
    let sharp = chars.next().map(|c| c == '#' || c == 's').unwrap_or(false);
    let octave = chars
        .next()
        .and_then(|c| c.to_digit(10))
        .unwrap_or(4) as i32;
    let mut semitone = match note {
        'c' => 0,
        'd' => 2,
        'e' => 4,
        'f' => 5,
        'g' => 7,
        'a' => 9,
        'b' => 11,
        _ => 0,
    };
    if sharp {
        semitone += 1;
    }
    semitone += (octave - 4) * 12;
    440.0 * 2.0f32.powf((semitone - 9) as f32 / 12.0)
}

/// Parse note string and optional short duration. Returns (string for freq, short_duration in seconds).
/// e.g. "c4" -> ("c4", None), "cq4" -> ("c4", Some(0.5)), "ch#4" -> ("c#4", Some(1.0))
fn parse_note_str_and_short_duration(note_str: &str) -> (String, Option<Duration>) {
    let s = note_str.to_lowercase();
    let mut chars = s.chars().peekable();
    let note_char = chars.next().unwrap_or('c');
    if !matches!(note_char, 'c' | 'd' | 'e' | 'f' | 'g' | 'a' | 'b') {
        return (s, None);
    }
    let mut out = note_char.to_string();
    let beats = chars.peek().and_then(|c| match c {
        'w' => Some(4.0),
        'h' => Some(2.0),
        'q' => Some(1.0),
        'e' => Some(0.5),
        's' => Some(0.25),
        't' => Some(0.125),
        _ => None,
    });
    if beats.is_some() {
        chars.next();
    }
    if chars.peek() == Some(&'#') || chars.peek() == Some(&'s') {
        chars.next();
        out.push('#');
    }
    if let Some(&d) = chars.peek() {
        if d.is_ascii_digit() {
            out.push(chars.next().unwrap());
        } else {
            out.push('4');
        }
    } else {
        out.push('4');
    }
    let short_duration = beats.map(|b| Duration::from_secs_f32(0.5 * b));
    (out, short_duration)
}

/// Parse a single token like "c4", "c4@80", "cq4:2:sine|reverb:small" into a NoteEvent.
fn parse_token(token: &str, default_duration: Duration) -> Option<NoteEvent> {
    let token = token.trim();
    if token.is_empty() {
        return None;
    }
    if token == "-" || token.eq_ignore_ascii_case("r") {
        return Some(NoteEvent {
            frequency: 0.0,
            duration: default_duration,
            volume: 0.0,
            waveform: Waveform::Triangle,
            effects: vec![],
        });
    }
    let (token_no_vol, volume) = if let Some(at_pos) = token.rfind('@') {
        let (note_part, vol_part) = token.split_at(at_pos);
        let vol_str = vol_part.trim_start_matches('@');
        let v = vol_str.parse::<f32>().ok().map(|x| (x / 100.0).clamp(0.0, 1.0)).unwrap_or(1.0);
        (note_part, v)
    } else {
        (token, 1.0)
    };
    let parts: Vec<&str> = token_no_vol.split('|').collect();
    let note_part = parts[0];
    let note_parts: Vec<&str> = note_part.split(':').collect();
    let note_str = note_parts[0];
    let (freq_str, short_duration) = parse_note_str_and_short_duration(note_str);
    let freq = parse_note_to_freq(&freq_str);
    let mut duration = short_duration.unwrap_or(default_duration);
    let mut waveform = Waveform::default();
    for part in note_parts.iter().skip(1) {
        if part.starts_with("layer") || part.contains(',') {
            let full_spec = note_parts[1..].join(":");
            if let Some(w) = Waveform::from_str(&full_spec) {
                waveform = w;
            }
            break;
        }
        if let Some(w) = Waveform::from_str(part) {
            waveform = w;
            continue;
        }
        if let Ok(beats) = part.parse::<f32>() {
            duration = Duration::from_secs_f32(0.5 * beats);
        }
    }
    let mut effects = Vec::new();
    for eff_spec in parts.iter().skip(1) {
        if let Some(e) = Effect::from_str(eff_spec) {
            effects.push(e);
        }
    }
    Some(NoteEvent {
        frequency: freq,
        duration,
        volume,
        waveform,
        effects,
    })
}

/// Parse melody string. Supports "c4 d4 e4", "c4:sine|reverb:small d4:tri", and "c4:piano:bright".
pub fn parse_melody(notation: &str, default_duration: Duration) -> Vec<NoteEvent> {
    let mut out = Vec::new();
    for token in notation.split_whitespace() {
        let expanded = expand_sound_token(token);
        if let Some(ev) = parse_token(&expanded, default_duration) {
            out.push(ev);
        }
    }
    out
}
