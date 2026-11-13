import dev.liquidsense.chat.*;
import org.json.*;
import java.util.*;
public final class AgentTests {
 static int checks=0;
 static void check(boolean v,String m){checks++;if(!v)throw new AssertionError(m);}
 static String xml(String name,String key,String value){return "<tool_call>\n<function="+name+">\n<parameter="+key+">\n"+value+"\n</parameter>\n</function>\n</tool_call>";}
 static JSONObject answer(String raw,String reason)throws Exception{return new JSONObject().put("raw_text",raw).put("text",ToolExecutor.content(raw)).put("finish_reason",reason).put("tokens",20).put("reasoning_complete",true);}
 static final class Events implements AgentRunner.Events {
  JSONArray diagnostics=new JSONArray(),history=new JSONArray();int calls=0;
  public void diagnostic(JSONArray v){diagnostics=v;}
  public void tool(JSONObject c,JSONObject o){calls++;}
  public void append(JSONObject m){history.put(m);}
 }
 static JSONObject run(List<JSONObject> replies,Events ev)throws Exception {
  int[] index={0};AgentRunner runner=new AgentRunner((m,o)->replies.get(index[0]++),(call)->new JSONObject().put("tool",call.getString("name")).put("ok",true).put("stdout","5\n"),ev,()->false);
  return runner.run("[{\"role\":\"user\",\"content\":\"Confira com Python\"}]","profundo");
 }
 public static void main(String[] args)throws Exception {
  String x=xml("run_python","code","print(2+3)");check(ToolExecutor.parse(x).getString("name").equals("run_python"),"native XML");
  check(ToolExecutor.parse(x+"<|im_end|>").getString("name").equals("run_python"),"protocol suffix");
  check(ToolExecutor.parse("<think>Maybe <tool_call>not an action</tool_call></think>"+x).getString("name").equals("run_python"),"skip completed thought");
  String json="{\"name\":\"search_web\",\"arguments\":{\"query\":\"Python documentation\"}}";check(ToolExecutor.parse("<tool_call>"+json+"</tool_call>").getString("name").equals("search_web"),"JSON wrapper");
  check(ToolExecutor.parse(json).getString("name").equals("search_web"),"JSON call");
  check(ToolExecutor.parse("{\"answer\":5}")==null,"ordinary JSON answer");
  for(String bad:new String[]{x+"unexpected suffix",x.substring(0,x.length()-12),xml("run_python","query","wrong"),xml("read_file","code","x"),xml("search_web","query",new String(new char[301]).replace('\0','a'))}){
   boolean rejected=false;try{ToolExecutor.parse(bad);}catch(Exception e){rejected=true;}check(rejected,"invalid call rejected");
  }
  boolean waiting=false;try{ToolExecutor.parse("I might call "+x,true);}catch(ToolExecutor.CallError e){waiting=e.code.equals("REASONING_INCOMPLETE");}check(waiting,"thought cannot execute");
  String longCode=new String(new char[1400]).replace('\0',' ')+"print(5)";check(ToolExecutor.parse(xml("run_python","code",longCode))!=null,"long complete call");
  Events ev=new Events();JSONObject result=run(Arrays.asList(answer(xml("search_web","query","Python docs"),"tool_call"),answer("<tool_call><function=run_python>","length"),answer("O resultado foi conferido.","stop")),ev);
  check(!result.has("error")&&ev.calls==1,"repair after successful search, no partial execution");check(ev.diagnostics.getJSONObject(1).getString("parse_error_code").equals("CALL_INCOMPLETE"),"fault raw diagnostic retained");check(ev.history.toString().contains("stdout"),"real observation survives repair");
  ev=new Events();result=run(Arrays.asList(answer(x,"tool_call"),answer(x,"tool_call"),answer("5","stop")),ev);check(ev.calls==1,"successful duplicate not reexecuted");check(result.getString("text").equals("5"),"duplicate still reaches final");
  ev=new Events();result=run(Arrays.asList(answer("<tool_call>","length"),answer("<tool_call>","length")),ev);check(result.has("error")&&ev.calls==0,"bounded repair rejects partial code");check(!result.getString("error").contains("pergunta menor"),"accurate error, not input-size blame");
  ev=new Events();JSONObject thought=answer("Maybe <tool_call>not an action</tool_call></think>"+x,"tool_call").put("text",x);result=run(Arrays.asList(thought,answer("5","stop")),ev);check(ev.calls==1&&!result.has("error"),"parse native final separately from unprefixed thought");check(!ev.history.toString().contains("not an action"),"keep reasoning out of tool history");check(ev.diagnostics.toString().contains("not an action"),"retain raw reasoning in local diagnostic");
  JSONObject deep=InferenceSettings.options("profundo"),extended=InferenceSettings.options("extenso");check(deep.getBoolean("thinking")&&deep.getInt("response_tokens")==2048,"real default thinking options");check(extended.getInt("reasoning_tokens")==2048&&extended.getInt("response_tokens")==4096&&extended.getInt("context_tokens")==16384,"extended independent caps");
  System.out.println(new JSONObject().put("status","AGENT_PARSER_TESTS_PASSED").put("checks",checks).put("partial_calls_executed",0));
 }
}
