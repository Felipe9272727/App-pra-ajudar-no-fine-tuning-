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
    private native String nativeGenerate(String messages,int budget);
    private native void nativeCancel();
    private native void nativeResetCancel();
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final Handler main=new Handler(Looper.getMainLooper());
    private JSONArray history=new JSONArray();
    private LinearLayout timeline;
    private ScrollView scroll;
    private EditText composer;
    private TextView status,send,pending,modelChoice;
    private String selectedModel="specialist";
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
        selectedModel=getPreferences(MODE_PRIVATE).getString("selected_model_v021","specialist");
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(bg);
        root.setOnApplyWindowInsetsListener((v,insets)->{v.setPadding(0,insets.getSystemWindowInsetTop(),0,insets.getSystemWindowInsetBottom());return insets;});setContentView(root);
        LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);pad(header,20,18,14,16);
        ImageView logo=new ImageView(this);logo.setImageResource(dev.liquidsense.chat.R.drawable.ic_launcher);header.addView(logo,lp(44,44));
        LinearLayout names=new LinearLayout(this);names.setOrientation(LinearLayout.VERTICAL);pad(names,10,0,0,0);TextView title=label("Liquid Sense",23,ink);title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);names.addView(title);names.addView(label("Modelos locais · prévia 0.2",12,muted));header.addView(names,new LinearLayout.LayoutParams(0,-2,1));
        TextView about=action("Sobre");about.setOnClickListener(v->new AlertDialog.Builder(this).setTitle("Liquid Sense · modelos locais").setMessage("Chat local e experimental.\n\nProjeto independente de um desenvolvedor, baseado no Qwen3.5, com adaptações inspiradas em SenseNova Loop e Liquid AI.\n\nA Especializada experimental 015E acompanha este APK e é a opção padrão. Resolveu 8/8 exemplos de programação ensinados, 0/8 diferentes e 6/12 controles gerais. Isso não é uma pontuação no HumanEval completo.\n\nA opção 1.0 Base usa os pesos do app geral original, se instalado. Cada modelo tem conversa separada. Nenhuma mensagem é enviada à internet.\n\nMotor de inferência em Rust; interface nativa Android. Pode errar e a velocidade depende do aparelho.").setPositiveButton("Entendi",null).show());header.addView(about);root.addView(header);
        modelChoice=action(modelName());modelChoice.setOnClickListener(v->chooseModel());LinearLayout.LayoutParams modelLayout=lp(-1,-2);modelLayout.setMargins(dp(20),0,dp(20),dp(10));root.addView(modelChoice,modelLayout);
        LinearLayout tools=new LinearLayout(this);tools.setGravity(Gravity.CENTER_VERTICAL);pad(tools,20,0,20,10);TextView badge=label("●  NO APARELHO",10,Color.rgb(142,228,207));pad(badge,10,6,10,6);badge.setBackground(shape(Color.rgb(24,49,49),12));tools.addView(badge);TextView spacer=label("",12,muted);tools.addView(spacer,new LinearLayout.LayoutParams(0,1,1));TextView clear=label("Nova conversa",13,muted);pad(clear,12,8,0,8);clear.setOnClickListener(v->{if(busy)return;history=new JSONArray();saveHistory();timeline.removeAllViews();welcome();});tools.addView(clear);root.addView(tools);
        scroll=new ScrollView(this);scroll.setFillViewport(true);timeline=new LinearLayout(this);timeline.setOrientation(LinearLayout.VERTICAL);pad(timeline,16,12,16,16);scroll.addView(timeline,new ScrollView.LayoutParams(-1,-2));root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        status=label("Carregando o modelo local…",12,muted);pad(status,22,8,22,8);root.addView(status);
        LinearLayout input=new LinearLayout(this);input.setGravity(Gravity.BOTTOM);pad(input,16,4,16,10);composer=new EditText(this);composer.setTextColor(ink);composer.setHintTextColor(muted);composer.setTextSize(16);composer.setHint("Escreva uma mensagem…");composer.setMinLines(1);composer.setMaxLines(6);composer.setInputType(android.text.InputType.TYPE_CLASS_TEXT|android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE|android.text.InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);composer.setImeOptions(EditorInfo.IME_FLAG_NO_EXTRACT_UI);pad(composer,16,13,16,13);composer.setBackground(shape(surface,20));input.addView(composer,new LinearLayout.LayoutParams(0,-2,1));send=action("Enviar");pad(send,15,15,15,15);LinearLayout.LayoutParams sb=lp(-2,-2);sb.leftMargin=dp(8);input.addView(send,sb);send.setAlpha(.4f);send.setOnClickListener(v->{if(busy){cancelRequested=true;nativeCancel();status.setText("Interrompendo…");}else submit();});root.addView(input);
        TextView note=label("Experimental · confira informações e códigos importantes.",10,muted);note.setGravity(Gravity.CENTER);pad(note,16,0,16,10);root.addView(note);
        try{history=new JSONArray(getPreferences(MODE_PRIVATE).getString("conversation_"+selectedModel,"[]"));}catch(Exception ignored){history=new JSONArray();}
        if(history.length()==0)welcome();else for(int i=0;i<history.length();i++){JSONObject m=history.optJSONObject(i);if(m!=null)bubble(m.optString("content"),m.optString("role").equals("user"));}
        loadSelectedModel();
    }
    private String modelName(){return selectedModel.equals("specialist")?"Especializada · Experimental 015E ▾":"1.0 Base · Geral ▾";}
    private void chooseModel(){
        if(busy||loading)return;
        new AlertDialog.Builder(this).setTitle("Escolha o modelo").setItems(new String[]{"Especializada · Experimental 015E","1.0 Base · Geral"},(d,index)->{
            String next=index==0?"specialist":"base";if(next.equals(selectedModel))return;
            if(next.equals("base")){try{createPackageContext("dev.liquidsense.chat",0);}catch(Exception missing){new AlertDialog.Builder(this).setTitle("Modelo Base").setMessage("Para usar a Base sem duplicar os pesos, mantenha instalado o app geral original Liquid Sense. A Especializada já está integrada neste APK.").setPositiveButton("Baixar o app geral",(a,b)->startActivity(new Intent(Intent.ACTION_VIEW,android.net.Uri.parse("https://gofile.io/d/A79W3fzk")))).setNegativeButton("Voltar",null).show();return;}}
            saveHistory();selectedModel=next;getPreferences(MODE_PRIVATE).edit().putString("selected_model_v021",next).apply();
            try{history=new JSONArray(getPreferences(MODE_PRIVATE).getString("conversation_"+next,"[]"));}catch(Exception ignored){history=new JSONArray();}
            timeline.removeAllViews();if(history.length()==0)welcome();else for(int i=0;i<history.length();i++){JSONObject m=history.optJSONObject(i);if(m!=null)bubble(m.optString("content"),m.optString("role").equals("user"));}
            modelChoice.setText(modelName());loadSelectedModel();
        }).show();
    }
    private void loadSelectedModel(){
        ready=false;loading=true;send.setAlpha(.4f);modelChoice.setEnabled(false);status.setText("Carregando "+(selectedModel.equals("specialist")?"a Especializada experimental…":"a Base…"));
        final String chosen=selectedModel;
        worker.execute(()->{
            try{
                android.content.res.AssetManager assets=chosen.equals("base")?createPackageContext("dev.liquidsense.chat",0).getAssets():getAssets();
                AssetFileDescriptor model=assets.openFd("model.lsp"),tokens=assets.openFd("tokenizer.json");
                long mo=model.getStartOffset(),ml=model.getLength(),to=tokens.getStartOffset(),tl=tokens.getLength();int mf=model.getParcelFileDescriptor().detachFd(),tf=tokens.getParcelFileDescriptor().detachFd();model.close();tokens.close();
                JSONObject identity=new JSONObject(readAsset("identity.json"));identity.put("selected_model",chosen);
                String result=nativeLoad(mf,mo,ml,tf,to,tl,identity.toString());if(!"ok".equals(result))throw new IOException(error(result));
                main.post(()->{if(destroyed)return;loading=false;ready=true;modelChoice.setEnabled(true);send.setAlpha(1);status.setText(chosen.equals("specialist")?"Pronto · Especializada experimental · offline":"Pronto · Base geral · offline");});
            }catch(Throwable e){main.post(()->{if(destroyed)return;loading=false;modelChoice.setEnabled(true);status.setText("Falha ao abrir o modelo: "+friendly(e));});}
        });
    }

    private void welcome(){LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);pad(box,12,32,12,24);TextView title=label("Vamos testar uma ideia?",27,ink);title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);box.addView(title);TextView sub=label("Converse, peça uma função ou cole um trecho de código. As respostas são geradas aqui no seu celular.",16,muted);pad(sub,0,14,0,24);box.addView(sub);for(String suggestion:new String[]{"Escreva uma função Python para inverter uma lista.","Explique como encontrar um erro em um programa."}){TextView chip=label(suggestion,14,ink);pad(chip,14,13,14,13);chip.setBackground(shape(surface,14));LinearLayout.LayoutParams p=lp(-1,-2);p.bottomMargin=dp(10);box.addView(chip,p);chip.setOnClickListener(v->{composer.setText(suggestion);composer.setSelection(composer.length());});}timeline.addView(box);}
    private TextView bubble(String text,boolean user){LinearLayout wrap=new LinearLayout(this);wrap.setOrientation(LinearLayout.VERTICAL);pad(wrap,user?28:0,0,user?0:12,12);TextView who=label(user?"VOCÊ":"LIQUID SENSE",10,user?accent:muted);pad(who,4,0,4,5);wrap.addView(who);TextView body=label(text,16,ink);body.setTextIsSelectable(true);body.setLineSpacing(dp(4),1);pad(body,16,14,16,14);body.setBackground(shape(user?Color.rgb(43,54,116):surface,18));if(text.contains("```"))body.setTypeface(Typeface.MONOSPACE);wrap.addView(body);timeline.addView(wrap);bottom();return body;}
    private void bottom(){scroll.post(()->{if(!destroyed)scroll.fullScroll(View.FOCUS_DOWN);});}
    private void submit(){if(!ready){status.setText("Aguarde o carregamento do modelo.");return;}String text=composer.getText().toString().trim();if(text.isEmpty())return;if(text.length()>16000){status.setText("Envie um trecho menor de texto.");return;}if(history.length()==0)timeline.removeAllViews();try{history.put(new JSONObject().put("role","user").put("content",text));}catch(Exception ignored){}bubble(text,true);composer.setText("");saveHistory();pending=bubble("Preparando sua mensagem…",false);busy=true;cancelRequested=false;latestMetrics="";nativeResetCancel();send.setText("Parar");status.setText("Lendo a conversa…");String payload=history.toString();
        worker.execute(()->{try{if(cancelRequested){finish("", "cancelled",null);return;}String result=nativeGenerate(payload,selectedModel.equals("specialist")?320:192);JSONObject data=new JSONObject(result);if(data.has("error")){finish("","error",data.optString("error"));return;}double prefill=data.optDouble("prefill_seconds",0),decode=data.optDouble("decode_seconds",0);int count=data.optInt("tokens",0),reused=data.optInt("reused_prompt_tokens",0);latestMetrics=String.format(java.util.Locale.ROOT," · %.1fs preparo · %.1f tokens/s%s",prefill,decode>0?count/decode:0,reused>0?" · histórico reutilizado":"");finish(data.optString("text"),data.optString("finish_reason"),null);}catch(Throwable e){finish("","error",friendly(e));}});
    }
    public void onNativeText(String text,int done,int total){main.post(()->{if(destroyed||!busy)return;if(text.isEmpty()){status.setText("Lendo contexto · "+done+"/"+total+" tokens");}else{pending.setText(text);if(text.contains("```"))pending.setTypeface(Typeface.MONOSPACE);status.setText("Gerando no aparelho…");bottom();}});}
    private void finish(String text,String reason,String failure){main.post(()->{if(destroyed)return;busy=false;send.setText("Enviar");if(failure!=null){pending.setText("Não consegui concluir: "+failure);status.setText("Você pode tentar novamente com uma mensagem menor.");return;}pending.setText(text.isEmpty()?"Geração interrompida.":text);if(!text.isEmpty()){try{history.put(new JSONObject().put("role","assistant").put("content",text));}catch(Exception ignored){}saveHistory();}status.setText("cancelled".equals(reason)?"Interrompido por você.":("length".equals(reason)?"Limite da resposta atingido. Peça para continuar.":"Pronto · resposta gerada localmente")+latestMetrics);bottom();});}
    private void saveHistory(){getPreferences(MODE_PRIVATE).edit().putString("conversation_"+selectedModel,history.toString()).apply();}
    private String readAsset(String name)throws IOException{try(InputStream in=getAssets().open(name);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return new String(out.toByteArray(),StandardCharsets.UTF_8);}}
    private String error(String result){try{return new JSONObject(result).optString("error",result);}catch(Exception e){return result;}}
    private String friendly(Throwable e){String s=e.getMessage();return s==null?e.getClass().getSimpleName():s;}
    @Override protected void onPause(){super.onPause();if(busy){cancelRequested=true;nativeCancel();}}
    @Override protected void onDestroy(){destroyed=true;if(busy)nativeCancel();worker.shutdown();super.onDestroy();}
}
