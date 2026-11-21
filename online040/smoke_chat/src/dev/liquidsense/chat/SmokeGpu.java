package dev.liquidsense.chat;

import android.app.*;
import android.content.*;
import android.os.*;
import android.webkit.WebView;
import java.lang.reflect.*;
import java.util.concurrent.*;

/** Drive the real installed WebView and Android bridge from a separate test APK. */
public final class SmokeGpu extends Instrumentation {
    @Override public void onCreate(Bundle b) { super.onCreate(b); start(); }
    private String js(WebView web, String code) throws Exception {
        CompletableFuture<String> result = new CompletableFuture<>();
        runOnMainSync(() -> web.evaluateJavascript(code, result::complete));
        return result.get(15, TimeUnit.SECONDS);
    }
    private void waitFor(WebView web, String expression, int seconds) throws Exception {
        long until = System.currentTimeMillis()+seconds*1000L;
        while (System.currentTimeMillis()<until) {
            if ("true".equals(js(web, expression))) return;
            Thread.sleep(300);
        }
        throw new IllegalStateException("UI timeout: "+expression+" / "+js(web,"document.body.innerText.slice(-500)"));
    }
    @Override public void onStart() {
        Bundle result=new Bundle();
        try {
            Context c=getTargetContext();
            Activity a=startActivitySync(new Intent().setClassName(c.getPackageName(),"dev.liquidsense.chat.MainActivity")
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            SharedPreferences preferences=a.getPreferences(0);
            if (!"retained".equals(preferences.getString("ci_update_marker", ""))) throw new IllegalStateException("Local app data lost during update");
            Field field=a.getClass().getDeclaredField("web");field.setAccessible(true);
            WebView web=(WebView)field.get(a);
            waitFor(web,"!!document.getElementById('model-button')",40);
            js(web,"document.getElementById('model-button').click()");
            waitFor(web,"!!document.querySelector('[data-model=gpu]')",15);
            js(web,"document.querySelector('[data-model=gpu]').click()");
            waitFor(web,"document.getElementById('model-caption').textContent.includes('Hugging Face')",90);
            js(web,"var box=document.getElementById('message');box.value='Quanto é 2 + 2? Responda apenas o número.';box.dispatchEvent(new Event('input'))");
            waitFor(web,"!document.getElementById('send').disabled",20);
            js(web,"document.getElementById('send').click()");
            waitFor(web,"document.querySelector('.message-actions')?.textContent.includes('Detalhes')",120);
            String reply=js(web,"document.querySelector('.answer').textContent.trim()");
            boolean quota=reply.contains("Cota do ZeroGPU atingida");
            if (!"\"4\"".equals(reply) && !quota) throw new IllegalStateException("Unexpected GPU reply: "+reply);
            result.putString("reply",reply);
            js(web,"document.getElementById('model-button').click()");
            waitFor(web,"!!document.querySelector('[data-model=base]')",15);
            js(web,"document.querySelector('[data-model=base]').click()");
            waitFor(web,"document.getElementById('model-caption').textContent.includes('Offline')",30);
            if (!preferences.getString("conversation_gpu", "").contains("Responda apenas o número")) throw new IllegalStateException("GPU history missing");
            if (!preferences.getString("conversation_base", "").contains("Marcador local antes da atualização")) throw new IllegalStateException("Local history missing");
            result.putString("claim",quota?"GPU selected and live quota rejection rendered; both histories retained and local mode reselected":"GPU selected, live HF answer received; both histories retained and local mode reselected");
            finish(Activity.RESULT_OK,result);
        } catch(Throwable e){result.putString("error",e.toString()); finish(Activity.RESULT_CANCELED,result);}
    }
}
