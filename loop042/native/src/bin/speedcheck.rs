use anyhow::{ensure, Context, Result};
use liquid_sense::{
    chat::{Chat, GenerationOptions, Message},
    kernels::{attention_values, greedy},
    model::{Model, Session, PREFILL_BLOCK},
};
use serde_json::{json, Value};
use std::{cell::RefCell, fs::File, hint::black_box, sync::atomic::AtomicBool, time::Instant};

fn same(a: &[f32], b: &[f32]) -> bool {
    a.len() == b.len() && a.iter().zip(b).all(|(a, b)| a.to_bits() == b.to_bits())
}

fn same_rows(a: &[Vec<f32>], b: &[Vec<f32>]) -> bool {
    a.len() == b.len() && a.iter().zip(b).all(|(a, b)| same(a, b))
}

fn same_queue(a: &std::collections::VecDeque<Vec<f32>>, b: &std::collections::VecDeque<Vec<f32>>) -> bool {
    a.len() == b.len() && a.iter().zip(b).all(|(a, b)| same(a, b))
}

fn equal_caches(reference: &Session, candidate: &Session) -> bool {
    reference.position == candidate.position && reference.slots.len() == candidate.slots.len()
        && reference.slots.iter().zip(&candidate.slots).all(|(x, y)| {
            same(&x.conv, &y.conv) && same(&x.recurrent, &y.recurrent)
                && same_queue(&x.k, &y.k) && same_queue(&x.v, &y.v)
        })
}

fn exact_prefill(model: &mut Model, inputs: &[u32], cancel: &AtomicBool) -> Result<Value> {
    let mut reference = Session::new();
    let mut candidate = Session::new();
    for (n, chunk) in inputs.chunks_exact(PREFILL_BLOCK).enumerate() {
        model.exact_speedups = false;
        let baseline: Vec<_> = chunk.iter().map(|&id| model.token(&mut reference, id, cancel, false)
            .map(|v| v.0)).collect::<Result<_>>()?;
        model.exact_speedups = true;
        let batch = model.prefill_block(&mut candidate, chunk, cancel)?;
        ensure!(same_rows(&baseline, &batch) && equal_caches(&reference, &candidate),
            "Batched activations/cache differ in block {n}");
        for (b, f) in baseline.iter().zip(&batch) {
            ensure!(same(&model.logits(b), &model.logits(f)), "Batched logits differ in block {n}");
        }
    }
    Ok(json!({"block_size": PREFILL_BLOCK, "tokens_compared": candidate.position,
        "cache_slots": candidate.slots.len(), "state_and_logits_bitwise_equal": true}))
}

fn exact(model: &mut Model, inputs: &[u32], cancel: &AtomicBool) -> Result<Value> {
    let mut reference = Session::new();
    let mut candidate = Session::new();
    let mut next_id = inputs[0];
    let mut generated = Vec::new();
    for step in 0..inputs.len() + 8 {
        let id = inputs.get(step).copied().unwrap_or(next_id);
        model.exact_speedups = false;
        let (a, layers_a) = model.token(&mut reference, id, cancel, true)?;
        model.exact_speedups = true;
        let (b, layers_b) = model.token(&mut candidate, id, cancel, true)?;
        ensure!(same(&a, &b) && same_rows(&layers_a, &layers_b), "Hidden states differ at {step}");
        ensure!(layers_a.len() == 57 && candidate.slots.len() == 56, "Unexpected loop length");
        for (slot, (x, y)) in reference.slots.iter().zip(&candidate.slots).enumerate() {
            ensure!(same(&x.conv, &y.conv) && same(&x.recurrent, &y.recurrent)
                && same_queue(&x.k, &y.k) && same_queue(&x.v, &y.v), "Cache differs at {step}/{slot}");
        }
        let logits_a = model.logits(&a);
        let logits_b = model.logits(&b);
        ensure!(same(&logits_a, &logits_b), "Logits differ at {step}");
        next_id = greedy(&logits_b) as u32;
        if step >= inputs.len() - 1 {
            generated.push(next_id);
        }
    }
    Ok(json!({"prompt_tokens": inputs.len(), "generated_ids": generated,
        "steps": inputs.len() + 8, "hidden_states": 57, "cache_slots": 56,
        "logits": model.manifest.tensors["embed_tokens.weight"].shape[0], "bitwise_equal": true}))
}

fn timings(model: &mut Model, inputs: &[u32], cancel: &AtomicBool) -> Result<Vec<Value>> {
    let mut rows = Vec::new();
    for (index, fast) in [false, true, false, true, true, false, true, false, false, true]
        .into_iter().enumerate() {
        model.exact_speedups = fast;
        let mut session = Session::new();
        let mut hidden = Vec::new();
        let start = Instant::now();
        let mut next = 0;
        if fast {
            for chunk in inputs.chunks_exact(PREFILL_BLOCK) {
                let mut block = model.prefill_block(&mut session, chunk, cancel)?;
                hidden = std::mem::take(&mut block[PREFILL_BLOCK - 1]);
                next += PREFILL_BLOCK;
            }
        }
        for &id in &inputs[next..] {
            hidden = model.token(&mut session, id, cancel, false)?.0;
        }
        let mut id = greedy(&model.logits(&hidden)) as u32;
        let first_token = start.elapsed().as_secs_f64();
        let start = Instant::now();
        for _ in 0..8 {
            hidden = model.token(&mut session, id, cancel, false)?.0;
            id = greedy(&model.logits(&hidden)) as u32;
        }
        rows.push(json!({"run": index, "warmup": index < 2, "optimized": fast,
            "prompt_tokens": inputs.len(), "first_token_seconds": first_token,
            "decode_tokens": 8, "decode_seconds": start.elapsed().as_secs_f64(),
            "final_id": black_box(id)}));
    }
    Ok(rows)
}

