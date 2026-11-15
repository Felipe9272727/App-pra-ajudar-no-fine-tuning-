package dev.liquidsense.installcheck;
import android.app.*;
import android.content.*;
import android.content.pm.*;
import android.net.Uri;
import android.os.*;
import android.provider.Settings;
import android.graphics.Color;
import android.widget.*;
import java.io.*;
import java.security.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.zip.*;

public final class MainActivity extends Activity {
 static final String TARGET="dev.liquidsense.chat.tools";
 static final String EXPECTED="4735be854079941188e5f918e82d7c21d5468a437efe1bf7f45e72c15ade0e10";
 static final String CERT="fcb504e5004b8e0be879b952d597248da3a731c481c1f24cd1ac01502df5ac5b";
 static final long BYTES=1967560403L;
 final ExecutorService worker=Executors.newSingleThreadExecutor();final Handler main=new Handler(Looper.getMainLooper());
 TextView report,status;Button choose,install;ProgressBar progress;boolean busy=false,valid=false,destroyed=false;
 File apk(){return new File(getCacheDir(),"verified.apk");}
 android.content.SharedPreferences prefs(){return getSharedPreferences("diagnostic",0);}
 @Override public void onCreate(Bundle saved){super.onCreate(saved);
  LinearLayout layout=new LinearLayout(this);layout.setOrientation(1);layout.setPadding(dp(20),dp(20),dp(20),dp(12));layout.setBackgroundColor(0xff18191b);layout.setFitsSystemWindows(true);setContentView(layout);
  TextView title=text("Liquid Sense · Verificador",23);layout.addView(title);
  layout.addView(text("Este app pequeno confere o APK já baixado e mostra o motivo detalhado do instalador. Não lê conversas e não tem acesso à internet.",14));
  choose=button("1. Escolher o APK 0.6.3 já baixado");choose.setOnClickListener(v->pick());layout.addView(choose);
  progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);progress.setMax(100);layout.addView(progress);status=text("Escolha o arquivo LiquidSense-0.6.3…apk em Downloads.",13);layout.addView(status);
  install=button("2. Tentar atualizar e capturar o erro");install.setEnabled(false);install.setOnClickListener(v->startInstall());layout.addView(install);
  Button copy=button("3. Copiar relatório");copy.setOnClickListener(v->{((android.content.ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("Diagnóstico Liquid Sense",prefs().getString("report","")));Toast.makeText(this,"Relatório copiado. Cole na conversa.",Toast.LENGTH_LONG).show();});layout.addView(copy);
  ScrollView scroll=new ScrollView(this);report=text("",12);report.setTypeface(android.graphics.Typeface.MONOSPACE);report.setTextIsSelectable(true);scroll.addView(report);layout.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
  valid=apk().isFile()&&prefs().getBoolean("valid",false)&&apk().length()==BYTES;install.setEnabled(valid);refresh();
 }
 int dp(int v){return (int)(v*getResources().getDisplayMetrics().density+.5f);}TextView text(String value,int size){TextView t=new TextView(this);t.setText(value);t.setTextColor(0xffeeeae5);t.setTextSize(size);t.setPadding(0,dp(8),0,dp(8));return t;}
 Button button(String s){Button b=new Button(this);b.setText(s);b.setAllCaps(false);return b;}
 void pick(){if(busy)return;Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(i,1);}
 @Override public void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request==1&&result==RESULT_OK&&data!=null&&data.getData()!=null)check(data.getData());}
 String environment(){return "Liquid Sense · diagnóstico 034\nAndroid: "+Build.VERSION.RELEASE+" / SDK "+Build.VERSION.SDK_INT+"\nAparelho: "+Build.MANUFACTURER+" "+Build.MODEL+"\nABIs: "+Arrays.toString(Build.SUPPORTED_ABIS)+"\n\n";}
 String certificate(PackageInfo p)throws Exception {if(p.signingInfo==null)return "indisponível";android.content.pm.Signature[] values=p.signingInfo.getApkContentsSigners();List<String> out=new ArrayList<>();for(android.content.pm.Signature s:values)out.add(hex(MessageDigest.getInstance("SHA-256").digest(s.toByteArray())));Collections.sort(out);return String.join(",",out);}
 void check(Uri uri){busy=true;valid=false;choose.setEnabled(false);install.setEnabled(false);prefs().edit().putBoolean("valid",false).putString("report",environment()+"Lendo arquivo e calculando SHA256…\n").apply();refresh();
  worker.execute(()->{StringBuilder out=new StringBuilder(environment());try{
   File temp=new File(getCacheDir(),"selected.copying");MessageDigest sha=MessageDigest.getInstance("SHA-256");long count=0,next=0;
   try(InputStream in=getContentResolver().openInputStream(uri);OutputStream dst=new FileOutputStream(temp)){if(in==null)throw new IOException("Não consegui ler o arquivo escolhido.");byte[] buf=new byte[1024*1024];int n;
    while((n=in.read(buf))!=-1){dst.write(buf,0,n);sha.update(buf,0,n);count+=n;if(count>=next){next=count+16*1024*1024;final long done=count;main.post(()->{if(!destroyed){progress.setProgress((int)Math.min(100,done*100/BYTES));status.setText("Conferindo "+(done/1048576)+" MiB…");}});}}
   }
   String hash=hex(sha.digest());out.append("ARQUIVO ESCOLHIDO\nBytes: ").append(count).append("\nSHA256: ").append(hash).append("\nCorresponde à 0.6.3 publicada: ").append(count==BYTES&&EXPECTED.equals(hash)).append("\n");
   PackageInfo installed=null;try{installed=getPackageManager().getPackageInfo(TARGET,PackageManager.GET_SIGNING_CERTIFICATES);out.append("\nAPP INSTALADO\nVersão: ").append(installed.versionName).append(" / ").append(installed.getLongVersionCode()).append("\nCertificado: ").append(certificate(installed)).append("\nÉ o certificado publicado: ").append(CERT.equals(certificate(installed))).append("\n");}catch(PackageManager.NameNotFoundException e){out.append("\nApp principal não encontrado pelo gerenciador.\n");}
   PackageInfo incoming=getPackageManager().getPackageArchiveInfo(temp.getAbsolutePath(),PackageManager.GET_SIGNING_CERTIFICATES);
   if(incoming==null)out.append("\nO parser deste Android não reconheceu o APK.\n");else{
    out.append("\nAPK SEGUNDO O ANDROID\nPacote: ").append(incoming.packageName).append("\nVersão: ").append(incoming.versionName).append(" / ").append(incoming.getLongVersionCode()).append("\nCertificado: ").append(certificate(incoming)).append("\n");
    if(installed!=null)out.append("Assinaturas iguais: ").append(certificate(installed).equals(certificate(incoming))).append("\nÉ downgrade: ").append(incoming.getLongVersionCode()<installed.getLongVersionCode()).append("\n");
   }
   valid=count==BYTES&&EXPECTED.equals(hash)&&(incoming==null||TARGET.equals(incoming.packageName));
   if(valid){if(apk().exists()&&!apk().delete())throw new IOException("Não consegui remover a cópia temporária anterior.");if(!temp.renameTo(apk()))throw new IOException("Não consegui finalizar a cópia verificada.");out.append("\nArquivo íntegro. Toque no botão 2 para obter o código real da instalação. A confirmação é do próprio Android.\n");}
   else {temp.delete();out.append("\nEscolha o APK 0.6.3 correto. Nenhuma instalação foi iniciada.\n");}
  }catch(Exception e){valid=false;out.append("\nErro no diagnóstico: ").append(e).append("\n");}
   prefs().edit().putString("report",out.toString()).putBoolean("valid",valid).apply();main.post(()->{busy=false;if(!destroyed){choose.setEnabled(true);install.setEnabled(valid);progress.setProgress(valid?100:0);status.setText(valid?"Arquivo conferido. Pronto para o botão 2.":"Veja o relatório abaixo.");refresh();}});
  });
 }
 void startInstall(){String pending=prefs().getString("confirmation","");if(!pending.isEmpty()){try{startActivity(Intent.parseUri(pending,Intent.URI_INTENT_SCHEME));}catch(Exception e){InstallResult.save(this,"\nFalha ao reabrir confirmação: "+e+"\n");refresh();}return;}if(!valid||busy||!apk().isFile())return;if(!getPackageManager().canRequestPackageInstalls()){new AlertDialog.Builder(this).setMessage("Para o botão 2 funcionar, permita instalações deste verificador na próxima tela. Depois volte e toque no botão 2 novamente.").setPositiveButton("Abrir permissão",(d,w)->startActivity(new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,Uri.parse("package:"+getPackageName())))).setNegativeButton("Voltar",null).show();return;}
  busy=true;choose.setEnabled(false);install.setEnabled(false);status.setText("Entregando o APK verificado ao instalador Android…");
  worker.execute(()->{int id=-1;try{
   PackageInstaller installer=getPackageManager().getPackageInstaller();PackageInstaller.SessionParams params=new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);params.setAppPackageName(TARGET);params.setSize(apk().length());if(Build.VERSION.SDK_INT>=31)params.setRequireUserAction(PackageInstaller.SessionParams.USER_ACTION_REQUIRED);
   id=installer.createSession(params);try(PackageInstaller.Session session=installer.openSession(id);InputStream in=new FileInputStream(apk());OutputStream target=session.openWrite("base.apk",0,apk().length())){byte[] buf=new byte[1024*1024];int n;while((n=in.read(buf))!=-1)target.write(buf,0,n);session.fsync(target);target.close();
    Intent result=new Intent(this,InstallResult.class).setAction("dev.liquidsense.installcheck.RESULT");PendingIntent receiver=PendingIntent.getBroadcast(this,id,result,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_MUTABLE);prefs().edit().putBoolean("install_pending",true).apply();session.commit(receiver.getIntentSender());}
  }catch(Exception e){if(id>=0)try{getPackageManager().getPackageInstaller().abandonSession(id);}catch(Exception ignored){}InstallResult.save(this,"\nFalha ao criar/entregar a sessão: "+e+"\n");}
   main.post(()->{busy=false;if(!destroyed){choose.setEnabled(true);install.setEnabled(valid);status.setText("Confira a confirmação do Android e depois copie o relatório.");refresh();}});
  });
 }
 static String hex(byte[] data){StringBuilder out=new StringBuilder();for(byte b:data)out.append(String.format(java.util.Locale.ROOT,"%02x",b&255));return out.toString();}
 void refresh(){if(report!=null)report.setText(prefs().getString("report",environment()));if(install!=null)install.setText(prefs().contains("confirmation")?"2. Confirmar instalação no Android":"2. Tentar atualizar e capturar o erro");}
 @Override protected void onResume(){super.onResume();refresh();}
 @Override protected void onNewIntent(Intent i){super.onNewIntent(i);refresh();}
 @Override protected void onDestroy(){destroyed=true;worker.shutdown();super.onDestroy();}
}
