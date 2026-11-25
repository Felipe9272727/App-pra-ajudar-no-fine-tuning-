use anyhow::{ensure, Context, Result};
use liquid_sense::model::Model;
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::{fs::File, io::{Read, Seek, SeekFrom}};
use tokenizers::Tokenizer;

const PARENT_045: &str = "e6e4528057543f0bdf35305c87b79197c639f2d77ddfcf140745a62f4441703c";

#[derive(Deserialize)]
struct Region { offset: u64, size: usize, sha256: String }

#[derive(Deserialize)]
struct Manifest { base: Region, alignment: Region, blocks: Region, tokenizer: Region }

pub(super) fn pack(path: &str, exact_parent: bool) -> Result<(Model, Vec<u8>)> {
    let mut file = File::open(path).with_context(|| format!("Não consegui abrir {path}"))?;
    let mut header = [0; 12];
    file.read_exact(&mut header)?;
    ensure!(matches!(&header[..8], b"LSMIX044" | b"LSMIX045"), "Use o checkpoint híbrido .lsmix");
    let length = u32::from_le_bytes(header[8..].try_into()?) as usize;
    ensure!(length < 64 * 1024, "Manifesto grande demais");
    let mut bytes = vec![0; length];
    file.read_exact(&mut bytes)?;
    let m: Manifest = serde_json::from_slice(&bytes)?;
    let expected_blocks = if &header[..8] == b"LSMIX045" { 1_020_000_256 } else { 214_736_896 };
    ensure!(m.blocks.size == expected_blocks, "Versão e blocos Gemma incompatíveis");
    ensure!(m.tokenizer.size < 32 * 1024 * 1024, "Tokenizer grande demais");
    let mut begin = 1024 * 1024;
    let mut buffer = vec![0; 1024 * 1024];
    let mut whole = exact_parent.then(Sha256::new);
    if let Some(hash) = &mut whole {
        file.seek(SeekFrom::Start(0))?;
        file.read_exact(&mut buffer)?;
        hash.update(&buffer);
    }
    for part in [&m.base, &m.alignment, &m.blocks, &m.tokenizer] {
        ensure!(part.offset == begin && part.size > 0, "Região inválida no checkpoint");
        begin = begin.checked_add(part.size as u64).context("Checkpoint grande demais")?;
        ensure!(begin <= file.metadata()?.len(), "Checkpoint incompleto");
        file.seek(SeekFrom::Start(part.offset))?;
        let mut remaining = part.size;
        let mut sha = Sha256::new();
        while remaining != 0 {
            let n = remaining.min(buffer.len());
            file.read_exact(&mut buffer[..n])?;
            sha.update(&buffer[..n]);
            if let Some(hash) = &mut whole { hash.update(&buffer[..n]); }
            remaining -= n;
        }
        ensure!(format!("{:x}", sha.finalize()) == part.sha256, "SHA-256 inválido no checkpoint");
    }
    ensure!(begin == file.metadata()?.len(), "Dados adicionais no checkpoint");
    if let Some(hash) = whole {
        ensure!(format!("{:x}", hash.finalize()) == PARENT_045, "Use o checkpoint 045 publicado e verificado");
    }
    let mut model = Model::region(&file, m.base.offset, m.base.size)?;
    model.attach_deep((&file, m.alignment.offset, m.alignment.size), (&file, m.blocks.offset, m.blocks.size))?;
    file.seek(SeekFrom::Start(m.tokenizer.offset))?;
    let mut tokenizer = vec![0; m.tokenizer.size];
    file.read_exact(&mut tokenizer)?;
    Ok((model, tokenizer))
}

pub(super) fn tokenizer(bytes: &[u8]) -> Result<Tokenizer> {
    let tk = Tokenizer::from_bytes(bytes).map_err(|e| anyhow::anyhow!(e.to_string()))?;
    ensure!(tk.get_vocab_size(true) == 248199 && tk.token_to_id("<|im_end|>") == Some(248046)
        && tk.token_to_id("<think>") == Some(248068), "Tokenizer híbrido incompatível");
    Ok(tk)
}
