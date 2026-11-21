package dev.liquidsense.chat;

import android.app.Activity;
import android.graphics.Rect;
import android.os.Build;
import android.view.*;
import android.webkit.WebView;
import android.widget.FrameLayout;
import java.util.List;

/** The WebView is actually remeasured above the IME, including edge-to-edge Android. */
public final class KeyboardLayout {
    public interface Listener {void changed(int cssHeight,boolean keyboard);}
    public static FrameLayout mount(Activity activity,WebView web,Listener listener){
        FrameLayout root=new FrameLayout(activity);root.setBackgroundColor(0xff18191b);
        root.addView(web,new FrameLayout.LayoutParams(-1,-1));
        final boolean[] keyboard={false};final int[] last={-1,-1};
        Runnable report=()->{int height=Math.round(web.getHeight()/activity.getResources().getDisplayMetrics().density);int active=keyboard[0]?1:0;if(height>0&&(last[0]!=height||last[1]!=active)){last[0]=height;last[1]=active;listener.changed(height,keyboard[0]);}};
        web.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->report.run());
        if(Build.VERSION.SDK_INT>=30)Api30.install(activity,root,web,keyboard,report);
        else {
            activity.getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
            root.getViewTreeObserver().addOnGlobalLayoutListener(()->{
                Rect visible=new Rect();root.getWindowVisibleDisplayFrame(visible);int[] position=new int[2];root.getLocationOnScreen(position);
                int available=Math.max(1,Math.min(root.getHeight(),visible.bottom-position[1]));
                FrameLayout.LayoutParams p=(FrameLayout.LayoutParams)web.getLayoutParams();if(p.height!=available){p.height=available;web.setLayoutParams(p);}
                keyboard[0]=root.getRootView().getHeight()-visible.bottom>100*activity.getResources().getDisplayMetrics().density;report.run();
            });
        }
        return root;
    }
    private static final class Api30 {
        static void install(Activity activity,FrameLayout root,WebView web,boolean[] keyboard,Runnable report){
            activity.getWindow().setDecorFitsSystemWindows(false);
            activity.getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_NOTHING);
            java.util.function.Consumer<WindowInsets> apply=insets->{
                android.graphics.Insets bars=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());
                android.graphics.Insets ime=insets.getInsets(WindowInsets.Type.ime());
                keyboard[0]=insets.isVisible(WindowInsets.Type.ime());int bottom=Math.max(bars.bottom,ime.bottom);
                if(root.getPaddingLeft()!=bars.left||root.getPaddingTop()!=bars.top||root.getPaddingRight()!=bars.right||root.getPaddingBottom()!=bottom)root.setPadding(bars.left,bars.top,bars.right,bottom);
                web.post(report);
            };
            root.setOnApplyWindowInsetsListener((v,insets)->{apply.accept(insets);return WindowInsets.CONSUMED;});
            root.setWindowInsetsAnimationCallback(new WindowInsetsAnimation.Callback(WindowInsetsAnimation.Callback.DISPATCH_MODE_CONTINUE_ON_SUBTREE){
                @Override public WindowInsets onProgress(WindowInsets insets,List<WindowInsetsAnimation> animations){apply.accept(insets);return insets;}
            });
            root.addOnAttachStateChangeListener(new View.OnAttachStateChangeListener(){public void onViewAttachedToWindow(View v){v.requestApplyInsets();}public void onViewDetachedFromWindow(View v){}});
        }
    }
}
