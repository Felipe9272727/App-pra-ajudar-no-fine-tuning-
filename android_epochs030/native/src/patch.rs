//! Exact native BF16/FP32 tensor patches: compression changes no weight bits.
use anyhow::{ensure,Context,Result};
use flate2::read::ZlibDecoder;
use serde::Deserialize;
use sha2::{Digest,Sha256};
use std::{collections::HashMap,io::Read};
pub const EPOCH02:&str="73b452641035c272aef3ecb76e7fd8b2fd75b1e261007bb32107ad04c4fe4b06";
#[derive(Deserialize)]
pub struct TensorPatch {
    pub shape:Vec<usize>,pub kind:String,pub sha256:String,pub base_sha256:String,
    pub changed:bool,#[serde(default)]pub offset:usize,
    #[serde(default)]pub compressed_bytes:usize,#[serde(default)]pub bytes:usize,
}
#[derive(Deserialize)]
pub struct Patch {
    pub format:String,pub base_checkpoint_sha256:String,pub source_archive_sha256:String,
    pub tensor_count:usize,pub tensors:HashMap<String,TensorPatch>,
    pub physical_layers:usize,pub executions:usize,pub general_quality_promotion:bool,
}
pub fn decode(bytes:&[u8],expected:&str)->Result<Patch> {
    ensure!(bytes.len()>=1024*1024 && &bytes[..8]==b"LSPATCH1","Pacote de edição inválido");
    ensure!(expected.len()==64 && format!("{:x}",Sha256::digest(bytes))==expected,"Integridade da edição inválida");
    let n=u64::from_le_bytes(bytes[8..16].try_into()?) as usize;
    ensure!(n>0 && n<=1024*1024-16,"Cabeçalho da edição inválido");
    let patch:Patch=serde_json::from_slice(&bytes[16..16+n])?;
    ensure!(patch.format=="liquid-sense-xor-patch-v1" && patch.tensor_count==546 && patch.physical_layers==32 && patch.executions==56 && !patch.general_quality_promotion,"Arquitetura da edição incompatível");
    Ok(patch)
}
pub fn decode_tensor(bytes:&[u8],t:&TensorPatch,prior:&[u8])->Result<Vec<u8>> {
    let width=match t.kind.as_str(){"bf16"=>2usize,"f32"=>4,_=>anyhow::bail!("Precisão incompatível")};
    ensure!(!t.shape.is_empty() && t.shape.iter().all(|x|*x>0),"Forma inválida");
    let count=t.shape.iter().try_fold(1usize,|a,b|a.checked_mul(*b)).context("Forma excessiva")?;
    ensure!(count.checked_mul(width)==Some(t.bytes) && t.bytes==prior.len() && t.bytes<=64*1024*1024,"Tamanho incompatível");
    let end=t.offset.checked_add(t.compressed_bytes).context("Faixa inválida")?;
    ensure!(t.offset>=1024*1024 && end<=bytes.len(),"Edição incompleta");
    let mut decoder=ZlibDecoder::new(&bytes[t.offset..end]);let mut out=Vec::with_capacity(t.bytes);
    (&mut decoder).take(t.bytes as u64+1).read_to_end(&mut out)?;
    ensure!(out.len()==t.bytes && decoder.total_in() as usize==t.compressed_bytes,"Tensor comprimido incompleto");
    for (a,b) in out.iter_mut().zip(prior){*a^=b;}
    ensure!(format!("{:x}",Sha256::digest(&out))==t.sha256,"Hash do tensor diferente");
    ensure!(if width==2 {out.chunks_exact(2).all(|b|u16::from_le_bytes([b[0],b[1]])&0x7f80!=0x7f80)}else{out.chunks_exact(4).all(|b|f32::from_le_bytes(b.try_into().unwrap()).is_finite())},"Pesos não finitos");
    Ok(out)
}
#[cfg(test)] mod tests {
    use super::*;use flate2::{write::ZlibEncoder,Compression};use std::io::Write;
    #[test] fn exact_patch_rejects_corruption_and_bad_shape() {
        let prior=[0u8,0,128,63];let next=[0u8,64,128,63];
        let mut encoder=ZlibEncoder::new(Vec::new(),Compression::default());encoder.write_all(&[0,64,0,0]).unwrap();let data=encoder.finish().unwrap();
        let mut bytes=vec![0u8;1024*1024];bytes.extend_from_slice(&data);
        let mut t=TensorPatch{shape:vec![2],kind:"bf16".into(),sha256:format!("{:x}",Sha256::digest(next)),base_sha256:String::new(),changed:true,offset:1024*1024,compressed_bytes:data.len(),bytes:4};
        assert_eq!(decode_tensor(&bytes,&t,&prior).unwrap(),next);
        bytes[t.offset]^=1;assert!(decode_tensor(&bytes,&t,&prior).is_err());bytes[t.offset]^=1;
        t.shape=vec![3];assert!(decode_tensor(&bytes,&t,&prior).is_err());
    }
    #[test] fn reject_incomplete_and_wrong_asset_digest() {
        assert!(decode(b"LSPATCH1","bad").is_err());
        let mut bytes=vec![0;1024*1024];bytes[..8].copy_from_slice(b"LSPATCH1");
        assert!(decode(&bytes,&"0".repeat(64)).is_err());
    }
}
