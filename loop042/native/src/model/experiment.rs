use super::*;
use serde::{Deserialize, Serialize};

pub const WINDOW: usize = 256;

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum KvMode {
    #[default]
    Full,
    Window,
    Hybrid,
}

#[derive(Clone, Copy, Debug, Default, Deserialize, Serialize)]
pub struct PassGates {
    pub bias: [f32; 2],
    pub slope: [f32; 2],
}

impl PassGates {
    pub(super) fn active(self) -> bool {
        self.bias != [0.; 2] || self.slope != [0.; 2]
    }

    pub(super) fn mix(self, visit: usize, input: &[f32], output: &mut [f32]) {
        let feature = if self.slope[visit] == 0. { 0. } else {
            let rms = (input.iter().map(|x| x * x).sum::<f32>() / input.len() as f32 + 1e-6).sqrt();
            let quarter = input.len() / 4;
            let contrast = input[..quarter].iter().sum::<f32>() - input[quarter..2 * quarter].iter().sum::<f32>();
            contrast / (quarter as f32 * rms)
        };
        let retained = 0.5 * (self.bias[visit] + self.slope[visit] * feature).tanh().max(0.);
        if retained > 0. {
            for (state, before) in output.iter_mut().zip(input) {
                *state = bf16(*state + retained * (*before - *state));
            }
        }
    }
}

impl Model {
    pub fn configure_experiment(&mut self, mode: KvMode, gates: PassGates) -> Result<()> {
        ensure!(gates.bias.into_iter().chain(gates.slope).all(|x| x.is_finite() && x.abs() <= 16.),
            "Invalid loop gate parameters");
        self.kv_mode = mode;
        self.pass_gates = gates;
        Ok(())
    }

    // For hybrid global attention, the first pass supplies only positions outside
    // the second pass's own trailing window. Its cache may also hold future prefill positions.
    pub(super) fn attention_state<'a>(&self, slots: &'a mut [Cache], slot: usize, physical: usize,
        visit: usize, window: bool) -> (&'a mut Cache, Option<&'a Cache>) {
        let (past_visits, current) = slots.split_at_mut(slot);
        let prefix = (self.kv_mode == KvMode::Hybrid && visit == 1 && !window)
            .then(|| &past_visits[physical]);
        (&mut current[0], prefix)
    }
}

impl Session {
    pub fn kv_payload_bytes(&self) -> usize {
        self.slots.iter().flat_map(|slot| slot.k.iter().chain(&slot.v))
            .map(|v| v.len() * std::mem::size_of::<f32>()).sum()
    }
}
