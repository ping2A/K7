//! Full synthesizer from survie tracker: waveforms, ADSR, and effects.

use std::f32::consts::PI;
use std::time::Duration;

/// ADSR envelope parameters.
#[derive(Debug, Clone, Copy)]
pub struct Envelope {
    pub attack: f32,
    pub decay: f32,
    pub sustain: f32,
    pub release: f32,
}

impl Default for Envelope {
    fn default() -> Self {
        Self {
            attack: 0.01,
            decay: 0.1,
            sustain: 0.7,
            release: 0.2,
        }
    }
}

impl Envelope {
    pub fn calculate(&self, t: f32, total_duration: f32) -> f32 {
        if t < self.attack {
            t / self.attack
        } else if t < self.attack + self.decay {
            let decay_progress = (t - self.attack) / self.decay;
            1.0 - (1.0 - self.sustain) * decay_progress
        } else if t < total_duration - self.release {
            self.sustain
        } else {
            let release_start = total_duration - self.release;
            let release_progress = (t - release_start) / self.release;
            self.sustain * (1.0 - release_progress)
        }
    }
}

/// Waveform type for generation.
#[derive(Clone, Copy, Debug)]
pub enum WaveformType {
    Sine,
    Square,
    Triangle,
    Sawtooth,
    Pwm(f32),
    Noise,
    PinkNoise,
}

pub struct Synth {
    sample_rate: u32,
}

impl Synth {
    pub fn new(sample_rate: u32) -> Self {
        Self { sample_rate }
    }

    fn envelope(&self, t: f32, total: f32) -> f32 {
        Envelope::default().calculate(t, total)
    }

    pub fn generate_tone_with_envelope(
        &self,
        frequency: f32,
        duration: Duration,
        volume: f32,
        envelope: Option<&Envelope>,
    ) -> Vec<f32> {
        if frequency == 0.0 {
            let n = (duration.as_secs_f32() * self.sample_rate as f32) as usize;
            return vec![0.0; n];
        }
        let num_samples = (duration.as_secs_f32() * self.sample_rate as f32) as usize;
        let mut samples = Vec::with_capacity(num_samples);
        let total_duration = duration.as_secs_f32();
        let default_env = Envelope::default();
        let env = envelope.unwrap_or(&default_env);
        for i in 0..num_samples {
            let t = i as f32 / self.sample_rate as f32;
            let ev = env.calculate(t, total_duration);
            let s = (2.0 * PI * frequency * t).sin() * volume * ev;
            samples.push(s);
        }
        samples
    }

    pub fn generate_tone(&self, frequency: f32, duration: Duration, volume: f32) -> Vec<f32> {
        self.generate_tone_with_envelope(frequency, duration, volume, None)
    }

    pub fn generate_beep(&self, frequency: f32, duration: Duration, volume: f32) -> Vec<f32> {
        if frequency == 0.0 {
            let n = (duration.as_secs_f32() * self.sample_rate as f32) as usize;
            return vec![0.0; n];
        }
        let num_samples = (duration.as_secs_f32() * self.sample_rate as f32) as usize;
        let mut samples = Vec::with_capacity(num_samples);
        let total = duration.as_secs_f32();
        for i in 0..num_samples {
            let t = i as f32 / self.sample_rate as f32;
            let env = self.envelope(t, total);
            let sine = (2.0 * PI * frequency * t).sin();
            samples.push(sine.signum() * volume * env * 0.5);
        }
        samples
    }

    pub fn generate_triangle(&self, frequency: f32, duration: Duration, volume: f32) -> Vec<f32> {
        if frequency == 0.0 {
            let n = (duration.as_secs_f32() * self.sample_rate as f32) as usize;
            return vec![0.0; n];
        }
        let num_samples = (duration.as_secs_f32() * self.sample_rate as f32) as usize;
        let mut samples = Vec::with_capacity(num_samples);
        let total = duration.as_secs_f32();
        for i in 0..num_samples {
            let t = i as f32 / self.sample_rate as f32;
            let env = self.envelope(t, total);
            let phase = (frequency * t) % 1.0;
            let tri = 4.0 * (phase - 0.5).abs() - 1.0;
            samples.push(tri * volume * env);
        }
        samples
    }

