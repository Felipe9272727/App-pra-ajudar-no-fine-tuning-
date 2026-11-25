//! Weight graft from Gemma 3 1B over the existing Liquid Sense readout.
use super::*;
use sha2::{Digest, Sha256};
use std::ops::Range;

const WIDTH: usize = 1152;
const CORE: usize = 1024;
const CHANNELS: usize = 512;
const RANK: usize = 32;
const TOKEN_START: usize = 248070;
const VOCAB_ROWS: usize = 248320;
const GEMMA_SHA: &str = "3d4ef8d71c14db7e448a09ebe891cfb6bf32c57a9b44499ae0d1c098e48516b6";

#[derive(Deserialize)]
struct Token { id: usize, piece: String }

#[derive(Deserialize)]
struct Header {
    kind: String,
    liquid_checkpoint_sha256: String,
    gemma_sha256: String,
    source_layer: u32,
    tokenizer_sha256: String,
    trained: bool,
    tokens: Vec<Token>,
    delta_limit: f32,
    added_token_logit_bias: f32,
}

pub(super) struct Graft {
    bytes: Vec<u8>,
    spans: [Range<usize>; 9],
    pre: Vec<f32>,
    post: Vec<f32>,
    size: usize,
    delta_limit: f32,
    bias: f32,
    active: bool,
}

impl Graft {
    fn open(bytes: Vec<u8>, expected: &str, tokenizer_bytes: &[u8], active: bool) -> Result<Self> {
        ensure!(bytes.starts_with(b"LSFUSE01") && bytes.len() >= 12, "Invalid graft header");
        ensure!(format!("{:x}", Sha256::digest(&bytes)) == expected, "Graft digest mismatch");
        let length = u32::from_le_bytes(bytes[8..12].try_into()?) as usize;
        ensure!(length < 64*1024 && bytes.len() >= 12+length, "Invalid graft manifest length");
        let header: Header = serde_json::from_slice(&bytes[12..12+length])?;
        ensure!(header.kind == "liquid-sense-gemma-3-1b-graft-v1" && header.liquid_checkpoint_sha256 == PRINCIPAL
            && header.gemma_sha256 == GEMMA_SHA && header.source_layer == 25
            && (!active || header.trained), "Wrong graft provenance or missing fit");
        ensure!(format!("{:x}", Sha256::digest(tokenizer_bytes)) == header.tokenizer_sha256,
            "Use the verified hybrid tokenizer with this graft");
        let size = header.tokens.len();
        ensure!(size > 0 && size <= VOCAB_ROWS-TOKEN_START, "Invalid graft vocabulary size");
        let tokenizer = tokenizers::Tokenizer::from_bytes(tokenizer_bytes).map_err(|e| anyhow::anyhow!(e.to_string()))?;
        for (i, t) in header.tokens.iter().enumerate() {
            ensure!(t.id == TOKEN_START+i && tokenizer.token_to_id(&t.piece) == Some(t.id as u32),
                "Graft vocabulary differs from the tokenizer");
        }
        ensure!((0.0..=0.25).contains(&header.delta_limit) && (-10.0..=0.0).contains(&header.added_token_logit_bias),
            "Graft scale out of range");
        let sizes = [WIDTH*CORE, CHANNELS*WIDTH, CHANNELS*WIDTH, WIDTH*CHANNELS, WIDTH,
            WIDTH, RANK*WIDTH, CORE*RANK, size*CORE];
        let mut begin = 12+length;
        let spans = sizes.map(|n| { let r=begin..begin+2*n; begin=r.end; r });
        ensure!(begin == bytes.len(), "Inconsistent graft tensor length");
        for r in &spans {
            ensure!(bytes[r.clone()].chunks_exact(2).all(|v| read_bf(v).is_finite()), "Nonfinite graft weight");
        }
        let pre = bytes[spans[4].clone()].chunks_exact(2).map(read_bf).collect();
        let post = bytes[spans[5].clone()].chunks_exact(2).map(read_bf).collect();
        Ok(Self { bytes,spans,pre,post,size,delta_limit:header.delta_limit,bias:header.added_token_logit_bias,active })
    }

    fn tensor(&self, index: usize) -> &[u8] { &self.bytes[self.spans[index].clone()] }

    fn project(&self,index:usize,x:&[f32]) -> Vec<f32> {
        self.tensor(index).par_chunks_exact(x.len()*2).map(|row|bf16(dot_bf(row,x))).collect()
    }

    fn lex_row(&self,id:usize) -> Option<&[u8]> {
        let row=id.checked_sub(TOKEN_START)?;
        (row<self.size).then(|| &self.tensor(8)[row*CORE*2..(row+1)*CORE*2])
    }

    pub(super) fn embedding(&self,id:usize) -> Option<Vec<f32>> {
        self.lex_row(id).map(|data|data.chunks_exact(2).map(read_bf).collect())
    }

    fn feature(&self,h:&[f32]) -> Vec<f32> {
        let x = rms(&self.project(0,h),&self.pre,true);
        let mut gate = self.project(1,&x);
        let up = self.project(2,&x);
        for (g, u) in gate.iter_mut().zip(up) {
            let v=*g;
            let gelu=0.5*v*(1.0 + (0.7978846*(v+0.044715*v*v*v)).tanh());
            *g = bf16(bf16(gelu)*u);
        }
        rms(&self.project(3,&gate),&self.post,true)
    }

    pub(super) fn logits(&self,model:&Model,h:&[f32]) -> Vec<f32> {
        let updated;
        let hidden=if self.active {
            let compressed=self.project(6,&self.feature(h));
            let delta=self.project(7,&compressed);
            updated=h.iter().zip(delta).map(|(a,b)|bf16(a+self.delta_limit*b.tanh())).collect::<Vec<_>>();
            updated.as_slice()
        } else { h };
        let mut result=model.mv("embed_tokens.weight",hidden);
        for (i,row) in self.tensor(8).chunks_exact(2*CORE).enumerate() {
            result[TOKEN_START+i]=bf16(dot_bf(row,hidden))+self.bias;
        }
        result
    }
}

impl Model {
    pub fn attach_graft(&mut self, bytes:Vec<u8>, expected:&str, tokenizer:&[u8], active:bool) -> Result<()> {
        ensure!(self.manifest.source_checkpoint_sha256 == PRINCIPAL && self.graft.is_none()
            && self.readout.is_none() && self.dense_override.is_none() && self.overrides.is_empty(),
            "Graft requires the published Base checkpoint");
        self.graft=Some(Graft::open(bytes,expected,tokenizer,active)?);
        Ok(())
    }

    pub fn gemma_feature(&self,h:&[f32]) -> Result<Vec<f32>> {
        ensure!(h.len()==CORE && h.iter().all(|x|x.is_finite()), "Invalid Liquid activation for the Gemma graft");
        Ok(self.graft.as_ref().context("Load a graft first")?.feature(h))
    }
}
