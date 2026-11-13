import dev.liquidsense.chat.*;
import org.json.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.io.*;
import java.util.*;
/** Real host Rust model + same Java agent + actual isolated-subset C interpreter. */
public final class NativeAgentSmoke {
 public static void main(String[] argv)throws Exception{
  Path out=Paths.get(argv[0]);Files.createDirectories(out);String profile=argv[1];String question=argv.length>2?argv[2]:"Use Python para conferir quanto é 18 vezes 23 e diga o resultado.";
  JSONArray history=new JSONArray().put(new JSONObject().put("role","user").put("content",question));final int[] turns={0};long started=System.nanoTime();
  AgentRunner runner=new AgentRunner((messages,options)->{
   int t=turns[0]++;Path input=out.resolve("messages_"+t+".json"),settings=out.resolve("options_"+t+".json"),stdout=out.resolve("native_"+t+".json"),stderr=out.resolve("native_"+t+".stderr");Files.write(input,messages.toString().getBytes(StandardCharsets.UTF_8));Files.write(settings,options.toString().getBytes(StandardCharsets.UTF_8));
   Process p=new ProcessBuilder("/dev/shm/liquid-android/prebuilt/thinking024/toolcheck","parent",input.toString(),settings.toString()).redirectOutput(stdout.toFile()).redirectError(stderr.toFile()).start();int status=p.waitFor();if(status!=0)throw new IOException("native exit "+status+": "+new String(Files.readAllBytes(stderr),StandardCharsets.UTF_8));return new JSONObject(new String(Files.readAllBytes(stdout),StandardCharsets.UTF_8));
  },call->{
   if(call.getString("name").equals("search_web"))return ToolExecutor.search(call.getJSONObject("arguments").getString("query"));
   Path stdout=out.resolve("python_"+turns[0]+".stdout"),stderr=out.resolve("python_"+turns[0]+".stderr");Process p=new ProcessBuilder("/dev/shm/liquid-android/tools022/python-host/liquid-python").directory(new File("/tmp")).redirectOutput(stdout.toFile()).redirectError(stderr.toFile()).start();try(OutputStream stream=p.getOutputStream()){stream.write(call.getJSONObject("arguments").getString("code").getBytes(StandardCharsets.UTF_8));}if(!p.waitFor(6,java.util.concurrent.TimeUnit.SECONDS)){p.destroyForcibly();throw new IOException("host Python watchdog timeout");}JSONObject obs=new JSONObject().put("tool","run_python").put("ok",p.exitValue()==0).put("runtime","MicroPython1.26.1 actual C interpreter, Python subset").put("stdout",new String(Files.readAllBytes(stdout),StandardCharsets.UTF_8));if(p.exitValue()!=0)obs.put("error",new String(Files.readAllBytes(stderr),StandardCharsets.UTF_8));return obs;
  },new AgentRunner.Events(){
   public void diagnostic(JSONArray records){try{Files.write(out.resolve("trace.json"),records.toString(2).getBytes(StandardCharsets.UTF_8));}catch(Exception e){throw new RuntimeException(e);}}
   public void append(JSONObject m){history.put(m);try{Files.write(out.resolve("history.json"),history.toString(2).getBytes(StandardCharsets.UTF_8));}catch(Exception e){throw new RuntimeException(e);}}
   public void tool(JSONObject c,JSONObject o){System.out.println("ACTUAL_TOOL "+c.getString("name")+" ok="+o.optBoolean("ok"));}
  },()->false);
  JSONObject result=runner.run(history.toString(),profile).put("scope","Linux host Rust model + identical Java agent + actual C Python subset; not Android phone execution").put("no_reference_answer_in_input",true).put("wall_seconds_descriptive_only",(System.nanoTime()-started)/1e9);Files.write(out.resolve("result.json"),result.toString(2).getBytes(StandardCharsets.UTF_8));System.out.println(result.toString(2));
 }
}
