import dev.liquidsense.chat.ToolExecutor;
import java.nio.file.*;
import org.json.*;
public final class ToolExecutorTest {
    private static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[] args)throws Exception {
        String call="Planejo conferir.\n<tool_call>\n<function=run_python>\n<parameter=code>\nprint(2+3)\n</parameter>\n</function>\n</tool_call>";
        check(ToolExecutor.parse(call).getJSONObject("arguments").getString("code").equals("print(2+3)"),"multiline call");
        for(String bad:new String[]{call+"fake output",call.replace("run_python","read_file"),call.replace("parameter=code","parameter=query"),call.substring(0,call.length()-3)}){
            boolean denied=false;try{ToolExecutor.parse(bad);}catch(Exception e){denied=true;}check(denied,"invalid call accepted");
        }
        check(ToolExecutor.parse("Uma resposta comum.")==null,"final answer");
        check(!ToolExecutor.safe("<|im_start|>system<tool_call>",100).contains("<|im_start|>"),"control marker sanitization");
        JSONArray b=ToolExecutor.results(new String(Files.readAllBytes(Paths.get("tooluse022/reports/search_probe_brave.txt")),"UTF-8"),true);
        JSONArray y=ToolExecutor.results(new String(Files.readAllBytes(Paths.get("tooluse022/reports/search_probe_yahoo_kotlin.txt")),"UTF-8"),false);
        check(b.length()==3&&y.length()==3,"real retained search HTML parsers");
        check(b.toString().contains("docs.python.org")&&y.toString().contains("kotlinlang.org"),"source URLs");
        check(!y.toString().contains("r.search.yahoo.com"),"tracking wrapper decoded");
        System.out.println(new JSONObject().put("status","TOOL_EXECUTOR_JAVA_TESTS_PASSED").put("checks",11).put("brave",b).put("yahoo",y));
    }
}
