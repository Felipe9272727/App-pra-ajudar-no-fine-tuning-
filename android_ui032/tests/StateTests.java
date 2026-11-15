import dev.liquidsense.chat.*;
import org.json.*;
public final class StateTests {
 static int count=0;static void check(boolean value,String label){count++;if(!value)throw new AssertionError(label);}
 public static void main(String[] args)throws Exception {
  JSONArray threads=new JSONArray(),messages=new JSONArray().put(new JSONObject().put("role","user").put("content","mensagem antiga"));
  ConversationBook.upsert(threads,ConversationBook.record("old","epochs029",messages,1));
  messages.put(new JSONObject().put("role","assistant").put("content","resposta tardia"));
  check(threads.getJSONObject(0).getJSONArray("messages").length()==1,"archive is an immutable message snapshot");
  ConversationBook.upsert(threads,ConversationBook.record("old","epochs029",messages,2));
  ConversationBook.upsert(threads,ConversationBook.record("new","epochs029",new JSONArray(),3));
  JSONArray restored=new JSONArray(threads.toString());check(restored.length()==2,"clear keeps old chat and new empty chat after reload");
  check(restored.getJSONObject(0).getJSONArray("messages").length()==2,"late old result preserved in old chat");
  check(restored.getJSONObject(1).getJSONArray("messages").length()==0,"new context has no old messages");
  check(ConversationBook.list(restored).getJSONObject(0).getString("id").equals("new"),"empty new chat immediately visible and active in list");
  ConversationBook.upsert(restored,ConversationBook.record("base","base",new JSONArray(),4));check(restored.length()==3,"switching model does not drop other chats");
  NavigationQueue queue=new NavigationQueue();JSONObject request=new JSONObject().put("type","newChat");queue.defer(request);request.put("type","send");
  check(queue.takeIfIdle(true,false)==null&&queue.waiting(),"busy new-chat request is retained");
  check(queue.takeIfIdle(false,true)==null&&queue.waiting(),"loading also retains navigation");
  check(queue.takeIfIdle(false,false).getString("type").equals("newChat"),"request cloned and consumed after cancellation");
  check(queue.takeIfIdle(false,false)==null&&!queue.waiting(),"navigation consumed exactly once");
  queue.defer(new JSONObject().put("type","newChat"));queue.defer(new JSONObject().put("type","selectModel").put("id","base"));
  check(queue.takeIfIdle(false,false).getString("id").equals("base"),"latest navigation intent wins without old action resurfacing");
  System.out.println("{\"checks\":"+count+",\"status\":\"passed\",\"scope\":\"production Java persistence and navigation queue on host JVM\"}");
 }
}
