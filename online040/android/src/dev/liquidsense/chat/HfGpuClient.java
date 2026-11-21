package dev.liquidsense.chat;

import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.function.BooleanSupplier;

/** Direct client for the project's fixed HTTPS Gradio endpoint. */
final class HfGpuClient {
    static final String SPACE = "https://felipe0282829273-liquid-sense-gpu.hf.space";
    private static final String ENDPOINT = "/gradio_api/call/generate_turn";
    private static final int MAX_PHASES = 128;
    private volatile HttpURLConnection active;

    interface Progress { void update(JSONObject result); }

    void cancel() {
        HttpURLConnection connection = active;
        if (connection != null) connection.disconnect();
    }

    JSONObject generate(JSONArray history, String profile, String token, BooleanSupplier stopped,
                        Progress progress) throws Exception {
        JSONArray messages = new JSONArray();
        int characters = 0;
        for (int i = history.length() - 1; i >= 0 && messages.length() < 256; i--) {
            JSONObject item = history.getJSONObject(i);
            String role = item.optString("role");
            if (item.optBoolean("internal") || (!role.equals("user") && !role.equals("assistant"))) continue;
            String content = item.optString("content");
            if (characters + content.length() > 256000) break;
            messages.put(new JSONObject().put("role", role).put("content", content));
            characters += content.length();
        }
        JSONArray chronological = new JSONArray();
        for (int i = messages.length() - 1; i >= 0; i--) chronological.put(messages.getJSONObject(i));
        JSONObject payload = new JSONObject().put("messages", chronological).put("profile", profile);
        JSONObject result = new JSONObject();
        int previousTokens = -1;
        double prefill = 0, decode = 0;
        for (int i = 0; i < MAX_PHASES; i++) {
            if (stopped.getAsBoolean()) return finish(result, "cancelled", null);
            JSONObject next;
            try {
                next = invoke(payload, token, stopped);
            } catch (Exception error) {
                if (stopped.getAsBoolean()) return finish(result, "cancelled", null);
                return finish(result, "error", error.getMessage() == null ? "Falha de rede no Hugging Face." : error.getMessage());
            }
            if (!next.optString("device").startsWith("cuda")) {
                return finish(result, "error", "O Space não confirmou processamento em GPU.");
            }
            result = next;
            prefill += next.optDouble("prefill_seconds", 0);
            decode += next.optDouble("decode_seconds", 0);
            result.put("prefill_seconds", prefill).put("decode_seconds", decode).put("backend", "Hugging Face GPU");
            progress.update(result);
            if (!"continue".equals(result.optString("finish_reason"))) return result;
            JSONObject cursor = result.optJSONObject("cursor");
            int tokens = result.optInt("tokens", -1);
            if (cursor == null || tokens <= previousTokens || tokens > 6144) {
                return finish(result, "error", "A GPU não enviou uma continuação válida.");
            }
            previousTokens = tokens;
            payload.put("cursor", cursor);
        }
        return finish(result, "length", null);
    }

    private JSONObject finish(JSONObject result, String reason, String message) throws Exception {
        result.put("backend", "Hugging Face GPU").put("finish_reason", reason);
        if (message != null) result.put("error", message);
        return result;
    }

    private JSONObject invoke(JSONObject payload, String token, BooleanSupplier stopped) throws Exception {
        byte[] body = new JSONObject().put("data", new JSONArray().put(payload)).toString().getBytes(StandardCharsets.UTF_8);
        HttpURLConnection submit = open(ENDPOINT, token);
        String event;
        try {
            submit.setRequestMethod("POST");
            submit.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            submit.setDoOutput(true);
            submit.setFixedLengthStreamingMode(body.length);
            try (OutputStream out = submit.getOutputStream()) { out.write(body); }
            checkHttp(submit);
            event = new JSONObject(readSmall(submit.getInputStream())).getString("event_id");
        } finally { close(submit); }
        if (stopped.getAsBoolean()) throw new IOException("Geração interrompida.");
        if (!event.matches("[A-Za-z0-9_-]{8,80}")) throw new IOException("Identificador inválido do Hugging Face.");
        HttpURLConnection watch = open(ENDPOINT + "/" + event, token);
        try {
            watch.setRequestProperty("Accept", "text/event-stream");
            checkHttp(watch);
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(watch.getInputStream(), StandardCharsets.UTF_8))) {
                return parseEvents(reader, stopped);
            }
        } finally { close(watch); }
    }

    static JSONObject parseEvents(BufferedReader reader, BooleanSupplier stopped) throws Exception {
        String eventType = "";
        long deadline = System.nanoTime() + java.util.concurrent.TimeUnit.MINUTES.toNanos(5);
        for (String line; (line = reader.readLine()) != null;) {
            if (stopped.getAsBoolean()) throw new IOException("Geração interrompida.");
            if (System.nanoTime() > deadline) throw new IOException("Tempo de espera na fila do Hugging Face excedido.");
            if (line.length() > 500000) throw new IOException("Resposta do Hugging Face grande demais.");
            if (line.startsWith("event:")) eventType = line.substring(6).trim();
            if (!line.startsWith("data:")) continue;
            String data = line.substring(5).trim();
            if ("complete".equals(eventType)) return new JSONArray(data).getJSONObject(0);
            if ("error".equals(eventType) || "unexpected_error".equals(eventType)) throw new IOException(serviceError(data));
        }
        throw new IOException("O Hugging Face encerrou a conexão antes de responder.");
    }

    private HttpURLConnection open(String path, String token) throws IOException {
        HttpURLConnection connection = (HttpURLConnection) new URL(SPACE + path).openConnection();
        active = connection;
        connection.setInstanceFollowRedirects(false);
        connection.setConnectTimeout(15000);
        connection.setReadTimeout(95000);
        if (!token.isEmpty()) connection.setRequestProperty("Authorization", "Bearer " + token);
        return connection;
    }

    private void checkHttp(HttpURLConnection connection) throws IOException {
        int code = connection.getResponseCode();
        if (code >= 200 && code < 300) return;
        if (code == 401 || code == 403) throw new IOException("Acesso recusado. Confira a credencial do Hugging Face.");
        if (code == 429) throw new IOException("Limite do ZeroGPU atingido. Aguarde a renovação da cota.");
        if (code == 404 || code == 502 || code == 503) throw new IOException("O Space GPU está iniciando ou indisponível.");
        throw new IOException("A chamada ao Hugging Face falhou (HTTP " + code + ").");
    }

    private static String serviceError(String data) {
        String lower = data.toLowerCase(java.util.Locale.ROOT);
        if (lower.contains("contexto") || lower.contains("histórico") || lower.contains("tamanho permitido")) {
            return "A conversa não cabe no contexto da GPU com este modo. Divida a mensagem ou crie uma nova conversa.";
        }
        if (lower.contains("quota") || lower.contains("cota") || lower.contains("rate limit")) {
            return "Cota do ZeroGPU atingida. Use o modo local ou tente quando a cota renovar.";
        }
        return "O Space não concluiu a etapa. Confira a fila e a cota do ZeroGPU ou tente no modo local.";
    }

    private void close(HttpURLConnection connection) {
        connection.disconnect();
        if (active == connection) active = null;
    }

    private static String readSmall(InputStream stream) throws IOException {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            char[] buffer = new char[1024];
            StringBuilder result = new StringBuilder();
            int size;
            while ((size = reader.read(buffer)) != -1) {
                if (result.length() + size > 16000) throw new IOException("Resposta inicial inválida do Hugging Face.");
                result.append(buffer, 0, size);
            }
            return result.toString();
        }
    }
}
