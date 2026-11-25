//! Complete Gemma 3 decoder blocks inserted between Liquid Sense loop layers.
use super::*;

const WIDTH: usize = 1152;
const HEAD: usize = 256;
const QUERY: usize = 4 * HEAD;
const MLP: usize = 6912;
const CORE: usize = 1024;
const FIRST_TOKEN: usize = 248070;
const TOKENS: usize = 129;
pub(super) const CACHE_COUNT: usize = 38;
const BLOCK_FLOATS: usize = 4 * WIDTH + 2 * HEAD + 2 * WIDTH * QUERY
    + 2 * WIDTH * HEAD + 3 * WIDTH * MLP;
const ALIGN_FLOATS: usize = 2 * WIDTH * CORE + TOKENS * CORE;
const SMALL_DONOR: [usize; 4] = [5, 11, 17, 23];
const SMALL_INSERTION: [usize; 4] = [7, 13, 19, 25];
const FULL_DONOR: [usize; 19] = [0, 1, 2, 4, 5, 6, 8, 9, 11, 12, 13, 15, 16, 17, 19, 20, 22, 23, 25];
const FULL_INSERTION: [usize; 19] = [4, 5, 6, 8, 9, 10, 11, 13, 14, 15, 16, 17, 19, 20, 21, 22, 24, 25, 26];

pub(super) struct Deep {
    pub(super) blocks: Mmap,
    pub(super) alignment: Mmap,
    donor: &'static [usize],
    insertion: &'static [usize],
    gain: f32,
}

fn project(matrix: &[u8], x: &[f32]) -> Vec<f32> {
    matrix.par_chunks_exact(x.len() * 2).map(|row| bf16(dot_bf(row, x))).collect()
}

fn norm(x: &[f32], weights: &[u8]) -> Vec<f32> {
    let inv = (x.iter().map(|v| v * v).sum::<f32>() / x.len() as f32 + 1e-6).sqrt().recip();
    x.iter().zip(weights.chunks_exact(2)).map(|(v, w)| bf16(v * inv * (1. + read_bf(w)))).collect()
}

fn rotate(x: &mut [f32], position: usize, base: f32) {
    let half = x.len() / 2;
    for i in 0..half {
        let theta = position as f32 / base.powf(i as f32 / half as f32);
        let (sin, cos) = theta.sin_cos();
        let (a, b) = (x[i], x[i + half]);
        x[i] = bf16(a * cos - b * sin);
        x[i + half] = bf16(b * cos + a * sin);
    }
}

impl Deep {
    fn new(blocks: Mmap, alignment: Mmap) -> Result<Self> {
        let (donor, insertion, gain): (&[usize], &[usize], _) = if blocks.len() == FULL_DONOR.len() * BLOCK_FLOATS * 2 {
            (&FULL_DONOR, &FULL_INSERTION, 0.0275)
        } else if blocks.len() == SMALL_DONOR.len() * BLOCK_FLOATS * 2 {
            (&SMALL_DONOR, &SMALL_INSERTION, 0.06)
        } else {
            bail!("Invalid Gemma block size");
        };
        ensure!(alignment.len() == ALIGN_FLOATS * 2, "Invalid fusion alignment size");
        Ok(Self { blocks, alignment, donor, insertion, gain })
    }

