package dev.liquidsense.chat;
import org.json.*;
import java.util.*;
import java.util.function.BooleanSupplier;

/** Bounded actual-tool orchestration; no partial call is ever executed. */
public final class AgentRunner {
    public interface Model {JSONObject generate(JSONArray messages,JSONObject options)throws Exception;}
    public interface Tools {JSONObject execute(JSONObject call)throws Exception;}
    public interface Events {
        void diagnostic(JSONArray records);
        void tool(JSONObject call,JSONObject observation);
        void append(JSONObject message);
    }
    private final Model model;private final Tools tools;private final Events events;private final BooleanSupplier cancelled;
    public AgentRunner(Model model,Tools tools,Events events,BooleanSupplier cancelled){this.model=model;this.tools=tools;this.events=events;this.cancelled=cancelled;}
    private JSONArray records,toolsTrace;private int tokens,reasoning,reused,forced;private double prefill,decode;
    private JSONObject summarize(JSONObject answer)throws Exception {
        return answer.put("actual_tool_calls",toolsTrace.length()).put("tokens",tokens).put("reasoning_tokens",reasoning).put("forced_control_tokens",forced).put("prefill_seconds",prefill).put("decode_seconds",decode).put("reused_prompt_tokens",reused);
    }
    private JSONObject failure(String code,String message)throws Exception {
        String prefix=toolsTrace.length()>0?"Os resultados das ferramentas foram preservados. ":"";
        return summarize(new JSONObject().put("error_code",code).put("error",prefix+message));
    }
    private void append(JSONArray messages,JSONObject m){messages.put(m);events.append(m);}
    private void control(JSONArray messages,String text)throws Exception {append(messages,new JSONObject().put("role","user").put("internal",true).put("content",text));}
    private JSONObject compact(JSONObject original)throws Exception {
        JSONObject value=new JSONObject(original.toString());String stdout=value.optString("stdout","");
        if(stdout.length()>2048)value.put("stdout",stdout.substring(0,2048)).put("stdout_truncated_for_context",true);
        return value;
    }
    public JSONObject run(String payload,String profile)throws Exception {
        JSONArray messages=new JSONArray(payload);records=new JSONArray();toolsTrace=new JSONArray();tokens=reasoning=reused=forced=0;prefill=decode=0;
        int repairs=0;boolean focusFinal=false;Set<String> successful=new HashSet<>();
        for(int turn=0;turn<6;turn++){
            if(cancelled.getAsBoolean())return summarize(new JSONObject().put("text","").put("finish_reason","cancelled"));
            int remaining=16384-tokens-forced;if(remaining<16)return failure("TASK_TOKEN_LIMIT","O orçamento total da mensagem terminou. Toque em Continuar resposta.");
            JSONObject options=InferenceSettings.options(focusFinal?"normal":profile);int think=options.optInt("reasoning_tokens");int response=options.optInt("response_tokens");
            if(think+response>remaining){think=Math.max(0,remaining-response);response=Math.min(response,remaining);options.put("thinking",think>0).put("reasoning_tokens",think).put("response_tokens",response);}
            JSONObject answer=model.generate(messages,options);JSONObject record=new JSONObject().put("turn",turn).put("options",options).put("answer",answer);records.put(record);events.diagnostic(records);
            if(answer.has("error")){String error=answer.optString("error");return failure(error.contains("CONTEXT_LIMIT")?"CONTEXT_LIMIT":"NATIVE_ERROR",error.contains("CONTEXT_LIMIT")?"A conversa e o espaço reservado para pensar e responder excederam 16 mil tokens; inicie uma nova conversa ou reduza o trecho.":error);}
            prefill+=answer.optDouble("prefill_seconds",0);decode+=answer.optDouble("decode_seconds",0);tokens+=answer.optInt("tokens");reasoning+=answer.optInt("reasoning_tokens");forced+=answer.optInt("forced_control_tokens");reused+=answer.optInt("reused_prompt_tokens");
            if(cancelled.getAsBoolean()||answer.optString("finish_reason").equals("cancelled"))return summarize(new JSONObject().put("text",answer.optString("text")).put("finish_reason","cancelled"));
            String raw=answer.optString("raw_text",answer.optString("text"));JSONObject call=null;
            try{
                call=ToolExecutor.parse(answer.optString("text",raw),!answer.optBoolean("reasoning_complete",true));
                if(call==null&&answer.optString("text",ToolExecutor.content(raw)).trim().isEmpty())throw new ToolExecutor.CallError("EMPTY_FINAL","O modelo encerrou sem uma resposta final.");
            }catch(Exception e){
                String code=e instanceof ToolExecutor.CallError?((ToolExecutor.CallError)e).code:"CALL_FORMAT";record.put("parse_error_code",code).put("parse_error",e.toString());events.diagnostic(records);
                if(repairs++==0&&turn<5){focusFinal=true;control(messages,"A etapa anterior não produziu uma chamada válida ou resposta final ("+code+"). Refaça a próxima etapa: use uma única chamada completa no formato definido, ou conclua com os resultados reais já recebidos. Não invente execuções nem fontes.");continue;}
                String detail=code.equals("CALL_INCOMPLETE")&&answer.optString("finish_reason").equals("length")?"A chamada atingiu o limite antes de ficar completa.":"O modelo não conseguiu corrigir o formato da chamada ("+code+").";
                return failure(code,detail+" Toque em Continuar resposta; o diagnóstico local foi guardado.");
            }
            if(call==null)return summarize(answer);
            String name=call.getString("name");JSONObject args=call.getJSONObject("arguments");String key=name+"\n"+args.toString();
            if(successful.contains(key)){
                record.put("duplicate_successful_call_suppressed",true);events.diagnostic(records);focusFinal=true;
                control(messages,"Essa chamada já foi executada com sucesso; o resultado real está acima. Conclua a resposta sem repetir a ferramenta.");continue;
            }
            if(toolsTrace.length()>=4)return failure("TOOL_CALL_LIMIT","Foram feitas quatro chamadas. Os resultados reais continuam na conversa; toque em Continuar resposta.");
            JSONObject observation;
            try{observation=tools.execute(call);}catch(Exception e){observation=new JSONObject().put("tool",name).put("ok",false).put("error",ToolExecutor.safe(e.toString(),1000));}
            toolsTrace.put(new JSONObject().put("call",call).put("observation",observation));record.put("call",call).put("observation",observation);events.diagnostic(records);events.tool(call,observation);
            if(observation.optBoolean("ok"))successful.add(key);
            append(messages,new JSONObject().put("role","assistant").put("content",answer.optString("text",ToolExecutor.content(raw))));
            append(messages,new JSONObject().put("role","tool").put("content",ToolExecutor.safe(compact(observation).toString(),12000)));
            control(messages,"Confira a observação real acima e conclua o pedido original. Cite somente URLs retornadas se fez uma busca. Se faltarem dados, diga isso ou faça uma nova consulta específica. Não repita uma chamada já bem-sucedida.");
            focusFinal=false;
        }
        return failure("MODEL_ROUND_LIMIT","O modelo não concluiu após seis etapas. Os dados foram mantidos; toque em Continuar resposta.");
    }
}
