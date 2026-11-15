package dev.liquidsense.chat;
import org.json.*;
import java.util.*;
/** Shared production history operations, independently executable without Android. */
public final class ConversationBook {
    public static JSONObject record(String id,String model,JSONArray messages,long updated)throws JSONException {
        String title="Nova conversa";
        for(int i=0;i<messages.length();i++){JSONObject m=messages.optJSONObject(i);if(m!=null&&m.optString("role").equals("user")&&!m.optBoolean("internal")){title=m.optString("content").replace('\n',' ').trim();if(title.length()>58)title=title.substring(0,58)+"…";break;}}
        return new JSONObject().put("id",id).put("model",model).put("title",title).put("updated",updated).put("messages",new JSONArray(messages.toString()));
    }
    public static void upsert(JSONArray threads,JSONObject record)throws JSONException {
        for(int i=0;i<threads.length();i++)if(threads.getJSONObject(i).optString("id").equals(record.getString("id"))){threads.put(i,record);return;}
        threads.put(record); // Empty new conversations must also be visible/persistent.
    }
    public static JSONArray list(JSONArray threads)throws JSONException {
        List<JSONObject> rows=new ArrayList<>();for(int i=0;i<threads.length();i++){JSONObject t=threads.getJSONObject(i);rows.add(new JSONObject().put("id",t.getString("id")).put("title",t.optString("title")).put("model",t.getString("model")).put("updated",t.optLong("updated")));}
        Collections.sort(rows,(a,b)->Long.compare(b.optLong("updated"),a.optLong("updated")));return new JSONArray(rows);
    }
}
