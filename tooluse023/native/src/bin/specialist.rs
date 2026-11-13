use anyhow::{ensure,Result};
use liquid_sense::model::{Model,Session};
use std::{fs::File,sync::atomic::AtomicBool,time::Instant};
fn main()->Result<()> {
 rayon::ThreadPoolBuilder::new().num_threads(4).build_global()?;
 let args:Vec<_>=std::env::args().collect();let loc:serde_json::Value=serde_json::from_slice(&std::fs::read(&args[1])?)?;
 let f=File::open(loc["path"].as_str().unwrap())?;let mut model=Model::region(&f,loc["offset"].as_u64().unwrap(),loc["length"].as_u64().unwrap() as usize)?;
 ensure!(model.manifest.source_checkpoint_sha256==liquid_sense::model::SPECIALIST,"Expected015E");model.optimize=true;
 let tok=tokenizers::Tokenizer::from_file("/dev/shm/liquid-android/model/tokenizer.json").map_err(|e|anyhow::anyhow!(e.to_string()))?;
 let inputs:Vec<serde_json::Value>=serde_json::from_slice(&std::fs::read(&args[2])?)?;let path=std::path::Path::new(&args[3]);
 let mut rows:Vec<serde_json::Value>=if path.exists(){serde_json::from_slice(&std::fs::read(path)?)?}else{vec![]};
 let cancel=AtomicBool::new(false);
 for row in inputs {
  if rows.iter().any(|r|r["id"]==row["id"]){continue;}
  let started=Instant::now();let ids:Vec<u32>=serde_json::from_value(row["input_ids"].clone())?;let mut session=Session::new();let mut hidden=vec![];
  for &id in &ids {hidden=model.token(&mut session,id,&cancel,false)?.0;}
  let mut generated=vec![];let budget=row["budget"].as_u64().unwrap() as usize;let mut reason="length";
  for _ in 0..budget {
   let next=liquid_sense::kernels::greedy(&model.logits(&hidden)) as u32;
   if next==248044 {reason="stop";break;}
   generated.push(next);if generated.len()==budget{break;}
   hidden=model.token(&mut session,next,&cancel,false)?.0;
  }
  let text=tok.decode(&generated,true).map_err(|e|anyhow::anyhow!(e.to_string()))?;
  rows.push(serde_json::json!({"id":row["id"],"output":text,"new_tokens":generated.len(),"generated_ids":generated,"hit_limit":reason=="length","finish_reason":reason,"seconds":started.elapsed().as_secs_f64(),"source_model_fingerprint":model.manifest.model_fingerprint_sha256}));
  let tmp=path.with_extension("json.tmp");std::fs::write(&tmp,serde_json::to_vec(&rows)?)?;std::fs::rename(tmp,path)?;
  eprintln!("PORT021 {} {} tokens",row["id"],generated.len());
 }
 Ok(())
}
