package dev.liquidsense.chat;

import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

final class HfCredential {
    private static final String KEY = "liquid_sense_hf_gpu_v1";
    private static final String PREF = "hf_gpu_encrypted";

    static String read(SharedPreferences preferences) throws Exception {
        String[] values = preferences.getString(PREF, "").split("\\.", 2);
        if (values.length != 2) return "";
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key(false), new GCMParameterSpec(128, Base64.decode(values[0], Base64.NO_WRAP)));
        return new String(cipher.doFinal(Base64.decode(values[1], Base64.NO_WRAP)), StandardCharsets.UTF_8);
    }

    static void write(SharedPreferences preferences, String token) throws Exception {
        if (token.isEmpty()) { preferences.edit().remove(PREF).apply(); return; }
        if (!token.matches("hf_[A-Za-z0-9]{20,200}")) throw new IllegalArgumentException("Formato de credencial inválido.");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key(true));
        String value = Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP) + "." +
                Base64.encodeToString(cipher.doFinal(token.getBytes(StandardCharsets.UTF_8)), Base64.NO_WRAP);
        preferences.edit().putString(PREF, value).apply();
    }

    private static SecretKey key(boolean create) throws Exception {
        KeyStore keys = KeyStore.getInstance("AndroidKeyStore");
        keys.load(null);
        if (keys.containsAlias(KEY)) return (SecretKey) keys.getKey(KEY, null);
        if (!create) throw new IllegalStateException("Salve novamente sua credencial do Hugging Face.");
        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(KEY, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256).build());
        return generator.generateKey();
    }
}
