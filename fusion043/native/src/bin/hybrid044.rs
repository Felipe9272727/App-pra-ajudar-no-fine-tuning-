use anyhow::{bail, ensure, Context, Result};
use liquid_sense::{chat::{Chat, GenerationOptions, Message}, model::{Model, Session, PREFILL_BLOCK}};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{cell::RefCell, fs::File, io::{self, Write}, sync::atomic::AtomicBool};
use tokenizers::Tokenizer;

mod weights { include!("hybrid_pack.inc"); }
use weights::pack;

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
        [mode, path, action, input] if mode == "pack" => (pack(path, action == "collect")?, action, input),
        [mode, base, tk, align, gemma, action, input] if mode == "parts" =>
            (parts(base, tk, align, gemma)?, action, input),
        [mode, path, calibration, sha, action, input] if mode == "calibrated" => {
            let (mut model, tokenizer) = pack(path, true)?;
            model.attach_calibration(std::fs::read(calibration)?, sha)?;
            ((model, tokenizer), action, input)
        }
        _ => bail!("hybrid044 pack MODELO.lsmix (ask|bench|parity|collect) INPUT"),
    };
    let (mut model, bytes) = model;
    model.optimize = true;
    let tk = weights::tokenizer(&bytes)?;
    match action.as_str() {
        "bench" => run_batch(model, tk, input, &mut io::stdout().lock()),
        "collect" => collect046(model, tk, input, &mut io::stdout().lock()),
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
include!("../../../../fusion046/collect.inc");
