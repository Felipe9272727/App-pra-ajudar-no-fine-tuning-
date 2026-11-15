package dev.liquidsense.chat;
import org.json.JSONObject;
/** Extract only the small model's actual generated thought, preserving code literals. */
public final class UiText {
    public static String thought(JSONObject answer) {
        if(!answer.optBoolean("thinking",false))return "";
        String raw=answer.optString("raw_text","");int end=raw.indexOf("</think>");
        if(end<0)return raw.startsWith("<think>")?raw.substring(7).trim():raw.trim();
        String thought=raw.substring(0,end);if(thought.startsWith("<think>"))thought=thought.substring(7);
        return thought.trim();
    }
}
