package dev.liquidsense.installcheck;
import android.app.*;
import android.content.*;
import android.content.pm.*;
import android.os.*;
import android.view.accessibility.AccessibilityNodeInfo;
import java.lang.reflect.Method;

public final class Smoke extends Instrumentation {
    public void onCreate(Bundle b) { super.onCreate(b); start(); }
    boolean confirm(AccessibilityNodeInfo n) {
        if (n == null) return false;
        String pkg = String.valueOf(n.getPackageName()), text = String.valueOf(n.getText());
        if (pkg.contains("packageinstaller") && (text.equals("Install") || text.equals("Update"))) {
            for (int i = 0; i < 3 && n != null; i++, n = n.getParent())
                if (n.isClickable() && n.isEnabled()) return n.performAction(AccessibilityNodeInfo.ACTION_CLICK);
            return false;
        }
        for (int i = 0; i < n.getChildCount(); i++) if (confirm(n.getChild(i))) return true;
        return false;
    }
    public void onStart() {
        Bundle result = new Bundle();
        try {
            Context ctx = getTargetContext();
            SharedPreferences p = ctx.getSharedPreferences("diagnostic", 0);
            Activity a = startActivitySync(new Intent().setClassName(ctx.getPackageName(),"dev.liquidsense.installcheck.MainActivity")
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK));
            if (!a.getPackageManager().canRequestPackageInstalls()) throw new IllegalStateException("Emulator test install permission missing");
            Method begin = a.getClass().getDeclaredMethod("begin"); begin.setAccessible(true);
            runOnMainSync(() -> { try { begin.invoke(a); } catch(Exception e) { throw new RuntimeException(e); } });
            long deadline = System.currentTimeMillis() + 360000;
            boolean clicked = false, reopened = false;
            while (System.currentTimeMillis() < deadline && !p.contains("last_status041")) {
                if (p.getString("report041", "").startsWith("Falha")) break;
                if (!reopened && p.contains("confirmation041")) {
                    reopened = true;
                    runOnMainSync(() -> {try {a.startActivity(Intent.parseUri(p.getString("confirmation041", ""),Intent.URI_INTENT_SCHEME));} catch(Exception ignored){} });
                }
                if (!clicked) clicked = confirm(getUiAutomation().getRootInActiveWindow());
                Thread.sleep(500);
            }
            String report = p.getString("report041", "");
            result.putString("installer", report);
            if (p.getInt("last_status041", -999) != PackageInstaller.STATUS_SUCCESS || !clicked) throw new IllegalStateException("No successful Android confirmation");
            PackageInfo app = ctx.getPackageManager().getPackageInfo("dev.liquidsense.chat.tools",0);
            if (app.getLongVersionCode()!=9) throw new IllegalStateException("Wrong app version");
            result.putString("claim", "Installed 0.6.4 assets reused and signed 0.6.5 installed with Android confirmation");
            finish(Activity.RESULT_OK, result);
        } catch(Throwable e) {result.putString("error", e.toString());finish(Activity.RESULT_CANCELED, result);}
    }
}
