use crate::model::{Model, Session};
use anyhow::{anyhow, ensure, Result};
use serde::{Deserialize, Serialize};
use std::{cell::RefCell, sync::atomic::{AtomicBool, Ordering}, time::Instant};
use tokenizers::Tokenizer;
#[derive(Clone, Serialize, Deserialize)]
pub struct Message { pub role: String, pub content: String }
#[derive(Serialize)]
pub struct Answer {
    pub text: String, pub tokens: usize, pub prompt_tokens: usize, pub finish_reason: String,
    pub generated_ids: Vec<u32>, pub reused_prompt_tokens: usize,
    pub prefill_seconds: f64, pub decode_seconds: f64, pub first_token_seconds: Option<f64>,
}
pub struct PrefixSnapshot { ids: Vec<u32>, session: Session, hidden: Vec<f32> }
pub struct Chat {
    pub model: Model, pub tokenizer: Tokenizer, pub system: String,
    pub cache: RefCell<Option<PrefixSnapshot>>, pub reuse_prefix: bool,
}
pub fn render(system: &str, messages: &[Message]) -> String {
    let mut s = if system.is_empty() { String::new() } else { format!("<|im_start|>system\n{system}<|im_end|>\n") };
    for m in messages { s += &format!("<|im_start|>{}\n{}<|im_end|>\n", m.role, m.content); }
    s + "<|im_start|>assistant\n<think>\n\n</think>\n\n"
}
fn common_prefix(a: &[u32], b: &[u32]) -> usize { a.iter().zip(b).take_while(|(a,b)| a == b).count() }
impl Chat {
    pub fn generate<F>(&self, messages: &[Message], max_tokens: usize, cancel: &AtomicBool, mut update: F) -> Result<Answer>
    where F: FnMut(&str, usize, usize) {
        let begin = Instant::now();
        ensure!(!messages.is_empty(), "Escreva uma mensagem");
        ensure!(messages.iter().all(|m| m.role == "user" || m.role == "assistant"), "Papel de mensagem inválido");
        let encode = |s: String| -> Result<Vec<u32>> { Ok(self.tokenizer.encode(s, false).map_err(|e| anyhow!(e.to_string()))?.get_ids().to_vec()) };
        let mut history = messages.to_vec(); let budget = max_tokens.clamp(16, 512);
        let (ids, boundary) = loop {
            let prompt = render(&self.system, &history);
            let ids = encode(prompt.clone())?;
            if ids.len() + budget <= 2048 {
                // History omits the empty think suffix of the generation prefix.
                // Snapshot at a tokenizer-confirmed prefix BEFORE that suffix.
                let base = prompt.strip_suffix("<think>\n\n</think>\n\n").unwrap();
                let base_ids = encode(base.into())?;
                let boundary = common_prefix(&ids, &base_ids);
                break (ids, boundary);
            }
            if history.len() <= 1 { return Err(anyhow!("A mensagem é longa demais. Envie um trecho menor.")); }
            history.remove(0);
            while history.len() > 1 && history[0].role != "user" { history.remove(0); }
        };
        let (mut session, mut last, reused) = if self.reuse_prefix {
            let cached = self.cache.borrow();
            match cached.as_ref().filter(|c| ids.starts_with(&c.ids)) {
                Some(c) => (c.session.clone(), Some(c.hidden.clone()), c.ids.len()),
                None => (Session::new(), None, 0),
            }
        } else { (Session::new(), None, 0) };
        let mut generated = vec![]; let mut text = String::new();
        for (i, id) in ids.iter().enumerate().skip(reused) {
            let result = self.model.token(&mut session, *id, cancel, false);
            let (h, _) = match result {
                Ok(v) => v,
                Err(e) if e.to_string() == "cancelled" => return Ok(Answer { text, tokens: 0, prompt_tokens: ids.len(), finish_reason: "cancelled".into(), generated_ids: generated, reused_prompt_tokens: reused, prefill_seconds: begin.elapsed().as_secs_f64(), decode_seconds: 0.0, first_token_seconds: None }),
                Err(e) => return Err(e),
            };
            if self.reuse_prefix && i + 1 == boundary {
                *self.cache.borrow_mut() = Some(PrefixSnapshot { ids: ids[..boundary].to_vec(), session: session.clone(), hidden: h.clone() });
            }
            last = Some(h);
            if i % 8 == 0 { update("", i + 1, ids.len()); }
        }
        let prefill_seconds = begin.elapsed().as_secs_f64();
        let mut hidden = last.ok_or_else(|| anyhow!("Empty token sequence"))?;
        let decode_begin = Instant::now(); let mut first_token_seconds = None; let mut reason = "length";
        for _ in 0..budget {
            if cancel.load(Ordering::Relaxed) { reason = "cancelled"; break; }
            let logits = self.model.logits(&hidden);
            let next = crate::kernels::greedy(&logits) as u32;
            if first_token_seconds.is_none() { first_token_seconds = Some(begin.elapsed().as_secs_f64()); }
            if next == 248044 || (self.model.manifest.source_checkpoint_sha256 != crate::model::SPECIALIST && next == 248046) { reason = "stop"; break; }
            generated.push(next);
            let raw = self.tokenizer.decode(&generated, true).map_err(|e| anyhow!(e.to_string()))?;
            text = raw.rsplit("</think>").next().unwrap_or(&raw).trim().to_string();
            update(&text, ids.len(), ids.len());
            if generated.len() == budget { break; }
            match self.model.token(&mut session, next, cancel, false) {
                Ok((h, _)) => hidden = h,
                Err(e) if e.to_string() == "cancelled" => { reason = "cancelled"; break; }
                Err(e) => return Err(e),
            }
        }
        Ok(Answer { text, tokens: generated.len(), prompt_tokens: ids.len(), finish_reason: reason.into(), generated_ids: generated, reused_prompt_tokens: reused, prefill_seconds, decode_seconds: decode_begin.elapsed().as_secs_f64(), first_token_seconds })
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn cache_requires_all_saved_tokens() {
        let a = [1,2,3];
        assert!([1,2,3,4].starts_with(&a));
        assert!(![1,2,9,4].starts_with(&a));
        assert!(![1,2].starts_with(&a));
        assert_eq!(common_prefix(&[1,2,8], &[1,2,9]), 2);
    }
}
