package dev.liquidsense.chat;
import android.content.*;
import android.os.*;
import org.json.JSONObject;
import java.util.concurrent.*;
public final class PythonClient {
    public static JSONObject run(Context context,String code)throws Exception {
        CompletableFuture<Messenger> connected=new CompletableFuture<>();CompletableFuture<String> result=new CompletableFuture<>();
        ServiceConnection connection=new ServiceConnection(){
            public void onServiceConnected(ComponentName n,IBinder b){connected.complete(new Messenger(b));}
            public void onServiceDisconnected(ComponentName n){result.completeExceptionally(new IllegalStateException("Interpretador interrompido pelo limite de execução."));}
        };
        boolean bound=context.bindService(new Intent(context,PythonService.class),connection,Context.BIND_AUTO_CREATE);
        if(!bound)throw new IllegalStateException("Não consegui iniciar o Python isolado.");
        try{
            Messenger worker=connected.get(5,TimeUnit.SECONDS);Message m=Message.obtain(null,1);Bundle data=new Bundle();data.putString("code",code);m.setData(data);
            m.replyTo=new Messenger(new Handler(Looper.getMainLooper(),answer->{if(answer.what==2){result.complete(answer.getData().getString("result","{}"));return true;}return false;}));worker.send(m);return new JSONObject(result.get(8,TimeUnit.SECONDS));
        }finally{context.unbindService(connection);}
    }
}
