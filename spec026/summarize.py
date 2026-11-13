"""Summarize the completed fixed pilot; never drive training or selection."""
import json
from pathlib import Path
from io_parts import save_json

H = Path(__file__).resolve().parent


def read(path):
    return json.loads((H / path).read_text())


def main():
    scores = {}
    for variant in ['target', 'small_initial', 'small_trained', 'large_initial', 'large_trained']:
        r = read(f'reports/quality_{variant}.json')
        assert r['status'] == 'complete'
        scores[variant] = {k: r[k] for k in ['code_tasks', 'code_cases', 'code_cases_total', 'general_correct']}
        scores[variant]['code_truncated_at_budget'] = sum(x['tokens'] == 96 and x['ids'][-1] not in {248044, 248046} for x in r['code'])
    children = {}
    for size in ['small', 'large']:
        r = read(f'reports/training_{size}.json')
        backward = read(f'reports/backward_{size}.json')
        children[size] = {
            'parameters': r['architecture']['unique_parameters'],
            'epochs': r['epochs'],
            'optimizer_steps': r['optimizer_steps'],
            'training_tokens': r['training_tokens'],
            'initial_preflight_NLL': backward['loss'],
            'online_training_NLL_by_epoch': r['epochs_online_NLL'],
            'changed_parameter_tensors': r['changed_parameter_tensors'],
            'eligible_parameter_tensors': r['all_eligible_parameter_tensors'],
            'inference_compressed_bytes': r['inference_compressed_bytes'],
            'pretrained_teacher_tensors_copied': 0,
            'all_finite': r['all_finite'],
        }
    speed = read('reports/speed_summary.json')
    assert speed['status'] == 'complete'
    summary = {
        'status': 'complete_experimental_pilot_no_target_promotion',
        'children': children,
        'standalone_quality': scores,
        'speculative_cpu_results': speed['models'],
        'target_weights_changed': False,
        'android_apk_changed': False,
        'limitations': [
            '192 conversations, 13644 unique next-token labels; bounded pilot, not corpus-scale pretraining',
            'Teacher output traces are behavior examples, not verified solutions',
            '8 custom code tasks and 8 general questions do not measure general intelligence',
            'Fixed short greedy CPU requests; no stochastic-decoding or Android speed claim',
            'Finite exact token agreement is not a universal numerical equivalence proof',
            'Minimum useful drafter size and speed at mature pretraining remain unknown',
        ],
    }
    save_json(H / 'summary.json', summary)
    lines = [
        '# Spec026 — pequenos modelos híbridos criados do zero', '',
        'Experimento concluído. O Liquid Sense principal e o APK continuam com os pesos anteriores.', '',
        'Os dois filhos receberam pesos aleatórios novos, sem copiar tensores do professor. '
        'Compartilham o tokenizer/vocabulário; preservam 32 camadas físicas, 56 visitas, '
        'loop 4–27 duas vezes, mHC de dois fluxos, mistura GatedDeltaNet/atenção e conv7. '
        'São versões de texto com larguras menores da arquitetura experimental do projeto, '
        'sem reivindicar reprodução oficial dos modelos SenseNova ou Liquid AI.', '',
        'Treino: 192 conversas, 13.644 rótulos únicos, três épocas, 40.932 exposições a tokens '
        'e 162 atualizações por tamanho. Adafactor, parâmetros mestres FP32, cálculo BF16/recorrência FP32. '
        'As 24 sequências reais do professor são exemplos de comportamento e não gabaritos verificados. '
        'Os checkpoints FP32 inicial/final, estado do otimizador e versões BF16 para inferência estão preservados.', '',
        '| Modelo | Parâmetros | Tensores alterados | NLL inicial | NLL online da última época |',
        '|---|---:|---:|---:|---:|',
    ]
    for size, r in children.items():
        lines.append(f"| {size} | {r['parameters']:,} | {r['changed_parameter_tensors']}/{r['eligible_parameter_tensors']} | {r['initial_preflight_NLL']:.3f} | {r['online_training_NLL_by_epoch'][-1]['mean_online_train_nll']:.3f} |")
    lines += ['', 'A NLL acima é de treino e não mede generalização.', '',
              '| Modelo | Programas corretos /8 | Casos /43 | Geral /8 |', '|---|---:|---:|---:|']
    for name, r in scores.items():
        lines.append(f"| {name} | {r['code_tasks']} | {r['code_cases']} | {r['general_correct']} |")
    lines += ['', 'Os testes novos usam os mesmos prompts, greedy e limites: 96 tokens para código e 32 para geral. '
              'Nenhuma solução é entregue no prompt. São testes pequenos próprios, sem comparação com grandes modelos públicos.', '',
              '| Rascunhador | Propostas aceitas | Razão de velocidade¹ | Tokens finais iguais | p pareado² |',
              '|---|---:|---:|---|---:|']
    for size, r in speed['models'].items():
        lines.append(f"| {size} | {r['accepted']}/{r['proposed']} ({100*r['acceptance']:.2f}%) | {r['speed_ratio_total']:.3f}× | {r['all_target_token_streams_identical']} | {r['paired_sign_flip_p_two_sided']:.5f} |")
    lines += ['', '¹ Tempo total sem especulação / tempo total com especulação. Abaixo de 1× significa mais lento. '
              'Seis pares fixos por filho, ordem ABBA, três prefixes, orçamento de 32 tokens. '
              'Modelos residentes: tokenização, prefill, rascunhos, verificações, snapshots, rollback, '
              'correções e decodificação incluídos; carga dos pesos separada. Tempos de CPU x86, quota de dois CPUs e quatro threads; '
              'não são medições do Snapdragon ou do APK.', '',
              '² Teste de inversão de sinais dos seis pares, bilateral, descritivo neste piloto curto. '
              'Resultados de diferenças numéricas nos tokens tornam a via inelegível como aceleração equivalente.', '',
              'A verificação em bloco usa recorrência temporal sequencial nos estados em cache; '
              'rejeições restauram todos os 56 estados e repetem o prefixo aceito. '
              'As sondas de paridade e os testes sintéticos não provam equivalência universal. '
              'A capacidade individual dos filhos é medida separadamente da aceitação pelo professor.', '',
              'Este piloto não estabelece o menor tamanho útil, inteligência geral ou velocidade após pré-treino amplo. '
              'Uma continuação precisa de muito mais dados de pré-treino/distilação e novos testes reservados, '
              'sem reutilizar estes resultados para ajustar e reavaliar no mesmo conjunto.', '',
              'Fontes e protocolo: [PROTOCOL.md](PROTOCOL.md), [config.json](config.json), [frozen.json](frozen.json). '
              'Resultados brutos: [reports/](reports/), [logs/](logs/). '
              'Pesos e metadados: [checkpoints/](checkpoints/). '
              'O alvo continua identificado pelo SHA256 `46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`.', '']
    (H / 'REPORT.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
