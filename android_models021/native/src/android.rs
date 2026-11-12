use crate::{
    chat::{Chat, Message},
    model::Model,
};
use anyhow::{anyhow, ensure, Result};
use jni::{
    objects::{JObject, JString, JValue},
    sys::{jint, jlong, jstring},
    JNIEnv,
};
use std::{
    fs::File,
    os::fd::FromRawFd,
    panic::{catch_unwind, AssertUnwindSafe},
    sync::{
        atomic::{AtomicBool, Ordering},
        Mutex, OnceLock,
    },
};
static ENGINE: OnceLock<Mutex<Option<Chat>>> = OnceLock::new();
static CANCEL: AtomicBool = AtomicBool::new(false);
fn engine() -> &'static Mutex<Option<Chat>> {
    ENGINE.get_or_init(|| Mutex::new(None))
}
fn output(env: &mut JNIEnv, value: String) -> jstring {
    env.new_string(value)
        .map(|s| s.into_raw())
        .unwrap_or(std::ptr::null_mut())
}
fn protected<F: FnOnce() -> Result<String>>(f: F) -> String {
    match catch_unwind(AssertUnwindSafe(f)) {
        Ok(Ok(s)) => s,
        Ok(Err(e)) => serde_json::json!({"error":e.to_string()}).to_string(),
        Err(_) => {
            serde_json::json!({"error":"Não foi possível concluir a operação local."}).to_string()
        }
    }
}
#[no_mangle]
pub extern "system" fn Java_dev_liquidsense_chat_MainActivity_nativeLoad(
    mut env: JNIEnv,
    _this: JObject,
    fd: jint,
    offset: jlong,
    length: jlong,
    token_fd: jint,
    token_offset: jlong,
    token_length: jlong,
    identity: JString,
) -> jstring {
    let value = protected(|| {
        let _ = rayon::ThreadPoolBuilder::new()
            .num_threads(4)
            .build_global();
        ensure!(
            fd >= 0
                && token_fd >= 0
                && offset >= 0
                && length > 0
                && token_offset >= 0
                && token_length > 0,
            "Asset inválido"
        );
        *engine().lock().map_err(|_| anyhow!("Motor indisponível"))? = None;
        let f = unsafe { File::from_raw_fd(fd) };
        let tf = unsafe { File::from_raw_fd(token_fd) };
        let mut model = Model::region(&f, offset as u64, length as usize)?;
        model.optimize = true;
        let map = unsafe {
            memmap2::MmapOptions::new()
                .offset(token_offset as u64)
                .len(token_length as usize)
                .map(&tf)?
        };
        let tokenizer =
            tokenizers::Tokenizer::from_bytes(&map).map_err(|e| anyhow!(e.to_string()))?;
        let identity: String = env.get_string(&identity)?.into();
        let info: serde_json::Value = serde_json::from_str(&identity)?;
        ensure!((info["selected_model"].as_str() == Some("specialist")) == (model.manifest.source_checkpoint_sha256 == crate::model::SPECIALIST), "Versão de pesos diferente da selecionada");
        *engine().lock().map_err(|_| anyhow!("Motor indisponível"))? = Some(Chat {
            cache: std::cell::RefCell::new(None), reuse_prefix: true,
            model,
            tokenizer,
            system: if info["selected_model"].as_str() == Some("specialist") { String::new() } else { info["system_message"]
                .as_str()
                .ok_or_else(|| anyhow!("Identidade inválida"))?
                .to_string() },
        });
        Ok("ok".into())
    });
    output(&mut env, value)
}
#[no_mangle]
pub extern "system" fn Java_dev_liquidsense_chat_MainActivity_nativeGenerate(
    mut env: JNIEnv,
    this: JObject,
    messages: JString,
    budget: jint,
) -> jstring {
    let value = protected(|| {
        let source: String = env.get_string(&messages)?.into();
        let messages: Vec<Message> = serde_json::from_str(&source)?;
        let guard = engine().lock().map_err(|_| anyhow!("Motor indisponível"))?;
        let chat = guard
            .as_ref()
            .ok_or_else(|| anyhow!("O modelo ainda está carregando"))?;
        let answer = chat.generate(
            &messages,
            budget.clamp(16, 512) as usize,
            &CANCEL,
            |text, done, total| {
                if let Ok(s) = env.new_string(text) {
                    let obj = JObject::from(s);
                    let _ = env.call_method(
                        &this,
                        "onNativeText",
                        "(Ljava/lang/String;II)V",
                        &[
                            JValue::Object(&obj),
                            JValue::Int(done as i32),
                            JValue::Int(total as i32),
                        ],
                    );
                    let _ = env.delete_local_ref(obj);
                }
            },
        )?;
        Ok(serde_json::to_string(&answer)?)
    });
    output(&mut env, value)
}
#[no_mangle]
pub extern "system" fn Java_dev_liquidsense_chat_MainActivity_nativeCancel(
    _env: JNIEnv,
    _this: JObject,
) {
    CANCEL.store(true, Ordering::Relaxed);
}
#[no_mangle]
pub extern "system" fn Java_dev_liquidsense_chat_MainActivity_nativeResetCancel(
    _env: JNIEnv,
    _this: JObject,
) {
    CANCEL.store(false, Ordering::Relaxed);
}
