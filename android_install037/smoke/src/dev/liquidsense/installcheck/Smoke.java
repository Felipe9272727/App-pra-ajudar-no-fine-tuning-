package dev.liquidsense.installcheck;
import android.app.*;import android.content.*;import android.content.pm.*;import android.os.*;import android.view.accessibility.*;import java.io.*;import java.lang.reflect.*;import java.util.*;
/** Separate CI-only instrumentation. Uses normal installer confirmation UI. */
public final class Smoke extends Instrumentation {
 String mode;@Override public void onCreate(Bundle b){mode=b==null?"full":b.getString("mode","full");super.onCreate(b);start();}
 void invoke(Activity a,String name)throws Exception {Method m=a.getClass().getDeclaredMethod(name);m.setAccessible(true);final Exception[] error={null};runOnMainSync(()->{try{m.invoke(a);}catch(Exception e){error[0]=e;}});if(error[0]!=null)throw error[0];}
 void waitWorker(Activity a)throws Exception{Field f=a.getClass().getDeclaredField("busy");f.setAccessible(true);long end=System.currentTimeMillis()+600000;while(f.getBoolean(a)){if(System.currentTimeMillis()>end)throw new IOException("worker timeout");Thread.sleep(250);}waitForIdleSync();}
 boolean confirm(AccessibilityNodeInfo node){if(node==null)return false;CharSequence t=node.getText(),p=node.getPackageName();String text=t==null?"":t.toString(),pkg=p==null?"":p.toString();
  if(pkg.contains("packageinstaller")&&(text.equals("Install")||text.equals("Update"))){AccessibilityNodeInfo target=node;for(int i=0;i<3&&target!=null;i++,target=target.getParent())if(target.isClickable()&&target.isEnabled())return target.performAction(AccessibilityNodeInfo.ACTION_CLICK);}
  for(int i=0;i<node.getChildCount();i++)if(confirm(node.getChild(i)))return true;return false;
 }
 @Override public void onStart(){Bundle result=new Bundle();try{
  Context context=getTargetContext();android.content.SharedPreferences prefs=context.getSharedPreferences("diagnostic",0);File apk=new File(context.getCacheDir(),"verified.apk");if(apk.length()!=1967560403L)throw new IOException("cached APK missing");
  if(mode.equals("old")){prefs.edit().putBoolean("valid036",true).putBoolean("install_pending",false).remove("confirmation").putString("report","CI037: reproduce old036 double-close with full cached APK\n").putString("preservation037","cached APK and helper data retained").commit();}
  else if(!"cached APK and helper data retained".equals(prefs.getString("preservation037",""))||!prefs.getBoolean("valid036",false))throw new IOException("helper data not preserved by update");
  Activity a=startActivitySync(new Intent().setComponent(new ComponentName(context.getPackageName(),"dev.liquidsense.installcheck.MainActivity")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));Field valid=a.getClass().getDeclaredField("apkValid");valid.setAccessible(true);if(!valid.getBoolean(a))throw new IOException("fresh activity did not load verified cached APK");if(!context.getPackageManager().canRequestPackageInstalls())throw new IOException("CI unknown-sources permission not granted");invoke(a,"startInstall");waitWorker(a);
  if(mode.equals("old")){long end=System.currentTimeMillis()+15000;String report="";do{report=prefs.getString("report","");if(report.contains("EBADF"))break;Thread.sleep(250);}while(System.currentTimeMillis()<end);if(!report.contains("EBADF"))throw new IOException("old error not reproduced: "+report);result.putString("old_report",report);result.putString("claim","old036 production Session path reproduced EBADF with full pinned APK");}
  else {
   long end=System.currentTimeMillis()+180000;boolean requestedConfirmation=false,clicked=false;
   while(System.currentTimeMillis()<end){if(prefs.contains("last_status037"))break;
    if(!requestedConfirmation&&prefs.contains("confirmation")){invoke(a,"startInstall");requestedConfirmation=true;Thread.sleep(1000);}
    AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();if(!clicked&&confirm(root)){clicked=true;result.putString("confirmation","Clicked Install/Update in normal Android packageinstaller UI");}
    Thread.sleep(500);
   }
   String report=prefs.getString("report","");result.putString("new_report",report);int status=prefs.getInt("last_status037",-999);
   if(status!=PackageInstaller.STATUS_SUCCESS)throw new IOException("actual installer status "+status+"; "+report);
   PackageInfo installed=context.getPackageManager().getPackageInfo("dev.liquidsense.chat.tools",0);if(installed.getLongVersionCode()!=7)throw new IOException("target version not installed");
   if(!report.contains("SHA256 dentro da sessão: 4735be854079941188e5f918e82d7c21d5468a437efe1bf7f45e72c15ade0e10"))throw new IOException("staged APK hash not verified");
   if(!apk.isFile()||!prefs.getBoolean("valid036",false))throw new IOException("cache/verified flag lost");
   result.putString("installed",installed.packageName+" "+installed.versionName+" / "+installed.getLongVersionCode());result.putString("claim","Old error reproduced, same cached APK and helper data preserved across update, production full Session write/fsync/single close/readback/commit, normal installer UI confirmation and final STATUS_SUCCESS passed. Physical Xiaomi result still pending.");
  }
  finish(Activity.RESULT_OK,result);
 }catch(Throwable e){result.putString("error",e.toString());finish(Activity.RESULT_CANCELED,result);}}
}