    pub fn generate_sawtooth(&self, frequency: f32, duration: Duration, volume: f32) -> Vec<f32> {
        if frequency == 0.0 {
            let n = (duration.as_secs_f32() * self.sample_rate as f32) as usize;
            return vec![0.0; n];
        }
        let num_samples = (duration.as_secs_f32() * self.sample_rate as f32) as usize;
        let mut samples = Vec::with_capacity(num_samples);
        let total = duration.as_secs_f32();
        for i in 0..num_samples {
            let t = i as f32 / self.sample_rate as f32;
            let env = self.envelope(t, total);
            let phase = (frequency * t) % 1.0;
            let saw = 2.0 * phase - 1.0;
            samples.push(saw * volume * env * 0.5);
        }
        samples
    }

    pub fn generate_pwm(
        &self,
        frequency: f32,
        duration: Duration,
        volume: f32,
        pulse_width: f32,
    ) -> Vec<f32> {
        if frequency == 0.0 {
            let n = (duration.as_secs_f32() * self.sample_rate as f32) as usize;
            return vec![0.0; n];
        }
        let pw = pulse_width.clamp(0.1, 0.9);
        let num_samples = (duration.as_secs_f32() * self.sample_rate as f32) as usize;
        let mut samples = Vec::with_capacity(num_samples);
        let total = duration.as_secs_f32();
        for i in 0..num_samples {
            let t = i as f32 / self.sample_rate as f32;
            let env = self.envelope(t, total);
            let phase = (frequency * t) % 1.0;
            let pwm = if phase < pw { 1.0 } else { -1.0 };
            samples.push(pwm * volume * env * 0.5);
        }
        samples
    }

    pub fn generate_noise(&self, duration: Duration, volume: f32) -> Vec<f32> {
        let num_samples = (duration.as_secs_f32() * self.sample_rate as f32) as usize;
        let mut samples = Vec::with_capacity(num_samples);
        let total = duration.as_secs_f32();
        let mut seed = 1234567u32;
        for i in 0..num_samples {
            let t = i as f32 / self.sample_rate as f32;
            let env = self.envelope(t, total);
            seed = seed.wrapping_mul(1664525).wrapping_add(1013904223);
            let noise = ((seed as f32 / u32::MAX as f32) * 2.0 - 1.0) * volume * env;
            samples.push(noise);
        }
        samples
    }

    pub fn generate_pink_noise(&self, duration: Duration, volume: f32) -> Vec<f32> {
        let num_samples = (duration.as_secs_f32() * self.sample_rate as f32) as usize;
        let mut samples = Vec::with_capacity(num_samples);
        let total = duration.as_secs_f32();
        let mut b0 = 0.0f32;
        let mut b1 = 0.0f32;
        let mut b2 = 0.0f32;
        let mut b3 = 0.0f32;
        let mut b4 = 0.0f32;
        let mut b5 = 0.0f32;
        let mut b6 = 0.0f32;
        let mut seed = 1234567u32;
        for i in 0..num_samples {
            let t = i as f32 / self.sample_rate as f32;
            let env = self.envelope(t, total);
            seed = seed.wrapping_mul(1664525).wrapping_add(1013904223);
            let white = (seed as f32 / u32::MAX as f32) * 2.0 - 1.0;
            b0 = 0.99886 * b0 + white * 0.0555179;
            b1 = 0.99332 * b1 + white * 0.0750759;
            b2 = 0.96900 * b2 + white * 0.1538520;
            b3 = 0.86650 * b3 + white * 0.3104856;
            b4 = 0.55000 * b4 + white * 0.5329522;
            b5 = -0.7616 * b5 - white * 0.0168980;
            let pink = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
            b6 = white * 0.115926;
            samples.push(pink * 0.11 * volume * env);
        }
        samples
    }

    /// Generate samples for a given waveform type.
    pub fn generate_by_waveform(
        &self,
        waveform: WaveformType,
        frequency: f32,
        duration: Duration,
        volume: f32,
    ) -> Vec<f32> {
        match waveform {
            WaveformType::Sine => self.generate_tone(frequency, duration, volume),
            WaveformType::Square => self.generate_beep(frequency, duration, volume),
            WaveformType::Triangle => self.generate_triangle(frequency, duration, volume),
            WaveformType::Sawtooth => self.generate_sawtooth(frequency, duration, volume),
            WaveformType::Pwm(pw) => self.generate_pwm(frequency, duration, volume, pw),
            WaveformType::Noise => self.generate_noise(duration, volume),
            WaveformType::PinkNoise => self.generate_pink_noise(duration, volume),
        }
    }

