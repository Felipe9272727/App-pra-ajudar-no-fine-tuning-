package dev.liquidsense.chat;

import android.app.*;
import android.os.*;
import android.content.*;
import android.content.res.AssetFileDescriptor;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.*;
import android.view.inputmethod.EditorInfo;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;

public final class MainActivity extends Activity {
    static { System.loadLibrary("liquid_sense"); }
    private native String nativeLoad(int fd,long offset,long length,int tokenizerFd,long tokenizerOffset,long tokenizerLength,String identity);
    private native String nativeAttachDense(int fd,long offset,long length);
    private native String nativeGenerate(String messages,int budget);
    private native void nativeCancel();
    private native void nativeResetCancel();
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final Handler main=new Handler(Looper.getMainLooper());
    private JSONArray history=new JSONArray();
    private JSONArray pendingToolHistory=new JSONArray();
    private LinearLayout timeline;
    private ScrollView scroll;
    private EditText composer;
    private TextView status,send,pending,modelChoice;
    private String selectedModel="tools";
    private boolean loading=false;
    private boolean ready=false,busy=false,destroyed=false;
    private String latestMetrics="";
    private volatile boolean cancelRequested=false;
    private final int bg=Color.rgb(11,16,32),surface=Color.rgb(23,32,52),ink=Color.rgb(235,240,255),muted=Color.rgb(150,165,191),accent=Color.rgb(153,170,255);

