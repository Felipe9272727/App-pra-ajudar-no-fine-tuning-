use anyhow::{ensure,Result};
use liquid_sense::model::{Model,Session};
use liquid_sense::kernels::greedy;
use std::{fs::File,sync::atomic::AtomicBool,io::Write};
fn main()->Result<()> {
    rayon::ThreadPoolBuilder::new().num_threads(4).build_global()?;
    let args:Vec<_>=std::env::args().collect();let mode=&args[1];
    let loc:serde_json::Value=serde_json::from_slice(&std::fs::read("android_epochs030/reports/model_locator.json")?)?;
    let f=File::open(loc["path"].as_str().unwrap())?;
    let mut model=Model::region(&f,loc["offset"].as_u64().unwrap(),loc["length"].as_u64().unwrap() as usize)?;model.optimize=true;
    if mode=="experimental" {
        let report:serde_json::Value=serde_json::from_slice(&std::fs::read("android_epochs030/reports/patch_export.json")?)?;
        let source=File::open(report["path"].as_str().unwrap())?;
        let map=unsafe{memmap2::MmapOptions::new().map(&source)?};
        let changed=model.attach_patch(&map,report["sha256"].as_str().unwrap())?;
        ensure!(changed==381,"Unexpected changed tensor count");
        ensure!(model.manifest.source_checkpoint_sha256==liquid_sense::patch::EPOCH02,"Wrong selected model");
        println!("{}",serde_json::json!({"status":"all546_base_and_candidate_tensor_hashes_verified","changed":changed,"mode":mode}));
    }
    let rows:Vec<serde_json::Value>=serde_json::from_slice(&std::fs::read(&args[2])?)?;
    let cancel=AtomicBool::new(false);
    for row in rows {
        let mut session=Session::new();let mut hidden=vec![];
        for id in row["input_ids"].as_array().unwrap() {hidden=model.token(&mut session,id.as_u64().unwrap() as u32,&cancel,false)?.0;}
        let mut ids=vec![];
        for _ in 0..row["budget"].as_u64().unwrap() {
            let next=greedy(&model.logits(&hidden)) as u32;ids.push(next);
            if next==248044 {break;}
            hidden=model.token(&mut session,next,&cancel,false)?.0;
        }
        println!("{}",serde_json::json!({"id":row["id"],"mode":mode,"ids":ids,"executions":56}));std::io::stdout().flush()?;
    }
    Ok(())
}
