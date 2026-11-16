package dev.liquidsense.installcheck;
import android.app.*;import android.content.*;import android.net.Uri;import android.os.*;import java.io.*;import java.lang.reflect.*;
/** Separate CI-only instrumentation: never bundled in the user helper APK. */
public final class Smoke extends Instrumentation {
 @Override public void onCreate(Bundle b){super.onCreate(b);start();}
 void invoke(Activity a,String name,Class<?>[] types,Object...args)throws Exception{Method m=a.getClass().getDeclaredMethod(name,types);m.setAccessible(true);final Exception[] error={null};runOnMainSync(()->{try{m.invoke(a,args);}catch(Exception e){error[0]=e;}});if(error[0]!=null)throw error[0];}
 void waitWorker(Activity a)throws Exception{Field f=a.getClass().getDeclaredField("busy");f.setAccessible(true);long end=System.currentTimeMillis()+240000;while(f.getBoolean(a)){if(System.currentTimeMillis()>end)throw new IOException("production worker timeout");Thread.sleep(250);}waitForIdleSync();}
 @Override public void onStart(){Bundle result=new Bundle();try{
  Context target=getTargetContext();Activity a=startActivitySync(new Intent().setComponent(new ComponentName(target.getPackageName(),"dev.liquidsense.installcheck.MainActivity")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
  File fixture=new File(target.getCacheDir(),"smoke-input.zip");if(!fixture.isFile())throw new IOException("CI fixture missing");invoke(a,"inspect",new Class<?>[]{Uri.class},Uri.fromFile(fixture));waitWorker(a);String before=target.getSharedPreferences("diagnostic",0).getString("report","");
  if(!before.contains("Blocos diferentes: 1 / 235")||!before.contains("Download necessário: 8388608 bytes"))throw new IOException("expected exactly one corrupt block; "+before);
  result.putString("scan",before);invoke(a,"recover",new Class<?>[]{});waitWorker(a);String after=target.getSharedPreferences("diagnostic",0).getString("report","");if(!target.getSharedPreferences("diagnostic",0).getBoolean("valid036",false)||!after.contains("APK íntegro"))throw new IOException("recovery failed: "+after);
  result.putString("recovery",after);result.putString("claim","Production Android scan/HTTPS range repair/ZIP extraction/APK validation passed. File picker UI and physical phone installation not tested.");finish(Activity.RESULT_OK,result);
 }catch(Throwable e){result.putString("error",e.toString());finish(Activity.RESULT_CANCELED,result);}}
}
