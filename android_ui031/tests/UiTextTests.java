import dev.liquidsense.chat.UiText;
import org.json.JSONObject;
public final class UiTextTests {
 public static void main(String[] args)throws Exception {
  if(!UiText.thought(new JSONObject().put("thinking",true).put("raw_text","Verificar o caso vazio.\n</think>\nResposta")).equals("Verificar o caso vazio."))throw new AssertionError("real thought split");
  if(!UiText.thought(new JSONObject().put("thinking",true).put("raw_text","<think>Raciocínio incompleto")).equals("Raciocínio incompleto"))throw new AssertionError("partial thought");
  if(!UiText.thought(new JSONObject().put("thinking",false).put("raw_text","print('</think>')")).isEmpty())throw new AssertionError("code literal is not thought");
  if(!UiText.thought(new JSONObject()).isEmpty())throw new AssertionError("no invented thought");
  System.out.println("{\"checks\":4,\"status\":\"passed\"}");
 }
}