    fn forward_block(&self, index: usize, x: &[f32], position: usize, cache: &mut Cache) -> Vec<f32> {
        let mut data = &self.blocks[index * BLOCK_FLOATS * 2..(index + 1) * BLOCK_FLOATS * 2];
        let mut take = |count| {
            let (matrix, tail) = data.split_at(2 * count);
            data = tail;
            matrix
        };
        let normalized = norm(x, take(WIDTH));
        let q = project(take(QUERY * WIDTH), &normalized);
        let k = project(take(HEAD * WIDTH), &normalized);
        let v = project(take(HEAD * WIDTH), &normalized);
        let output = take(WIDTH * QUERY);
        let qnorm = take(HEAD);
        let mut k = norm(&k, take(HEAD));
        let is_global = (self.donor[index] + 1) % 6 == 0;
        let rope = if is_global { 1_000_000. } else { 10_000. };
        rotate(&mut k, position, rope);
        cache.k.push(k);
        cache.v.push(v);
        if !is_global && cache.k.len() > 512 {
            cache.k.remove(0);
            cache.v.remove(0);
        }
        let heads: Vec<_> = q.par_chunks_exact(HEAD).flat_map_iter(|head| {
            let mut head = norm(head, qnorm);
            rotate(&mut head, position, rope);
            let mut scores: Vec<f32> = cache.k.iter().map(|key|
                head.iter().zip(key).map(|(a,b)| a*b).sum::<f32>() * (1. / 16.)
            ).collect();
            let max = scores.iter().copied().fold(f32::NEG_INFINITY, f32::max);
            let total: f32 = scores.iter_mut().map(|s| { *s = (*s - max).exp(); *s }).sum();
            let mut values = vec![0.; HEAD];
            for (score, row) in scores.iter().zip(&cache.v) {
                let p = bf16(score / total);
                for (value, input) in values.iter_mut().zip(row) {
                    *value += p * input;
                }
            }
            values.into_iter().map(bf16)
        }).collect();
        let attn = norm(&project(output, &heads), take(WIDTH));
        let h: Vec<_> = x.iter().zip(attn).map(|(a,b)| bf16(a+b)).collect();
        let normalized = norm(&h, take(WIDTH));
        let mut gate = project(take(MLP * WIDTH), &normalized);
        let up = project(take(MLP * WIDTH), &normalized);
        for (g, u) in gate.iter_mut().zip(up) {
            let v = *g;
            let gelu = 0.5 * v * (1. + (0.7978846 * (v + 0.044715 * v * v * v)).tanh());
            *g = bf16(bf16(gelu) * u);
        }
        let ff = norm(&project(take(WIDTH * MLP), &gate), take(WIDTH));
        h.iter().zip(ff).map(|(a,b)| bf16(a+b)).collect()
    }

    pub(super) fn insert(&self, h: &mut [f32], physical: usize, visit: usize, position: usize, caches: &mut [Cache]) {
        if let Some(index) = self.insertion.iter().position(|&layer| layer == physical) {
            let shared: Vec<_> = h[..CORE].iter().zip(&h[CORE..]).map(|(a,b)| bf16((a+b)*0.5)).collect();
            let split = WIDTH * CORE * 2;
            let x = project(&self.alignment[..split], &shared);
            let donor = self.forward_block(index, &x, position, &mut caches[index + visit * self.insertion.len()]);
            let delta: Vec<_> = donor.iter().zip(x).map(|(a,b)| a-b).collect();
            let projected = project(&self.alignment[split..2*split], &delta);
            // Scale the correction to this layer's residual and share it with both mHC streams.
            let scale = self.gain * (shared.iter().map(|v| v*v).sum::<f32>() / CORE as f32).sqrt();
            for stream in h.chunks_exact_mut(CORE) {
                for (value, shift) in stream.iter_mut().zip(&projected) {
                    *value = bf16(*value + scale * shift.tanh());
                }
            }
        }
    }

    fn row(&self, index: usize) -> &[u8] {
        let start = 4 * WIDTH * CORE + 2 * CORE * index;
        &self.alignment[start..start + 2 * CORE]
    }

    pub(super) fn embedding(&self, id: usize) -> Option<Vec<f32>> {
        let index = id.checked_sub(FIRST_TOKEN)?;
        (index < TOKENS).then(|| self.row(index).chunks_exact(2).map(read_bf).collect())
    }

    pub(super) fn logits(&self, model: &Model, h: &[f32]) -> Vec<f32> {
        let mut result = model.mv("embed_tokens.weight", h);
        for i in 0..TOKENS {
            result[FIRST_TOKEN + i] = bf16(dot_bf(self.row(i), h)) - 0.75;
        }
        result
    }
}

impl Model {
    pub fn attach_deep(&mut self, alignment: (&File, u64, usize), blocks: (&File, u64, usize)) -> Result<()> {
        ensure!(self.manifest.source_checkpoint_sha256 == PRINCIPAL && self.graft.is_none()
            && self.deep.is_none() && self.readout.is_none() && self.overrides.is_empty()
            && self.dense_override.is_none(), "Gemma decoder requires the published Base checkpoint");
        let map = |(f,offset,size): (&File,u64,usize)| -> Result<Mmap> {
            Ok(unsafe { MmapOptions::new().offset(offset).len(size).map(f)? })
        };
        self.deep = Some(Deep::new(map(blocks)?, map(alignment)?)?);
        Ok(())
    }
}
