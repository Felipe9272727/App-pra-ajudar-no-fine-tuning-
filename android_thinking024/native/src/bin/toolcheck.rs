use anyhow::{Result,ensure};
use liquid_sense::chat::{Chat,Message,render_tools,GenerationOptions};
use liquid_sense::model::Model;
use std::{fs::File,sync::atomic::AtomicBool,cell::RefCell,io::{Read,Seek,SeekFrom}};
fn main()->Result<()> {
    rayon::ThreadPoolBuilder::new().num_threads(4).build_global()?;
    let args:Vec<_>=std::env::args().collect();let prefix=std::fs::read_to_string("tooluse022/tools_prefix.txt")?;
    let fixtures:Vec<serde_json::Value>=serde_json::from_slice(&std::fs::read("tooluse022/reports/tool_template_fixtures.json")?)?;
    for f in fixtures {let ms:Vec<Message>=serde_json::from_value(f["messages"].clone())?;ensure!(render_tools(&prefix,&ms)==f["expected"].as_str().unwrap(),"Native tools template mismatch");}
    if args.len()==1 {println!("TOOLS_TEMPLATES_MATCH_HF");return Ok(());}
    let loc:serde_json::Value=serde_json::from_slice(&std::fs::read("tooluse023/reports/model_locator.json")?)?;
    let file=File::open(loc["path"].as_str().unwrap())?;let mut model=Model::region(&file,loc["offset"].as_u64().unwrap(),loc["length"].as_u64().unwrap() as usize)?;model.optimize=true;
    let spec=&model.manifest.tensors["layers.31.mlp.down_proj.weight"];ensure!(spec.kind=="bf16","Expected exactBF16");let mut base=file.try_clone()?;base.seek(SeekFrom::Start(loc["offset"].as_u64().unwrap()+spec.offset as u64))?;let mut bytes=vec![0u8;spec.bytes];base.read_exact(&mut bytes)?;
    let x:Vec<f32>=(0..3584).map(|i|(i as f32-1000.)*0.001).collect();let reference=model.mv("layers.31.mlp.down_proj.weight",&x);model.attach_dense(bytes)?;let repeated=model.mv("layers.31.mlp.down_proj.weight",&x);ensure!(reference.iter().zip(&repeated).all(|(a,b)|a.to_bits()==b.to_bits()),"Dense override changed reference accumulation");
    if args[1]=="candidate"{let chosen:serde_json::Value=serde_json::from_slice(&std::fs::read("tooluse023/candidate_artifact.json")?)?;model.attach_dense(std::fs::read(format!("tooluse023/{}",chosen["weights"].as_str().unwrap()))?)?;}
    let tokenizer=tokenizers::Tokenizer::from_file("/dev/shm/liquid-android/model/tokenizer.json").map_err(|e|anyhow::anyhow!(e.to_string()))?;
    let chat=Chat{model,tokenizer,system:String::new(),cache:RefCell::new(None),reuse_prefix:true,tools_prefix:Some(prefix)};
    let messages:Vec<Message>=serde_json::from_slice(&std::fs::read(&args[2])?)?;
    let answer=if args.len()>3 {let options:GenerationOptions=serde_json::from_slice(&std::fs::read(&args[3])?)?;chat.generate_profile(&messages,options,&AtomicBool::new(false),|_,_,_|{})?}else{chat.generate(&messages,256,&AtomicBool::new(false),|_,_,_|{})?};println!("{}",serde_json::to_string(&answer)?);Ok(())
}
