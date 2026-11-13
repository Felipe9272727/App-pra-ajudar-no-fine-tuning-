# Artefatos nativos e recuperação

`rust_manifest.json` descreve os binários finais0.4, comprimidos em zlib.
Os arquivos `before_eos_fix_*` preservam os binários intermediários anteriores
à correção de parada. Seu manifesto copiado é o original histórico; para abri-los,
use os nomes com prefixo `before_eos_fix_`, preservando os hashes registrados.

`prior_tools023/manifest.json` registra a reconstrução SHA-256 exata do APK0.3
assinado. Restaure para um caminho NOVO usando o comando do manifesto. O corpo
neural é referenciado pelo arquivo deduplicado022e seus backings imutáveis;
eles não podem ser removidos. Prefixo e sufixo incluem tudo necessário à
assinatura original. Não substitua esses bytes por uma nova assinatura.

O intérprete Python ARM64 final é reutilizado do artefato023, sem alterações
de runtime nesta atualização. Não há chaves de assinatura nem tokens Gofile
dentro desta pasta ou do APK.
