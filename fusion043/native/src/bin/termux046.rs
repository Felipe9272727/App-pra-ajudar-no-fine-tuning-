use anyhow::{bail, ensure, Context, Result};
use liquid_sense::chat::{Chat, GenerationOptions, Message};
use std::{
    cell::RefCell,
    io::{self, BufRead, IsTerminal, Write},
    sync::atomic::AtomicBool,
};

mod weights {
    include!("hybrid_pack.inc");
}

const IDENTITY: &str = "Liquid Sense × Gemma 046 · Termux 1.0";
const ADAPTER_SHA: &str = "941daca310736af121cdd337317b5e1bddb741b88ea085d684d3760ecc1fecfd";

fn answer(chat: &Chat, history: &mut Vec<Message>, prompt: &str, thinking: bool) -> Result<String> {
    let item = Message { role: "user".into(), content: prompt.into(), internal: false };
    history.push(item);
    let options = GenerationOptions {
        thinking,
        reasoning_tokens: 192,
        response_tokens: 384,
        context_tokens: 16384,
    };
    let result = chat.generate_profile(history, options, &AtomicBool::new(false), |_, _, _| {});
    match result {
        Ok(answer) => {
            history.push(Message { role: "assistant".into(), content: answer.text.clone(), internal: false });
            Ok(answer.text)
        }
        Err(error) => {
            history.pop();
            Err(error)
        }
    }
}

fn interactive(chat: &Chat) -> Result<()> {
    println!("{IDENTITY}");
    println!("/think alterna o raciocínio · /clear limpa a conversa · /exit sai");
    let tty = io::stdin().is_terminal();
    let mut input = io::stdin().lock();
    let mut line = String::new();
    let mut history = Vec::new();
    let mut thinking = false;
    loop {
        if tty {
            print!("Você> ");
            io::stdout().flush()?;
        }
        line.clear();
        if input.read_line(&mut line)? == 0 {
            return Ok(());
        }
        match line.trim() {
            "" => {}
            "/exit" => return Ok(()),
            "/clear" => {
                history.clear();
                chat.cache.replace(None);
                println!("Conversa limpa.");
            }
            "/think" => {
                thinking = !thinking;
                println!("Raciocínio {}.", if thinking { "ativado" } else { "desativado" });
            }
            prompt => {
                if tty { eprintln!("Gerando resposta…"); }
                match answer(chat, &mut history, prompt, thinking) {
                    Ok(response) => println!("Liquid Sense> {response}"),
                    Err(error) => eprintln!("Falha na geração: {error:#}"),
                }
            }
        }
    }
}

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.as_slice() == ["--version"] {
        println!("{IDENTITY}");
        return Ok(());
    }
    let (model_path, adapter_path, prompt) = match args.as_slice() {
        [model, adapter] => (model, adapter, None),
        [model, adapter, prompt] => (model, adapter, Some(prompt)),
        _ => bail!("Uso: liquid-sense-termux MODELO-045.lsmix readout.lscal [pergunta]"),
    };
    let adapter = std::fs::read(adapter_path)
        .with_context(|| format!("Não consegui abrir {adapter_path}"))?;
    ensure!(adapter.len() <= 256 * 1024, "Arquivo de correção 046 inválido");
    rayon::ThreadPoolBuilder::new().num_threads(2).build_global()?;
    eprintln!("Verificando e carregando o modelo 046…");
    let (mut model, data) = weights::pack(model_path, true)?;
    model.attach_calibration(adapter, ADAPTER_SHA)?;
    model.optimize = true;
    let chat = Chat {
        model,
        tokenizer: weights::tokenizer(&data)?,
        tools_prefix: None,
        system: "Você é Liquid Sense, um modelo experimental de um desenvolvedor independente.".into(),
        cache: RefCell::new(None),
        reuse_prefix: true,
    };
    if let Some(prompt) = prompt {
        println!("{}", answer(&chat, &mut Vec::new(), prompt.trim(), false)?);
        Ok(())
    } else {
        interactive(&chat)
    }
}
