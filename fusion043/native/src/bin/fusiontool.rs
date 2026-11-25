use anyhow::{ensure,Context,Result};
use liquid_sense::{chat::{render, Chat, GenerationOptions,Message},model::{Model,Session,PREFILL_BLOCK}};
use serde::Deserialize;
use serde_json::{json,Value};
use std::{cell::RefCell,fs::File,io::{self,Write},sync::atomic::AtomicBool};
use tokenizers::Tokenizer;

#[derive(Deserialize)]
struct Training { split: String, prompt:String, completion:String }

fn encode(tk:&Tokenizer,text:&str)->Result<Vec<u32>> {
    Ok(tk.encode(text,false).map_err(|e|anyhow::anyhow!(e.to_string()))?.get_ids().to_vec())
}

fn collect(model:Model, tk:Tokenizer, path:&str) -> Result<()> {
    let cases:Vec<Training>=serde_json::from_reader(File::open(path)?)?;
    let cancel=AtomicBool::new(false);
    let valid=tk.get_vocab_size(true);
    let output=io::stdout();
    let mut writer=output.lock();
    for case in cases {
        ensure!(matches!(case.split.as_str(),"train"|"validation"), "Unknown calibration split");
        let input=render("", &[Message {role:"user".into(),content:case.prompt,internal:false}]);
        let ids=encode(&tk,&input)?;
        let mut session=Session::new();
        let mut chunks=ids.chunks_exact(PREFILL_BLOCK);
        let mut h=Vec::new();
        for ids in &mut chunks {
            let mut block=model.prefill_block(&mut session,ids,&cancel)?;
            h=std::mem::take(&mut block[PREFILL_BLOCK-1]);
        }
        for &id in chunks.remainder() {h=model.token(&mut session,id,&cancel,false)?.0;}
        let mut target=encode(&tk,&case.completion)?;
        target.extend(encode(&tk,"<|im_end|>")?);
        ensure!(!target.is_empty() && target.len()<=64,"Invalid calibration continuation");
        for (index,&id) in target.iter().enumerate() {
            let scores=model.logits(&h);
            let mut labels:Vec<usize>=(0..valid).filter(|&i|i!=id as usize).collect();
            labels.select_nth_unstable_by(15,|a,b|scores[*b].total_cmp(&scores[*a]).then(a.cmp(b)));
            labels.truncate(15);
            labels.sort_by(|a,b|scores[*b].total_cmp(&scores[*a]).then(a.cmp(b)));
            labels.insert(0,id as usize);
            let base_scores:Vec<_>=labels.iter().map(|&i|scores[i]).collect();
            writeln!(writer,"{}",json!({"split":case.split,"gemma":model.gemma_feature(&h)?,
                "labels":labels,"base_scores":base_scores}))?;
            if index+1<target.len() {h=model.token(&mut session,id,&cancel,false)?.0;}
        }
        writer.flush()?;
    }
    Ok(())
}

fn main()->Result<()> {
    let a:Vec<_>=std::env::args().collect();
    ensure!(a.len()==8,"fusiontool LOCATOR TOKENIZER (base|lexicon|fusion) GRAFT SHA (collect|bench|ask) INPUT");
    rayon::ThreadPoolBuilder::new().num_threads(2).build_global()?;
    let loc:Value=serde_json::from_reader(File::open(&a[1])?)?;
    let file=File::open(loc["path"].as_str().context("Missing APK")?)?;
    let mut model=Model::region(&file,loc["model_offset"].as_u64().context("Missing offset")?,
        loc["model_bytes"].as_u64().context("Missing length")? as usize)?;
    model.optimize=true;
    let tb=std::fs::read(&a[2])?;
    let tk=Tokenizer::from_bytes(&tb).map_err(|e|anyhow::anyhow!(e.to_string()))?;
    match a[3].as_str() {
        "base" => {},
        "lexicon" | "fusion" => model.attach_graft(std::fs::read(&a[4])?,&a[5],&tb,a[3]=="fusion")?,
        _ => anyhow::bail!("Unknown executor variant"),
    }
    match a[6].as_str() {
        "collect"=>collect(model,tk,&a[7]),
        "bench"=>run_batch(model,tk,&a[7],&mut io::stdout().lock()),
        "ask"=>{
            let chat=Chat {model,tokenizer:tk,tools_prefix:None,system:"".into(),
                cache:RefCell::new(None),reuse_prefix:true};
            let options=GenerationOptions{thinking:false,response_tokens:256,reasoning_tokens:0,context_tokens:16384};
            let item=Message{role:"user".into(),content:a[7].clone(),internal:false};
            let answer=chat.generate_profile(&[item],options,&AtomicBool::new(false),|_,_,_|{})?;
            println!("{}",answer.text);
            Ok(())
        }
        _=>anyhow::bail!("Unknown action"),
    }
}

include!("../../../../loop042/batch_runner.inc");
