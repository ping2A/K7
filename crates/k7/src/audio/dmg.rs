//! Game Boy DMG-style generators: CH3 wave RAM, CH4 LFSR noise, CH1/CH2 pulse (+ CH1 sweep).
//! Frame sequencer at 512 Hz: length 256 Hz, sweep 128 Hz, envelope 64 Hz (Pan Docs).
//! LFSR step matches SameBoy (`step_lfsr`).

use std::time::Duration;

/// NR43 noise divisors; clock = 524288 / (divisor × 2^(shift+1)) Hz.
const NOISE_DIV: [f32; 8] = [8.0, 16.0, 32.0, 48.0, 64.0, 80.0, 96.0, 112.0];

const FS_HZ: f32 = 512.0;

#[inline]
pub fn pack_nr43(divider_code: u8, shift: u8, seven_bit_lfsr: bool) -> u8 {
    ((shift & 0x0F) << 4) | ((seven_bit_lfsr as u8) << 3) | (divider_code & 7)
}

pub fn dmg_noise_clock_hz(nr43: u8) -> f32 {
    let shift = (nr43 >> 4) & 0x0F;
    if shift >= 14 {
        return 0.0;
    }
    let d = (nr43 & 7) as usize;
    let divisor = NOISE_DIV[d];
    524_288.0 / (divisor * 2.0_f32.powi(i32::from(shift) + 1))
}

pub fn nr43_best_fit(target_hz: f32) -> u8 {
    if target_hz <= 0.0 {
        return pack_nr43(0, 0, false);
    }
    let mut best = pack_nr43(0, 0, false);
    let mut best_err = f32::MAX;
    for div in 0u8..8 {
        for shift in 0u8..14 {
            let packed = pack_nr43(div, shift, false);
            let f = dmg_noise_clock_hz(packed);
            if f <= 0.0 {
                continue;
            }
            let e = (f - target_hz).abs();
            if e < best_err {
                best_err = e;
                best = packed;
            }
        }
    }
    best
}

pub fn dmg_period_from_freq_hz(freq_hz: f32) -> u16 {
    if freq_hz <= 0.0 {
        return 0;
    }
    let p = 2048.0 - 131_072.0 / freq_hz;
    p.clamp(0.0, 2047.0) as u16
}

pub fn parse_wave_hex32(hex: &str) -> Option<[u8; 16]> {
    let mut digits: Vec<u8> = Vec::with_capacity(32);
    for b in hex.as_bytes() {
        let v = match b {
            b'0'..=b'9' => b - b'0',
            b'a'..=b'f' => b - b'a' + 10,
            b'A'..=b'F' => b - b'A' + 10,
            _ => continue,
        };
        digits.push(v);
        if digits.len() >= 32 {
            break;
        }
    }
    if digits.len() < 32 {
        return None;
    }
    let mut ram = [0u8; 16];
    for i in 0..16 {
        ram[i] = (digits[i * 2] << 4) | digits[i * 2 + 1];
    }
    Some(ram)
}

#[inline]
pub fn dmg_noise_step_lfsr(lfsr: &mut u16, narrow: bool) {
    let high_bit_mask = if narrow { 0x4040u16 } else { 0x4000u16 };
    let new_high_bit = ((*lfsr ^ (*lfsr >> 1)) ^ 1) & 1;
    *lfsr >>= 1;
    if new_high_bit != 0 {
        *lfsr |= high_bit_mask;
    } else {
        *lfsr &= !high_bit_mask;
    }
}

/// NRx2-style volume envelope: `pace` 0 = no automatic steps (hold `initial`).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DmgHwEnvelope {
    pub initial: u8,
    /// NR12/NR42 bit 3: `true` = volume increases each step.
    pub increasing: bool,
    pub pace: u8,
}

impl Default for DmgHwEnvelope {
    fn default() -> Self {
        Self {
            initial: 15,
            increasing: false,
            pace: 0,
        }
    }
}

/// Length: 256 Hz ticks; `load` 0–63 (higher = shorter). Disabled = ignore.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DmgHwLength {
    pub load: u8,
    pub enabled: bool,
}

