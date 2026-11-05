"""Render completed measured results; never edits candidate construction/golds."""
from pathlib import Path
import json,collections
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent

def read(n):return json.loads((HERE/n).read_text())
def main():
 audit=read('audit_complete.json');comparison=read('screen_comparison.json');unloaded=read('unloaded_weights.json')
 assert len(comparison['candidates'])==3
 reports={v:read('screen_'+v+'.json') for v in ['original','parent','depth','liquid','routed']}
 assert all(r['status']=='complete' for r in reports.values())
 rows=[]
 labels={'original':'Qwen original','parent':'Liquid Sense preservado','depth':'A: profundidade ativa','liquid':'B: A + calibração temporal','routed':'C: B + roteamento condicional'}
 for v,r in reports.items():
  rows.append(f"| {labels[v]} | {r['cases_passed']}/{r['total_cases']} | {r['tasks_passed']}/7 | {sum(x['hit_limit'] for x in r['rows'])}/7 |")
 candrows=[]
 for v in ['depth','liquid','routed']:
  m=read('checkpoint_'+v+'.json');s=comparison['candidates'][v];arch=m['architecture']
  candrows.append(f"| {v} | {m['actual_changed_tensors']} | {m['actual_changed_values']:,} | {len(arch['neutral_layers'])} | {arch['input_dependent_routers']}/48 | {s['wins']} | {s['losses']} |")
 caps='\n'.join(rows);candidates='\n'.join(candrows)
 objective=read('temporal_objective.json');probe=read('stream_probe.json')
 doc=f'''# Varredura integral e adaptação nativa 010 — 2026-11-05

O estudo terminou. Nenhuma das três variantes passou a triagem registrada antes
das gerações. O checkpoint anterior foi preservado, com SHA256
`46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`.
Os candidatos permanecem arquivados como experimentos reproduzíveis.
Não houve backward, gradientes, otimizador convencional ou solução correta
inserida nas entradas do modelo. Nenhum gabarito ou avaliador foi alterado.

## O que Python examinou

Foram percorridos todos os **1.020.252.592 valores em 699 tensores únicos** do
híbrido realmente carregado, depois da aplicação de best.pt, mais quatro buffers
com 96 valores. O alias lm_head/input embedding foi contado uma vez. Não houve
NaN ou infinito. O inventário registra forma, dtype, hash dos bytes, zeros,
sinais, distribuição de magnitudes, mínimo/máximo, média, desvio, RMS e L2.
Para 373 tensores matriciais há normas completas de todas as linhas/colunas e
seis iterações de potência sobre a matriz inteira: diagnóstico espectral
**aproximado**, sem alegação de SVD exata. Nenhum escalar foi amostrado nas
estatísticas integrais de integridade/distribuição ou diferenças de origem.

A comparação com os doadores Qwen percorreu 1.019.465.728 valores compatíveis.
52 tensores diferem dos arquivos de origem: 16 projetores zerados
(46.137.344 valores), 12 kernels temporais (440.792) e 24 normas gated RMS
(2.721 valores com arredondamento FP32→BF16, também usado no original carregado).
Esses arredondamentos não são apresentados como aprendizado.

O rastreio de acessos reais a armazenamento observou 546 parâmetros no prefill
de texto e em um passo de próximo token próprio. Os 153 não observados são do
encoder visual, como esperado nesse teste de texto. Todos os 100.592.896 pesos
visuais foram inspecionados; não foi feito benchmark de visão.

O arquivo Qwen ainda contém **15 tensores MTP, com 20.452.864 valores**, que
não são instanciados pelo runtime autoregressivo original nem pelo híbrido.
Todos foram escaneados separadamente, sem não finitos, e estão intactos no
scaffold. Isso explica original bruto 873.438.784 versus original carregado
852.985.920 parâmetros. MTP é previsão de múltiplos tokens; esse inventário não
identifica um suposto módulo de pensamento ausente. Os dois arquivos grandes
foram novamente verificados por SHA256, sem sobrescrevê-los.

## Diagnóstico e hipótese

O modelo preservado já usa 32 camadas físicas, 56 execuções, bloco [4,28)
compartilhado em duas passagens, mHC de dois streams, convoluções de sete taps
e janelas locais. Entretanto, as camadas 8–11 e 20–23 estão neutralizadas por
seus dois projetores de saída zerados. Elas contêm 166.410.320 parâmetros,
a neutralização decorre dos projetores de saída, deixando os demais pesos
pré-treinados desses blocos sem contribuição efetiva para o resultado. Os 48 pesos de entrada dos roteadores
mHC são zero, mantendo roteamento constante. Isso era uma inicialização
conservadora, e não corrupção dos pesos.

As estatísticas não atribuem causalidade exclusiva a um peso por erro de
programação. O experimento intervém em grupos arquiteturais identificados,
mede o comportamento resultante e rejeita regressões.

A restaurou os oito blocos a partir dos respectivos doadores, copiando os
kernels temporais completos antes de alterar os doadores. Repartiu a
contribuição de cada doador original entre suas cópias e duas visitas por
fatores exatos 1/4 ou 1/2 nos projetores, com gains [1,1]. A soma dos
coeficientes por doador é um; essa igualdade é apenas de primeira ordem,
pois os blocos não lineares não comutam. Todas as 32 camadas passaram a
contribuir para a saída, preservando número de parâmetros e 56 execuções.

B ajustou os 24 kernels com sistemas de ridge de sete coeficientes por canal,
usando ativações em 19 textos/enunciados já observados, sem respostas.
Alvos eram preativações numéricas internas do Qwen, armazenadas em BF16;
nenhum programa de referência foi gerado. Limite antes da quantização: 5% da
norma do canal; maior variação escrita após BF16: 5,36%. O MSE médio dos
sinais de calibração caiu de {objective['mean_layer_mse_before']:.9f} para
{objective['mean_layer_mse_after']:.9f} ({objective['relative_calibration_mse_reduction']*100:.2f}%).
Esse ajuste interno não foi tratado como ganho em tarefas ou generalização.

C acrescentou uma inicialização de rank um para roteamento dependente da
entrada, usando a diferença entre as ativações da primeira e segunda visita.
As linhas pareadas preservam soma dos gates pre=1, post=2 e mistura
aproximadamente duplamente estocástica. Os 48 roteadores passaram a ter pesos
de entrada não zero. No diagnóstico com contexto sem respostas, houve gates
post distintos em {probe['routers_with_observed_conditional_post_gates']}/48 roteadores e separação observada dos streams
em {probe['routers_with_observed_stream_separation']}/48, com diferença absoluta máxima {probe['maximum_stream_difference']:.7f}.
Isso prova uma mudança funcional no mecanismo, sem provar melhor raciocínio.
A_log/dt_bias foram analisados e preservados por falta de hipótese causal
específica que justificasse alterá-los.

| Variante | Tensores alterados | Valores alterados vs parent | Camadas neutras | Roteadores condicionais | Casos ganhos vs parent | Casos perdidos vs parent |
|---|---:|---:|---:|---:|---:|---:|
{candidates}

## Comparação efetivamente executada

Sete tarefas de desenvolvimento já observadas, 36 casos, mesma tokenização,
mesmo contexto por problema, greedy, thinking desativado, 160 tokens novos,
BF16 e quatro threads em CPU. Os programas foram avaliados no mesmo sandbox
sem credenciais, com limites de recursos e seccomp. Os casos esperados só
entram no avaliador, depois da geração; não entram no contexto dos modelos.

| Modelo | Casos corretos | Tarefas completas | Gerações no limite de tokens |
|---|---:|---:|---:|
{caps}

As referências foram geradas novamente. O parent reproduziu byte por byte
as saídas e os bits de avaliação anteriores nas sete tarefas. O Qwen
reproduziu 27/36 e 5/7. Não houve amostragem aleatória nessa comparação.
Os casos de uma tarefa não são amostras independentes de inteligência geral;
o conjunto é pequeno e observado, portanto não sustenta alegação de
superioridade geral. O critério registrado de retenção exige não perder
nenhum caso previamente correto, além de ganho estrito.

As mudanças amplas introduziram repetição, erros de código e muitas gerações
que atingiram o limite. Os três componentes foram congelados antes das suas
avaliações; nenhum foi reajustado após os resultados. A intervenção A combina
restauração, redistribuição de contribuição e uma janela adicional, portanto
não isola qual dessas mudanças causou cada erro. B e C são ablações fixas,
não etapas promovidas para o modelo principal.

Nenhuma variante se qualificou para desenvolvimento completo de 16 tarefas,
quatro controles e 12 âncoras NLL. Esses testes adicionais não foram executados
para candidatos já reprovados. As oito tarefas RSI100 de validação independente
continuam sem uso. Os controles e a capacidade do checkpoint escolhido
permanecem os da versão anterior, porque seus pesos não mudaram. Não foi
relatado ganho de linguagem ou generalização para os candidatos novos.

## O que foi realmente salvo

Os três checkpoints são **bundles incrementais completos e determinísticos**:
parent imutável + receita de cópia/escala + overlays temporais/roteadores +
hashes de todos os tensores tocados. Não são arquivos safetensors monolíticos.
Cada um foi reconstruído após carregar o parent do zero e verificado bit a bit.
Todos passaram em testes de cache prefill/decode a 17,257,513 tokens, incluindo
o limite da janela: mesmo top token, maior diferença de logits entre 0,125
e 0,3515625, abaixo do limite registrado 0,5. Isso valida somente essas sondas.
55 testes técnicos passaram. O pacote inclui o código, entradas, estatísticas,
saídas completas, decisões e ativações de construção, estas em nove partes
ZIP concatenáveis com hashes por parte, arquivo e membro.

**Carregamento correto:** `native010.reload.load_candidate("routed")`, ou
`python native010/reload.py routed`, no ambiente de quatro threads. O loader
confere fontes, parent, overlays e cada tensor antes/depois. Não chamar o
loader legado sozinho para reconstruir os candidatos: ele restaura a
inicialização antiga e neutraliza novamente os oito blocos. Preparação dos
ativos segue `download_model.py` e `build_sensenova_port.py`, com a revisão
Qwen fixada no projeto. `python native010/restore_activations.py` restaura e
verifica as observações arquivadas; não é necessário recalibrar para recarregar
os checkpoints. Não repetir estudos concluídos.

Arquivos de consulta: `native010/audit_complete.json`, `parameters.jsonl`,
`row_column_norms.pt`, `unloaded_weights.json`, `NATIVE_PROTOCOL.md`,
`checkpoint_*.json`, `technical_*.json`, `screen_*.json`, `screen_comparison.json`,
`selection.json`, `activation_archive.json` e `artifact_integrity.json`.

## Relação com as arquiteturas oficiais

O plano 32/56, [4,28) duas vezes e mHC com dois streams coincide com a
configuração oficial do SenseNova Loop consultada. A largura continua Qwen
1024, não os 4096 do SenseNova 9B. O LFM3-1.7B oficial usa largura 2048,
24 camadas (13 conv, cinco atenções locais e seis globais); nosso DeltaNet
continua uma adaptação inspirada, não uma reprodução do LFM3. Mudar pesos
não transforma um bloco DeltaNet nesse outro operador.

As configurações oficiais foram preservadas com revisões imutáveis em
`native010/official/sources.json`. A lista oficial de benchmarks Liquid AI
inclui LiveCodeBench v6/Pro25Q2, SciCode, IFEval, SWE-bench, Terminal-Bench e
outros registrados em `benchmark_inventory.json`. O piloto público anterior
do projeto permanece arquivado e observado; não foi renomeado como teste
novo nem comparado diretamente a números de fornecedores com protocolos
diferentes. Nenhum modelo maior foi executado nesta rodada. Portanto ainda
não há demonstração de que Liquid Sense supera modelos maiores.

Fontes: [SenseNova Loop](https://huggingface.co/sensenova/SenseNova-Loop-9B-Preview)
e [LFM3-1.7B](https://huggingface.co/LiquidAI/LFM3-1.7B).

O resultado permite rejeitar esta inicialização algébrica como melhoria. Não
permite concluir que uma arquitetura Loop/Liquid bem adaptada seja inferior.
O objetivo arquitetural permanece no projeto; a versão principal não recebeu
as mudanças que pioraram a avaliação. Não há processo de melhoria prometido
em segundo plano após o encerramento da sessão.
'''
 (ROOT/'NATIVE_ARCHITECTURE_REPORT.md').write_text(doc)
 print('Completed report written.')
if __name__=='__main__':main()
