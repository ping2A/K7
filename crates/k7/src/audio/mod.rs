//! Audio: 4 channels, 64 definable sounds, 8 music tracks.
//! Full synth, SFX and effects from survie tracker.

mod synth;
mod dmg;
mod note_parser;

use std::time::Duration;
use crate::constants::{AUDIO_CHANNELS, SOUND_COUNT, MUSIC_TRACK_COUNT};

pub use synth::{Synth, Envelope, WaveformType};
pub use note_parser::{expand_sound_token, parse_melody, NoteEvent, Waveform, WaveformBase, Effect};

/// Sound identifier (0..63).
pub type SoundId = u8;
/// Music track identifier (0..7).
pub type MusicId = u8;

/// Audio engine: 4 channels, 64 sounds, 8 music tracks.
/// Host (native/web) pulls samples via fill_buffer() and plays them.
pub struct AudioEngine {
    pub sample_rate: u32,
    pub synth: Synth,
    /// 64 definable sounds (notation strings).
    pub sounds: [Option<String>; SOUND_COUNT],
    /// 8 music tracks (notation strings, can reference patterns).
    pub music_tracks: [Option<String>; MUSIC_TRACK_COUNT],
    /// 4 channels: each can play a sound or a music track.
    pub channels: [ChannelState; AUDIO_CHANNELS],
    /// Custom DMG wave tables for `dmgwavepreset(n)` (16 bytes each).
    pub dmg_wave_cart: Vec<[u8; 16]>,
}

#[derive(Clone, Default)]
pub struct ChannelState {
    pub playing_sound: Option<SoundId>,
    pub playing_music: Option<MusicId>,
    pub volume: f32,
    pub melody: Vec<NoteEvent>,
    pub current_note: usize,
    pub samples_until_next_note: usize,
}

impl AudioEngine {
    pub fn new(sample_rate: u32) -> Self {
        Self {
            sample_rate,
            synth: Synth::new(sample_rate),
            sounds: std::array::from_fn(|_| None),
            music_tracks: std::array::from_fn(|_| None),
            channels: std::array::from_fn(|_| ChannelState::default()),
            dmg_wave_cart: Vec::new(),
        }
    }

    /// Replace DMG wave cart (e.g. from share JSON `audio_cart.gb.waves_hex`). Invalid hex entries are skipped.
    pub fn set_dmg_wave_cart_hexes(&mut self, hexes: &[String]) {
        self.dmg_wave_cart.clear();
        for h in hexes {
            if let Some(ram) = dmg::parse_wave_hex32(h) {
                self.dmg_wave_cart.push(ram);
            }
        }
    }

    /// Clear cart entries (preset indices resolve to a flat mid wave).
    pub fn clear_dmg_wave_cart(&mut self) {
        self.dmg_wave_cart.clear();
    }

    /// Define sound at index 0..63 with notation (e.g. "c4 e4 g4").
    pub fn set_sound(&mut self, id: SoundId, notation: String) {
        if (id as usize) < SOUND_COUNT {
            self.sounds[id as usize] = Some(notation);
        }
    }

    /// Define music track at index 0..7.
    pub fn set_music_track(&mut self, id: MusicId, notation: String) {
        if (id as usize) < MUSIC_TRACK_COUNT {
            self.music_tracks[id as usize] = Some(notation);
        }
    }

    /// Play sound on channel (0..3).
    pub fn play_sound(&mut self, channel: u8, sound_id: SoundId) {
        if channel as usize >= AUDIO_CHANNELS || (sound_id as usize) >= SOUND_COUNT {
            return;
        }
        if let Some(ref notation) = self.sounds[sound_id as usize] {
            let melody = parse_melody(notation, Duration::from_millis(100));
            let samples_until_next = melody.first().map(|n| (n.duration.as_secs_f32() * self.sample_rate as f32) as usize).unwrap_or(0);
            self.channels[channel as usize] = ChannelState {
                playing_sound: Some(sound_id),
                playing_music: None,
                volume: 0.7,
                melody,
                current_note: 0,
                samples_until_next_note: samples_until_next,
            };
        }
    }

    /// Play music track on channel.
    pub fn play_music(&mut self, channel: u8, track_id: MusicId) {
        if channel as usize >= AUDIO_CHANNELS || (track_id as usize) >= MUSIC_TRACK_COUNT {
            return;
        }
        if let Some(ref notation) = self.music_tracks[track_id as usize] {
            let melody = parse_melody(notation, Duration::from_millis(250));
            let samples_until_next = melody.first().map(|n| (n.duration.as_secs_f32() * self.sample_rate as f32) as usize).unwrap_or(0);
            self.channels[channel as usize] = ChannelState {
                playing_sound: None,
                playing_music: Some(track_id),
                volume: 0.6,
                melody,
                current_note: 0,
                samples_until_next_note: samples_until_next,
            };
        }
    }

