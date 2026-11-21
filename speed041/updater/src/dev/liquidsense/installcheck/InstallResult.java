package dev.liquidsense.installcheck;
import android.content.*;
import android.content.pm.PackageInstaller;
/** Capture the real installer result; no signature or system verification bypass. */
public final class InstallResult extends BroadcastReceiver {
 @Override public void onReceive(Context context,Intent intent){
  int incoming=intent.getIntExtra("session041",-1);android.content.SharedPreferences state=context.getSharedPreferences("diagnostic",0);if(incoming<0||incoming!=state.getInt("session041",-2))return;
  int status=intent.getIntExtra(PackageInstaller.EXTRA_STATUS,PackageInstaller.STATUS_FAILURE);
  if(status==PackageInstaller.STATUS_PENDING_USER_ACTION){
   Intent confirmation=intent.getParcelableExtra(Intent.EXTRA_INTENT);
   if(confirmation!=null)try{context.getSharedPreferences("diagnostic",0).edit().putString("confirmation041",confirmation.toUri(Intent.URI_INTENT_SCHEME)).apply();context.startActivity(confirmation.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));}catch(Exception e){save(context,"Não consegui abrir a confirmação: "+e+"\n");}
   return;
  }
  state.edit().putInt("last_status041",status).apply();
  String message=intent.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE);int legacy=intent.getIntExtra("android.content.pm.extra.LEGACY_STATUS",Integer.MIN_VALUE);
  String line="\nRESULTADO REAL DO INSTALADOR 041\nStatus: "+status+"\nCódigo legado: "+legacy+"\nMensagem: "+message+"\n";
  if(status==PackageInstaller.STATUS_SUCCESS)line+="Atualização concluída. O Android preserva os dados do app atualizado.\n";
  save(context,line);
  Intent show=new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_SINGLE_TOP);
  try{context.startActivity(show);}catch(Exception ignored){}
 }
 static void save(Context c,String line){android.content.SharedPreferences p=c.getSharedPreferences("diagnostic",0);p.edit().putString("report041",p.getString("report041","")+line).putBoolean("pending041",false).remove("confirmation041").apply();}
}
