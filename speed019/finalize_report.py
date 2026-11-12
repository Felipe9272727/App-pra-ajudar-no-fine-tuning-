"""Finalize only after all fixed tests; preserve original results."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'speed019'
def main():
 s=json.loads((HERE/'reports/summary.json').read_text());assert s['fixed_pairs']==12 and s['all16_trace_steps_bit_identical'] and s['all56_cache_slots_preserved'];assert 'test result: ok. 8 passed' in (HERE/'reports/unit_tests.log').read_text()
 for p,h in json.loads((HERE/'frozen.json').read_text()).items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 old=json.loads((ROOT/'speed017/reports/confirmation_summary.json').read_text());binary=Path('/dev/shm/liquid-android/prebuilt/speed019/bench');(HERE/'reports/host_binary.json').write_text(json.dumps({'path':str(binary),'bytes':binary.stat().st_size,'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'rust':'1.90.0','target':'x86_64','android_binary_built':False},indent=2)+'\n')
 evidence='O critério estatístico registrado foi satisfeito neste protocolo de CPU.' if s['confirmed_cloud_cpu_benefit'] else 'O critério estatístico registrado NÃO foi satisfeito; não declarar benefício confirmado.'
 report=f'''# Speed019 — multiplicações por zero verificadas

Protótipo de runtime, sem treinamento nem alteração de pesos. Durante o
carregamento, verifica quais matrizes BF16 contêm somente zeros positivos ou
negativos. Em AVX2/NEON, para entrada finita, o produto retorna o mesmo +0 da
redução SIMD de referência. Outros casos mantêm o caminho original. Foram
verificadas16matrizes/46.137.344valores; todas as32camadas físicas e56visitas
continuam executando seus operadores, convoluções, estados e merges. O atalho
é somente a multiplicação de matriz comprovadamente nula, sem remover camadas.

Oito testes técnicos passaram. No traço de16tokens, as912saídas de estágio,
896slots de cache e3.973.120logits ficaram bit a bit iguais; houve512atalhos
(32por token). Três conversas produziram os mesmos26tokens, textos e términos.
Isso inclui segunda mensagem com cache e uma troca de prefixo. A equivalência
é evidência no conjunto verificado, não uma prova para todo input/CPU ARM.

Uma repetição fixa de12pares ABBA, três processos, quatro threads, CPUx86:
referência{s['reference_mean_seconds']:.6f}s/16tokens, otimizado{s['optimized_mean_seconds']:.6f}s,
razão{s['mean_ratio']:.4f}x; redução de tempo{s['time_reduction_fraction']*100:.2f}%.
IC95%da diferença emparelhada[{s['paired_95_ci'][0]:.6f},{s['paired_95_ci'][1]:.6f}]s;
teste exato de permutação de sinais bilateral p={s['exact_sign_flip_two_sided_p']:.8f}.
{evidence}

Todos os12pares foram incluídos, sem repetição ou parada por significância.
Os métodos de intervalo/permutação usam a simetria/intercambialidade dos pares;
a ordem ABBA balanceia deriva e as observações são da mesma máquina. Isso não
é medida em Snapdragon, de concorrência móvel ou do aplicativo completo.
O escopo é o backbone por16tokens, sem projeção do vocabulário/tokenização.

A razão acima inclui TODAS as otimizações, contra o caminho de referência no
mesmo binário. Não multiplicar pela razão017({old['mean_ratio']:.4f}x em sua
repetição independente). 017continua preservado, com4pares exploratórios e
12confirmatórios. A economia de prefixo em segunda mensagem é separada:
6,04→2,68segundos em uma observação017, mesma resposta, não estimativa global.

O APK0.1.0já instalado permanece preservado. Este estudo fornece fontes e um
executável de teste no servidor; não produziu um novo APK/compilação ARM ou
medição no telefone. A integração móvel e o seletor base/especialista continuam
registrados em speed017/MODEL_SELECTOR_BACKLOG.md. Nenhum novo checkpoint foi
promovido por um ganho de desempenho de runtime.
'''
 (HERE/'REPORT.md').write_text(report);(HERE/'status.json').write_text(json.dumps({'status':'completed_exact_host_prototype','model_process_active':False,'weights_changed':False,'checkpoint_promoted':False,'android_apk_updated':False,'confirmed_cloud_cpu_benefit':s['confirmed_cloud_cpu_benefit']},indent=2)+'\n')
 print(json.dumps({k:s[k] for k in ['mean_ratio','time_reduction_fraction','confirmed_cloud_cpu_benefit']}))
if __name__=='__main__':main()
