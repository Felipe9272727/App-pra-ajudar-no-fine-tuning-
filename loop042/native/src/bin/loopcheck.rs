use anyhow::{ensure, Context, Result};
use liquid_sense::{chat::{render, Chat, Message}, kernels::greedy,
    model::{KvMode, Model, PassGates, Session, PREFILL_BLOCK}};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{fs::File, io::{self, Write}, sync::atomic::AtomicBool, time::Instant};
use tokenizers::Tokenizer;

#[derive(Deserialize)]
struct Example { prompt: String, answer: usize }

fn tokenizer(path: &str) -> Result<Tokenizer> {
    Tokenizer::from_file(path).map_err(|e| anyhow::anyhow!(e.to_string()))
}

fn tokens(tok: &Tokenizer, text: &str) -> Result<Vec<u32>> {
    Ok(tok.encode(text, false).map_err(|e| anyhow::anyhow!(e.to_string()))?.get_ids().to_vec())
}

fn prefilling(model: &Model, session: &mut Session, ids: &[u32], cancel: &AtomicBool) -> Result<Vec<f32>> {
    let mut h = Vec::new();
    let mut groups = ids.chunks_exact(PREFILL_BLOCK);
    for ids in &mut groups {
        let mut block = model.prefill_block(session, ids, cancel)?;
        h = std::mem::take(&mut block[PREFILL_BLOCK - 1]);
    }
    for &id in groups.remainder() { h = model.token(session, id, cancel, false)?.0; }
    Ok(h)
}

fn equal(a: &[f32], b: &[f32]) -> bool {
    a.len() == b.len() && a.iter().zip(b).all(|(a,b)| a.to_bits() == b.to_bits())
}

fn cache_suffix(a: &Session, b: &Session) -> bool {
    a.position == b.position && a.slots.iter().zip(&b.slots).all(|(x,y)| {
        equal(&x.conv,&y.conv) && equal(&x.recurrent,&y.recurrent) &&
        x.k.iter().skip(x.k.len() - y.k.len()).zip(&y.k).all(|(a,b)| equal(a,b)) &&
        x.v.iter().skip(x.v.len() - y.v.len()).zip(&y.v).all(|(a,b)| equal(a,b))
    })
}

fn check(mut model: Model, tok: &Tokenizer, cancel: &AtomicBool) -> Result<()> {
    let pattern = tokens(tok,"First read the code, then verify its output and verify its invariants.\n")?;
    let ids: Vec<_> = pattern.iter().copied().cycle().take(272).collect();
    let mut old=Session::new(); let mut compact=Session::new();
    let mut rows=Vec::new(); let mut candidate_token=0;
    let mut full_seconds=0.; let mut compact_seconds=0.;
    let gates=PassGates::default(); let mut n=0;
    for end in [252, 255, 256, 257, 260, 264, 272] {
        model.configure_experiment(KvMode::Full,gates)?;
        let start=Instant::now(); let a=prefilling(&model,&mut old,&ids[n..end],cancel)?;
        full_seconds+=start.elapsed().as_secs_f64();
        model.configure_experiment(KvMode::Window,gates)?;
        let start=Instant::now(); let b=prefilling(&model,&mut compact,&ids[n..end],cancel)?;
        compact_seconds+=start.elapsed().as_secs_f64();
        ensure!(equal(&a,&b) && cache_suffix(&old,&compact),"Window changes states at {end}");
        let x=model.logits(&a); let y=model.logits(&b);
        ensure!(equal(&x,&y),"Window changes logits at {end}");
        candidate_token=greedy(&y) as u32;
        rows.push(json!({"tokens": end, "old_payload":old.kv_payload_bytes(),
            "window_payload":compact.kv_payload_bytes(),"logits_equal":true}));
        n=end;
    }
    model.configure_experiment(KvMode::Window,gates)?;
    let mut cloned=compact.clone();
    let (a, _)=model.token(&mut compact,candidate_token,cancel,false)?;
    let (b, _)=model.token(&mut cloned,candidate_token,cancel,false)?;
    ensure!(equal(&a,&b) && cache_suffix(&compact,&cloned),"Reused cache changed generation");
    // Verify the hybrid never reads future tokens batched by its first pass.
    model.configure_experiment(KvMode::Hybrid,PassGates {bias:[0.5,0.3],slope:[1.,-1.]})?;
    let mut batch=Session::new(); let mut sequential=Session::new();
    let a=prefilling(&model,&mut batch,&ids,cancel)?;
    let mut b=Vec::new();
    for id in ids { b=model.token(&mut sequential,id,cancel,false)?.0; }
    ensure!(equal(&a,&b) && cache_suffix(&batch,&sequential),"Hybrid or gates break causal prefill");
    println!("{}",json!({"checkpoint":model.manifest.source_checkpoint_sha256,"parity":rows,
        "window_clone_equal":true,"hybrid_enabled_gates_batch_vs_sequential_equal":true,
        "full_seconds":full_seconds,"window_seconds":compact_seconds,"hybrid_payload_272": batch.kv_payload_bytes()}));
    Ok(())
}