impl Default for DmgHwLength {
    fn default() -> Self {
        Self {
            load: 0,
            enabled: false,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DmgSweep {
    pub pace: u8,
    pub shift: u8,
    pub subtract: bool,
}

/// NR32-style output: 0 = mute, 1 = 100%, 2 = 50%, 3 = 25% (nibble >> n).
#[inline]
fn apply_wave_output_level(nibble: u8, level: u8) -> u8 {
    match level.min(3) {
        0 => 0,
        1 => nibble,
        2 => nibble >> 1,
        _ => nibble >> 2,
    }
}

#[inline]
fn dmg_dac_to_f32(d: u8) -> f32 {
    1.0 - 2.0 * (f32::from(d) / 15.0)
}

#[inline]
fn digital_from_pulse(high: bool, vol: u8) -> u8 {
    if high { vol } else { 0 }
}

fn advance_frame_sequencer(
    fs_acc: &mut f32,
    fs_step: &mut u32,
    sample_rate: f32,
    length: &DmgHwLength,
    len_remain: &mut Option<u8>,
    sweep: &mut Option<DmgSweepState>,
    env: &DmgHwEnvelope,
    env_vol: &mut u8,
    env_div: &mut u8,
    ch_off: &mut bool,
) {
    *fs_acc += 1.0 / sample_rate;
    while *fs_acc >= 1.0 / FS_HZ {
        *fs_acc -= 1.0 / FS_HZ;
        let step = *fs_step;
        *fs_step = step.wrapping_add(1);

        if length.enabled {
            if step % 2 == 0 {
                if let Some(ref mut r) = len_remain {
                    if *r > 0 {
                        *r -= 1;
                        if *r == 0 {
                            *ch_off = true;
                        }
                    }
                }
            }
        }

        if step % 4 == 0 {
            if let Some(sw) = sweep.as_mut() {
                sw.tick(ch_off);
            }
        }

        if step % 8 == 0 {
            tick_hardware_envelope(env, env_vol, env_div, ch_off);
        }
    }
}

fn tick_hardware_envelope(env: &DmgHwEnvelope, vol: &mut u8, div: &mut u8, ch_off: &mut bool) {
    if env.pace == 0 {
        return;
    }
    *div = div.saturating_add(1);
    if *div < env.pace {
        return;
    }
    *div = 0;
    if env.increasing {
        if *vol < 15 {
            *vol += 1;
        }
    } else if *vol > 0 {
        *vol -= 1;
        if *vol == 0 {
            *ch_off = true;
        }
    }
}

struct DmgSweepState {
    shadow: u32,
    pace: u8,
    shift: u8,
    subtract: bool,
    accum: u8,
    muted: bool,
}

impl DmgSweepState {
    fn new(period: u16, pace: u8, shift: u8, subtract: bool) -> Self {
        let shadow = u32::from(period.max(1));
        let mut muted = false;
        if shift != 0 && !subtract {
            let w = shadow + (shadow >> shift);
            if w > 2047 {
                muted = true;
            }
        }
        Self {
            shadow,
            pace,
            shift,
            subtract,
            accum: 0,
            muted,
        }
    }

    fn tick(&mut self, ch_off: &mut bool) {
        if self.muted || self.pace == 0 || self.shift == 0 {
            return;
        }
        self.accum = self.accum.wrapping_add(1);
        if self.accum < self.pace {
            return;
        }
        self.accum = 0;
        let sh = self.shadow;
        let delta = sh >> self.shift;
        let new_p = if self.subtract {
            sh.saturating_sub(delta)
        } else {
            sh.saturating_add(delta)
        };
        if !self.subtract && new_p > 2047 {
            self.muted = true;
            *ch_off = true;
            return;
        }
        if new_p > 2047 {
            return;
        }
        self.shadow = new_p;
        if !self.subtract {
            let w = new_p + (new_p >> self.shift);
            if w > 2047 {
                self.muted = true;
                *ch_off = true;
            }
        }
    }

    fn period(&self) -> u16 {
        if self.muted {
            return 2047;
        }
        self.shadow.min(2047) as u16
    }
}

const PULSE_DUTY: [[u8; 8]; 4] = [
    [0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 1, 1],
    [0, 1, 1, 1, 1, 1, 1, 0],
];

#[inline]
fn read_wave_nibble(ram: &[u8; 16], idx: u32) -> u8 {
    let i = idx as usize;
    let byte = ram[i / 2];
    if (i & 1) == 0 {
        byte >> 4
    } else {
        byte & 0x0F
    }
}

/// CH3 with NR32 output level (0–3). No NRx2-style envelope on hardware CH3; gain via `volume`.
pub fn render_dmg_wave(
    ram: &[u8; 16],
    output_level: u8,
    freq_hz: f32,
    duration: Duration,
    sample_rate: u32,
    volume: f32,
    length: DmgHwLength,
) -> Vec<f32> {
    let num_samples = (duration.as_secs_f32() * sample_rate as f32) as usize;
    if freq_hz <= 0.0 {
        return vec![0.0; num_samples];
    }
    let period = dmg_period_from_freq_hz(freq_hz).max(1);
    let nibble_hz = 32.0 * 131_072.0 / (2048.0 - f32::from(period));
    let mut nibble_phase = 0.0f32;
    let mut sample_index: u32 = 1;
    let mut last_nibble = read_wave_nibble(ram, sample_index);
    let mut fs_acc = 0.0f32;
    let mut fs_step = 0u32;
    let hold_env = DmgHwEnvelope::default();
    let mut env_vol = 15u8;
    let mut env_div = 0u8;
    let mut ch_off = false;
    let mut len_remain = if length.enabled {
        Some((64u8).saturating_sub(length.load.min(63)).max(1))
    } else {
        None
    };
    let sr = sample_rate as f32;
    let mut samples = Vec::with_capacity(num_samples);
    let mut sweep_none = None;
    for _ in 0..num_samples {
        advance_frame_sequencer(
            &mut fs_acc,
            &mut fs_step,
            sr,
            &length,
            &mut len_remain,
            &mut sweep_none,
            &hold_env,
            &mut env_vol,
            &mut env_div,
            &mut ch_off,
        );
        nibble_phase += nibble_hz / sr;
        while nibble_phase >= 1.0 {
            nibble_phase -= 1.0;
            sample_index = (sample_index + 1) & 31;
            last_nibble = read_wave_nibble(ram, sample_index);
        }
        let nib = apply_wave_output_level(last_nibble, output_level.min(3));
        let digital = nib.min(15);
        let s = if ch_off || output_level == 0 {
            0.0
        } else {
            dmg_dac_to_f32(digital) * volume * 0.5
        };
        samples.push(s);
    }
    samples
}

/// CH4 with hardware envelope + length.
pub fn render_dmg_noise(
    nr43: u8,
    duration: Duration,
    sample_rate: u32,
    volume: f32,
    env: DmgHwEnvelope,
    length: DmgHwLength,
) -> Vec<f32> {
    let num_samples = (duration.as_secs_f32() * sample_rate as f32) as usize;
    let clock_hz = dmg_noise_clock_hz(nr43);
    let narrow = (nr43 >> 3) & 1 != 0;
    let mut lfsr: u16 = 0;
    let mut phase = 0.0f32;
    let mut fs_acc = 0.0f32;
    let mut fs_step = 0u32;
    let mut env_vol = env.initial.min(15);
    let mut env_div = 0u8;
    let mut ch_off = false;
    let mut len_remain = if length.enabled {
        Some((64u8).saturating_sub(length.load.min(63)).max(1))
    } else {
        None
    };
    let sr = sample_rate as f32;
    let mut samples = Vec::with_capacity(num_samples);
    let mut sweep_none = None;
    for _ in 0..num_samples {
        advance_frame_sequencer(
            &mut fs_acc,
            &mut fs_step,
            sr,
            &length,
            &mut len_remain,
            &mut sweep_none,
            &env,
            &mut env_vol,
            &mut env_div,
            &mut ch_off,
        );
        if clock_hz > 0.0 {
            phase += clock_hz / sr;
            while phase >= 1.0 {
                phase -= 1.0;
                dmg_noise_step_lfsr(&mut lfsr, narrow);
            }
        }
        let digital = if (lfsr & 1) != 0 { env_vol } else { 0 };
        let s = if ch_off {
            0.0
        } else {
            dmg_dac_to_f32(digital.min(15)) * volume * 0.5
        };
        samples.push(s);
    }
    samples
}

/// CH1 pulse + optional sweep, or CH2 if `sweep` is None.
pub fn render_dmg_pulse(
    duty: u8,
    sweep: Option<DmgSweep>,
    freq_hz: f32,
    duration: Duration,
    sample_rate: u32,
    volume: f32,
    env: DmgHwEnvelope,
    length: DmgHwLength,
) -> Vec<f32> {
    let num_samples = (duration.as_secs_f32() * sample_rate as f32) as usize;
    if freq_hz <= 0.0 {
        return vec![0.0; num_samples];
    }
    let duty = (duty.min(3)) as usize;
    let period0 = dmg_period_from_freq_hz(freq_hz).max(1);
    let mut sweep_st = sweep.map(|sw| {
        DmgSweepState::new(period0, sw.pace & 7, sw.shift & 7, sw.subtract)
    });
    let mut fs_acc = 0.0f32;
    let mut fs_step = 0u32;
    let mut env_vol = env.initial.min(15);
    let mut env_div = 0u8;
    let mut ch_off = false;
    let mut len_remain = if length.enabled {
        Some((64u8).saturating_sub(length.load.min(63)).max(1))
    } else {
        None
    };
    let mut pulse_phase = 0.0f32;
    let sr = sample_rate as f32;
    let mut samples = Vec::with_capacity(num_samples);
    for _ in 0..num_samples {
        advance_frame_sequencer(
            &mut fs_acc,
            &mut fs_step,
            sr,
            &length,
            &mut len_remain,
            &mut sweep_st,
            &env,
            &mut env_vol,
            &mut env_div,
            &mut ch_off,
        );
        let period = sweep_st
            .as_ref()
            .map(|s| s.period().max(1))
            .unwrap_or(period0)
            .max(1);
        let pulse_sample_hz = 1_048_576.0 / (2048.0 - period as f32);
        pulse_phase = (pulse_phase + pulse_sample_hz / sr).fract();
        let step = ((pulse_phase * 8.0) as usize).min(7);
        let high = PULSE_DUTY[duty][step] != 0;
        let muted_pulse = sweep_st.as_ref().map(|s| s.muted).unwrap_or(false);
        let digital = digital_from_pulse(high, env_vol);
        let s = if ch_off || muted_pulse {
            0.0
        } else {
            dmg_dac_to_f32(digital.min(15)) * volume * 0.5
        };
        samples.push(s);
    }
    samples
}

/// Parse `dmgpan` / default: both channels.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DmgStereoPan {
    pub left: bool,
    pub right: bool,
}

impl Default for DmgStereoPan {
    fn default() -> Self {
        Self {
            left: true,
            right: true,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lfsr_first_steps_15bit_match_sameboy_style() {
        let mut l = 0u16;
        dmg_noise_step_lfsr(&mut l, false);
        assert_eq!(l, 0x4000);
        dmg_noise_step_lfsr(&mut l, false);
        assert_eq!(l, 0x6000);
    }

    #[test]
    fn sweep_addition_overflow_mutes() {
        let hz = 131_072.0 / (2048.0 - 1000.0);
        let buf = render_dmg_pulse(
            2,
            Some(DmgSweep {
                pace: 1,
                shift: 1,
                subtract: false,
            }),
            hz,
            Duration::from_millis(400),
            44100,
            0.8,
            DmgHwEnvelope::default(),
            DmgHwLength::default(),
        );
        let max_late = buf[buf.len().saturating_sub(2000)..]
            .iter()
            .map(|x| x.abs())
            .fold(0.0f32, f32::max);
        assert!(max_late < 1.0e-3, "should mute: {}", max_late);
    }

    #[test]
    fn parse_wave_ram() {
        let h = "0123456789abcdef0123456789abcdef";
        let ram = parse_wave_hex32(h).unwrap();
        assert_eq!(ram[0], 0x01);
        assert_eq!(ram[15], 0xef);
    }

    #[test]
    fn envelope_decreases_volume() {
        let buf = render_dmg_noise(
            pack_nr43(4, 4, false),
            Duration::from_millis(500),
            44100,
            1.0,
            DmgHwEnvelope {
                initial: 15,
                increasing: false,
                pace: 1,
            },
            DmgHwLength::default(),
        );
        let e0 = buf[1000..2000].iter().map(|x| x.abs()).sum::<f32>();
        let e1 = buf[8000..9000].iter().map(|x| x.abs()).sum::<f32>();
        assert!(e1 < e0 * 0.85, "envelope should decay: {} vs {}", e1, e0);
    }

    #[test]
    fn length_cuts_noise() {
        let buf = render_dmg_noise(
            pack_nr43(4, 4, false),
            Duration::from_millis(400),
            44100,
            1.0,
            DmgHwEnvelope {
                initial: 15,
                increasing: false,
                pace: 0,
            },
            // load 0 → 64 length ticks at 256 Hz ≈ 250 ms; 400 ms buffer tail should be quiet.
            DmgHwLength {
                load: 0,
                enabled: true,
            },
        );
        let early = buf[500..800].iter().map(|x| x.abs()).sum::<f32>();
        let late = buf[buf.len().saturating_sub(500)..]
            .iter()
            .map(|x| x.abs())
            .sum::<f32>();
        assert!(late < early * 0.2, "length should silence tail");
    }
}