    /// Generate layered waveform (mix of multiple waveforms with blend amounts).
    pub fn generate_layered(
        &self,
        frequency: f32,
        duration: Duration,
        volume: f32,
        layers: &[(WaveformType, f32)],
    ) -> Vec<f32> {
        if frequency == 0.0 || layers.is_empty() {
            let n = (duration.as_secs_f32() * self.sample_rate as f32) as usize;
            return vec![0.0; n];
        }
        let num_samples = (duration.as_secs_f32() * self.sample_rate as f32) as usize;
        let mut samples = vec![0.0; num_samples];
        for (wt, blend) in layers {
            let wave_samples = self.generate_by_waveform(*wt, frequency, duration, volume * blend);
            for (i, &s) in wave_samples.iter().enumerate() {
                if i < samples.len() {
                    samples[i] += s;
                }
            }
        }
        let max_amp = samples.iter().fold(0.0f32, |m, &s| m.max(s.abs()));
        if max_amp > 1.0 {
            for s in &mut samples {
                *s /= max_amp;
            }
        }
        samples
    }

    /// Apply ADSR envelope to samples (in-place).
    pub fn apply_envelope(&self, samples: &mut [f32], envelope: &Envelope, duration_secs: f32) {
        for (i, s) in samples.iter_mut().enumerate() {
            let t = i as f32 / self.sample_rate as f32;
            *s *= envelope.calculate(t, duration_secs);
        }
    }

    /// Arpeggio: cycle through chord intervals at rate_hz, preserving amplitude envelope.
    pub fn apply_arpeggio(
        &self,
        samples: &mut Vec<f32>,
        base_freq: f32,
        intervals: &[i32],
        rate_hz: f32,
    ) {
        if intervals.is_empty() || rate_hz <= 0.0 {
            return;
        }
        let original = samples.clone();
        let cycle_samples = (self.sample_rate as f32 / rate_hz) as usize;
        let notes_per_cycle = intervals.len();
        let samples_per_note = (cycle_samples / notes_per_cycle).max(1);
        for i in 0..samples.len() {
            let cycle_pos = i % cycle_samples;
            let note_index = (cycle_pos / samples_per_note).min(intervals.len().saturating_sub(1));
            let semitone = intervals[note_index];
            let freq_mult = 2.0f32.powf(semitone as f32 / 12.0);
            let target_freq = base_freq * freq_mult;
            let t = i as f32 / self.sample_rate as f32;
            let phase = (2.0 * PI * target_freq * t).sin();
            let env = original[i].abs();
            samples[i] = phase * env;
        }
    }

    /// Portamento: smooth pitch slide from start_freq to target_freq over time_ms.
    /// If target_freq <= 0, no-op (used when "next note" is not available).
    pub fn apply_portamento(
        &self,
        samples: &mut [f32],
        start_freq: f32,
        target_freq: f32,
        time_ms: f32,
    ) {
        if start_freq <= 0.0 || target_freq <= 0.0 || time_ms <= 0.0 {
            return;
        }
        let slide_samps = ((time_ms / 1000.0) * self.sample_rate as f32) as usize;
        let slide_samps = slide_samps.min(samples.len());
        if slide_samps == 0 {
            return;
        }
        let mut phase = 0.0f32;
        for i in 0..samples.len() {
            let t = (i as f32 / slide_samps as f32).min(1.0);
            let freq_ratio = target_freq / start_freq;
            let current_freq = start_freq * freq_ratio.powf(t);
            phase += 2.0 * PI * current_freq / self.sample_rate as f32;
            let env = samples[i].abs();
            samples[i] = phase.sin() * env;
        }
    }

    /// AutoPan: stereo pan modulation (mono buffer: modulate amplitude as L/R balance).
    pub fn apply_autopan(&self, samples: &mut [f32], rate: f32, depth: f32) {
        let depth = depth.clamp(0.0, 1.0);
        for (i, s) in samples.iter_mut().enumerate() {
            let t = i as f32 / self.sample_rate as f32;
            let pan = 0.5 + 0.5 * depth * (2.0 * PI * rate * t).sin();
            *s *= 2.0 * (1.0 - pan).max(pan);
        }
    }

