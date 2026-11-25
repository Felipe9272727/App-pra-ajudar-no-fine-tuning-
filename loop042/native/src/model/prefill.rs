use super::*;

pub const BLOCK: usize = 4;
type Activations = [Vec<f32>; BLOCK];

impl Model {
    fn mv_block(&self, name: &str, x: &Activations) -> Activations {
        let spec = &self.manifest.tensors[name];
        if spec.kind != "bf16" || (name == "layers.31.mlp.down_proj.weight" && self.dense_override.is_some()) {
            return std::array::from_fn(|i| self.mv(name, &x[i]));
        }
        let (rows, columns) = (spec.shape[0], spec.shape[1]);
        assert!(x.iter().all(|v| v.len() == columns));
        if simd_positive_zero() && self.proven_zero.contains(name)
            && x.iter().flatten().all(|v| v.is_finite()) {
            self.zero_mv_hits.fetch_add(BLOCK as u64, Ordering::Relaxed);
            return std::array::from_fn(|_| vec![0.; rows]);
        }
        let inputs = std::array::from_fn(|i| x[i].as_slice());
        let products: Vec<_> = self.tensor_data(name).par_chunks_exact(columns * 2)
            .map(|row| dot_bf_block(row, inputs).map(bf16)).collect();
        let mut out = std::array::from_fn(|_| Vec::with_capacity(rows));
        for row in products {
            for (output, value) in out.iter_mut().zip(row) {
                output.push(value);
            }
        }
        out
    }

    fn mlp_block(&self, base: &str, x: &Activations) -> Activations {
        let mut gate = self.mv_block(&format!("{base}.mlp.gate_proj.weight"), x);
        let up = self.mv_block(&format!("{base}.mlp.up_proj.weight"), x);
        for (gate, up) in gate.iter_mut().zip(up) {
            for (g, u) in gate.iter_mut().zip(up) {
                *g = bf16(bf16(silu(*g)) * u);
            }
        }
        self.mv_block(&format!("{base}.mlp.down_proj.weight"), &gate)
    }

    fn time_block(&self, base: &str, x: &Activations, (cache, prefix_cache): (&mut Cache, Option<&Cache>),
                  physical: usize, position: usize, rotary: &[[(f32, f32); 32]; BLOCK]) -> Activations {
        if physical % 4 == 3 {
            let prefix = format!("{base}.self_attn");
            let q = self.mv_block(&format!("{prefix}.q_proj.weight"), x);
            let k = self.mv_block(&format!("{prefix}.k_proj.weight"), x);
            let mut v = self.mv_block(&format!("{prefix}.v_proj.weight"), x);
            let window = [7, 15, 27].contains(&physical);
            let outputs = std::array::from_fn(|i| self.attention_projected(&prefix, &q[i], &k[i],
                std::mem::take(&mut v[i]), cache, position + i, window, Some(&rotary[i]), prefix_cache));
            self.mv_block(&format!("{prefix}.o_proj.weight"), &outputs)
        } else {
            let prefix = format!("{base}.linear_attn");
            let qkv = self.mv_block(&format!("{prefix}.in_proj_qkv.weight"), x);
            let z = self.mv_block(&format!("{prefix}.in_proj_z.weight"), x);
            let b = self.mv_block(&format!("{prefix}.in_proj_b.weight"), x);
            let a = self.mv_block(&format!("{prefix}.in_proj_a.weight"), x);
            let outputs = std::array::from_fn(|i| self.delta_projected(&prefix, &qkv[i], &z[i], &b[i], &a[i], cache));
            self.mv_block(&format!("{prefix}.out_proj.weight"), &outputs)
        }
    }

