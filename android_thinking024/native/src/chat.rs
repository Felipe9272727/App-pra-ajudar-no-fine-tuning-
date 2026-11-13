use crate::model::{Model, Session};
use anyhow::{anyhow,ensure,Result};
use serde::{Deserialize,Serialize};
use std::{cell::RefCell,sync::atomic::{AtomicBool,Ordering},time::Instant};
use tokenizers::Tokenizer;
#[derive(Clone,Serialize,Deserialize)]
pub struct Message {pub role:String,pub content:String,#[serde(default)]pub internal:bool}
#[derive(Clone,Debug,Serialize,Deserialize)]
#[serde(default)]
pub struct GenerationOptions {pub thinking:bool,pub reasoning_tokens:usize,pub response_tokens:usize,pub context_tokens:usize}
impl Default for GenerationOptions {fn default()->Self{Self{thinking:true,reasoning_tokens:1024,response_tokens:2048,context_tokens:16384}}}
impl GenerationOptions {
 pub fn bounded(mut self)->Self {self.reasoning_tokens=if self.thinking{self.reasoning_tokens.clamp(1,2048)}else{0};self.response_tokens=self.response_tokens.clamp(16,4096);self.context_tokens=self.context_tokens.clamp(2048,16384);self}
}
#[derive(Serialize)]
pub struct Answer {
 pub raw_text:String,pub text:String,pub tokens:usize,pub prompt_tokens:usize,pub finish_reason:String,pub generated_ids:Vec<u32>,pub reused_prompt_tokens:usize,
 pub prefill_seconds:f64,pub decode_seconds:f64,pub first_token_seconds:Option<f64>,
 pub thinking:bool,pub reasoning_tokens:usize,pub response_tokens:usize,pub reasoning_complete:bool,pub forced_reasoning_close:bool,pub forced_control_tokens:usize,
}
pub struct PrefixSnapshot {ids:Vec<u32>,session:Session,hidden:Vec<f32>}
pub struct Chat {pub tools_prefix:Option<String>,pub model:Model,pub tokenizer:Tokenizer,pub system:String,pub cache:RefCell<Option<PrefixSnapshot>>,pub reuse_prefix:bool}
pub fn split_content(raw:&str,thinking:bool)->Option<&str> {
 if thinking || raw.trim_start().starts_with("<think>") {return raw.find("</think>").map(|i|raw[i+8..].trim());}
 if let Some(i)=raw.find("</think>") {
  if raw.find("<tool_call>").is_none_or(|t|i<t) && !raw.trim_start().starts_with('{') {return Some(raw[i+8..].trim());}
 }
 Some(raw.trim())
}
fn separate_history(content:&str)->(&str,&str) {
 if let Some((r,t))=content.split_once("</think>") {
  if content.find("<tool_call>").is_none_or(|i|i>r.len()) {return (r.split("<think>").last().unwrap_or(r).trim(),t.trim());}
 }
 ("",content)
}
pub fn render_tools_mode(prefix:&str,messages:&[Message],thinking:bool)->String {
 let mut s=prefix.to_string();let last=messages.iter().rposition(|m|m.role=="user").unwrap_or(0);
 for (i,m) in messages.iter().enumerate(){let c=m.content.trim();
  match m.role.as_str(){
   "tool"=>s+=&format!("<|im_start|>user\n<tool_response>\n{c}\n</tool_response><|im_end|>\n"),
   "assistant"=>{let(r,t)=separate_history(c);if i>last{s+=&format!("<|im_start|>assistant\n<think>\n{r}\n</think>\n\n{t}<|im_end|>\n");}else{s+=&format!("<|im_start|>assistant\n{t}<|im_end|>\n");}},
   _=>s+=&format!("<|im_start|>{}\n{c}<|im_end|>\n",m.role)
  }
 }
 s+if thinking{"<|im_start|>assistant\n<think>\n"}else{"<|im_start|>assistant\n<think>\n\n</think>\n\n"}
}
pub fn render_tools(prefix:&str,messages:&[Message])->String {render_tools_mode(prefix,messages,false)}
pub fn render(system:&str,messages:&[Message])->String {
 let prefix=if system.is_empty(){String::new()}else{format!("<|im_start|>system\n{system}<|im_end|>\n")};render_plain(&prefix,messages,false)
}
fn render_plain(prefix:&str,messages:&[Message],thinking:bool)->String {
 let mut s=prefix.to_string();for m in messages {let(_,c)=separate_history(m.content.trim());s+=&format!("<|im_start|>{}\n{c}<|im_end|>\n",m.role);}
 s+if thinking{"<|im_start|>assistant\n<think>\n"}else{"<|im_start|>assistant\n<think>\n\n</think>\n\n"}
}
fn json_call(v:&serde_json::Value)->bool {
 let f=v.get("function").unwrap_or(v);let name=f.get("name").and_then(|n|n.as_str());let args=f.get("arguments");
 matches!(name,Some("search_web"|"run_python")) && args.is_some_and(|a|a.is_object()||a.is_string())
}
pub fn complete_action(text:&str)->bool {
 let s=text.trim();
 if let Some(start)=s.find("<tool_call>") {
  let Some(body)=s[start+11..].strip_suffix("</tool_call>") else{return false};let body=body.trim();
  if let Ok(v)=serde_json::from_str::<serde_json::Value>(body){return json_call(&v);}
  let Some(f)=body.strip_suffix("</function>") else{return false};return f.trim_end().ends_with("</parameter>") && f.trim_start().starts_with("<function=");
 }
 serde_json::from_str::<serde_json::Value>(s).ok().is_some_and(|v|json_call(&v))
}
fn common_prefix(a:&[u32],b:&[u32])->usize{a.iter().zip(b).take_while(|(a,b)|a==b).count()}
fn is_stop(next:Option<u32>,specialist:bool)->bool {next==Some(248044)||(!specialist&&next==Some(248046))}
impl Chat {
 pub fn generate<F>(&self,messages:&[Message],max_tokens:usize,cancel:&AtomicBool,update:F)->Result<Answer> where F:FnMut(&str,usize,usize){
  self.generate_profile(messages,GenerationOptions{thinking:false,reasoning_tokens:0,response_tokens:max_tokens.clamp(16,512),context_tokens:if self.tools_prefix.is_some(){4096}else{2048}},cancel,update)
 }
 pub fn generate_profile<F>(&self,messages:&[Message],options:GenerationOptions,cancel:&AtomicBool,mut update:F)->Result<Answer> where F:FnMut(&str,usize,usize){
  let o=options.bounded();let begin=Instant::now();ensure!(!messages.is_empty(),"Escreva uma mensagem");
  ensure!(messages.iter().all(|m|m.role=="user"||m.role=="assistant"||(self.tools_prefix.is_some()&&m.role=="tool")),"Papel de mensagem inválido");
  let encode=|s:&str|->Result<Vec<u32>>{Ok(self.tokenizer.encode(s,false).map_err(|e|anyhow!(e.to_string()))?.get_ids().to_vec())};
  let mut history=messages.to_vec();let reserve=o.response_tokens+o.reasoning_tokens+16;
  let (ids,boundary)=loop{
   let prompt=if let Some(prefix)=&self.tools_prefix{render_tools_mode(prefix,&history,o.thinking)}else{let prefix=if self.system.is_empty(){String::new()}else{format!("<|im_start|>system\n{}<|im_end|>\n",self.system)};render_plain(&prefix,&history,o.thinking)};
   let ids=encode(&prompt)?;
   if ids.len()+reserve<=o.context_tokens {
    let suffix=if o.thinking{"<think>\n"}else{"<think>\n\n</think>\n\n"};let base=prompt.strip_suffix(suffix).ok_or_else(||anyhow!("Prefixo de geração inválido"))?;let base_ids=encode(base)?;let b=common_prefix(&ids,&base_ids);break(ids,b)
   }
   let actual=history.iter().rposition(|m|m.role=="user"&&!m.internal).unwrap_or(0);
   if actual==0{return Err(anyhow!("CONTEXT_LIMIT: a mensagem e as verificações atuais excedem {} tokens de contexto",o.context_tokens));}
   history.remove(0);while history.len()>1&&!(history[0].role=="user"&&!history[0].internal){history.remove(0);}
  };
  let (mut session,mut last,reused)=if self.reuse_prefix{let cache=self.cache.borrow();match cache.as_ref().filter(|c|ids.starts_with(&c.ids)){Some(c)=>(c.session.clone(),Some(c.hidden.clone()),c.ids.len()),None=>(Session::new(),None,0)}}else{(Session::new(),None,0)};
  let mut stopped=false;
  for(i,id)in ids.iter().enumerate().skip(reused){
   match self.model.token(&mut session,*id,cancel,false){Ok((h,_))=>last=Some(h),Err(e)if e.to_string()=="cancelled"=>{stopped=true;break},Err(e)=>return Err(e)}
   if self.reuse_prefix&&i+1==boundary{*self.cache.borrow_mut()=Some(PrefixSnapshot{ids:ids[..boundary].to_vec(),session:session.clone(),hidden:last.as_ref().unwrap().clone()});}
   if i%8==0{update("",i+1,ids.len());}
  }
  let prefill_seconds=begin.elapsed().as_secs_f64();let decode_begin=Instant::now();let mut first=None;let mut generated=vec![];let mut raw=String::new();let mut reason=if stopped{"cancelled"}else{"length"};let mut thinking_done=!o.thinking;let mut reasoning=0;let mut response=0;let mut forced=false;let mut forced_tokens=0;
  let mut hidden=last.unwrap_or_default();
  while !stopped {
   if cancel.load(Ordering::Relaxed){reason="cancelled";break;}
   let at_thought_limit=!thinking_done&&reasoning>=o.reasoning_tokens;
   if thinking_done&&response>=o.response_tokens{reason="length";break;}
   let next=if at_thought_limit{None}else{let logits=self.model.logits(&hidden);Some(crate::kernels::greedy(&logits)as u32)};
   let eos=is_stop(next,self.model.manifest.source_checkpoint_sha256==crate::model::SPECIALIST);
   if !thinking_done&&(at_thought_limit||eos){
    let close=encode("</think>\n\n")?;forced=true;
    for id in close {generated.push(id);forced_tokens+=1;match self.model.token(&mut session,id,cancel,false){Ok((h,_))=>hidden=h,Err(e)if e.to_string()=="cancelled"=>{reason="cancelled";stopped=true;break},Err(e)=>return Err(e)}}
    thinking_done=true;raw=self.tokenizer.decode(&generated,false).map_err(|e|anyhow!(e.to_string()))?;continue;
   }
   if eos{reason="stop";break;}
   let next=next.unwrap();if first.is_none(){first=Some(begin.elapsed().as_secs_f64());}generated.push(next);
   raw=self.tokenizer.decode(&generated,false).map_err(|e|anyhow!(e.to_string()))?;
   if !thinking_done {reasoning+=1;thinking_done=split_content(&raw,true).is_some();}else{response+=1;}
   let content=split_content(&raw,o.thinking).unwrap_or("");if !thinking_done{update("",reasoning,0);}else{update(content,ids.len(),ids.len());}
   if self.tools_prefix.is_some()&&thinking_done&&complete_action(content){reason="tool_call";break;}
   if thinking_done&&response>=o.response_tokens{reason="length";break;}
   match self.model.token(&mut session,next,cancel,false){Ok((h,_))=>hidden=h,Err(e)if e.to_string()=="cancelled"=>{reason="cancelled";break},Err(e)=>return Err(e)}
  }
  let text=split_content(&raw,o.thinking).unwrap_or("").trim().to_string();
  Ok(Answer{raw_text:raw,text,tokens:generated.len()-forced_tokens,prompt_tokens:ids.len(),finish_reason:reason.into(),generated_ids:generated,reused_prompt_tokens:reused,prefill_seconds,decode_seconds:decode_begin.elapsed().as_secs_f64(),first_token_seconds:first,thinking:o.thinking,reasoning_tokens:reasoning,response_tokens:response,reasoning_complete:thinking_done,forced_reasoning_close:forced,forced_control_tokens:forced_tokens})
 }
}
#[cfg(test)]mod tests{
 use super::*;
 #[test]fn prefix_tokens_match(){assert_eq!(common_prefix(&[1,2,8],&[1,2,9]),2);}
 #[test]fn general_chat_ends_at_im_end(){assert!(is_stop(Some(248046),false));assert!(is_stop(Some(248044),false));assert!(!is_stop(Some(248069),false));}
 #[test]fn specialist_preserves_previous_stop_policy(){assert!(!is_stop(Some(248046),true));assert!(is_stop(Some(248044),true));}
 #[test]fn incomplete_call_not_complete(){assert!(!complete_action("<tool_call><function=run_python><parameter=code>print('</tool_call>')"));}
 #[test]fn full_xml_complete(){assert!(complete_action("<tool_call>\n<function=run_python><parameter=code>print(4)</parameter></function></tool_call>"));}
 #[test]fn thought_tools_are_not_actions(){assert!(split_content("I might use <tool_call></tool_call>",true).is_none());}
 #[test]fn preserve_think_tag_in_code(){let x="<tool_call><function=run_python><parameter=code>print('</think>')</parameter></function></tool_call>";assert_eq!(split_content(x,false),Some(x));}
 #[test]fn old_reasoning_not_in_later_prompt(){let ms=vec![Message{role:"user".into(),content:"Hi".into(),internal:false},Message{role:"assistant".into(),content:"<think>private reasoning</think>Answer".into(),internal:false},Message{role:"user".into(),content:"Next".into(),internal:false}];assert!(!render_tools("",&ms).contains("private reasoning"));}
 #[test]fn caps_are_separate(){let o=GenerationOptions{thinking:true,reasoning_tokens:9000,response_tokens:9000,context_tokens:90000}.bounded();assert_eq!((o.reasoning_tokens,o.response_tokens,o.context_tokens),(2048,4096,16384));}
}