    /// Sidechain ducking (simplified: gain reduction envelope).
    pub fn apply_sidechain(
        &self,
        samples: &mut [f32],
        _threshold: f32,
        ratio: f32,
        attack_ms: f32,
        release_ms: f32,
    ) {
        let ratio = ratio.clamp(1.0, 20.0);
        let attack_c = Self::envelope_coeff(attack_ms, self.sample_rate);
        let release_c = Self::envelope_coeff(release_ms, self.sample_rate);
        let mut env = 0.0f32;
        for s in samples.iter_mut() {
            let lvl = s.abs();
            if lvl > env {
                env += (lvl - env) * attack_c;
            } else {
                env += (lvl - env) * release_c;
            }
            let gain = 1.0 / (1.0 + (env * (ratio - 1.0)));
            *s *= gain;
        }
    }

    /// 3-band EQ: apply low/mid/high gain in dB (simplified: single combined gain).
    pub fn apply_eq(&self, samples: &mut [f32], low_db: f32, mid_db: f32, high_db: f32) {
        let combined_db = (low_db + mid_db + high_db) / 3.0;
        let g = 10.0f32.powf(combined_db / 20.0);
        for s in samples.iter_mut() {
            *s *= g;
        }
    }

    // --- Effects (from survie) ---

    pub fn apply_tremolo(&self, samples: &mut [f32], rate: f32, depth: f32) {
        let depth = depth.clamp(0.0, 1.0);
        for (i, s) in samples.iter_mut().enumerate() {
            let t = i as f32 / self.sample_rate as f32;
            let mod_ = 1.0 - depth + depth * (2.0 * PI * rate * t).sin();
            *s *= mod_;
        }
    }

    pub fn apply_vibrato(&self, samples: &mut [f32], rate: f32, depth: f32) {
        let depth = depth.clamp(0.0, 0.1);
        for (i, s) in samples.iter_mut().enumerate() {
            let t = i as f32 / self.sample_rate as f32;
            let pitch_mod = 1.0 + depth * (2.0 * PI * rate * t).sin();
            *s *= pitch_mod;
        }
    }

    pub fn apply_echo(
        &self,
        samples: &mut Vec<f32>,
        delay_ms: f32,
        feedback: f32,
        mix: f32,
    ) {
        let delay_samps =
            ((delay_ms / 1000.0) * self.sample_rate as f32) as usize;
        let feedback = feedback.clamp(0.0, 0.95);
        let mix = mix.clamp(0.0, 1.0);
        if delay_samps >= samples.len() {
            return;
        }
        let orig = samples.clone();
        for i in delay_samps..samples.len() {
            let echo = orig[i - delay_samps] * feedback;
            samples[i] = samples[i] * (1.0 - mix) + (samples[i] + echo) * mix;
        }
    }

    pub fn apply_reverb(
        &self,
        samples: &mut Vec<f32>,
        room_size: f32,
        damping: f32,
        mix: f32,
    ) {
        let room_size = room_size.clamp(0.0, 1.0);
        let damping = damping.clamp(0.0, 1.0);
        let mix = mix.clamp(0.0, 1.0);
        let delays = [
            (37.0 * room_size, 0.7 * (1.0 - damping)),
            (47.0 * room_size, 0.65 * (1.0 - damping)),
            (53.0 * room_size, 0.6 * (1.0 - damping)),
            (61.0 * room_size, 0.55 * (1.0 - damping)),
        ];
        let orig = samples.clone();
        for (delay_ms, fb) in delays.iter() {
            let delay_samps = ((delay_ms / 1000.0) * self.sample_rate as f32) as usize;
            if delay_samps < samples.len() {
                for i in delay_samps..samples.len() {
                    samples[i] += orig[i - delay_samps] * fb * mix;
                }
            }
        }
        let max = samples
            .iter()
            .fold(0.0f32, |m, &x| m.max(x.abs()));
        if max > 1.0 {
            for s in samples.iter_mut() {
                *s /= max;
            }
        }
    }