fn fit(mut model: Model, tok: &Tokenizer, examples: &[Example], cancel: &AtomicBool) -> Result<()> {
    let label_ids: Vec<_> = ["A","B","C","D"].iter().map(|c| tokens(tok,c).map(|t|t[0] as usize)).collect::<Result<_>>()?;
    let prompts: Vec<_> = examples.iter().map(|e| tokens(tok,&render("",&[Message {
        role:"user".into(),content:e.prompt.clone(),internal:false,
    }]))).collect::<Result<_>>()?;
    let mut evaluate = |gates: PassGates| -> Result<f64> {
        model.configure_experiment(KvMode::Window,gates)?;
        let mut loss=0.;
        for (ids,e) in prompts.iter().zip(examples) {
            let h=prefilling(&model,&mut Session::new(),ids,cancel)?;
            let logits=model.logits(&h);
            let scores: Vec<_>=label_ids.iter().map(|&i|logits[i] as f64).collect();
            let max=scores.iter().copied().fold(f64::NEG_INFINITY,f64::max);
            loss+=max+scores.iter().map(|s|(s-max).exp()).sum::<f64>().ln()-scores[e.answer];
        }
        Ok(loss / examples.len() as f64)
    };
    let zero=PassGates::default(); let initial=evaluate(zero)?;
    let mut all=Vec::new();
    for adaptive in [false,true] {
        let mut picked=zero;
        let mut best=initial;
        let mut trial_rows=Vec::new();
        for visit in 0..2 {
            let current=picked;
            for (bias,slope) in if adaptive { [(0.20,-1.5),(0.20,1.5),(0.45,-3.),(0.45,3.)] }
                else {[(0.10,0.),(0.20,0.),(0.35,0.),(0.50,0.)]} {
                let mut trial=current;
                trial.bias[visit]=bias; trial.slope[visit]=slope;
                let loss=evaluate(trial)?;
                eprintln!("fit {} visit {visit}: {loss:.5}",if adaptive {"token"}else{"static"});
                trial_rows.push(json!({"gates":trial,"loss":loss}));
                if loss < best { best=loss; picked=trial; }
            }
        }
        all.push(json!({"adaptive":adaptive,"gates":picked,"loss":best,"trials":trial_rows}));
    }
    println!("{}",json!({"initial_loss":initial,"calibration_examples":examples.len(),"fits":all}));
    Ok(())
}

fn main() -> Result<()> {
    let args: Vec<_>=std::env::args().collect();
    ensure!(args.len() >= 5, "loopcheck LOCATOR TOKENIZER MODE INPUT [variant checkpoint]");
    rayon::ThreadPoolBuilder::new().num_threads(2).build_global()?;
    let loc:Value=serde_json::from_reader(File::open(&args[1])?)?;
    let file=File::open(loc["path"].as_str().context("Missing APK")?)?;
    let mut model=Model::region(&file,loc["model_offset"].as_u64().unwrap(),loc["model_bytes"].as_u64().unwrap() as usize)?;
    model.optimize=true;
    if args.last().is_some_and(|x|x=="epoch02") {
        let patch=unsafe {memmap2::MmapOptions::new().offset(loc["patch_offset"].as_u64().unwrap())
            .len(loc["patch_bytes"].as_u64().unwrap() as usize).map(&file)?};
        ensure!(model.attach_patch(&patch,loc["patch_sha256"].as_str().unwrap())?==381,"Wrong trained checkpoint");
    }
    let tok=tokenizer(&args[2])?;
    let cancel=AtomicBool::new(false);
    match args[3].as_str() {
        "check" => check(model,&tok,&cancel),
        "fit" => {
            let examples: Vec<Example> = serde_json::from_reader(File::open(&args[4])?)?;
            ensure!(!examples.is_empty() && examples.iter().all(|e| e.answer < 4), "Invalid calibration examples");
            fit(model,&tok,&examples,&cancel)
        }
        "bench" => {
            let config:Value=serde_json::from_reader(File::open(&args[5])?)?;
            model.configure_experiment(serde_json::from_value(config["mode"].clone())?,
                serde_json::from_value(config["gates"].clone())?)?;
            let output=io::stdout();
            run_batch(model,tok,&args[4],&mut output.lock())
        }
        _=>anyhow::bail!("Unknown mode"),
    }
}

include!("../../../batch_runner.inc");