    /// Stop channel.
    pub fn stop_channel(&mut self, channel: u8) {
        if (channel as usize) < AUDIO_CHANNELS {
            self.channels[channel as usize] = ChannelState::default();
        }
    }

    /// Render a full sound notation to a mono sample buffer (same parser and synth as fill_buffer).
    /// Uses default_duration for notes that don't specify one. Returns samples at self.sample_rate.
    pub fn render_sound_to_buffer(&self, notation: &str, default_duration: Duration, volume: f32) -> Vec<f32> {
        let melody = parse_melody(notation, default_duration);
        if melody.is_empty() {
            return Vec::new();
        }
        let mut out = Vec::new();
        for note in &melody {
            let secs = note.duration.as_secs_f32();
            let num_samples = (secs * self.sample_rate as f32) as usize;
            if num_samples == 0 {
                continue;
            }
            let dur = Duration::from_secs_f32(secs);
            let vol = volume * note.volume;
            let mut samples = self.generate_note_samples(note, dur, vol);
            self.apply_note_effects(&mut samples, note);
            let pan = dmg_pan_from_note(note);
            let g = (u8::from(pan.left) + u8::from(pan.right)) as f32;
            let g = g.min(1.0);
            let take = num_samples.min(samples.len());
            if g < 1.0 {
                for s in &mut samples[..take] {
                    *s *= g;
                }
            }
            out.extend_from_slice(&samples[..take]);
        }
        out
    }

    /// Fill interleaved stereo buffer (left, right, left, right, ...).
    /// Uses each note's waveform and effects (survie-style).
    pub fn fill_buffer(&mut self, buffer: &mut [f32]) {
        let frame_count = buffer.len() / 2;
        buffer.fill(0.0);
        let mut work: Vec<(NoteEvent, f32, usize)> = Vec::new();
        for ch in &self.channels {
            if ch.melody.is_empty() {
                continue;
            }
            let to_gen = ch.samples_until_next_note.min(frame_count);
            if to_gen > 0 && ch.current_note < ch.melody.len() {
                let note = ch.melody[ch.current_note].clone();
                work.push((note, ch.volume, to_gen));
            }
        }
        for (note, ch_vol, to_gen) in work {
            let dur = Duration::from_secs_f32(to_gen as f32 / self.sample_rate as f32);
            let vol = ch_vol * note.volume;
            let mut samples = self.generate_note_samples(&note, dur, vol);
            self.apply_note_effects(&mut samples, &note);
            let pan = dmg_pan_from_note(&note);
            let gl = if pan.left { 1.0f32 } else { 0.0 };
            let gr = if pan.right { 1.0f32 } else { 0.0 };
            for i in 0..to_gen.min(samples.len()) {
                let s = samples[i];
                buffer[i * 2] += s * gl;
                buffer[i * 2 + 1] += s * gr;
            }
        }
        for ch in &mut self.channels {
            if ch.melody.is_empty() {
                continue;
            }
            ch.samples_until_next_note = ch.samples_until_next_note.saturating_sub(frame_count);
            if ch.samples_until_next_note == 0 {
                ch.current_note += 1;
                if ch.current_note >= ch.melody.len() {
                    ch.current_note = 0;
                }
                if ch.current_note < ch.melody.len() {
                    let note = &ch.melody[ch.current_note];
                    ch.samples_until_next_note = (note.duration.as_secs_f32() * self.sample_rate as f32) as usize;
                }
            }
        }
    }

    fn base_to_type(b: &note_parser::WaveformBase) -> synth::WaveformType {
        use note_parser::WaveformBase;
        match b {
            WaveformBase::Sine => synth::WaveformType::Sine,
            WaveformBase::Square => synth::WaveformType::Square,
            WaveformBase::Triangle => synth::WaveformType::Triangle,
            WaveformBase::Sawtooth => synth::WaveformType::Sawtooth,
            WaveformBase::Pwm(pw) => synth::WaveformType::Pwm(*pw),
            WaveformBase::Noise => synth::WaveformType::Noise,
            WaveformBase::PinkNoise => synth::WaveformType::PinkNoise,
        }
    }