    pub fn apply_chorus(&self, samples: &mut Vec<f32>, rate: f32, depth: f32, mix: f32) {
        let depth = depth.clamp(0.0, 20.0);
        let mix = mix.clamp(0.0, 1.0);
        let max_delay = ((depth / 1000.0) * self.sample_rate as f32) as usize;
        let orig = samples.clone();
        for i in max_delay..samples.len() {
            let t = i as f32 / self.sample_rate as f32;
            let lfo = (2.0 * PI * rate * t).sin();
            let delay_ms = (depth / 2.0) * (1.0 + lfo);
            let delay_samps = ((delay_ms / 1000.0) * self.sample_rate as f32) as usize;
            if i >= delay_samps {
                let chorus_samp = orig[i - delay_samps];
                samples[i] = samples[i] * (1.0 - mix) + (samples[i] + chorus_samp) * mix * 0.5;
            }
        }
    }

    pub fn apply_lowpass(&self, samples: &mut [f32], cutoff: f32, resonance: f32) {
        let cutoff = cutoff.clamp(20.0, 20000.0);
        let resonance = resonance.clamp(0.0, 1.0);
        let rc = 1.0 / (2.0 * PI * cutoff);
        let dt = 1.0 / self.sample_rate as f32;
        let alpha = dt / (rc + dt);
        let mut prev = 0.0f32;
        for s in samples.iter_mut() {
            prev = prev + alpha * (*s - prev);
            *s = prev * (1.0 + resonance);
        }
    }

    pub fn apply_highpass(&self, samples: &mut [f32], cutoff: f32, resonance: f32) {
        let cutoff = cutoff.clamp(20.0, 20000.0);
        let resonance = resonance.clamp(0.0, 1.0);
        let rc = 1.0 / (2.0 * PI * cutoff);
        let dt = 1.0 / self.sample_rate as f32;
        let alpha = rc / (rc + dt);
        let mut prev_in = 0.0f32;
        let mut prev_out = 0.0f32;
        for s in samples.iter_mut() {
            let cur = *s;
            let out = alpha * (prev_out + cur - prev_in);
            *s = out * (1.0 + resonance);
            prev_in = cur;
            prev_out = out;
        }
    }

    pub fn apply_distortion(&self, samples: &mut [f32], amount: f32) {
        let amount = amount.clamp(0.0, 1.0);
        for s in samples.iter_mut() {
            let x = *s * (1.0 + amount * 10.0);
            *s = if x > 1.0 {
                1.0
            } else if x < -1.0 {
                -1.0
            } else {
                x - (x.powi(3)) / 3.0
            };
        }
    }

    pub fn apply_bitcrush(&self, samples: &mut [f32], bits: f32, rate_factor: f32) {
        let bits = bits.clamp(1.0, 16.0);
        let levels = 2.0f32.powf(bits);
        let rate_factor = rate_factor.clamp(0.1, 1.0);
        let step = (1.0 / rate_factor) as usize;
        let mut last = 0.0f32;
        for (i, s) in samples.iter_mut().enumerate() {
            if i % step == 0 {
                last = (*s * levels).round() / levels;
            }
            *s = last;
        }
    }

    fn db_to_linear(db: f32) -> f32 {
        10.0f32.powf(db / 20.0)
    }

    fn envelope_coeff(time_ms: f32, sample_rate: u32) -> f32 {
        let time_samps = (time_ms / 1000.0) * sample_rate as f32;
        1.0 - (-1.0 / time_samps).exp()
    }

    pub fn apply_compressor(
        &self,
        samples: &mut [f32],
        threshold_db: f32,
        ratio: f32,
        attack_ms: f32,
        release_ms: f32,
        makeup_db: f32,
    ) {
        if samples.is_empty() {
            return;
        }
        let threshold_db = threshold_db.clamp(-60.0, 0.0);
        let ratio = ratio.clamp(1.0, 20.0);
        let attack_ms = attack_ms.max(0.1);
        let release_ms = release_ms.max(1.0);
        let makeup_db = makeup_db.clamp(0.0, 24.0);
        let threshold = Self::db_to_linear(threshold_db);
        let makeup = Self::db_to_linear(makeup_db);
        let attack_c = Self::envelope_coeff(attack_ms, self.sample_rate);
        let release_c = Self::envelope_coeff(release_ms, self.sample_rate);
        let mut env = 0.0f32;
        for s in samples.iter_mut() {
            let lvl = s.abs();
            if lvl > env {
                env += (lvl - env) * attack_c;
            } else {
                env += (lvl - env) * release_c;
            }
            let gain = if env > threshold {
                let over = env / threshold;
                threshold * over.powf(1.0 / ratio) / env
            } else {
                1.0
            };
            *s = *s * gain * makeup;
        }
    }

