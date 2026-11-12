# Liquid Sense — adaptação conjunta balanceada, estudo 016

**Candidata rejeitada por falha na retenção.** O checkpoint geral principal foi preservado.

Partimos do checkpoint 015E íntegro e preservado. Executamos uma candidata de 16 atualizações supervisionadas: 330 tensores e 6.345.904 parâmetros elegíveis, incluindo ganhos do Loop, roteamento mHC, operadores temporais inspirados na Liquid, normalizações e a última projeção MLP. Gradientes percorrem as duas visitas compartilhadas; isso não prova que o loop melhora a qualidade.

| Modelo | Programas ensinados /8 | MBPP observado /8 | Grupos MBPP /24 | Controles /12 | NLL âncoras |
|---|---:|---:|---:|---:|---:|
| Qwen original | 1 | 0 | 2 | 10 | 3.186715643 |
| Principal geral | 1 | 0 | 3 | 10 | 3.183729251 |
| Especialista 015E | 8 | 0 | 0 | 6 | 3.168259660 |
| Candidata 016 | 8 | 0 | 1 | 8 | 3.166700621 |

Os oito programas foram ensinados deliberadamente; pontuação nesse conjunto mede especialização/memorização. O MBPP e os 12 controles são diagnósticos antigos já observados. Baselines anteriores foram reutilizados sem repetir experimentos. Mesma inferência: BF16/eager/cache, greedy, seed 0, thinking=False, quatro threads, 320 tokens de código e 64 para controles. Nenhuma solução/gabarito entra na geração de avaliação.

A candidata recuperou a ordenação Ana/Bia/Caio e o formato exigido para “frio” e “went”. Em contrapartida, perdeu a multiplicação 7 × 8: antes respondia 56, agora 7. A subtração 17 − 5 continuou produzindo 15; plural de animal e tradução em uma única palavra também falharam. São três controles recuperados e um perdido contra E; nenhuma resposta de controle foi ensinada nesta etapa.

O único grupo MBPP novo aprovado não demonstra avanço algorítmico: em MBPP/407 o programa retorna sempre 0. Passa no caso sem próxima permutação porque o assert usa 0 == False, mas falha nos dois casos que exigem construir a permutação. Os testes e a pontuação oficial permanecem intactos; ver mbpp_partial_case_audit.json.

Mudanças reais em relação a E: 298 tensores, 2,815,113 valores; stream `e6e628ad8b82c4ebf2a008b1805163640cbdc75329b173a587d213ebd6923a35`. Todos os 369 tensores congelados preservados, incluindo 153 de visão. Restauração integral verificada pelos hashes dos 546 tensores de texto; 699 tensores finitos. Família de mudanças e cobertura de gradientes constam em summary/training_complete/steps.

Critérios fixados antes dos resultados: 8/8 programas ensinados, pelo menos 10/12 controles sem perder nenhum acerto do principal, nenhuma perda MBPP de E e NLL no máximo igual ao principal + 0,005.

- taught_all8_retained: True
- every_principal_correct_control_retained: False
- at_least10_of12_controls: False
- no_E_mbpp_task_or_test_group_loss: True
- anchor_nll_within_principal_plus_005: True

A auditoria de novidade encontrou quatro controles v1 já existentes em estudos antigos. O conjunto inicial ficou preservado sem uso, e a versão v2 foi registrada antes de qualquer consulta nova; ver NOVELTY_AMENDMENT.md.

A candidata falhou na retenção e foi rejeitada. Os oito problemas novos de programação e oito controles novos ficaram sem consulta pelo modelo. As referências dos oito programas foram verificadas previamente por execução isolada e rejeição de mutantes, o que não constitui avaliação de modelo. Nenhum ajuste adicional usou esses testes.

O ganho médio da segunda visita passou de 0.046107916 para 0.045093243. A direção foi aprendida pela perda conjunta, sem obrigação de aumentar a segunda visita. Isso não demonstra mais pensamento. A projeção FP32 tem raio de 0,5%; a normalização posterior levou três vetores de ganhos a deslocamento relativo final até 0,521908%, conforme weight_audit.json.

A arquitetura mantém 32 camadas físicas e 56 execuções, duas visitas no bloco 4–27, mHC com dois fluxos, convolução de tamanho 7 e janela local 256. Usa dimensões Qwen e operadores inspirados na Liquid, não uma reprodução completa do modelo Liquid AI. Treino conjunto e mudanças internas são fatos mecânicos; benefício causal do loop permanece não demonstrado.

Todos os pesos, logs e relatórios anteriores são preservados. O principal geral continua best.pt com SHA256 `46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8`; 015E continua separado como especialista no conjunto ensinado.

Reprodução: ambiente sem credenciais, offline, quatro threads; restaurar balanced016.restore.load_candidate() verifica a cadeia B→C→E→016. Protocolo, congelamento inicial e configuração registrados no commit 4bb01a00eed3fc19ede62906751d421a4979a680 antes de carregar a candidata. Rastreio da publicação em balanced016/artifact_manifest.json, artifact_verification.json, publication_receipt.json. Nenhum processo de modelo continua entre turnos.
