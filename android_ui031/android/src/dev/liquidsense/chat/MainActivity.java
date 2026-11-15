package dev.liquidsense.chat;

import android.app.Activity;
import android.os.*;
import android.content.*;
import android.content.res.*;
import android.graphics.Color;
import android.net.Uri;
import android.webkit.*;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

/** Local-only presentation; the exact030 Rust JNI engine and tool agent are retained. */
public final class MainActivity extends Activity {
    static { System.loadLibrary("liquid_sense"); }
    private native String nativeLoad(int fd,long offset,long length,int tokenizerFd,long tokenizerOffset,long tokenizerLength,String identity);
    private native String nativeAttachPatch(int fd,long offset,long length,String sha256);
    private native String nativeAttachDense(int fd,long offset,long length);
    private native String nativeGenerate(String messages,String options);
    private native void nativeCancel();
    private native void nativeResetCancel();
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final Handler main=new Handler(Looper.getMainLooper());
    private WebView web;
    private JSONArray history=new JSONArray(),threads=new JSONArray(),pendingTools=new JSONArray(),activity=new JSONArray();
    private String selectedModel="tools",threadId="";
    private volatile boolean busy=false,loading=false,ready=false,destroyed=false,cancelRequested=false;
    private boolean pageReady=false;
    private long lastStream;
    private String currentStage="",lastThought="";
    private boolean forced=false;
    private static final String PAGE="https://appassets.androidplatform.net/chat/index.html";

