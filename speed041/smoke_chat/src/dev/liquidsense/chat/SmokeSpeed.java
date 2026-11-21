package dev.liquidsense.chat;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.webkit.WebView;
import java.lang.reflect.Field;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

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
            String answer=send(view,"Quanto é dois mais dois? Responda apenas o número.",240);
            result.putString("local_reply",answer);
            if(!prefs.getString("conversation_base", "").contains("Marcador local antes da atualização")) throw new IllegalStateException("Missing prior local messages");
            js(view,"document.getElementById('model-button').click()");
            waitFor(view,"!!document.querySelector('[data-model=gpu]')",15);
            js(view,"document.querySelector('[data-model=gpu]').click()");
            waitFor(view,"document.getElementById('model-caption').textContent.includes('Hugging Face')",30);
            String identity=send(view,"Você é o Qwen?",15);
            if(!identity.startsWith("\"Sou o Liquid Sense") || !identity.contains("Qwen3.5-0.8B")) throw new IllegalStateException(identity);
            result.putString("identity",identity);
            result.putString("claim","0.6.5 local inference completed; prior history retained; GPU-mode identity answered from app metadata");
            finish(Activity.RESULT_OK,result);
        } catch(Throwable error){ result.putString("error",error.toString()); finish(Activity.RESULT_CANCELED,result); }
    }
}
