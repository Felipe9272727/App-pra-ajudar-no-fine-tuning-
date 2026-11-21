use anyhow::Result;
use liquid_sense::model::{Model, Session};
use std::{io::Write, path::Path, sync::atomic::AtomicBool};
fn main() -> Result<()> {
    rayon::ThreadPoolBuilder::new()
        .num_threads(4)
        .build_global()?;
    let a: Vec<_> = std::env::args().collect();
    let model = Model::open(Path::new(&a[1]))?;
    let tokenizer =
        tokenizers::Tokenizer::from_file(Path::new(&a[1]).parent().unwrap().join("tokenizer.json"))
            .map_err(|e| anyhow::anyhow!(e.to_string()))?;
    let fixtures: serde_json::Value = serde_json::from_slice(&std::fs::read(&a[2])?)?;
    let cancel = AtomicBool::new(false);
    for row in fixtures.as_array().unwrap() {
        let mut s = Session::new();
        let mut hidden = vec![];
        for id in row["ids"].as_array().unwrap() {
            hidden = model
                .token(&mut s, id.as_u64().unwrap() as u32, &cancel, false)?
                .0;
        }
        let mut generated = vec![];
        let mut stopped = false;
        for _ in 0..64 {
            let logits = model.logits(&hidden);
            let next = liquid_sense::kernels::greedy(&logits) as u32;
            if next == 248044 {
                stopped = true;
                break;
            }
            generated.push(next);
            if generated.len() == 64 {
                break;
            }
            hidden = model.token(&mut s, next, &cancel, false)?.0;
        }
        let text = tokenizer
            .decode(&generated, true)
            .map_err(|e| anyhow::anyhow!(e.to_string()))?;
        println!(
            "{}",
            serde_json::json!({"id":row["id"],"output":text,"new_tokens":generated.len(),"hit_limit":!stopped,"native_eos":248044,"branded":false,"prefill":"sequential_cached","precision":model.manifest.quantization})
        );
        std::io::stdout().flush()?;
    }
    Ok(())
}