    fn waveform_to_type(w: &note_parser::Waveform) -> Option<synth::WaveformType> {
        use note_parser::Waveform;
        match w {
            Waveform::Sine => Some(synth::WaveformType::Sine),
            Waveform::Square => Some(synth::WaveformType::Square),
            Waveform::Triangle => Some(synth::WaveformType::Triangle),
            Waveform::Sawtooth => Some(synth::WaveformType::Sawtooth),
            Waveform::Pwm(pw) => Some(synth::WaveformType::Pwm(*pw)),
            Waveform::Noise => Some(synth::WaveformType::Noise),
            Waveform::PinkNoise => Some(synth::WaveformType::PinkNoise),
            Waveform::Layered(_)
            | Waveform::DmgWave { .. }
            | Waveform::DmgWaveCart { .. }
            | Waveform::DmgNoise { .. }
            | Waveform::DmgPulse1 { .. }
            | Waveform::DmgPulse2 { .. } => None,
        }
    }

    fn generate_note_samples(&self, note: &NoteEvent, duration: Duration, volume: f32) -> Vec<f32> {
        use note_parser::Waveform;
        match &note.waveform {
            Waveform::Layered(layers) => {
                let conv: Vec<(synth::WaveformType, f32)> = layers
                    .iter()
                    .map(|(b, w)| (Self::base_to_type(b), *w))
                    .collect();
                self.synth.generate_layered(note.frequency(), duration, volume, &conv)
            }
            Waveform::DmgWave { ram, output_shift } => {
                let (_, len, _, wsh) = merge_dmg_hw(note, *output_shift);
                dmg::render_dmg_wave(
                    ram,
                    wsh,
                    note.frequency(),
                    duration,
                    self.sample_rate,
                    volume,
                    len,
                )
            }
            Waveform::DmgWaveCart {
                index,
                output_shift,
            } => {
                let ram = self
                    .dmg_wave_cart
                    .get(*index)
                    .copied()
                    .unwrap_or_else(dmg_flat_wave_ram);
                let (_, len, _, wsh) = merge_dmg_hw(note, *output_shift);
                dmg::render_dmg_wave(
                    &ram,
                    wsh,
                    note.frequency(),
                    duration,
                    self.sample_rate,
                    volume,
                    len,
                )
            }
            Waveform::DmgNoise { nr43, seven_bit } => {
                let nr43 = match nr43 {
                    Some(b) => *b,
                    None => {
                        let b = dmg::nr43_best_fit(note.frequency());
                        (b & 0xF7) | ((*seven_bit as u8) << 3)
                    }
                };
                let (env, len, _, _) = merge_dmg_hw(note, 1);
                dmg::render_dmg_noise(nr43, duration, self.sample_rate, volume, env, len)
            }
            Waveform::DmgPulse1 {
                duty,
                sweep_pace,
                sweep_shift,
                sweep_subtract,
            } => {
                let (env, len, _, _) = merge_dmg_hw(note, 1);
                dmg::render_dmg_pulse(
                    *duty,
                    Some(dmg::DmgSweep {
                        pace: *sweep_pace,
                        shift: *sweep_shift,
                        subtract: *sweep_subtract,
                    }),
                    note.frequency(),
                    duration,
                    self.sample_rate,
                    volume,
                    env,
                    len,
                )
            }
            Waveform::DmgPulse2 { duty } => {
                let (env, len, _, _) = merge_dmg_hw(note, 1);
                dmg::render_dmg_pulse(
                    *duty,
                    None,
                    note.frequency(),
                    duration,
                    self.sample_rate,
                    volume,
                    env,
                    len,
                )
            }
            _ => {
                let wt = Self::waveform_to_type(&note.waveform).unwrap_or(synth::WaveformType::Triangle);
                self.synth.generate_by_waveform(wt, note.frequency(), duration, volume)
            }
        }
    }

