use anyhow::{Result,ensure};
use liquid_sense::chat::{Chat,Message,render_tools};
use liquid_sense::model::Model;
use std::{fs::File,sync::atomic::AtomicBool,cell::RefCell};
fn main()->Result<()> {
    rayon::ThreadPoolBuilder::new().num_threads(4).build_global()?;
    let args:Vec<_>=std::env::args().collect();let prefix=std::fs::read_to_string("tooluse022/tools_prefix.txt")?;
    let fixtures:Vec<serde_json::Value>=serde_json::from_slice(&std::fs::read("tooluse022/reports/tool_template_fixtures.json")?)?;
    for f in fixtures {let ms:Vec<Message>=serde_json::from_value(f["messages"].clone())?;ensure!(render_tools(&prefix,&ms)==f["expected"].as_str().unwrap(),"Native tools template mismatch");}
    if args.len()==1 {println!("TOOLS_TEMPLATES_MATCH_HF");return Ok(());}
    let loc:serde_json::Value=serde_json::from_slice(&std::fs::read("android_models021/reports/model_locator.json")?)?;
    let file=File::open(loc["path"].as_str().unwrap())?;let mut model=Model::region(&file,loc["offset"].as_u64().unwrap(),loc["length"].as_u64().unwrap() as usize)?;model.optimize=true;
    if args[1]=="candidate"{model.attach_readout(&std::fs::read("tooluse022/readout.json")?)?;}
    let tokenizer=tokenizers::Tokenizer::from_file("/dev/shm/liquid-android/model/tokenizer.json").map_err(|e|anyhow::anyhow!(e.to_string()))?;
    let chat=Chat{model,tokenizer,system:String::new(),cache:RefCell::new(None),reuse_prefix:true,tools_prefix:Some(prefix)};
    let messages:Vec<Message>=serde_json::from_slice(&std::fs::read(&args[2])?)?;
    let answer=chat.generate(&messages,256,&AtomicBool::new(false),|_,_,_|{})?;println!("{}",serde_json::to_string(&answer)?);Ok(())
}
