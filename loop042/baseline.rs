use anyhow::{Context, Result};
use liquid_sense::{chat::{Chat, Message}, model::Model};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{fs::File, io::{self,Write}, sync::atomic::AtomicBool};
use tokenizers::Tokenizer;

fn main() -> Result<()> {
    let args:Vec<_>=std::env::args().collect();
    rayon::ThreadPoolBuilder::new().num_threads(2).build_global()?;
    let loc:Value=serde_json::from_reader(File::open(&args[1])?)?;
    let file=File::open(loc["path"].as_str().context("Missing APK")?)?;
    let mut model=Model::region(&file,loc["model_offset"].as_u64().unwrap(),loc["model_bytes"].as_u64().unwrap() as usize)?;
    model.optimize=true;
    let tokenizer=Tokenizer::from_file(&args[2]).map_err(|e| anyhow::anyhow!(e.to_string()))?;
    run_batch(model,tokenizer,&args[3],&mut io::stdout().lock())
}

include!(env!("LOOP042_BATCH_RUNNER"));
