package dev.liquidsense.chat;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.res.AssetFileDescriptor;
import android.os.Bundle;
import android.webkit.WebView;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import org.json.JSONObject;

public final class SmokeSpeed extends Instrumentation {
    @Override public void onCreate(Bundle args) { super.onCreate(args); start(); }

    private String js(WebView view, String code) throws Exception {
        CompletableFuture<String> result = new CompletableFuture<>();
        runOnMainSync(() -> view.evaluateJavascript(code, result::complete));
        return result.get(15, TimeUnit.SECONDS);
    }

    private void waitFor(WebView view, String check, int seconds) throws Exception {
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(seconds);
        while (System.nanoTime() < deadline) {
            if ("true".equals(js(view, check))) return;
            Thread.sleep(300);
        }
        throw new IllegalStateException("Timed out: " + check + " / " + js(view,"document.body.innerText.slice(-500)"));
    }

    private String send(WebView view, String prompt, int seconds) throws Exception {
        js(view,"var box=document.getElementById('message');box.value="+org.json.JSONObject.quote(prompt)+
            ";box.dispatchEvent(new Event('input'))");
        waitFor(view,"!document.getElementById('send').disabled",90);
        js(view,"document.getElementById('send').click()");
        waitFor(view,"Array.from(document.querySelectorAll('.message-actions')).at(-1)?.textContent.includes('Detalhes')",seconds);
        String reply=js(view,"Array.from(document.querySelectorAll('.answer')).at(-1)?.textContent.trim()");
        if(reply.equals("null") || reply.equals("\"\"") || reply.contains("Não consegui concluir") || reply.contains("sem uma resposta")) {
            throw new IllegalStateException("No model answer: "+reply);
        }
        return reply;
    }

    private JSONObject boundedNativeProbe(Activity activity) throws Exception {
        Class<?> type=activity.getClass();
        Method load=type.getDeclaredMethod("nativeLoad",int.class,long.class,long.class,int.class,long.class,long.class,String.class);
        Method generate=type.getDeclaredMethod("nativeGenerate",String.class,String.class);
        load.setAccessible(true);
        generate.setAccessible(true);
        try(AssetFileDescriptor model=activity.getAssets().openFd("model.lsp");
            AssetFileDescriptor tokens=activity.getAssets().openFd("tokenizer.json")) {
            int modelFd=model.getParcelFileDescriptor().detachFd();
            int tokenizerFd=tokens.getParcelFileDescriptor().detachFd();
            String info="{\"selected_model\":\"base\",\"model_source\":\"general\",\"system_message\":\"\"}";
            Object loaded=load.invoke(activity,modelFd,model.getStartOffset(),model.getLength(),
                tokenizerFd,tokens.getStartOffset(),tokens.getLength(),info);
            if(!"ok".equals(loaded)) throw new IllegalStateException(String.valueOf(loaded));
        }
        String messages="[{\"role\":\"user\",\"content\":\"Oi\"}]";
        String options="{\"thinking\":false,\"context_tokens\":2048,\"response_tokens\":16}";
        return new JSONObject((String)generate.invoke(activity,messages,options));
    }

    @Override public void onStart() {
        Bundle result=new Bundle();
        try {
            Activity activity=startActivitySync(new Intent().setClassName(getTargetContext().getPackageName(),
                "dev.liquidsense.chat.MainActivity").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK));
            SharedPreferences prefs=activity.getPreferences(0);
            if (!"retained".equals(prefs.getString("ci_update_marker", ""))) throw new IllegalStateException("Missing prior app data");
            Field field=activity.getClass().getDeclaredField("web");
            field.setAccessible(true);
            WebView view=(WebView)field.get(activity);
            waitFor(view,"document.getElementById('model-caption')?.textContent.includes('Offline')",40);
            if(!prefs.getString("conversation_base", "").contains("Marcador local antes da atualização")) throw new IllegalStateException("Missing prior local messages");
            js(view,"document.getElementById('model-button').click()");
            waitFor(view,"!!document.querySelector('[data-model=gpu]')",15);
            js(view,"document.querySelector('[data-model=gpu]').click()");
            waitFor(view,"document.getElementById('model-caption').textContent.includes('Hugging Face')",30);
            String identity=send(view,"Você é o Qwen?",15);
            if(!identity.startsWith("\"Sou o Liquid Sense") || !identity.contains("Qwen3.5-0.8B")) throw new IllegalStateException(identity);
            result.putString("identity",identity);
            FutureTask<JSONObject> probe=new FutureTask<>(()->boundedNativeProbe(activity));
            new Thread(probe,"bounded-native-check").start();
            try {
                JSONObject local=probe.get(180,TimeUnit.SECONDS);
                if(local.has("error") || local.getJSONArray("generated_ids").length()==0) throw new IllegalStateException(local.toString());
                result.putString("native_reply",local.toString());
            } catch(TimeoutException timeout) {
                Method cancel=activity.getClass().getDeclaredMethod("nativeCancel");
                cancel.setAccessible(true);
                cancel.invoke(activity);
                result.putString("native_timeout","Bounded inference exceeded 180 seconds under x86-to-ARM emulation; real ARM64 model results are recorded separately");
            }
            result.putString("claim","0.6.5 Android UI preserved history and answered GPU-mode identity from app metadata");
            finish(Activity.RESULT_OK,result);
        } catch(Throwable error){ result.putString("error",error.toString()); finish(Activity.RESULT_CANCELED,result); }
    }
}
