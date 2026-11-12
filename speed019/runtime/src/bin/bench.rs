use anyhow::{ensure, Result};
use liquid_sense::{chat::{Chat, Message},model::{Model,Session}};
use std::{fs::File,cell::RefCell,sync::atomic::AtomicBool,time::Instant};
fn same(a: &[f32], b: &[f32]) -> bool { a.len()==b.len() && a.iter().zip(b).all(|(a,b)|a.to_bits()==b.to_bits()) }
fn main() -> Result<()> {
    rayon::ThreadPoolBuilder::new().num_threads(4).build_global()?;
    let args: Vec<_> = std::env::args().collect();
    let loc: serde_json::Value = serde_json::from_slice(&std::fs::read(&args[1])?)?;
    let f=File::open(loc["path"].as_str().unwrap())?;
    let mut model=Model::region(&f,loc["offset"].as_u64().unwrap(),loc["length"].as_u64().unwrap() as usize)?;
    let cancel=AtomicBool::new(false);
    if args[2]=="trace" {
        let fixture: serde_json::Value = serde_json::from_slice(&std::fs::read(&args[3])?)?;
        let ids: Vec<u32> = fixture["steps"].as_array().unwrap().iter().map(|s|s["input_id"].as_u64().unwrap() as u32).collect();
        let mut a=Session::new();let mut b=Session::new();let mut steps=vec![];model.profile=true;
        for id in ids {
            model.optimize=false;let start=Instant::now();let (h1,s1)=model.token(&mut a,id,&cancel,true)?;let t1=start.elapsed().as_secs_f64();let l1=model.logits(&h1);
            model.optimize=true;let start=Instant::now();let (h2,s2)=model.token(&mut b,id,&cancel,true)?;let t2=start.elapsed().as_secs_f64();let l2=model.logits(&h2);
            ensure!(same(&h1,&h2) && s1.iter().zip(&s2).all(|(x,y)|same(x,y)),"Hidden states differ");
            for (x,y) in a.slots.iter().zip(&b.slots) {
                ensure!(same(&x.conv,&y.conv) && same(&x.recurrent,&y.recurrent),"Memory differs");
                ensure!(x.k.iter().zip(&y.k).all(|(x,y)|same(x,y)) && x.v.iter().zip(&y.v).all(|(x,y)|same(x,y)),"KV differs");
            }
            ensure!(same(&l1,&l2),"Logits differ");
            steps.push(serde_json::json!({"id":id,"reference_seconds":t1,"optimized_seconds":t2,"all_57_hidden_states_bits_equal":true,"all_56_cache_slots_bits_equal":true,"all_248320_logits_bits_equal":true}));
        }
        println!("{}",serde_json::json!({"steps":steps,"combined_phase_timings_nanoseconds":*model.timings.lock().unwrap(),"proven_zero_matrices":model.proven_zero_count(),"zero_mv_shortcut_hits":model.zero_mv_hits.load(std::sync::atomic::Ordering::Relaxed)}));
    } else if args[2]=="time" {
        // Identical fixed token sequence; warm both code paths, ABBA with fresh states.
        let ids: Vec<u32>=serde_json::from_slice(&std::fs::read(&args[3])?)?;
        let mut rows=vec![];
        for (run,fast) in [false,true,false,true,true,false,false,true,true,false].into_iter().enumerate() {
            model.optimize=fast;model.profile=true;model.timings.lock().unwrap().clear();let mut session=Session::new();let start=Instant::now();
            for &id in &ids { model.token(&mut session,id,&cancel,false)?; }
            rows.push(serde_json::json!({"run":run,"warmup":run<2,"optimized":fast,"tokens":ids.len(),"seconds":start.elapsed().as_secs_f64(),"phases_nanoseconds":*model.timings.lock().unwrap()}));
            eprintln!("timing run {} complete",run);
        }
        println!("{}",serde_json::json!({"threads":4,"timing_scope":"token backbone excluding vocabulary readout","rows":rows}));
    } else {
        let tokenizer=tokenizers::Tokenizer::from_file("/dev/shm/liquid-android/model/tokenizer.json").map_err(|e|anyhow::anyhow!(e.to_string()))?;
        let fast=args[2]=="chat_fast";model.optimize=fast;
        let chat=Chat {model,tokenizer,system:"You are a helpful assistant.".into(),cache:RefCell::new(None),reuse_prefix:fast};
        let cases: Vec<Vec<Message>>=serde_json::from_slice(&std::fs::read(&args[3])?)?;
        let mut out=vec![];
        for messages in cases { let a=chat.generate(&messages,16,&cancel,|_,_,_|{})?;eprintln!("chat {} done, reused {}",out.len(),a.reused_prompt_tokens);out.push(a); }
        println!("{}",serde_json::to_string(&out)?);
    }
    Ok(())
}
