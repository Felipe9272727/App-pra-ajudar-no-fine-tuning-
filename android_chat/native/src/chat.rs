use crate::model::{Model, Session};
use anyhow::{anyhow, ensure, Result};
use serde::{Deserialize, Serialize};
use std::sync::atomic::{AtomicBool, Ordering};
use tokenizers::Tokenizer;
#[derive(Clone, Serialize, Deserialize)]
pub struct Message {
    pub role: String,
    pub content: String,
}
#[derive(Serialize)]
pub struct Answer {
    pub text: String,
    pub tokens: usize,
    pub prompt_tokens: usize,
    pub finish_reason: String,
}
pub struct Chat {
    pub model: Model,
    pub tokenizer: Tokenizer,
    pub system: String,
}
pub fn render(system: &str, messages: &[Message]) -> String {
    let mut s = format!("<|im_start|>system\n{system}<|im_end|>\n");
    for m in messages {
        s += &format!("<|im_start|>{}\n{}<|im_end|>\n", m.role, m.content);
    }
    s + "<|im_start|>assistant\n<think>\n\n</think>\n\n"
}
impl Chat {
    pub fn generate<F>(
        &self,
        messages: &[Message],
        max_tokens: usize,
        cancel: &AtomicBool,
        mut update: F,
    ) -> Result<Answer>
    where
        F: FnMut(&str, usize, usize),
    {
        ensure!(!messages.is_empty(), "Escreva uma mensagem");
        ensure!(
            messages
                .iter()
                .all(|m| m.role == "user" || m.role == "assistant"),
            "Papel de mensagem inválido"
        );
        let mut history = messages.to_vec();
        let budget = max_tokens.clamp(16, 256);
        let ids = loop {
            let prompt = render(&self.system, &history);
            let ids = self
                .tokenizer
                .encode(prompt, false)
                .map_err(|e| anyhow!(e.to_string()))?
                .get_ids()
                .to_vec();
            if ids.len() + budget <= 2048 {
                break ids;
            }
            if history.len() <= 1 {
                return Err(anyhow!("A mensagem é longa demais. Envie um trecho menor."));
            }
            history.remove(0);
            while history.len() > 1 && history[0].role != "user" {
                history.remove(0);
            }
        };
        let mut session = Session::new();
        let mut last = None;
        let mut generated = vec![];
        let mut text = String::new();
        for (i, id) in ids.iter().enumerate() {
            if cancel.load(Ordering::Relaxed) {
                return Ok(Answer {
                    text,
                    tokens: 0,
                    prompt_tokens: ids.len(),
                    finish_reason: "cancelled".into(),
                });
            }
            let (h, _) = match self.model.token(&mut session, *id, cancel, false) {
                Ok(v) => v,
                Err(e) if e.to_string() == "cancelled" => {
                    return Ok(Answer {
                        text,
                        tokens: 0,
                        prompt_tokens: ids.len(),
                        finish_reason: "cancelled".into(),
                    })
                }
                Err(e) => return Err(e),
            };
            if i + 1 == ids.len() {
                last = Some(h);
            }
            if i % 8 == 0 {
                update("", i + 1, ids.len());
            }
        }
        let mut hidden = last.unwrap();
        let mut reason = "length";
        for _ in 0..budget {
            if cancel.load(Ordering::Relaxed) {
                reason = "cancelled";
                break;
            }
            let logits = self.model.logits(&hidden);
            let next = crate::kernels::greedy(&logits) as u32;
            if [248044, 248046].contains(&next) {
                reason = "stop";
                break;
            }
            generated.push(next);
            let raw = self
                .tokenizer
                .decode(&generated, true)
                .map_err(|e| anyhow!(e.to_string()))?;
            text = raw
                .rsplit("</think>")
                .next()
                .unwrap_or(&raw)
                .trim()
                .to_string();
            update(&text, ids.len(), ids.len());
            if generated.len() == budget {
                break;
            }
            match self.model.token(&mut session, next, cancel, false) {
                Ok((h, _)) => hidden = h,
                Err(e) if e.to_string() == "cancelled" => {
                    reason = "cancelled";
                    break;
                }
                Err(e) => return Err(e),
            }
        }
        Ok(Answer {
            text,
            tokens: generated.len(),
            prompt_tokens: ids.len(),
            finish_reason: reason.into(),
        })
    }
}
