package dev.liquidsense.chat;
import org.json.*;
/** Last navigation intent wins; drain once only after generation/loading is idle. */
public final class NavigationQueue {
    private volatile JSONObject pending;
    public synchronized void defer(JSONObject request)throws JSONException {pending=new JSONObject(request.toString());}
    public boolean waiting(){return pending!=null;}
    public synchronized JSONObject takeIfIdle(boolean busy,boolean loading){if(busy||loading)return null;JSONObject value=pending;pending=null;return value;}
}
