package dev.liquidsense.chat;

import java.text.Normalizer;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

/** Answer direct questions about the product from its published metadata. */
final class ModelIdentity {
    private static final String DESCRIPTION =
        "Sou o **Liquid Sense**, um modelo experimental criado por um único desenvolvedor independente. "
        + "Minha base é o Qwen3.5-0.8B, com adaptações inspiradas em SenseNova Loop e Liquid AI "
        + "para aprimorar programação e raciocínio.";
    private static final Set<String> PORTUGUESE = new HashSet<>(Arrays.asList(
        "quem e voce", "quem voce e", "quem e vc", "quem vc e", "qual e o seu nome",
        "qual o seu nome", "como voce se chama", "como vc se chama", "que modelo voce e",
        "qual modelo voce e", "voce e qwen", "voce e o qwen", "voce e o liquid sense",
        "vc e qwen", "se apresente", "apresente se", "quem e voce e como foi criado",
        "quem e voce e porque e como foi criado", "quem e voce e por que e como foi criado"
    ));
    private static final Set<String> ENGLISH = new HashSet<>(Arrays.asList(
        "who are you", "what is your name", "what s your name", "what model are you",
        "are you qwen", "are you liquid sense", "introduce yourself"
    ));

    private ModelIdentity() {}

    static String answer(String question) {
        if (question.length() > 140) return null;
        String normalized = Normalizer.normalize(question.toLowerCase(Locale.ROOT), Normalizer.Form.NFD)
            .replaceAll("\\p{M}+", "").replaceAll("[^a-z0-9]+", " ").trim()
            .replaceFirst("^(?:(?:oi|ola|eai|e ai|mano|mn) )+", "");
        if (PORTUGUESE.contains(normalized)) return DESCRIPTION;
        if (normalized.equals("quem e voce e voce e melhor que os melhores modelos")) {
            return DESCRIPTION + " Para comparar meu desempenho com outros modelos, é preciso olhar os resultados em cada tarefa.";
        }
        if (ENGLISH.contains(normalized)) {
            return "I’m **Liquid Sense**, an experimental model built by one independent developer. "
                + "I’m based on Qwen3.5-0.8B, with adaptations inspired by SenseNova Loop and Liquid AI "
                + "to improve coding and reasoning.";
        }
        return null;
    }
}