fn attention_kernel() -> Result<Vec<Value>> {
    let mut rows = Vec::new();
    let values: Vec<Vec<f32>> = (0..4096)
        .map(|t| (0..512).map(|j| ((t * 13 + j * 17) % 509) as f32 / 250.0 - 1.0).collect())
        .collect();
    for size in [256, 1024, 4096] {
        let values = &values[..size];
        let weights: Vec<f32> = (0..size).map(|i| ((i * 5) % 17) as f32 / (size * 8) as f32).collect();
        let column_major = || -> [f32; 256] {
            std::array::from_fn(|j| values.iter().zip(&weights).map(|(v, w)| *w * v[256 + j]).sum())
        };
        ensure!(same(&column_major(), &attention_values(&weights, values, 256)), "Attention differs at {size}");
        for (n, fast) in [false, true, true, false, false, true, true, false].into_iter().enumerate() {
            let begin = Instant::now();
            for _ in 0..16 {
                black_box(if fast { attention_values(black_box(&weights), black_box(values), 256) }
                          else { black_box(column_major)() });
            }
            rows.push(json!({"context": size, "run": n, "optimized": fast,
                "repetitions": 16, "seconds": begin.elapsed().as_secs_f64(), "bitwise_equal": true}));
        }
    }
    Ok(rows)
}

fn chat_flow(model: Model, tokenizer_path: &str, cancel: &AtomicBool) -> Result<Value> {
    let tokenizer = tokenizers::Tokenizer::from_file(tokenizer_path)
        .map_err(|error| anyhow::anyhow!(error.to_string()))?;
    let mut chat = Chat { model, tokenizer, tools_prefix: None,
        system: "Você é um assistente de programação.".into(),
        cache: RefCell::new(None), reuse_prefix: true };
    let mut answers = Vec::new();
    for fast in [false, true] {
        chat.model.exact_speedups = fast;
        chat.cache.replace(None);
        let mut messages = vec![Message { role: "user".into(),
            content: "Qual é a soma de dois e três? Responda em uma linha.".into(), internal: false }];
        let mut run = Vec::new();
        for thinking in [false, true] {
            let options = GenerationOptions { thinking, reasoning_tokens: 32, response_tokens: 16, context_tokens: 2048 };
            let reply = chat.generate_profile(&messages, options, cancel, |_, _, _| {})?;
            messages.push(Message { role: "assistant".into(), content: reply.text.clone(), internal: false });
            messages.push(Message { role: "user".into(), content: "Dobre a soma anterior.".into(), internal: false });
            let mut output = serde_json::to_value(reply)?;
            let result = output.as_object_mut().context("Invalid chat answer")?;
            for time in ["prefill_seconds", "decode_seconds", "first_token_seconds"] { result.remove(time); }
            run.push(output);
        }
        answers.push(run);
    }
    ensure!(answers[0] == answers[1], "Chat or prefix reuse changed across executors");
    ensure!(answers[0][1]["reused_prompt_tokens"].as_u64().unwrap_or(0) > 0, "Followup did not reuse prefix");
    Ok(json!({"answers": answers.remove(0), "exact": true}))
}

fn main() -> Result<()> {
    let args: Vec<_> = std::env::args().collect();
    let location: Value = serde_json::from_reader(File::open(args.get(1).context("APK locator required")?)?)?;
    let inputs: Vec<u32> = serde_json::from_reader(File::open(args.get(2).context("Prompt ids required")?)?)?;
    ensure!(!inputs.is_empty(), "Empty prompt");
    let threads: usize = args.get(4).context("Thread count required")?.parse()?;
    rayon::ThreadPoolBuilder::new().num_threads(threads).build_global()?;
    let source = File::open(location["path"].as_str().context("APK path required")?)?;
    let mut model = Model::region(&source, location["model_offset"].as_u64().unwrap(),
        location["model_bytes"].as_u64().unwrap() as usize)?;
    model.optimize = true;
    let experimental = args.get(3).is_some_and(|name| name == "epoch02");
    let changed = if experimental {
        let patch = unsafe { memmap2::MmapOptions::new().offset(location["patch_offset"].as_u64().unwrap())
            .len(location["patch_bytes"].as_u64().unwrap() as usize).map(&source)? };
        let changed = model.attach_patch(&patch, location["patch_sha256"].as_str().unwrap())?;
        ensure!(changed == 381, "Wrong trained checkpoint");
        changed
    } else { 0 };
    let cancel = AtomicBool::new(false);
    let exact = exact(&mut model, &inputs, &cancel)?;
    let prefill = exact_prefill(&mut model, &inputs, &cancel)?;
    eprintln!("Exact parity verified for checkpoint {}", model.manifest.source_checkpoint_sha256);
    let timings = timings(&mut model, &inputs, &cancel)?;
    let kernels = if experimental { Vec::new() } else { attention_kernel()? };
    let checkpoint=model.manifest.source_checkpoint_sha256.clone();
    let flow=args.get(5).map(|tokenizer|chat_flow(model,tokenizer,&cancel)).transpose()?;
    println!("{}", json!({"checkpoint": checkpoint, "changed_tensors": changed,
        "arch": std::env::consts::ARCH, "threads": threads, "parity": exact, "prefill_parity": prefill,
        "timing": timings, "attention_kernel": kernels, "chat_history_parity": flow}));
    Ok(())
}
