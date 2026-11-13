package dev.liquidsense.chat;
import org.json.JSONObject;
public final class InferenceSettings {
    public static JSONObject options(String mode)throws Exception {
        int think=0,response=2048;
        if(mode.equals("profundo"))think=1024;
        else if(mode.equals("extenso")){think=2048;response=4096;}
        return new JSONObject().put("thinking",think>0).put("reasoning_tokens",think).put("response_tokens",response).put("context_tokens",16384).put("profile",mode);
    }
    public static String title(String mode){return mode.equals("extenso")?"Extenso experimental · pensar 2048 + responder 4096":mode.equals("profundo")?"Profundo experimental · pensar 1024 + responder 2048":"Normal · responder até 2048";}
}
