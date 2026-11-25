const NEGATIVES: usize = 23;

#[derive(Deserialize)]
struct CalibrationCase {
    id: String,
    split: String,
    domain: String,
    prompt: String,
    thought: Option<String>,
    completion: Option<String>,
}

fn collect046(model: Model, tk: Tokenizer, dataset: &str, output: &mut impl Write) -> Result<()> {
    let cases: Vec<CalibrationCase> = serde_json::from_reader(File::open(dataset)?)?;
    let provider = "You are a helpful assistant.";
    let cancel = AtomicBool::new(false);
    let valid = tk.get_vocab_size(true);
    let encode = |text: &str| -> Result<Vec<u32>> {
        Ok(tk.encode(text, false).map_err(|e| anyhow::anyhow!(e.to_string()))?.get_ids().to_vec())
    };
    let inputs: Vec<_> = cases.iter().map(|row| {
        let item = Message {role: "user".into(), content: row.prompt.clone(), internal: false};
        let mut prefix = liquid_sense::chat::render(provider, &[item]);
        if row.thought.is_some() {
            prefix.truncate(prefix.len() - "\n</think>\n\n".len());
        }
        encode(&prefix)
    }).collect::<Result<_>>()?;
    ensure!(!inputs.is_empty(), "Empty calibration corpus");
    let common = (0..inputs.iter().map(Vec::len).min().unwrap())
        .take_while(|&i| inputs.iter().all(|item| item[i] == inputs[0][i])).count();
    let mut prefix_session = Session::new();
    prefix_session.deep_response = Some(Box::new([0.; 38]));
    let mut prefix_hidden = Vec::new();
    let mut next = |session: &mut Session, ids: &[u32], last: &mut Vec<f32>| -> Result<()> {
        let mut chunks = ids.chunks_exact(PREFILL_BLOCK);
        for block in &mut chunks {
            let mut h = model.prefill_block(session, block, &cancel)?;
            *last = std::mem::take(&mut h[PREFILL_BLOCK - 1]);
        }
        for &id in chunks.remainder() { *last = model.token(session, id, &cancel, false)?.0; }
        Ok(())
    };
    next(&mut prefix_session, &inputs[0][..common], &mut prefix_hidden)?;
    for (case, input) in cases.into_iter().zip(inputs) {
        ensure!(matches!(case.split.as_str(), "train" | "dev"), "Unknown calibration split");
        let mut h = prefix_hidden.clone();
        let mut session = prefix_session.clone();
        next(&mut session, &input[common..], &mut h)?;
        let completion = if let Some(answer) = &case.completion {
            let final_text = if let Some(thought) = &case.thought {
                format!("{thought}\n</think>\n\n{answer}<|im_end|>")
            } else {
                format!("{answer}<|im_end|>")
            };
            encode(&final_text)?
        } else { Vec::new() };
        ensure!(completion.len() <= 64, "Target more than 64 tokens");
        let steps = if completion.is_empty() { 5 } else { completion.len() };
        let mut record = Vec::new();
        for j in 0..steps {
            let logits = model.logits(&h);
            let best = liquid_sense::kernels::greedy(&logits[..valid]);
            let target = completion.get(j).copied().map_or(best, |v| v as usize);
            let mut labels: Vec<_> = (0..valid).filter(|&i| i != target).collect();
            let order = |a: &usize,b: &usize| logits[*b].total_cmp(&logits[*a]).then(a.cmp(b));
            labels.select_nth_unstable_by(NEGATIVES, order);
            labels.truncate(NEGATIVES);
            labels.sort_by(order);
            labels.insert(0, target);
            let scores: Vec<_> = labels.iter().map(|&i| logits[i]).collect();
            record.push(json!({"hidden":h,"labels":labels,"scores":scores,
                              "gemma_response":session.deep_response.as_deref().unwrap().as_slice()}));
            if j+1 == steps || (completion.is_empty() && matches!(target,248044|248046)) { break; }
            h = model.token(&mut session, target as u32, &cancel, false)?.0;
        }
        writeln!(output, "{}", json!({"id":case.id,"split":case.split,"domain":case.domain,
            "retention":case.completion.is_none(),"positions":record}))?;
        output.flush()?;
        eprintln!("Collected {}", case.id);
    }
    Ok(())
}
