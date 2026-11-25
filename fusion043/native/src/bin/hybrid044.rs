use anyhow::{bail, ensure, Context, Result};
use liquid_sense::{chat::{Chat, GenerationOptions, Message}, model::{Model, Session, PREFILL_BLOCK}};
use serde::Deserialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{cell::RefCell, fs::File, io::{self, Read, Seek, SeekFrom, Write}, sync::atomic::AtomicBool};
use tokenizers::Tokenizer;

#[derive(Deserialize)]
struct Region { offset: u64, size: usize, sha256: String }

#[derive(Deserialize)]
struct Manifest { base: Region, alignment: Region, blocks: Region, tokenizer: Region }

fn pack(path: &str) -> Result<(Model, Vec<u8>)> {
    let mut file = File::open(path)?;
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
            remaining -= n;
        }
        ensure!(format!("{:x}", sha.finalize()) == part.sha256, "SHA-256 inválido no checkpoint");
    }
    ensure!(begin == file.metadata()?.len(), "Dados adicionais no checkpoint");
    let mut model = Model::region(&file, m.base.offset, m.base.size)?;
    model.attach_deep((&file, m.alignment.offset, m.alignment.size), (&file, m.blocks.offset, m.blocks.size))?;
    file.seek(SeekFrom::Start(m.tokenizer.offset))?;
    let mut tokenizer = vec![0; m.tokenizer.size];
    file.read_exact(&mut tokenizer)?;
    Ok((model, tokenizer))
}

fn parts(loc: &str, tokenizer: &str, alignment: &str, donor: &str) -> Result<(Model, Vec<u8>)> {
    let loc: Value = serde_json::from_reader(File::open(loc)?)?;
    let base = File::open(loc["path"].as_str().context("Missing base")?)?;
    let mut model = Model::region(&base, loc["model_offset"].as_u64().context("Missing offset")?,
                                  loc["model_bytes"].as_u64().context("Missing length")? as usize)?;
    let alignment = File::open(alignment)?;
    let donor = File::open(donor)?;
    model.attach_deep((&alignment, 0, alignment.metadata()?.len() as usize),
                      (&donor, 0, donor.metadata()?.len() as usize))?;
    Ok((model, std::fs::read(tokenizer)?))
}

fn main() -> Result<()> {
    rayon::ThreadPoolBuilder::new().num_threads(2).build_global()?;
    let args: Vec<_> = std::env::args().collect();
    let (model, action, input) = match args[1..].as_ref() {
        [mode, path, action, input] if mode == "pack" => (pack(path)?, action, input),
        [mode, base, tk, align, gemma, action, input] if mode == "parts" =>
            (parts(base, tk, align, gemma)?, action, input),
        _ => bail!("hybrid044 pack MODELO.lsmix (ask|bench|parity) INPUT"),
    };
    let (mut model, bytes) = model;
    model.optimize = true;
    let tk = Tokenizer::from_bytes(&bytes).map_err(|e| anyhow::anyhow!(e.to_string()))?;
    ensure!(tk.get_vocab_size(true) == 248199 && tk.token_to_id("<|im_end|>") == Some(248046)
        && tk.token_to_id("<think>") == Some(248068), "Tokenizer híbrido incompatível");
    match action.as_str() {
        "bench" => run_batch(model, tk, input, &mut io::stdout().lock()),
        "parity" => {
            let ids = tk.encode(input.as_str(), false).map_err(|e| anyhow::anyhow!(e.to_string()))?;
            let ids = ids.get_ids();
            ensure!(ids.len() >= PREFILL_BLOCK, "Use uma frase de teste mais longa");
            let cancel = AtomicBool::new(false);
            let mut a = Session::new();
            let mut b = Session::new();
            let mut chunks = ids.chunks_exact(PREFILL_BLOCK);
            let mut checked = 0;
            for block in &mut chunks {
                let grouped = model.prefill_block(&mut a, block, &cancel)?;
                for (expected, &id) in grouped.iter().zip(block) {
                    let scalar = model.token(&mut b, id, &cancel, false)?.0;
                    ensure!(*expected == scalar, "Diferença entre prefill e geração token a token");
                    checked += 1;
                }
            }
            println!("Paridade exata de ativação para {checked} tokens");
            Ok(())
        }
        "ask" => {
            let chat = Chat { model, tokenizer: tk, tools_prefix: None,
                system: "Você é Liquid Sense, um modelo experimental de um desenvolvedor independente.".into(),
                cache: RefCell::new(None), reuse_prefix: true };
            let item = Message { role: "user".into(), content: input.clone(), internal: false };
            let options = GenerationOptions { thinking: true, reasoning_tokens: 192,
                                               response_tokens: 384, context_tokens: 16384 };
            let answer = chat.generate_profile(&[item], options, &AtomicBool::new(false), |_, _, _| {})?;
            println!("{}", answer.text);
            Ok(())
        }
        _ => bail!("Ação desconhecida"),
    }
}

include!("../../../../loop042/batch_runner.inc");