    fn apply_note_effects(&self, samples: &mut Vec<f32>, note: &NoteEvent) {
        use note_parser::Effect;
        let duration_secs = samples.len() as f32 / self.sample_rate as f32;
        for eff in &note.effects {
            match eff {
                Effect::Tremolo { rate, depth } => self.synth.apply_tremolo(samples, *rate, *depth),
                Effect::Vibrato { rate, depth } => self.synth.apply_vibrato(samples, *rate, *depth),
                Effect::Echo { delay_ms, feedback, mix } => self.synth.apply_echo(samples, *delay_ms, *feedback, *mix),
                Effect::Reverb { room_size, damping, mix } => self.synth.apply_reverb(samples, *room_size, *damping, *mix),
                Effect::Chorus { rate, depth, mix } => self.synth.apply_chorus(samples, *rate, *depth, *mix),
                Effect::Lowpass { cutoff, resonance } => self.synth.apply_lowpass(samples, *cutoff, *resonance),
                Effect::Highpass { cutoff, resonance } => self.synth.apply_highpass(samples, *cutoff, *resonance),
                Effect::Distortion { amount } => self.synth.apply_distortion(samples, *amount),
                Effect::Bitcrush { bits, rate_factor } => self.synth.apply_bitcrush(samples, *bits, *rate_factor),
                Effect::Compressor { threshold, ratio, attack_ms, release_ms, makeup_gain } => {
                    self.synth.apply_compressor(samples, *threshold, *ratio, *attack_ms, *release_ms, *makeup_gain);
                }
                Effect::Delay { delay_ms, feedback, mix } => self.synth.apply_delay(samples, *delay_ms, *feedback, *mix),
                Effect::Phaser { rate, depth, feedback, mix } => self.synth.apply_phaser(samples, *rate, *depth, *feedback, *mix),
                Effect::Flanger { rate, depth, feedback, mix } => self.synth.apply_flanger(samples, *rate, *depth, *feedback, *mix),
                Effect::RingMod { carrier_freq, mix } => self.synth.apply_ring_mod(samples, *carrier_freq, *mix),
                Effect::Limiter { threshold, release_ms } => self.synth.apply_limiter(samples, *threshold, *release_ms),
                Effect::Envelope { attack, decay, sustain, release } => {
                    let env = synth::Envelope { attack: *attack, decay: *decay, sustain: *sustain, release: *release };
                    self.synth.apply_envelope(samples, &env, duration_secs);
                }
                Effect::Arpeggio { intervals, rate_hz } => {
                    self.synth.apply_arpeggio(samples, note.frequency(), intervals, *rate_hz);
                }
                Effect::Portamento { target_freq, time_ms } => {
                    if *target_freq > 0.0 {
                        self.synth.apply_portamento(samples, note.frequency(), *target_freq, *time_ms);
                    }
                }
                Effect::AutoPan { rate, depth } => self.synth.apply_autopan(samples, *rate, *depth),
                Effect::Sidechain { threshold, ratio, attack_ms, release_ms } => {
                    self.synth.apply_sidechain(samples, *threshold, *ratio, *attack_ms, *release_ms);
                }
                Effect::Eq { low_gain, mid_gain, high_gain } => {
                    self.synth.apply_eq(samples, *low_gain, *mid_gain, *high_gain);
                }
                Effect::DmgGbEnvelope { .. }
                | Effect::DmgLength { .. }
                | Effect::DmgPan { .. }
                | Effect::DmgWaveOut { .. } => {}
            }
        }
    }
}

fn dmg_flat_wave_ram() -> [u8; 16] {
    [0x88; 16]
}

/// Merge DMG hardware-style effects into envelope, length, pan, and wave output level.
fn merge_dmg_hw(note: &NoteEvent, base_wave_shift: u8) -> (dmg::DmgHwEnvelope, dmg::DmgHwLength, dmg::DmgStereoPan, u8) {
    use note_parser::Effect;
    let mut env = dmg::DmgHwEnvelope::default();
    let mut len = dmg::DmgHwLength::default();
    let mut pan = dmg::DmgStereoPan::default();
    let mut wsh = base_wave_shift.min(3);
    for e in &note.effects {
        match e {
            Effect::DmgGbEnvelope {
                initial,
                increasing,
                pace,
            } => {
                env.initial = (*initial).min(15);
                env.increasing = *increasing;
                env.pace = (*pace).min(7);
            }
            Effect::DmgLength { load, enabled } => {
                len.load = (*load).min(63);
                len.enabled = *enabled;
            }
            Effect::DmgPan { left, right } => {
                pan.left = *left;
                pan.right = *right;
            }
            Effect::DmgWaveOut { shift } => {
                wsh = (*shift).min(3);
            }
            _ => {}
        }
    }
    (env, len, pan, wsh)
}

fn dmg_pan_from_note(note: &NoteEvent) -> dmg::DmgStereoPan {
    use note_parser::Effect;
    let mut pan = dmg::DmgStereoPan::default();
    for e in &note.effects {
        if let Effect::DmgPan { left, right } = e {
            pan.left = *left;
            pan.right = *right;
        }
    }
    pan
}