    private int dp(float n){return (int)(getResources().getDisplayMetrics().density*n+.5f);}
    private GradientDrawable shape(int color,int radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(radius));return d;}
    private TextView label(String text,int size,int color){TextView v=new TextView(this);v.setText(text);v.setTextSize(size);v.setTextColor(color);return v;}
    private void pad(View v,int a,int b,int c,int d){v.setPadding(dp(a),dp(b),dp(c),dp(d));}
    private LinearLayout.LayoutParams lp(int w,int h){return new LinearLayout.LayoutParams(w<0?w:dp(w),h<0?h:dp(h));}
    private TextView action(String text){TextView v=label(text,14,accent);pad(v,12,10,12,10);v.setGravity(Gravity.CENTER);v.setBackground(shape(surface,14));return v;}

    @Override public void onCreate(Bundle saved){super.onCreate(saved);getWindow().setStatusBarColor(bg);getWindow().setNavigationBarColor(bg);
        if(!getPreferences(MODE_PRIVATE).contains("conversation_base"))getPreferences(MODE_PRIVATE).edit().putString("conversation_base",getPreferences(MODE_PRIVATE).getString("conversation","[]")).apply();
        selectedModel=getPreferences(MODE_PRIVATE).getString("selected_model_v022","tools");
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(bg);
        root.setOnApplyWindowInsetsListener((v,insets)->{v.setPadding(0,insets.getSystemWindowInsetTop(),0,insets.getSystemWindowInsetBottom());return insets;});setContentView(root);
        LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);pad(header,20,18,14,16);
        ImageView logo=new ImageView(this);logo.setImageResource(dev.liquidsense.chat.R.drawable.ic_launcher);header.addView(logo,lp(44,44));
        LinearLayout names=new LinearLayout(this);names.setOrientation(LinearLayout.VERTICAL);pad(names,10,0,0,0);TextView title=label("Liquid Sense",23,ink);title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);names.addView(title);names.addView(label("Chat · internet e Python · prévia 0.3",12,muted));header.addView(names,new LinearLayout.LayoutParams(0,-2,1));
        TextView about=action("Sobre");about.setOnClickListener(v->new AlertDialog.Builder(this).setTitle("Liquid Sense · modelos locais").setMessage("Liquid Sense é um projeto experimental independente baseado no Qwen3.5, com adaptações inspiradas em SenseNova Loop e Liquid AI.\n\nFerramentas: o modelo pode buscar na web e executar cálculos em Python3 limitado no aparelho (math/json, sem pacotes externos). Apenas os termos de busca são enviados ao buscador; o modelo e os cálculos ficam locais. Fontes e resultados aparecem na conversa.\n\nA Base geral acompanha este APK. A Especializada 015E pode ser aberta a partir do app especialista instalado. No motor Python original acertou 8/8 exemplos ensinados; na portabilidade Rust foram 7/8. Esses números não representam o HumanEval completo nem garantem generalização.\n\nOs pesos gerais ficam integrados, com os operadores híbridos preservados. Cada opção tem conversa separada. Confira os resultados: o modelo pode errar, inclusive ao escolher ferramentas.").setPositiveButton("Entendi",null).show());header.addView(about);root.addView(header);
        modelChoice=action(modelName());modelChoice.setOnClickListener(v->chooseModel());LinearLayout.LayoutParams modelLayout=lp(-1,-2);modelLayout.setMargins(dp(20),0,dp(20),dp(10));root.addView(modelChoice,modelLayout);
        LinearLayout tools=new LinearLayout(this);tools.setGravity(Gravity.CENTER_VERTICAL);pad(tools,20,0,20,10);TextView badge=label("●  MODELO NO APARELHO",10,Color.rgb(142,228,207));pad(badge,10,6,10,6);badge.setBackground(shape(Color.rgb(24,49,49),12));tools.addView(badge);TextView spacer=label("",12,muted);tools.addView(spacer,new LinearLayout.LayoutParams(0,1,1));TextView clear=label("Nova conversa",13,muted);pad(clear,12,8,0,8);clear.setOnClickListener(v->{if(busy)return;history=new JSONArray();saveHistory();timeline.removeAllViews();welcome();});tools.addView(clear);root.addView(tools);
        scroll=new ScrollView(this);scroll.setFillViewport(true);timeline=new LinearLayout(this);timeline.setOrientation(LinearLayout.VERTICAL);pad(timeline,16,12,16,16);scroll.addView(timeline,new ScrollView.LayoutParams(-1,-2));root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        status=label("Carregando o modelo local…",12,muted);pad(status,22,8,22,8);root.addView(status);
        LinearLayout input=new LinearLayout(this);input.setGravity(Gravity.BOTTOM);pad(input,16,4,16,10);composer=new EditText(this);composer.setTextColor(ink);composer.setHintTextColor(muted);composer.setTextSize(16);composer.setHint("Escreva uma mensagem…");composer.setMinLines(1);composer.setMaxLines(6);composer.setInputType(android.text.InputType.TYPE_CLASS_TEXT|android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE|android.text.InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);composer.setImeOptions(EditorInfo.IME_FLAG_NO_EXTRACT_UI);pad(composer,16,13,16,13);composer.setBackground(shape(surface,20));input.addView(composer,new LinearLayout.LayoutParams(0,-2,1));send=action("Enviar");pad(send,15,15,15,15);LinearLayout.LayoutParams sb=lp(-2,-2);sb.leftMargin=dp(8);input.addView(send,sb);send.setAlpha(.4f);send.setOnClickListener(v->{if(busy){cancelRequested=true;nativeCancel();status.setText("Interrompendo…");}else submit();});root.addView(input);
        TextView note=label("Experimental · confira informações e códigos importantes.",10,muted);note.setGravity(Gravity.CENTER);pad(note,16,0,16,10);root.addView(note);
        try{history=new JSONArray(getPreferences(MODE_PRIVATE).getString("conversation_"+selectedModel,"[]"));}catch(Exception ignored){history=new JSONArray();}
        if(history.length()==0)welcome();else restoreBubbles();
        loadSelectedModel();
    }
    private String modelName(){return "Trocar modelo · "+(selectedModel.equals("tools")?"Web e Python ▾":selectedModel.equals("specialist")?"Especializada 015E ▾":"1.0 Base geral ▾");}
    private void chooseModel(){
        if(busy||loading)return;
        new AlertDialog.Builder(this).setTitle("Escolha o modelo").setItems(new String[]{"Liquid Sense · Web e Python (experimental)","Especializada · Experimental 015E (offline)","1.0 Base · Geral (offline)"},(d,index)->{
            String next=index==0?"tools":index==1?"specialist":"base";if(next.equals(selectedModel))return;
            if(next.equals("specialist")){try{if(getPackageManager().getPackageInfo("dev.liquidsense.chat.fast",0).versionCode<3)throw new IOException("Atualize a Especializada");createPackageContext("dev.liquidsense.chat.fast",0);}catch(Exception missing){new AlertDialog.Builder(this).setTitle("Especializada 015E").setMessage("A Base geral já está integrada neste app. Para alternar para a Especializada, instale ou atualize o app especialista para a versão 0.2; ele tem os pesos 015E e sua conversa preservada.").setPositiveButton("Baixar a Especializada",(a,b)->startActivity(new Intent(Intent.ACTION_VIEW,android.net.Uri.parse("https://gofile.io/d/iNjQRGpN")))).setNegativeButton("Voltar",null).show();return;}}
            saveHistory();selectedModel=next;getPreferences(MODE_PRIVATE).edit().putString("selected_model_v022",next).apply();
            try{history=new JSONArray(getPreferences(MODE_PRIVATE).getString("conversation_"+next,"[]"));}catch(Exception ignored){history=new JSONArray();}
            timeline.removeAllViews();if(history.length()==0)welcome();else restoreBubbles();
            modelChoice.setText(modelName());loadSelectedModel();
        }).show();
    }
    private void loadSelectedModel(){
        ready=false;loading=true;send.setAlpha(.4f);modelChoice.setEnabled(false);status.setText("Carregando "+(selectedModel.equals("specialist")?"a Especializada experimental…":"a Base…"));
        final String chosen=selectedModel;
        worker.execute(()->{
            try{
                android.content.res.AssetManager assets=chosen.equals("specialist")?createPackageContext("dev.liquidsense.chat.fast",0).getAssets():getAssets();
                AssetFileDescriptor model=assets.openFd("model.lsp"),tokens=assets.openFd("tokenizer.json");
                long mo=model.getStartOffset(),ml=model.getLength(),to=tokens.getStartOffset(),tl=tokens.getLength();int mf=model.getParcelFileDescriptor().detachFd(),tf=tokens.getParcelFileDescriptor().detachFd();model.close();tokens.close();
                JSONObject identity=new JSONObject(readAsset("identity.json"));identity.put("selected_model",chosen).put("model_source",chosen.equals("specialist")?"specialist":"general");if(chosen.equals("tools"))identity.put("tools_prefix",readAsset("tools_prefix.txt"));
                String result=nativeLoad(mf,mo,ml,tf,to,tl,identity.toString());if(!"ok".equals(result))throw new IOException(error(result));
                JSONObject build=new JSONObject(readAsset("build_config.json"));if(chosen.equals("tools")&&build.optBoolean("use_validated_dense",false)){verifyDense(build.getString("dense_sha256"));AssetFileDescriptor dense=getAssets().openFd("down_proj.bf16.bin");long off=dense.getStartOffset(),len=dense.getLength();int fd=dense.getParcelFileDescriptor().detachFd();dense.close();String attached=nativeAttachDense(fd,off,len);if(!"ok".equals(attached))throw new IOException(error(attached));}
                main.post(()->{if(destroyed)return;loading=false;ready=true;modelChoice.setEnabled(true);send.setAlpha(1);status.setText(chosen.equals("tools")?"Pronto · busca na web e Python local":chosen.equals("specialist")?"Pronto · Especializada experimental · offline":"Pronto · Base geral · offline");});
            }catch(Throwable e){main.post(()->{if(destroyed)return;loading=false;modelChoice.setEnabled(true);status.setText("Falha ao abrir o modelo: "+friendly(e));});}
        });
    }

    private void welcome(){LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);pad(box,12,32,12,24);TextView title=label("Vamos testar uma ideia?",27,ink);title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);box.addView(title);TextView sub=label("Peça uma função, confira um cálculo ou busque uma fonte. O modelo responde no aparelho; na opção Web e Python ele pode usar ferramentas reais.",16,muted);pad(sub,0,14,0,24);box.addView(sub);for(String suggestion:new String[]{"Use Python para conferir a soma dos quadrados de 1 até 20.","Busque na web a documentação de listas em Python e cite a fonte."}){TextView chip=label(suggestion,14,ink);pad(chip,14,13,14,13);chip.setBackground(shape(surface,14));LinearLayout.LayoutParams p=lp(-1,-2);p.bottomMargin=dp(10);box.addView(chip,p);chip.setOnClickListener(v->{composer.setText(suggestion);composer.setSelection(composer.length());});}timeline.addView(box);}
    private TextView bubble(String text,boolean user){LinearLayout wrap=new LinearLayout(this);wrap.setOrientation(LinearLayout.VERTICAL);pad(wrap,user?28:0,0,user?0:12,12);TextView who=label(user?"VOCÊ":"LIQUID SENSE",10,user?accent:muted);pad(who,4,0,4,5);wrap.addView(who);TextView body=label(text,16,ink);body.setTextIsSelectable(true);body.setLineSpacing(dp(4),1);pad(body,16,14,16,14);body.setBackground(shape(user?Color.rgb(43,54,116):surface,18));if(text.contains("```"))body.setTypeface(Typeface.MONOSPACE);wrap.addView(body);timeline.addView(wrap);bottom();return body;}
    private void bottom(){scroll.post(()->{if(!destroyed)scroll.fullScroll(View.FOCUS_DOWN);});}
    private void submit(){if(!ready){status.setText("Aguarde o carregamento do modelo.");return;}String text=composer.getText().toString().trim();if(text.isEmpty())return;if(text.length()>16000){status.setText("Envie um trecho menor de texto.");return;}if(history.length()==0)timeline.removeAllViews();try{history.put(new JSONObject().put("role","user").put("content",text));}catch(Exception ignored){}bubble(text,true);composer.setText("");saveHistory();pending=bubble("Preparando sua mensagem…",false);pendingToolHistory=new JSONArray();busy=true;cancelRequested=false;latestMetrics="";nativeResetCancel();send.setText("Parar");status.setText("Lendo a conversa…");String payload=history.toString();
        worker.execute(()->{try{if(cancelRequested){finish("", "cancelled",null);return;}JSONObject data=selectedModel.equals("tools")?generateWithTools(payload):new JSONObject(nativeGenerate(payload,selectedModel.equals("specialist")?320:192));if(data.has("error")){finish("","error",data.optString("error"));return;}double prefill=data.optDouble("prefill_seconds",0),decode=data.optDouble("decode_seconds",0);int count=data.optInt("tokens",0),reused=data.optInt("reused_prompt_tokens",0);latestMetrics=String.format(java.util.Locale.ROOT," · %.1fs preparo · %.1f tokens/s%s",prefill,decode>0?count/decode:0,reused>0?" · histórico reutilizado":"");if(selectedModel.equals("tools"))latestMetrics+=" · "+data.optInt("actual_tool_calls",0)+" ferramenta(s)";finish(data.optString("text"),data.optString("finish_reason"),null);}catch(Throwable e){finish("","error",friendly(e));}});
    }
    public void onNativeText(String text,int done,int total){main.post(()->{if(destroyed||!busy)return;if(selectedModel.equals("tools")&&!text.isEmpty()){pending.setText("Analisando e conferindo…");status.setText("Gerando a próxima etapa no aparelho…");return;}if(text.isEmpty()){status.setText("Lendo contexto · "+done+"/"+total+" tokens");}else{pending.setText(text);if(text.contains("```"))pending.setTypeface(Typeface.MONOSPACE);status.setText("Gerando no aparelho…");bottom();}});}
    private void finish(String text,String reason,String failure){main.post(()->{if(destroyed)return;busy=false;send.setText("Enviar");for(int i=0;i<pendingToolHistory.length();i++)history.put(pendingToolHistory.optJSONObject(i));pendingToolHistory=new JSONArray();saveHistory();if(failure!=null){pending.setText("Não consegui concluir: "+failure);status.setText("Você pode tentar novamente com uma mensagem menor.");return;}pending.setText(text.isEmpty()?"Geração interrompida.":text);if(!text.isEmpty()){try{history.put(new JSONObject().put("role","assistant").put("content",text));}catch(Exception ignored){}saveHistory();}status.setText("cancelled".equals(reason)?"Interrompido por você.":("length".equals(reason)?"Limite da resposta atingido. Peça para continuar.":"Pronto · resposta gerada localmente")+latestMetrics);bottom();});}
    private JSONObject generateWithTools(String payload)throws Exception {
        JSONArray messages=new JSONArray(payload),trace=new JSONArray();double prefill=0,decode=0;int count=0,reused=0;
        for(int turn=0;turn<3;turn++){
            if(cancelRequested)return new JSONObject().put("text","").put("finish_reason","cancelled");
            JSONObject answer=new JSONObject(nativeGenerate(messages.toString(),256));if(answer.has("error"))return answer;
            prefill+=answer.optDouble("prefill_seconds",0);decode+=answer.optDouble("decode_seconds",0);count+=answer.optInt("tokens",0);reused+=answer.optInt("reused_prompt_tokens",0);
            String raw=answer.optString("raw_text",answer.optString("text"));JSONObject call;
            try{call=ToolExecutor.parse(raw);}catch(Exception e){return new JSONObject().put("error","O modelo não concluiu uma chamada válida. Tente uma pergunta menor.");}
            if(call==null){answer.put("actual_tool_calls",trace.length()).put("prefill_seconds",prefill).put("decode_seconds",decode).put("tokens",count).put("reused_prompt_tokens",reused);return answer;}
            if(turn==2)return new JSONObject().put("error","O modelo fez duas verificações e ainda não concluiu. Os resultados reais estão na conversa.");
            final String name=call.getString("name");JSONObject args=call.getJSONObject("arguments"),observation;
            main.post(()->{if(!destroyed){pending.setText(name.equals("search_web")?"Buscando fontes na internet…":"Executando e conferindo Python…");status.setText(name.equals("search_web")?"Consultando a web…":"Cálculo isolado no aparelho…");}});
            try{observation=name.equals("search_web")?ToolExecutor.search(args.getString("query")):PythonClient.run(this,args.getString("code"));}
            catch(Exception e){observation=new JSONObject().put("tool",name).put("ok",false).put("error",ToolExecutor.safe(e.toString(),500));}
            trace.put(new JSONObject().put("call",call).put("observation",observation));getPreferences(MODE_PRIVATE).edit().putString("tool_trace_last",trace.toString()).apply();
            final JSONObject shown=observation;main.post(()->showToolResult(shown));
            JSONObject assistant=new JSONObject().put("role","assistant").put("content",raw);JSONObject resultMessage=new JSONObject().put("role","tool").put("content",ToolExecutor.safe(observation.toString(),12000));messages.put(assistant);messages.put(resultMessage);pendingToolHistory.put(assistant);pendingToolHistory.put(resultMessage);
            JSONObject next=new JSONObject().put("role","user").put("internal",true).put("content","Confira a observação real acima e conclua o pedido original com uma resposta breve. Cite somente URLs retornadas se fez uma busca. Se os dados forem insuficientes, diga isso. Faça outra chamada apenas para corrigir um erro ou obter uma informação que falta; não repita uma chamada já bem-sucedida.");messages.put(next);pendingToolHistory.put(next);getPreferences(MODE_PRIVATE).edit().putString("conversation_tools",messages.toString()).apply();
        }throw new IllegalStateException("Limite de ferramentas");
    }
    private void showToolResult(JSONObject result){
        if(destroyed)return;StringBuilder text=new StringBuilder();boolean web=result.optString("tool").equals("search_web");text.append(web?"BUSCA NA WEB\n":"PYTHON · EXECUÇÃO LOCAL\n");
        if(!result.optBoolean("ok")){text.append("Não concluído: ").append(result.optString("error","Nenhum resultado retornado."));}
        else if(web){JSONArray items=result.optJSONArray("items");if(items!=null)for(int i=0;i<items.length();i++){JSONObject x=items.optJSONObject(i);if(x!=null)text.append("\n").append(x.optString("title")).append("\n").append(x.optString("url")).append("\n").append(x.optString("snippet")).append("\n");}}
        else{text.append(result.optString("stdout","(sem saída)"));}
        TextView card=bubble(text.toString().trim(),false);card.setTextSize(13);android.text.util.Linkify.addLinks(card,android.text.util.Linkify.WEB_URLS);card.setLinkTextColor(accent);bottom();
    }
    private void restoreBubbles(){
        for(int i=0;i<history.length();i++){
            JSONObject m=history.optJSONObject(i);if(m==null||m.optBoolean("internal",false))continue;String role=m.optString("role"),content=m.optString("content");
            if(role.equals("tool")){try{showToolResult(new JSONObject(content));}catch(Exception ignored){}continue;}
            if(role.equals("assistant")&&content.contains("<tool_call>"))continue;
            bubble(content,role.equals("user"));
        }
    }
    private void verifyDense(String expected)throws Exception {
        java.security.MessageDigest sha=java.security.MessageDigest.getInstance("SHA-256");
        try(InputStream in=getAssets().open("down_proj.bf16.bin")){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)sha.update(b,0,n);}
        StringBuilder hex=new StringBuilder();for(byte b:sha.digest())hex.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
        if(!hex.toString().equals(expected))throw new IOException("A edição de pesos não passou na verificação.");
    }
    private void saveHistory(){getPreferences(MODE_PRIVATE).edit().putString("conversation_"+selectedModel,history.toString()).apply();}
    private String readAsset(String name)throws IOException{try(InputStream in=getAssets().open(name);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return new String(out.toByteArray(),StandardCharsets.UTF_8);}}
    private String error(String result){try{return new JSONObject(result).optString("error",result);}catch(Exception e){return result;}}
    private String friendly(Throwable e){String s=e.getMessage();return s==null?e.getClass().getSimpleName():s;}
    @Override protected void onPause(){super.onPause();if(busy){cancelRequested=true;nativeCancel();}}
    @Override protected void onDestroy(){destroyed=true;if(busy)nativeCancel();worker.shutdown();super.onDestroy();}
}
