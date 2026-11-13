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
    public static JSONObject parse(String raw)throws Exception {
        int a=raw.indexOf("<tool_call>");if(a<0)return null;
        int b=raw.indexOf("</tool_call>",a);if(b<0||!raw.substring(b+12).trim().isEmpty())throw new IOException("Chamada de ferramenta incompleta ou com sufixo.");
        Matcher m=CALL.matcher(raw.substring(a+11,b));if(!m.matches())throw new IOException("Formato de ferramenta inválido.");
        String name=m.group(1),key=m.group(2),value=m.group(3);
        if(!key.equals(name.equals("search_web")?"query":"code")||value.isEmpty()||value.length()>(key.equals("query")?300:6000))throw new IOException("Argumento de ferramenta inválido.");
        return new JSONObject().put("name",name).put("arguments",new JSONObject().put(key,value));
    }
    public static String safe(String s,int max){
        for(String t:new String[]{"<|im_start|>","<|im_end|>","<think>","</think>","<tool_call>","</tool_call>","<tool_response>","</tool_response>"})s=s.replace(t,t.replace('<','‹'));
        return s.substring(0,Math.min(max,s.length()));
    }
    public static String clean(String s){
        s=s.replaceAll("(?s)<[^>]*>"," ").replace("&amp;","&").replace("&quot;","\"").replace("&#39;","'").replace("&lt;","<").replace("&gt;",">").replace("&nbsp;"," ");
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
    public static JSONObject search(String query)throws Exception {
        if(query.trim().isEmpty()||query.length()>300)throw new IOException("Termos de busca inválidos");String provider="Brave Search HTML";JSONArray failures=new JSONArray();byte[] bytes;JSONArray items;
        try{bytes=get("https://search.brave.com/search?q="+URLEncoder.encode(query,"UTF-8")+"&source=web");items=results(new String(bytes,StandardCharsets.UTF_8),true);if(items.length()==0)throw new IOException("Nenhum resultado interpretável");}
        catch(Exception e){failures.put(new JSONObject().put("provider",provider).put("error",safe(e.toString(),180)));provider="Yahoo Search HTML";bytes=get("https://search.yahoo.com/search?p="+URLEncoder.encode(query,"UTF-8"));items=results(new String(bytes,StandardCharsets.UTF_8),false);}
        SimpleDateFormat f=new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'",Locale.ROOT);f.setTimeZone(TimeZone.getTimeZone("UTC"));StringBuilder sha=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes))sha.append(String.format(Locale.ROOT,"%02x",b&255));
        return new JSONObject().put("tool","search_web").put("ok",items.length()>0).put("query",query).put("retrieved_at_utc",f.format(new Date())).put("transport","real HTTPS "+provider).put("response_sha256",sha.toString()).put("items",items).put("untrusted_evidence",true).put("provider_failures",failures);
    }
}
