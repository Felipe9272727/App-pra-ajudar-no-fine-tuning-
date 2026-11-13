package dev.liquidsense.chat;

import org.json.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.regex.*;

/** Actual HTTPS search. Generated Python is handled by the isolated service. */
public final class ToolExecutor {
    private static final Pattern CALL=Pattern.compile("\\s*<function=(search_web|run_python)>\\s*<parameter=(query|code)>\\s*([\\s\\S]*?)\\s*</parameter>\\s*</function>\\s*");
    public static final class CallError extends IOException {
        public final String code;
        CallError(String code,String message){super(message);this.code=code;}
    }
    public static String content(String raw){
        String s=raw.trim();int close=s.indexOf("</think>"),call=s.indexOf("<tool_call>");
        if(close>=0&&(s.startsWith("<think>")||call<0||close<call)&&!s.startsWith("{"))s=s.substring(close+8).trim();
        boolean changed=true;while(changed){changed=false;for(String stop:new String[]{"<|im_end|>","<|endoftext|>","<|fim_suffix|>"})if(s.endsWith(stop)){s=s.substring(0,s.length()-stop.length()).trim();changed=true;}}
        return s;
    }
    public static JSONObject parse(String raw)throws Exception {return parse(raw,false);}
    public static JSONObject parse(String raw,boolean unfinishedThinking)throws Exception {
        if(unfinishedThinking||(raw.trim().startsWith("<think>")&&!raw.contains("</think>")))throw new CallError("REASONING_INCOMPLETE","O raciocínio ainda não terminou.");
        String s=content(raw);int start=s.indexOf("<tool_call>");String payload;
        if(start>=0){
            int end=s.lastIndexOf("</tool_call>");if(end<start)throw new CallError("CALL_INCOMPLETE","A geração parou antes de completar a chamada.");
            if(!s.substring(end+12).trim().isEmpty())throw new CallError("CALL_SUFFIX","O modelo acrescentou texto depois da chamada.");
            payload=s.substring(start+11,end).trim();
            if(Pattern.compile("</tool_call>\\s*<tool_call>").matcher(payload).find())throw new CallError("MULTIPLE_CALLS","O modelo emitiu mais de uma chamada no mesmo turno.");
        }else{
            payload=s;if(payload.startsWith("```json")&&payload.endsWith("```"))payload=payload.substring(7,payload.length()-3).trim();
            if(!payload.startsWith("{"))return null;
            try{JSONObject candidate=new JSONObject(payload);JSONObject f=candidate.optJSONObject("function");if(f==null)f=candidate;if(!f.has("name")||!f.has("arguments"))return null;}catch(JSONException normalAnswer){return null;}
        }
        if(payload.startsWith("{")){
            JSONObject obj;try{obj=new JSONObject(payload);}catch(JSONException e){throw new CallError("CALL_INCOMPLETE","O JSON da chamada não foi concluído.");}
            JSONObject f=obj.optJSONObject("function");if(f==null)f=obj;String name=f.optString("name","");Object v=f.opt("arguments");JSONObject args=v instanceof JSONObject?(JSONObject)v:v instanceof String?new JSONObject((String)v):null;
            if(args==null)throw new CallError("CALL_ARGUMENTS","Os argumentos da ferramenta precisam ser um objeto.");return validate(name,args);
        }
        Matcher m=CALL.matcher(payload);if(!m.matches())throw new CallError("CALL_FORMAT","O modelo gerou uma chamada com formato inválido.");
        return validate(m.group(1),new JSONObject().put(m.group(2),m.group(3)));
    }
    private static JSONObject validate(String name,JSONObject args)throws Exception {
        if(!name.equals("search_web")&&!name.equals("run_python"))throw new CallError("UNKNOWN_TOOL","Ferramenta não disponível.");String key=name.equals("search_web")?"query":"code";
        if(args.length()!=1||!(args.opt(key) instanceof String))throw new CallError("CALL_ARGUMENTS","Argumentos incompatíveis com a ferramenta.");String value=args.getString(key);
        if(value.trim().isEmpty())throw new CallError("CALL_ARGUMENTS","Argumento vazio.");
        if(value.length()>(key.equals("query")?300:6000))throw new CallError("CALL_ARGUMENT_LIMIT",key.equals("query")?"A consulta ultrapassou 300 caracteres.":"O programa ultrapassou 6.000 caracteres.");
        return new JSONObject().put("name",name).put("arguments",args);
    }
    public static String safe(String s,int max){
        for(String t:new String[]{"<|im_start|>","<|im_end|>","<think>","</think>","<tool_call>","</tool_call>","<tool_response>","</tool_response>"})s=s.replace(t,t.replace('<','‹'));
        return s.substring(0,Math.min(max,s.length()));
    }
    public static String clean(String s){
        s=s.replaceAll("(?s)<[^>]*>"," ").replace("&amp;","&").replace("&quot;","\"").replace("&#39;","'").replace("&lt;","<").replace("&gt;",">").replace("&nbsp;"," ").replace("&mdash;","—").replace("&ndash;","–").replace("&rsquo;","’").replace("&lsquo;","‘").replace("&hellip;","…");
        Matcher m=Pattern.compile("&#(x[0-9A-Fa-f]+|[0-9]+);").matcher(s);StringBuffer out=new StringBuffer();
        while(m.find()){String v=m.group(1),r="";try{int n=Integer.parseInt(v.startsWith("x")?v.substring(1):v,v.startsWith("x")?16:10);if(Character.isValidCodePoint(n))r=new String(Character.toChars(n));}catch(Exception ignored){}m.appendReplacement(out,Matcher.quoteReplacement(r));}m.appendTail(out);return out.toString().replaceAll("\\s+"," ").trim();
    }
    private static byte[] get(String address)throws Exception {
        HttpURLConnection c=(HttpURLConnection)new URL(address).openConnection();c.setConnectTimeout(12000);c.setReadTimeout(12000);c.setInstanceFollowRedirects(false);c.setRequestProperty("User-Agent","Mozilla/5.0 LiquidSenseResearch/0.1");c.setRequestProperty("Accept","text/html");
        try{int status=c.getResponseCode();if(status!=200)throw new IOException("HTTP "+status);try(InputStream in=c.getInputStream();ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1){if(out.size()+n>1048576)throw new IOException("Resposta de busca grande demais");out.write(b,0,n);}return out.toByteArray();}}finally{c.disconnect();}
    }
    public static JSONArray results(String html,boolean brave)throws Exception {
        Pattern boundary=Pattern.compile(brave?"<div class=\"snippet [^\"]*\"[^>]*data-type=\"web\"[^>]*>":"<div class=\"dd [^\"]*\\balgo\\b[^\"]*\"[^>]*>");
        Matcher split=boundary.matcher(html);ArrayList<Integer> starts=new ArrayList<>();while(split.find())starts.add(split.start());starts.add(html.length());JSONArray items=new JSONArray();Set<String> seen=new HashSet<>();
        for(int i=0;i+1<starts.size()&&items.length()<3;i++){
            String piece=html.substring(starts.get(i),starts.get(i+1));Matcher link=Pattern.compile("<a\\b[^>]*href=\"([^\"]+)\"[^>]*>").matcher(piece);if(!link.find())continue;String url=clean(link.group(1));
            if(!brave){Matcher redirect=Pattern.compile("/RU=([^/]+)/RK=").matcher(url);if(redirect.find())url=URLDecoder.decode(redirect.group(1),"UTF-8");}
            URI u=new URI(url);if(!Arrays.asList("https","http").contains(u.getScheme())||u.getHost()==null||u.getUserInfo()!=null||!seen.add(url))continue;
            Matcher title=Pattern.compile(brave?"<div[^>]*class=\"[^\"]*search-snippet-title[^\"]*\"[^>]*>([\\s\\S]*?)</div>":"<h3\\b[^>]*>([\\s\\S]*?)</h3>").matcher(piece);
            Matcher desc=Pattern.compile(brave?"<div[^>]*class=\"[^\"]*generic-snippet[^\"]*\"[^>]*>([\\s\\S]*?)</div>":"<div class=\"compText[^\"]*\"[^>]*>([\\s\\S]*?)</div>").matcher(piece);
            items.put(new JSONObject().put("title",safe(title.find()?clean(title.group(1)):url,180)).put("url",safe(url,800)).put("snippet",safe(desc.find()?clean(desc.group(1)):"",450)));
        }return items;
    }
    private static JSONObject officialPython(String query)throws Exception {
        if(!query.toLowerCase(Locale.ROOT).contains("python"))return null;
        Matcher symbol=Pattern.compile("(?<![A-Za-z0-9_])([a-z_][a-z0-9_]*(?:\\.[a-z_][a-z0-9_]*)+)").matcher(query);int tries=0;
        while(symbol.find()&&tries++<3){
            String name=symbol.group(1),module=name.substring(0,name.indexOf('.'));String url="https://docs.python.org/3/library/"+module+".html";byte[] bytes;
            try{bytes=get(url);}catch(IOException unavailable){continue;}
            String html=new String(bytes,StandardCharsets.UTF_8);int anchor=html.indexOf("id=\""+name+"\"");if(anchor<0)continue;
            String section=html.substring(anchor,Math.min(html.length(),anchor+16000));int dd=section.indexOf("<dd"),end=section.indexOf("</dd>");if(dd>=0&&end>dd)section=section.substring(dd,end);
            Matcher title=Pattern.compile("(?s)<title>(.*?)</title>").matcher(html);StringBuilder sha=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes))sha.append(String.format(Locale.ROOT,"%02x",b&255));
            JSONObject item=new JSONObject().put("title",safe(title.find()?clean(title.group(1)):name,180)).put("url",url+"#"+name).put("snippet",safe(clean(section),450)).put("source","official_python_documentation");
            SimpleDateFormat f=new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'",Locale.ROOT);f.setTimeZone(TimeZone.getTimeZone("UTC"));
            return new JSONObject().put("tool","search_web").put("ok",true).put("query",query).put("retrieved_at_utc",f.format(new Date())).put("transport","real HTTPS official Python documentation lookup").put("response_sha256",sha.toString()).put("documented_symbol",name).put("anchor_verified_in_fetched_HTML",true).put("items",new JSONArray().put(item)).put("untrusted_evidence",true).put("provider_failures",new JSONArray());
        }return null;
    }
    public static JSONObject search(String query)throws Exception {
        if(query.trim().isEmpty()||query.length()>300)throw new IOException("Termos de busca inválidos");String provider="Brave Search HTML";JSONArray failures=new JSONArray();byte[] bytes;JSONArray items;
        // Generic stdlib symbol lookup: fetch real official HTML and verify its
        // anchor. No predefined task answers or fabricated source URLs.
        try{JSONObject official=officialPython(query);if(official!=null)return official;}catch(Exception unavailable){failures.put(new JSONObject().put("provider","official Python docs").put("error",safe(unavailable.toString(),180)));}
        try{bytes=get("https://search.brave.com/search?q="+URLEncoder.encode(query,"UTF-8")+"&source=web");items=results(new String(bytes,StandardCharsets.UTF_8),true);if(items.length()==0)throw new IOException("Nenhum resultado interpretável");}
        catch(Exception e){failures.put(new JSONObject().put("provider",provider).put("error",safe(e.toString(),180)));provider="Yahoo Search HTML";bytes=get("https://search.yahoo.com/search?p="+URLEncoder.encode(query,"UTF-8"));items=results(new String(bytes,StandardCharsets.UTF_8),false);}
        SimpleDateFormat f=new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'",Locale.ROOT);f.setTimeZone(TimeZone.getTimeZone("UTC"));StringBuilder sha=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes))sha.append(String.format(Locale.ROOT,"%02x",b&255));
        return new JSONObject().put("tool","search_web").put("ok",items.length()>0).put("query",query).put("retrieved_at_utc",f.format(new Date())).put("transport","real HTTPS "+provider).put("response_sha256",sha.toString()).put("items",items).put("untrusted_evidence",true).put("provider_failures",failures);
    }
}