    fn route_block(&self, base: &str, router: &str, norm: &str, residual: &Activations)
        -> (Activations, [Vec<f32>; BLOCK], [Vec<f32>; BLOCK]) {
        let name = format!("{base}.{router}");
        let mut post = std::array::from_fn(|_| Vec::new());
        let mut mix = std::array::from_fn(|_| Vec::new());
        let values = std::array::from_fn(|i| {
            let (branch, p, m) = self.router(&name, &residual[i]);
            post[i] = p;
            mix[i] = m;
            self.norm(base, norm, &branch)
        });
        (values, post, mix)
    }

    pub fn can_prefill_block(&self) -> bool { self.optimize && self.exact_speedups }

    /// Run each physical visit for four tokens, advancing that visit's cache in causal order.
    pub fn prefill_block(&self, session: &mut Session, ids: &[u32], cancel: &AtomicBool) -> Result<Activations> {
        ensure!(self.can_prefill_block() && ids.len() == BLOCK, "Bloco de contexto inválido");
        ensure!(session.position <= MAX_CONTEXT - BLOCK, "CONTEXT_LIMIT: limite de16384tokens atingido");
        let mut h: Activations = Default::default();
        for (h, id) in h.iter_mut().zip(ids) { *h = self.embedding(*id as usize)?; }
        let pos = session.position;
        let mut pass_input: Activations = Default::default();
        let rotary = std::array::from_fn(|i| std::array::from_fn(|j| rotary_factor(pos + i, j)));
        let mut visits = [0usize; 32];
        for (slot, &physical) in self.manifest.execution_plan.iter().enumerate() {
            if cancel.load(Ordering::Relaxed) { bail!("cancelled"); }
            let base = format!("layers.{physical}");
            let visit = visits[physical];
            visits[physical] += 1;
            if (4..28).contains(&physical) {
                if physical == 4 {
                    if self.pass_gates.active() { pass_input.clone_from(&h); }
                    for residual in &mut h { residual.extend_from_within(..); }
                }
                let gain = self.vector(&format!("{base}.native_visit_gain"))[visit];
                let (x, post, mix) = self.route_block(&base, "mhc_attn", "input_layernorm", &h);
                let window = [7, 15, 27].contains(&physical);
                let cache = self.attention_state(&mut session.slots, slot, physical, visit, window);
                let values = self.time_block(&base, &x, cache, physical, pos, &rotary);
                for i in 0..BLOCK { h[i] = Self::merge(&h[i], &values[i], &post[i], &mix[i], gain); }
                let (x, post, mix) = self.route_block(&base, "mhc_ffn", "post_attention_layernorm", &h);
                let values = self.mlp_block(&base, &x);
                for i in 0..BLOCK { h[i] = Self::merge(&h[i], &values[i], &post[i], &mix[i], gain); }
                if physical == 27 {
                    for (i, residual) in h.iter_mut().enumerate() {
                        for i in 0..1024 { residual[i] = bf16((residual[i] + residual[1024 + i]) * 0.5); }
                        residual.truncate(1024);
                        if self.pass_gates.active() { self.pass_gates.mix(visit, &pass_input[i], residual); }
                    }
                }
            } else {
                let x = std::array::from_fn(|i| self.norm(&base, "input_layernorm", &h[i]));
                let values = self.time_block(&base, &x, (&mut session.slots[slot], None), physical, pos, &rotary);
                add_residual(&mut h, values);
                let x = std::array::from_fn(|i| self.norm(&base, "post_attention_layernorm", &h[i]));
                add_residual(&mut h, self.mlp_block(&base, &x));
            }
            ensure!(h.iter().flatten().all(|v| v.is_finite()), "Estado numérico inválido na camada {physical}");
        }
        let norm = self.vector("norm.weight");
        session.position += BLOCK;
        Ok(h.map(|h| rms(&h, norm, true)))
    }
}

fn add_residual(residual: &mut Activations, branch: Activations) {
    for (residual, branch) in residual.iter_mut().zip(branch) {
        for (x, b) in residual.iter_mut().zip(branch) { *x = bf16(*x + b); }
    }
}
