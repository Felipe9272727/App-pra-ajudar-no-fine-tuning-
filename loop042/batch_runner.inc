#[derive(Deserialize)]
struct Case {
    id: String,
    group: String,
    prompt: String,
    options: liquid_sense::chat::GenerationOptions,
}

fn run_batch(model: Model, tokenizer: Tokenizer, prompts: &str, output: &mut impl Write) -> Result<()> {
    use std::cell::RefCell;
    let cases: Vec<Case> = serde_json::from_reader(File::open(prompts)?)?;
    let chat = Chat { model, tokenizer, tools_prefix: None,
        system: "You are a helpful assistant.".into(), cache: RefCell::new(None), reuse_prefix: false };
    let cancel = AtomicBool::new(false);
    for case in cases {
        let input = [Message { role: "user".into(), content: case.prompt, internal: false }];
        let started = std::time::Instant::now();
        let answer = chat.generate_profile(&input, case.options, &cancel, |_,_,_| {});
        let seconds = started.elapsed().as_secs_f64();
        let mut row = json!({"id":case.id,"group":case.group,"seconds": seconds});
        match answer {
            Ok(value) => row["answer"] = serde_json::to_value(value)?,
            Err(error) => row["error"] = json!(error.to_string()),
        }
        writeln!(output,"{row}")?;
        output.flush()?;
    }
    Ok(())
}
