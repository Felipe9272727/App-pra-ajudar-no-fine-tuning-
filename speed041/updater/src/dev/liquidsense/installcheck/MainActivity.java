package dev.liquidsense.installcheck;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.PendingIntent;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageInstaller;
import android.content.pm.PackageInfo;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.security.DigestOutputStream;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import java.util.zip.ZipInputStream;

public final class MainActivity extends Activity {
    private static final String TARGET = "dev.liquidsense.chat.tools";
    private static final String PREFS = "diagnostic";
    private static final int BUFFER = 1 << 20;
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private Button update;
    private TextView report;
    private ProgressBar progress;
    private volatile boolean busy, destroyed;

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        int padding = Math.round(18 * getResources().getDisplayMetrics().density);
        page.setPadding(padding, padding, padding, padding);
        page.setFitsSystemWindows(true);
        TextView title = new TextView(this);
        title.setText("Atualizar Liquid Sense"); title.setTextSize(23);
        page.addView(title);
        TextView details = new TextView(this);
        details.setText("Atualização 0.6.5 · motor local otimizado. O instalador reaproveita os pesos da 0.6.4 já instalada. Suas conversas ficam no Liquid Sense.");
        page.addView(details);
        update = new Button(this); update.setAllCaps(false); update.setOnClickListener(v -> begin()); page.addView(update);
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(100); page.addView(progress);
        Button open = new Button(this); open.setAllCaps(false); open.setText("Abrir Liquid Sense");
        open.setOnClickListener(v -> { Intent launch = getPackageManager().getLaunchIntentForPackage(TARGET); if (launch != null) startActivity(launch); });
        page.addView(open);
        ScrollView scroll = new ScrollView(this);
        report = new TextView(this); report.setTextIsSelectable(true); scroll.addView(report);
        page.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(page); refresh();
    }

    private SharedPreferences prefs() { return getSharedPreferences(PREFS, MODE_PRIVATE); }

    @Override protected void onResume() { super.onResume(); refresh(); }
    @Override protected void onNewIntent(Intent intent) { super.onNewIntent(intent); refresh(); }
    @Override protected void onDestroy() { destroyed = true; worker.shutdown(); super.onDestroy(); }

    private void refresh() {
        if (destroyed || update == null) return;
        update.setEnabled(!busy);
        update.setText(prefs().contains("confirmation041") ? "Confirmar instalação no Android" : "Atualizar para 0.6.5");
        report.setText(prefs().getString("report041", "Toque em Atualizar. O Android pedirá confirmação em seguida."));
    }

    private void write(String value) {
        prefs().edit().putString("report041", value).apply();
        runOnUiThread(this::refresh);
    }

    private void begin() {
        if (busy) return;
        String confirmation = prefs().getString("confirmation041", "");
        if (!confirmation.isEmpty()) {
            try { startActivity(Intent.parseUri(confirmation, Intent.URI_INTENT_SCHEME)); }
            catch (Exception error) { write("Não consegui abrir a confirmação. Volte ao instalador do Android."); }
            return;
        }
        PackageInstaller installer = getPackageManager().getPackageInstaller();
        if (prefs().getBoolean("pending041", false) && installer.getSessionInfo(prefs().getInt("session041", -1)) != null) {
            write("Aguardando a confirmação ou o resultado da sessão do Android."); return;
        }
        if (!getPackageManager().canRequestPackageInstalls()) {
            new AlertDialog.Builder(this).setMessage("Autorize este atualizador a abrir o instalador do Android. Depois volte e toque em Atualizar novamente.")
                    .setPositiveButton("Abrir permissão", (dialog, which) -> startActivity(new Intent(
                            Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:" + getPackageName()))))
                    .setNegativeButton("Voltar", null).show();
            return;
        }
        busy = true; refresh();
        worker.execute(() -> install(installer));
    }

    private void install(PackageInstaller installer) {
        int id = -1;
        boolean committed = false;
        try {
            PackageInfo phone = getPackageManager().getPackageInfo(TARGET, 0);
            if (phone.getLongVersionCode() == 9) { write("A versão 0.6.5 já está instalada."); return; }
            if (phone.getLongVersionCode() != 8) throw new IOException("É necessária a versão 0.6.4 instalada.");
            JSONObject manifest;
            try (InputStream in = getAssets().open("delta-manifest.json")) {
                ByteArrayOutputStream json = new ByteArrayOutputStream();
                transfer(in, json, null, 0, 0);
                manifest = new JSONObject(json.toString(StandardCharsets.UTF_8.name()));
            }
            write("Conferindo o APK 0.6.4 instalado…");
            File base = new File(phone.applicationInfo.sourceDir);
            try (InputStream in = new FileInputStream(base)) {
                MessageDigest hash = MessageDigest.getInstance("SHA-256");
                transfer(in, null, hash, 0, 0);
                if (!hex(hash.digest()).equals(manifest.getString("installed_base_sha256"))) {
                    throw new IOException("O aplicativo instalado tem outro SHA256. Mantenha sua instalação atual.");
                }
            }
            long size = manifest.getLong("bytes");
            String expected = manifest.getString("sha256");
            PackageInstaller.SessionParams params = new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
            params.setAppPackageName(TARGET); params.setSize(size);
            if (Build.VERSION.SDK_INT >= 31) params.setRequireUserAction(PackageInstaller.SessionParams.USER_ACTION_REQUIRED);
            id = installer.createSession(params);
            prefs().edit().putInt("session041", id).remove("last_status041").apply();
            write("Preparando a atualização com os pesos do aparelho…");
            try (PackageInstaller.Session session = installer.openSession(id)) {
                MessageDigest working = MessageDigest.getInstance("SHA-256");
                try (OutputStream out = session.openWrite("base.apk", 0, size);
                     ZipInputStream delta = new ZipInputStream(getAssets().open("delta.zip")); ZipFile installed = new ZipFile(base)) {
                    DigestOutputStream signedBytes = new DigestOutputStream(out, working);
                    long copied = 0;
                    JSONArray order = manifest.getJSONArray("segments");
                    for (int i = 0; i < order.length(); i++) {
                        JSONObject segment = order.getJSONObject(i);
                        if (segment.has("reuse")) {
                            ZipEntry source = installed.getEntry(segment.getString("reuse"));
                            MessageDigest hash = MessageDigest.getInstance("SHA-256");
                            if (source == null || source.getSize() != segment.getLong("bytes")) throw new IOException("Pesos instalados incompatíveis.");
                            try (InputStream input = installed.getInputStream(source)) {
                                copied += transfer(input, signedBytes, hash, copied, size);
                            }
                            if (!hex(hash.digest()).equals(segment.getString("sha256"))) throw new IOException("SHA256 dos pesos instalados divergente.");
                        } else {
                            ZipEntry part = delta.getNextEntry();
                            if (part == null || !part.getName().equals(segment.getString("part"))) throw new IOException("Atualização compacta incompleta.");
                            copied += transfer(delta, signedBytes, null, copied, size);
                            delta.closeEntry();
                        }
                    }
                    if (copied != size || !hex(working.digest()).equals(expected)) throw new IOException("SHA256 da atualização divergente.");
                    session.fsync(out);
                }
                if (!Arrays.asList(session.getNames()).contains("base.apk")) throw new IOException("APK ausente na sessão.");
                write("Conferindo o APK gravado no instalador…");
                try (InputStream staged = session.openRead("base.apk")) {
                    MessageDigest verified = MessageDigest.getInstance("SHA-256");
                    if (transfer(staged, null, verified, 0, size) != size || !hex(verified.digest()).equals(expected)) {
                        throw new IOException("SHA256 do APK na sessão divergente.");
                    }
                }
                write("APK 0.6.5 verificado · SHA256 " + expected + "\nConfirme a instalação no Android.");
                Intent callback = new Intent(this, InstallResult.class).setAction("dev.liquidsense.installcheck.UPDATE041").putExtra("session041", id);
                PendingIntent receiver = PendingIntent.getBroadcast(this, id, callback, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_MUTABLE);
                prefs().edit().putBoolean("pending041", true).commit();
                committed = true;
                session.commit(receiver.getIntentSender());
            }
        } catch (Exception error) {
            if (!committed && id >= 0) try { installer.abandonSession(id); } catch (Exception ignored) {}
            if (!committed) prefs().edit().putBoolean("pending041", false).apply();
            write("Falha ao preparar ou instalar a atualização: " + error.getMessage());
        } finally { busy = false; runOnUiThread(this::refresh); }
    }

    private long transfer(InputStream in, OutputStream out, MessageDigest hash, long before, long total) throws IOException {
        byte[] buffer = new byte[BUFFER];
        long count = 0, last = 0;
        for (int n; (n = in.read(buffer)) != -1;) {
            if (out != null) out.write(buffer, 0, n);
            if (hash != null) hash.update(buffer, 0, n);
            count += n;
            if (total > 0 && count - last >= 32L * BUFFER) {
                int percent = (int) Math.min(100, 100 * (before + count) / total);
                runOnUiThread(() -> { if (!destroyed) progress.setProgress(percent); }); last = count;
            }
        }
        return count;
    }

    private static String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder();
        for (byte b : bytes) out.append(String.format(Locale.ROOT, "%02x", b & 255));
        return out.toString();
    }
}
