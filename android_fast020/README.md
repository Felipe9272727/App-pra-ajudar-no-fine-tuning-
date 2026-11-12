# Liquid Sense Rápido — prévia0.1.1

APK pronto, ARM64/Android9+,1.613.898.825bytes (~1,61GB), com o MESMO modelo
geral BF16 integrado. Download público: https://gofile.io/d/j7WqfPBY .
SHA2563a8eab346270899706671c04bf900f0061fc713b798baf768c079063fa793bef.

Instala separadamente como “Liquid Sense Rápido”, aplicativo
`dev.liquidsense.chat.fast`. A prévia anterior e seu histórico permanecem no
aplicativo antigo. A chave antiga não estava preservada; esta versão tem nova
chave privada local, mantida para futuras atualizações, sem publicação.

Núcleo Rust019 ativado: DeltaNet com ordem numérica preservada, gates constantes,
cache de prefixo exato e atalho para matrizes comprovadamente nulas. Mesmas
32camadas físicas/56execuções, mHC2, conv7/window256. Mesmo tokenizer, identidade,
contexto2048e geração192tokens/semthinking da versão anterior. Nenhum download
de pesos após instalar e nenhuma permissão INTERNET. A interface mostra tempo
de preparação e tokens/s; a seleção base/especialista permanece para depois.
O checkpoint de treino018foi REJEITADO e não entrou neste APK.

Medição019no servidor:1,1633x throughput do backbone,14,04%menos tempo,12pares;
8testes técnicos,16tokens com todos os estados/logits/caches idênticos e3conversas
com26tokens iguais. Esse é resultadoCPUx86, não medição no seu Snapdragon nem
velocidade garantida do app completo. APK foi compilado paraARM64, mas não
executado em aparelho/emulador nesta sessão. Os contadores permitem obter a
medição real no dispositivo. Pensamento longo continua sem ganho demonstrado.

Verificações reais: assinatura válida, ELFARM64/segmentos16KB, zipalign4/16KB,
atividade/classeR/JNI consistentes, hashes de TODAS as assets idênticos aoAPK
original, incluindo pacote de pesos SHA256
6c774a434438add704b1993b8e013493fb95bc9802c4d9b30227832115c07288.
Tamanho eMD5 do retornoGofile conferidos contra o arquivo local; páginaHTTP200.
Não foi repetido o download completo remoto nem se afirma execução no telefone.

Fontes em native/ e android/. tools/build_native.sh recompila comRust1.90e
sysrootAndroidAPI28; tools/build_apk.py monta o APK copiando assets do original,
sem exportar de novo os pesos. Chaves/credenciais/respostas privadas ficam fora
do repositório. Os dois APKs assinados permanecem em /dev/shm/liquid-android;
dist/contém apenas um atalho local, não um segundo arquivo de1,6GB noGit.
