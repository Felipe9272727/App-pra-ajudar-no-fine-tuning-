package dev.liquidsense.chat;

import android.app.Service;
import android.content.Intent;
import android.os.*;
import org.json.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;

/** Separate isolated Android UID, no app data/network access or exported API. */
public final class PythonService extends Service {
    static {System.loadLibrary("liquid_python");}
    private static native byte[] nativeRun(byte[] code);
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final Handler clock=new Handler(Looper.getMainLooper());
    private final Messenger receiver=new Messenger(new Handler(Looper.getMainLooper(),msg->{
        if(msg.what!=1||msg.replyTo==null)return false;final Messenger reply=msg.replyTo;final String code=msg.getData().getString("code","");
        worker.execute(()->{
            // Independent wall watchdog also stops a native builtin that does
            // not return to the VM hook. This process contains no model/chat.
            Runnable watchdog=()->android.os.Process.killProcess(android.os.Process.myPid());clock.postDelayed(watchdog,5000);
            JSONObject result=new JSONObject();try{
                if(code.getBytes(StandardCharsets.UTF_8).length>6000)throw new IllegalArgumentException("Código grande demais");byte[] out=nativeRun(code.getBytes(StandardCharsets.UTF_8));if(out==null||out.length<1)throw new IllegalStateException("Falha no interpretador");
                boolean ok=out[0]==1;String text=new String(out,1,out.length-1,StandardCharsets.UTF_8);
                result.put("tool","run_python").put("ok",ok).put("stdout",ok?ToolExecutor.safe(text,6000):"").put("runtime","MicroPython1.26.1 Python3 subset, math/json; no packages").put("filesystem",false).put("network",false);if(!ok)result.put("error",ToolExecutor.safe(text,1000));
            }catch(Throwable e){try{result.put("tool","run_python").put("ok",false).put("error",e.toString());}catch(Exception ignored){}}
            finally{clock.removeCallbacks(watchdog);}
            Message answer=Message.obtain(null,2);Bundle b=new Bundle();b.putString("result",result.toString());answer.setData(b);try{reply.send(answer);}catch(Exception ignored){}
        });return true;
    }));
    @Override public IBinder onBind(Intent i){return receiver.getBinder();}
    @Override public void onDestroy(){worker.shutdownNow();super.onDestroy();}
}
