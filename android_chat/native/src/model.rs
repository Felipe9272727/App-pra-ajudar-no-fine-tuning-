use anyhow::{bail,ensure,Context,Result};
use memmap2::{Mmap,MmapOptions};
use rayon::prelude::*;
use serde::Deserialize;
use std::{collections::HashMap,fs::File,path::Path,sync::atomic::{AtomicBool,Ordering}};
use crate::kernels::*;
const PRINCIPAL:&str="46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8";
#[derive(Clone,Deserialize)]
pub struct Spec {pub shape:Vec<usize>,pub kind:String,pub offset:usize,pub bytes:usize}
#[derive(Deserialize)]
pub struct Manifest {pub format:String,pub source_checkpoint_sha256:String,pub quantization:String,pub tensor_count:usize,pub text_parameters:usize,pub execution_plan:Vec<usize>,pub tensors:HashMap<String,Spec>}
pub struct Model {map:Mmap,pub manifest:Manifest,small:HashMap<String,Vec<f32>>}
#[derive(Default)]
pub struct Cache {pub conv:Vec<f32>,pub recurrent:Vec<f32>,pub k:Vec<Vec<f32>>,pub v:Vec<Vec<f32>>}
pub struct Session {pub slots:Vec<Cache>,pub position:usize}
impl Session {pub fn new()->Self {Self{slots:(0..56).map(|_|Cache::default()).collect(),position:0}}}
impl Model {
 pub fn open(path:&Path)->Result<Self> {let f=File::open(path)?;let len=f.metadata()?.len() as usize;Self::region(&f,0,len)}
 pub fn region(f:&File,offset:u64,len:usize)->Result<Self> {
  ensure!(len>=1024*1024,"Pacote de modelo incompleto");let map=unsafe{MmapOptions::new().offset(offset).len(len).map(f)?};
  ensure!(&map[..8]==b"LSENSE01","Formato de modelo incompatível");let n=u64::from_le_bytes(map[8..16].try_into()?) as usize;ensure!(n<=1024*1024-16,"Cabeçalho inválido");
  let manifest:Manifest=serde_json::from_slice(&map[16..16+n])?;
  ensure!(manifest.format=="liquid-sense-pack-v1" && manifest.source_checkpoint_sha256==PRINCIPAL,"Checkpoint diferente do selecionado");
  let expected:Vec<_>=(0..4).chain(4..28).chain(4..28).chain(28..32).collect();ensure!(manifest.execution_plan==expected && manifest.tensor_count==546 && manifest.tensors.len()==546,"Arquitetura híbrida incompatível");
  for (name,s) in &manifest.tensors {
   ensure!(!s.shape.is_empty() && s.shape.iter().all(|x|*x>0),"Forma inválida: {name}");let count=s.shape.iter().try_fold(1usize,|a,b|a.checked_mul(*b)).context("Tensor grande demais")?;
   let expected=match s.kind.as_str(){"zero"=>0,"bf16"=>count.checked_mul(2).context("Tamanho")?,"f32"=>count.checked_mul(4).context("Tamanho")?,"q8_32"=>{ensure!(s.shape.len()==2 && s.shape[1]%32==0,"Bloco Q8 inválido");count/32*36},_=>bail!("Precisão desconhecida")};
   ensure!(s.bytes==expected && s.offset>=1024*1024 && s.offset.checked_add(s.bytes).is_some_and(|end|end<=map.len()),"Tensor fora do pacote: {name}");
  }
  let mut m=Self{map,manifest,small:HashMap::new()};
  for (n,s) in &m.manifest.tensors {if s.shape.len()!=2 {m.small.insert(n.clone(),m.values(s));}}
  for i in 4..28 {let g=m.vector(&format!("layers.{i}.native_visit_gain"));ensure!(g.len()==2 && g.iter().all(|x|x.is_finite()&&*x>0.) && (g[0]+g[1]-1.).abs()<1e-6,"Ganhos de loop inválidos");}
  Ok(m)
 }
 fn values(&self,s:&Spec)->Vec<f32> {let count:sizetype=s.shape.iter().product();match s.kind.as_str(){"zero"=>vec![0.;count],"bf16"=>self.map[s.offset..s.offset+s.bytes].chunks_exact(2).map(read_bf).collect(),"f32"=>self.map[s.offset..s.offset+s.bytes].chunks_exact(4).map(read_f32).collect(),_=>panic!("Expected small unquantized tensor")}}
 pub fn vector(&self,n:&str)->&[f32] {self.small.get(n).unwrap_or_else(||panic!("Missing vector {n}"))}
 pub fn mv(&self,n:&str,x:&[f32])->Vec<f32> {
  let s=self.manifest.tensors.get(n).unwrap_or_else(||panic!("Missing matrix {n}"));assert_eq!(s.shape.len(),2);assert_eq!(s.shape[1],x.len());let rows=s.shape[0];let cols=s.shape[1];if s.kind=="zero"{return vec![0.;rows];}
  let rowbytes=s.bytes/rows;let d=&self.map[s.offset..s.offset+s.bytes];
  (0..rows).into_par_iter().map(|r|{let row=&d[r*rowbytes..(r+1)*rowbytes];let sum=match s.kind.as_str(){"bf16"=>dot_bf(row,x),"q8_32"=>dot_q8(row,x),"f32"=>(0..cols).map(|j|read_f32(&row[j*4..])*x[j]).sum(),_=>unreachable!()};if s.kind=="f32"{sum}else{bf16(sum)}}).collect()
 }
 pub fn embedding(&self,id:usize)->Result<Vec<f32>> {let s=&self.manifest.tensors["embed_tokens.weight"];ensure!(id<s.shape[0],"Token inválido");let width=s.shape[1];let stride=s.bytes/s.shape[0];let data=&self.map[s.offset+id*stride..s.offset+(id+1)*stride];let out=match s.kind.as_str(){"bf16"=>data.chunks_exact(2).map(read_bf).collect(),"q8_32"=>{let mut v=Vec::with_capacity(width);for block in data.chunks_exact(36){let scale=read_f32(block);v.extend(block[4..].iter().map(|q|bf16(*q as i8 as f32*scale)));}v},_=>bail!("Embedding inválido")};Ok(out)}
 fn norm(&self,base:&str,suffix:&str,x:&[f32])->Vec<f32>{rms(x,self.vector(&format!("{base}.{suffix}.weight")),true)}
 fn mlp(&self,base:&str,x:&[f32])->Vec<f32>{let mut a=self.mv(&format!("{base}.mlp.gate_proj.weight"),x);let b=self.mv(&format!("{base}.mlp.up_proj.weight"),x);for (a,b) in a.iter_mut().zip(b){*a=bf16(bf16(silu(*a))*b);}self.mv(&format!("{base}.mlp.down_proj.weight"),&a)}
 fn router(&self,base:&str,r:&[f32])->(Vec<f32>,Vec<f32>,Vec<f32>){
  assert_eq!(r.len(),2048);let inv=(r.iter().map(|x|x*x).sum::<f32>()/2048.+1e-6).sqrt().recip();let normalized:Vec<_>=r.iter().map(|x|x*inv).collect();let mut logits=self.mv(&format!("{base}.weight"),&normalized);for (x,b) in logits.iter_mut().zip(self.vector(&format!("{base}.bias"))){*x+=b;}
  let pre=[bf16(sigmoid(logits[0])),bf16(sigmoid(logits[1]))];let post=vec![2.*sigmoid(logits[2]),2.*sigmoid(logits[3])];let mut mix=logits[4..8].to_vec();
  for _ in 0..20 {for row in 0..2{let a=mix[row*2];let b=mix[row*2+1];let m=a.max(b);let z=m+((a-m).exp()+(b-m).exp()).ln();mix[row*2]-=z;mix[row*2+1]-=z;}for col in 0..2{let a=mix[col];let b=mix[2+col];let m=a.max(b);let z=m+((a-m).exp()+(b-m).exp()).ln();mix[col]-=z;mix[2+col]-=z;}}
  for x in &mut mix{*x=bf16(x.exp());}
  let branch=(0..1024).map(|j|bf16(pre[0]*r[j]+pre[1]*r[1024+j])).collect();(branch,post,mix)
 }
 fn merge(r:&[f32],branch:&[f32],post:&[f32],mix:&[f32],gain:f32)->Vec<f32>{
  let mut out=vec![0.;2048];for i in 0..2{let p=bf16(post[i]*gain);for j in 0..1024{let mixed=bf16(mix[i*2]*r[j]+mix[i*2+1]*r[1024+j]);out[i*1024+j]=bf16(mixed+bf16(p*branch[j]));}}out
 }
 fn delta(&self,base:&str,x:&[f32],cache:&mut Cache)->Vec<f32>{
  let prefix=format!("{base}.linear_attn");let input=self.mv(&format!("{prefix}.in_proj_qkv.weight"),x);let z=self.mv(&format!("{prefix}.in_proj_z.weight"),x);let b=self.mv(&format!("{prefix}.in_proj_b.weight"),x);let a=self.mv(&format!("{prefix}.in_proj_a.weight"),x);
  let conv=self.vector(&format!("{prefix}.conv1d.weight"));if cache.conv.is_empty(){cache.conv=vec![0.;6144*7];cache.recurrent=vec![0.;16*128*128];}
  let mut qkv=vec![0.;6144];for i in 0..6144 {let c=&mut cache.conv[i*7..(i+1)*7];c.copy_within(1..7,0);c[6]=input[i];let sum=(0..7).map(|j|c[j]*conv[i*7+j]).sum::<f32>();qkv[i]=bf16(silu(bf16(sum)));}
  let alog=self.vector(&format!("{prefix}.A_log"));let bias=self.vector(&format!("{prefix}.dt_bias"));let norm=self.vector(&format!("{prefix}.norm.weight"));
  let pieces:Vec<Vec<f32>>=cache.recurrent.par_chunks_mut(128*128).enumerate().map(|(head,state)|{
   let mut q=qkv[head*128..head*128+128].to_vec();let mut k=qkv[2048+head*128..2048+head*128+128].to_vec();let v=&qkv[4096+head*128..4096+head*128+128];let qi=(q.iter().map(|x|x*x).sum::<f32>()+1e-6).sqrt().recip()/128f32.sqrt();let ki=(k.iter().map(|x|x*x).sum::<f32>()+1e-6).sqrt().recip();for x in &mut q{*x*=qi;}for x in &mut k{*x*=ki;}
   let t=a[head]+bias[head];let sp=if t>20.{t}else{t.exp().ln_1p()};let decay=(-alog[head].exp()*sp).exp();let beta=bf16(sigmoid(b[head]));for s in state.iter_mut(){*s*=decay;}
   let mut delta=vec![0.;128];for col in 0..128{let prediction=(0..128).map(|row|state[row*128+col]*k[row]).sum::<f32>();delta[col]=(v[col]-prediction)*beta;}
   for row in 0..128{for col in 0..128{state[row*128+col]+=k[row]*delta[col];}}
   let mut o:Vec<f32>=(0..128).map(|col|bf16((0..128).map(|row|state[row*128+col]*q[row]).sum())).collect();let inv=(o.iter().map(|x|x*x).sum::<f32>()/128.+1e-6).sqrt().recip();for j in 0..128 {o[j]=bf16(bf16(norm[j]*bf16(o[j]*inv))*silu(z[head*128+j]));}o
  }).collect();let out:Vec<_>=pieces.into_iter().flatten().collect();self.mv(&format!("{prefix}.out_proj.weight"),&out)
 }
 fn attention(&self,base:&str,x:&[f32],cache:&mut Cache,pos:usize,window:bool)->Vec<f32>{
  let prefix=format!("{base}.self_attn");let projected=self.mv(&format!("{prefix}.q_proj.weight"),x);let kk=self.mv(&format!("{prefix}.k_proj.weight"),x);let value=self.mv(&format!("{prefix}.v_proj.weight"),x);
  let mut q=vec![0.;2048];let mut gate=vec![0.;2048];for h in 0..8 {q[h*256..(h+1)*256].copy_from_slice(&rms(&projected[h*512..h*512+256],self.vector(&format!("{prefix}.q_norm.weight")),true));gate[h*256..(h+1)*256].copy_from_slice(&projected[h*512+256..(h+1)*512]);}
  let mut k=vec![0.;512];for h in 0..2{k[h*256..(h+1)*256].copy_from_slice(&rms(&kk[h*256..(h+1)*256],self.vector(&format!("{prefix}.k_norm.weight")),true));}
  for vector in [&mut q,&mut k] {for head in vector.chunks_exact_mut(256){for j in 0..32{let theta=pos as f32/10000000f32.powf(j as f32/32.);let c=bf16(theta.cos());let s=bf16(theta.sin());let a=head[j];let b=head[j+32];head[j]=bf16(bf16(a*c)+bf16(-b*s));head[j+32]=bf16(bf16(b*c)+bf16(a*s));}}}
  cache.k.push(k);cache.v.push(value);let start=if window{cache.k.len().saturating_sub(256)}else{0};let mut out=vec![0.;2048];
  for h in 0..8 {let kv=h/4;let scores:Vec<_>=(start..cache.k.len()).map(|t|bf16(bf16((0..256).map(|j|q[h*256+j]*cache.k[t][kv*256+j]).sum::<f32>())*0.0625)).collect();let mut weights=softmax(&scores);round(&mut weights);for j in 0..256{let value=bf16(weights.iter().enumerate().map(|(i,a)|*a*cache.v[start+i][kv*256+j]).sum());out[h*256+j]=bf16(value*bf16(sigmoid(gate[h*256+j])));}}
  self.mv(&format!("{prefix}.o_proj.weight"),&out)
 }
 pub fn token(&self,session:&mut Session,id:u32,cancel:&AtomicBool,trace:bool)->Result<(Vec<f32>,Vec<Vec<f32>>)> {
  ensure!(session.position<2048,"Limite de contexto atingido");let mut h=self.embedding(id as usize)?;let mut states=if trace{vec![h.clone()]}else{vec![]};let mut visits=[0usize;32];
  for (slot,&physical) in self.manifest.execution_plan.iter().enumerate(){if cancel.load(Ordering::Relaxed){bail!("cancelled");}let base=format!("layers.{physical}");let visit=visits[physical];visits[physical]+=1;let routed=(4..28).contains(&physical);
   if routed {
    if physical==4 {assert_eq!(h.len(),1024);h=[h.clone(),h].concat();}
    let gain=self.vector(&format!("{base}.native_visit_gain"))[visit];let (branch,post,mix)=self.router(&format!("{base}.mhc_attn"),&h);let x=self.norm(&base,"input_layernorm",&branch);
    let branch=if physical%4==3 {self.attention(&base,&x,&mut session.slots[slot],session.position,[7,15,27].contains(&physical))}else{self.delta(&base,&x,&mut session.slots[slot])};
    h=Self::merge(&h,&branch,&post,&mix,gain);let (branch,post,mix)=self.router(&format!("{base}.mhc_ffn"),&h);let x=self.norm(&base,"post_attention_layernorm",&branch);let branch=self.mlp(&base,&x);h=Self::merge(&h,&branch,&post,&mix,gain);
    if physical==27 {h=(0..1024).map(|j|bf16((h[j]+h[1024+j])*0.5)).collect();}
   } else {let x=self.norm(&base,"input_layernorm",&h);let branch=if physical%4==3{self.attention(&base,&x,&mut session.slots[slot],session.position,false)}else{self.delta(&base,&x,&mut session.slots[slot])};for (x,b) in h.iter_mut().zip(branch){*x=bf16(*x+b);}let x=self.norm(&base,"post_attention_layernorm",&h);let branch=self.mlp(&base,&x);for (x,b) in h.iter_mut().zip(branch){*x=bf16(*x+b);}}
   ensure!(h.iter().all(|x|x.is_finite()),"Estado numérico inválido na camada {physical}");if trace{states.push(h.clone());}
  }
  h=rms(&h,self.vector("norm.weight"),true);if trace{*states.last_mut().unwrap()=h.clone();}session.position+=1;Ok((h,states))
 }
 pub fn logits(&self,h:&[f32])->Vec<f32>{self.mv("embed_tokens.weight",h)}
}
#[allow(non_camel_case_types)]type sizetype=usize;
#[cfg(test)]mod tests {use super::*;#[test]fn slots_are_independent(){let mut s=Session::new();s.slots[4].conv.push(1.);assert!(s.slots[28].conv.is_empty());assert_eq!(s.slots.len(),56);}}