    pub fn apply_delay(
        &self,
        samples: &mut Vec<f32>,
        delay_ms: f32,
        feedback: f32,
        mix: f32,
    ) {
        let delay_samps = ((delay_ms / 1000.0) * self.sample_rate as f32) as usize;
        let feedback = feedback.clamp(0.0, 0.95);
        let mix = mix.clamp(0.0, 1.0);
        if delay_samps == 0 || delay_samps >= samples.len() {
            return;
        }
        let orig = samples.clone();
        let mut buf = vec![0.0; delay_samps];
        let mut wp = 0usize;
        for i in 0..samples.len() {
            let delayed = buf[wp];
            buf[wp] = orig[i] + delayed * feedback;
            samples[i] = orig[i] * (1.0 - mix) + delayed * mix;
            wp = (wp + 1) % delay_samps;
        }
    }

    pub fn apply_phaser(
        &self,
        samples: &mut Vec<f32>,
        rate: f32,
        depth: f32,
        feedback: f32,
        mix: f32,
    ) {
        let depth = depth.clamp(0.0, 1.0);
        let feedback = feedback.clamp(0.0, 0.95);
        let mix = mix.clamp(0.0, 1.0);
        let orig = samples.clone();
        let num_stages = 4;
        let mut stages = vec![0.0f32; num_stages];
        for i in 0..samples.len() {
            let t = i as f32 / self.sample_rate as f32;
            let lfo = (2.0 * PI * rate * t).sin();
            let sweep = 0.5 + 0.5 * depth * lfo;
            let coef = (1.0 - sweep) / (1.0 + sweep);
            let mut out = orig[i];
            for st in 0..num_stages {
                let inp = out;
                out = coef * (out - stages[st]) + stages[st];
                stages[st] = inp;
            }
            out = out + samples[i] * feedback;
            samples[i] = orig[i] * (1.0 - mix) + out * mix;
        }
    }

    pub fn apply_flanger(
        &self,
        samples: &mut Vec<f32>,
        rate: f32,
        depth: f32,
        feedback: f32,
        mix: f32,
    ) {
        let depth = depth.clamp(0.0, 10.0);
        let feedback = feedback.clamp(-0.95, 0.95);
        let mix = mix.clamp(0.0, 1.0);
        let max_samps = ((depth / 1000.0) * self.sample_rate as f32) as usize + 1;
        let orig = samples.clone();
        let mut buf = vec![0.0; max_samps];
        let mut wp = 0usize;
        for i in 0..samples.len() {
            let t = i as f32 / self.sample_rate as f32;
            let lfo = (2.0 * PI * rate * t).sin();
            let delay_ms = (depth / 2.0) * (1.0 + lfo);
            let delay_samps = ((delay_ms / 1000.0) * self.sample_rate as f32) as usize;
            let delay_samps = delay_samps.min(max_samps - 1);
            let rp = (wp + max_samps - delay_samps) % max_samps;
            let delayed = buf[rp];
            buf[wp] = orig[i] + delayed * feedback;
            samples[i] = orig[i] * (1.0 - mix) + delayed * mix;
            wp = (wp + 1) % max_samps;
        }
    }

    pub fn apply_ring_mod(&self, samples: &mut [f32], carrier_hz: f32, mix: f32) {
        let carrier_hz = carrier_hz.clamp(0.1, 20000.0);
        let mix = mix.clamp(0.0, 1.0);
        for (i, s) in samples.iter_mut().enumerate() {
            let t = i as f32 / self.sample_rate as f32;
            let car = (2.0 * PI * carrier_hz * t).sin();
            let mod_ = *s * car;
            *s = *s * (1.0 - mix) + mod_ * mix;
        }
    }

    pub fn apply_limiter(&self, samples: &mut [f32], threshold_db: f32, release_ms: f32) {
        let threshold_db = threshold_db.clamp(-12.0, 0.0);
        let release_ms = release_ms.max(1.0);
        let threshold = Self::db_to_linear(threshold_db);
        let release_c = Self::envelope_coeff(release_ms, self.sample_rate);
        let mut env = 0.0f32;
        for s in samples.iter_mut() {
            let lvl = s.abs();
            if lvl > env {
                env = lvl;
            } else {
                env += (lvl - env) * release_c;
            }
            let gain = if env > threshold { threshold / env } else { 1.0 };
            *s = *s * gain;
        }
    }
}