    @Override public void onCreate(Bundle saved){super.onCreate(saved);
        getWindow().setStatusBarColor(Color.rgb(24,25,27));getWindow().setNavigationBarColor(Color.rgb(24,25,27));
        if(!getPreferences(MODE_PRIVATE).contains("conversation_base"))getPreferences(MODE_PRIVATE).edit().putString("conversation_base",getPreferences(MODE_PRIVATE).getString("conversation","[]")).apply();
        selectedModel=getPreferences(MODE_PRIVATE).getString("selected_model_v022","tools");if(!validModel(selectedModel))selectedModel="tools";
        try{threads=new JSONArray(getPreferences(MODE_PRIVATE).getString("threads_v031","[]"));}catch(Exception ignored){}
        migrateHistories();readHistory();saveHistory();
        web=new WebView(this);web.setBackgroundColor(Color.rgb(24,25,27));web.setOnApplyWindowInsetsListener((v,insets)->{v.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());return insets;});
        WebSettings settings=web.getSettings();settings.setJavaScriptEnabled(true);settings.setDomStorageEnabled(false);settings.setAllowFileAccess(false);settings.setAllowContentAccess(false);settings.setAllowFileAccessFromFileURLs(false);settings.setAllowUniversalAccessFromFileURLs(false);settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);settings.setSupportZoom(false);
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE);web.addJavascriptInterface(new Bridge(),"Android");
        web.setWebViewClient(new WebViewClient(){
            @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){return true;}
            @Override public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest r){Uri u=r.getUrl();String path=u.getPath();
                if("https".equals(u.getScheme())&&"appassets.androidplatform.net".equals(u.getHost())&&Arrays.asList("/chat/index.html","/chat/chat.css","/chat/chat.js").contains(path)){
                    try{String mime=path.endsWith(".css")?"text/css":path.endsWith(".js")?"application/javascript":"text/html";return new WebResourceResponse(mime,"utf-8",200,"OK",Collections.singletonMap("X-Content-Type-Options","nosniff"),getAssets().open(path.substring(1)));}catch(IOException ignored){}
                }
                return new WebResourceResponse("text/plain","utf-8",new ByteArrayInputStream(new byte[0]));}
        });setContentView(web);web.loadUrl(PAGE);
    }
    public final class Bridge {@JavascriptInterface public void dispatch(String source){if(source==null||source.length()>300000)return;main.post(()->{if(destroyed)return;try{command(new JSONObject(source));}catch(Exception e){toast(friendly(e));}});}}
    private void command(JSONObject m)throws Exception {
        String type=m.optString("type");
        switch(type){
            case "boot":if(pageReady)return;pageReady=true;loading=true;state();loadSelectedModel();break;
            case "send":submit(m.optString("text"));break;
            case "cancel":if(busy){cancelRequested=true;nativeCancel();toast("Interrompendo a geração…");}break;
            case "selectModel":if(!busy&&!loading&&validModel(m.optString("id")))select(m.getString("id"),null);break;
            case "setProfile":if(!busy&&!loading&&Arrays.asList("normal","profundo","extenso").contains(m.optString("id"))){getPreferences(MODE_PRIVATE).edit().putString("reasoning_mode_"+selectedModel,m.getString("id")).apply();emit(new JSONObject().put("type","profile").put("id",profileMode()));}break;
            case "newChat":if(!busy&&!loading){saveHistory();threadId=UUID.randomUUID().toString();history=new JSONArray();saveHistory();state();}break;
            case "openChat":if(!busy&&!loading){for(int i=0;i<threads.length();i++){JSONObject t=threads.optJSONObject(i);if(t!=null&&t.optString("id").equals(m.optString("id"))){select(t.getString("model"),new JSONObject(t.toString()));break;}}}break;
            case "openLink":String url=m.optString("url");Uri uri=Uri.parse(url);if(("https".equals(uri.getScheme())||"http".equals(uri.getScheme()))&&uri.getHost()!=null)startActivity(new Intent(Intent.ACTION_VIEW,uri));break;
            case "copy":copy(m.optString("text"));break;
            case "copyDiagnostic":copy(getPreferences(MODE_PRIVATE).getString("inference_trace_last","[]"));break;
        }
    }
    private boolean validModel(String id){return Arrays.asList("tools","base","epochs029","specialist").contains(id);}
    private boolean usesTools(String id){return id.equals("tools")||id.equals("epochs029");}
    private boolean specialistAvailable(){try{return getPackageManager().getPackageInfo("dev.liquidsense.chat.fast",0).versionCode>=3;}catch(Exception e){return false;}}
    private String profileMode(){return getPreferences(MODE_PRIVATE).getString("reasoning_mode_"+selectedModel,"normal");}
    private void migrateHistories(){
        String chosen=selectedModel;
        for(String id:new String[]{"tools","base","epochs029","specialist"}){
            selectedModel=id;readHistory();if(history.length()>0)saveHistory();
        }
        selectedModel=chosen;
    }
    private void readHistory(){try{history=new JSONArray(getPreferences(MODE_PRIVATE).getString("conversation_"+selectedModel,"[]"));}catch(Exception e){history=new JSONArray();}threadId=getPreferences(MODE_PRIVATE).getString("thread_id_v031_"+selectedModel,UUID.randomUUID().toString());}
    private void select(String id,JSONObject thread)throws Exception {
        if(id.equals("specialist")&&!specialistAvailable()){emit(new JSONObject().put("type","installSpecialist"));return;}
        saveHistory();boolean reload=!id.equals(selectedModel)||!ready;selectedModel=id;getPreferences(MODE_PRIVATE).edit().putString("selected_model_v022",id).apply();
        if(thread==null)readHistory();else{history=new JSONArray(thread.getJSONArray("messages").toString());threadId=thread.getString("id");}
        saveHistory();if(reload){ready=false;loading=true;}state();if(reload)loadSelectedModel();
    }
    private synchronized void saveHistory(){
        try{String title="Nova conversa";for(int i=0;i<history.length();i++){JSONObject m=history.optJSONObject(i);if(m!=null&&m.optString("role").equals("user")&&!m.optBoolean("internal")){title=m.optString("content").replace('\n',' ').trim();if(title.length()>58)title=title.substring(0,58)+"…";break;}}
            JSONObject record=new JSONObject().put("id",threadId).put("model",selectedModel).put("title",title).put("updated",System.currentTimeMillis()).put("messages",new JSONArray(history.toString()));boolean found=false;
            for(int i=0;i<threads.length();i++)if(threads.getJSONObject(i).optString("id").equals(threadId)){threads.put(i,record);found=true;break;}if(!found&&history.length()>0)threads.put(record);
            getPreferences(MODE_PRIVATE).edit().putString("conversation_"+selectedModel,history.toString()).putString("thread_id_v031_"+selectedModel,threadId).putString("threads_v031",threads.toString()).apply();
        }catch(Exception ignored){}
    }
    private JSONArray threadList()throws Exception {List<JSONObject> list=new ArrayList<>();for(int i=0;i<threads.length();i++){JSONObject t=threads.getJSONObject(i);list.add(new JSONObject().put("id",t.getString("id")).put("title",t.optString("title")).put("model",t.getString("model")).put("updated",t.optLong("updated")));}Collections.sort(list,(a,b)->Long.compare(b.optLong("updated"),a.optLong("updated")));return new JSONArray(list);}
    private void state(){try{emit(new JSONObject().put("type","state").put("model",selectedModel).put("profile",profileMode()).put("ready",ready).put("loading",loading).put("busy",busy).put("history",new JSONArray(history.toString())).put("threads",threadList()).put("thread",threadId).put("available",specialistAvailable()));}catch(Exception e){toast(friendly(e));}}
    private void threadsChanged(){try{emit(new JSONObject().put("type","threads").put("threads",threadList()).put("thread",threadId));}catch(Exception ignored){}}
    private void loadSelectedModel(){ready=false;loading=true;final String chosen=selectedModel;
        worker.execute(()->{try{
            AssetManager assets=chosen.equals("specialist")?createPackageContext("dev.liquidsense.chat.fast",0).getAssets():getAssets();
            AssetFileDescriptor model=assets.openFd("model.lsp"),tokens=assets.openFd("tokenizer.json");long mo=model.getStartOffset(),ml=model.getLength(),to=tokens.getStartOffset(),tl=tokens.getLength();int mf=model.getParcelFileDescriptor().detachFd(),tf=tokens.getParcelFileDescriptor().detachFd();model.close();tokens.close();
            JSONObject identity=new JSONObject(readAsset("identity.json"));identity.put("selected_model",chosen).put("model_source",chosen.equals("specialist")?"specialist":"general");if(usesTools(chosen))identity.put("tools_prefix",readAsset("tools_prefix.txt"));
            String result=nativeLoad(mf,mo,ml,tf,to,tl,identity.toString());if(!"ok".equals(result))throw new IOException(error(result));
            JSONObject build=new JSONObject(readAsset("build_config.json"));if(chosen.equals("epochs029")){AssetFileDescriptor patch=getAssets().openFd("epoch02.lspatch");long off=patch.getStartOffset(),len=patch.getLength();int fd=patch.getParcelFileDescriptor().detachFd();patch.close();String attached=nativeAttachPatch(fd,off,len,build.getString("experimental_patch_sha256"));if(!"ok".equals(attached))throw new IOException(error(attached));}
            if(chosen.equals("tools")&&build.optBoolean("use_validated_dense",false))throw new IOException("Configuração de pesos incompatível com esta prévia");
            main.post(()->{if(destroyed)return;loading=false;ready=true;emitType("ready");});
        }catch(Throwable e){main.post(()->{loading=false;ready=false;try{emit(new JSONObject().put("type","loadError").put("error",friendly(e)));}catch(Exception ignored){}});}});
    }
    private void submit(String text)throws Exception {
        if(!ready||busy||loading)return;text=text.trim();if(text.isEmpty())return;if(text.length()>64000){toast("Divida mensagens com mais de 64 mil caracteres.");return;}
        history.put(new JSONObject().put("role","user").put("content",text));saveHistory();pendingTools=new JSONArray();activity=new JSONArray();currentStage="";lastThought="";forced=false;lastStream=0;busy=true;cancelRequested=false;nativeResetCancel();emit(new JSONObject().put("type","begin").put("text",text));threadsChanged();final String payload=history.toString();
        worker.execute(()->{try{if(cancelRequested){finish(new JSONObject().put("finish_reason","cancelled"));return;}JSONObject answer=usesTools(selectedModel)?generateWithTools(payload):new JSONObject(nativeGenerate(payload,InferenceSettings.options(profileMode()).toString()));captureThought(answer);finish(answer);}catch(Throwable e){try{finish(new JSONObject().put("error",friendly(e)));}catch(Exception ignored){}}});
    }
    private void stage(String stage,String detail,int tokens){try{if(!stage.equals(currentStage)){currentStage=stage;activity.put(new JSONObject().put("kind","stage").put("stage",stage).put("detail",detail));}emit(new JSONObject().put("type","stage").put("stage",stage).put("detail",detail).put("tokens",tokens));}catch(Exception ignored){}}
    public void onNativeText(String text,int done,int total){
        if(destroyed||!busy)return;if(total==0){stage("thinking","",done);return;}if(text.isEmpty()){stage("reading","Lendo o contexto da conversa",0);return;}if(text.contains("<tool_call>")){stage("preparing","Aguardando uma chamada completa",0);return;}
        stage("writing","",0);long now=SystemClock.elapsedRealtime();if(now-lastStream<90)return;lastStream=now;try{emit(new JSONObject().put("type","stream").put("text",text));}catch(Exception ignored){}
    }
    private void captureThought(JSONObject answer){try{String thought=UiText.thought(answer);forced|=answer.optBoolean("forced_reasoning_close");if(!thought.isEmpty()&&!thought.equals(lastThought)){lastThought=thought;JSONObject event=new JSONObject().put("kind","thought").put("text",thought).put("forced",answer.optBoolean("forced_reasoning_close"));activity.put(event);emit(new JSONObject(event.toString()).put("type","thought"));}}catch(Exception ignored){}}
    private JSONObject generateWithTools(String payload)throws Exception {
        final JSONArray persisted=new JSONArray(payload);
        AgentRunner runner=new AgentRunner((messages,options)->new JSONObject(nativeGenerate(messages.toString(),options.toString())),call->{String name=call.getString("name");JSONObject args=call.getJSONObject("arguments");stage(name.equals("search_web")?"searching":"python",name.equals("search_web")?args.getString("query"):"Executando o código escolhido pelo modelo",0);return name.equals("search_web")?ToolExecutor.search(args.getString("query")):PythonClient.run(this,args.getString("code"));},new AgentRunner.Events(){
            public void diagnostic(JSONArray records){getPreferences(MODE_PRIVATE).edit().putString("inference_trace_last",records.toString()).apply();JSONObject r=records.optJSONObject(records.length()-1);if(r!=null){JSONObject a=r.optJSONObject("answer");if(a!=null)captureThought(a);}}
            public void append(JSONObject m){pendingTools.put(m);persisted.put(m);getPreferences(MODE_PRIVATE).edit().putString("conversation_"+selectedModel,persisted.toString()).apply();}
            public void tool(JSONObject call,JSONObject observation){try{emit(new JSONObject().put("type","tool").put("call",call).put("observation",observation));}catch(Exception ignored){}}
        },()->cancelRequested);return runner.run(payload,profileMode());
    }
    private void finish(JSONObject answer){main.post(()->{if(destroyed)return;try{
        for(int i=0;i<pendingTools.length();i++)history.put(pendingTools.getJSONObject(i));pendingTools=new JSONArray();String text=answer.optString("text");if(!text.isEmpty())history.put(new JSONObject().put("role","assistant").put("content",text).put("ui_activity",new JSONArray(activity.toString())));saveHistory();busy=false;
        int count=answer.optInt("tokens");double decode=answer.optDouble("decode_seconds");String metrics=String.format(Locale.ROOT,"%d tokens · %.1fs de preparo · %.1f tokens/s · %d tokens de raciocínio · %d ferramenta(s)",count,answer.optDouble("prefill_seconds"),decode>0?count/decode:0,answer.optInt("reasoning_tokens"),answer.optInt("actual_tool_calls"));
        emit(new JSONObject().put("type","finish").put("text",text).put("reason",answer.optString("finish_reason")).put("error",answer.optString("error")).put("metrics",metrics).put("forced",forced));threadsChanged();
        }catch(Exception e){busy=false;toast(friendly(e));}});}
    private void emitType(String type){try{emit(new JSONObject().put("type",type));}catch(Exception ignored){}}
    private void emit(JSONObject value){final String json=value.toString();main.post(()->{if(!destroyed&&pageReady)web.evaluateJavascript("window.Liquid&&window.Liquid.receive("+JSONObject.quote(json)+");",null);});}
    private void toast(String text){try{emit(new JSONObject().put("type","toast").put("text",text));}catch(Exception ignored){}}
    private void copy(String text){((android.content.ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("Liquid Sense",text));toast("Copiado para a área de transferência.");}
    private String readAsset(String name)throws IOException{try(InputStream in=getAssets().open(name);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return new String(out.toByteArray(),StandardCharsets.UTF_8);}}
    private String error(String result){try{return new JSONObject(result).optString("error",result);}catch(Exception e){return result;}}
    private String friendly(Throwable e){return e.getMessage()==null?e.getClass().getSimpleName():e.getMessage();}
    @Override public void onBackPressed(){web.evaluateJavascript("window.Liquid&&window.Liquid.back()",v->{if(!"true".equals(v))MainActivity.super.onBackPressed();});}
    @Override protected void onPause(){super.onPause();if(busy){cancelRequested=true;nativeCancel();}}
    @Override protected void onDestroy(){destroyed=true;if(busy)nativeCancel();worker.shutdown();if(web!=null){web.removeJavascriptInterface("Android");web.destroy();}super.onDestroy();}
}
