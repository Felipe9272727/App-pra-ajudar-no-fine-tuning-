# liquid sense 0.8 b LOOP

Nome nominal da base: 0,8B. Híbrido ampliado: aproximadamente 1,02B parâmetros carregados.

Novo piloto baseado em referências públicas de pesquisa automatizada: [LAB_METHODS.md](LAB_METHODS.md). SenseNova e componentes inspirados na Liquid devem permanecer ativos nas novas candidatas.

## Primeiro piloto concluído

Código, estado retomável, patch de calibração e seis rodadas reais salvos. Nenhuma das seis candidatas de RSI venceu o critério de desenvolvimento; o checkpoint foi preservado.

| Teste novo, 24 perguntas | Acertos |
|---|---:|
| Qwen original | 17/24 |
| Loop adaptado preservado | 18/24 |
| Loop + componentes inspirados no LFM3, experimental | 19/24 |

A vantagem de duas perguntas é limitada e não prova melhora geral. A variante experimental permanece registrada, sem promoção com base no teste. Consulte [PILOT_REPORT.md](PILOT_REPORT.md) para todas as respostas e decisões. Estado atual: piloto concluído e pausado no checkpoint.


Experimento de Felipe. O assistente ChatGPT Work controla os ciclos: propõe
uma alteração, escreve valores diretamente nos pesos, mede o resultado e
aceita ou rejeita a candidata. A IA pequena também produz sugestões reais,
registradas sem correção em cada rodada. A escolha executada é identificada
como decisão do assistente; não inventamos uma proposta da IA quando ela falha.

Isso é uma pesquisa de melhoria guiada com feedback. Não é demonstração de
autoaperfeiçoamento recursivo geral, consciência da arquitetura ou crescimento
ilimitado de inteligência. O estado real está em `rsi/status.json`.

## Modelo e alterações

- Base pública: `Qwen/Qwen3.5-0.8B`, revisão fixa no manifesto.
- Núcleo SenseNova: 32 camadas físicas, bloco [4,28) visitado duas vezes,
  56 execuções, mHC de duas vias. Dimensões menores do Qwen preservadas.
- Controle por visita: divide a contribuição residual entre primeira e
  segunda passagem. Na inicialização conservadora, duas sondas tiveram logits
  idênticos aos do Qwen original.
- LFM3: inspiração na convolução curta de sete posições e na atenção local
  de 256 tokens. Mantemos Gated DeltaNet do Qwen; não é a arquitetura completa
  ou os pesos treinados do LFM3.
- Ajuste dos pesos de convolução por regressão ridge fechada, regularizada
  pelo original, usando ativações em oito textos. Zero backward passes.
- A adaptação é aprendida por dados e feedback. Não é correto chamá-la de
  processo totalmente sem aprendizagem só por não usar gradientes.

O arquivo `v2_adaptation/closed_form_fit.json` registra os coeficientes
efetivamente alterados. Os pesos de entrada e os conhecimentos do LFM3 não
foram transplantados entre espaços latentes incompatíveis.

## Persistência e retomada

`checkpoints/liquid_patch.pt` guarda exatamente os pequenos tensores ajustados
(carregar com `weights_only=True`). `checkpoints/incumbent.json` registra o
modelo base, revisão, receita de cirurgia e hash do patch. Juntos com o código,
permitem reconstruir o mesmo checkpoint sem versionar gigabytes de pesos base.
`rsi/round_*.json` preserva proposta, sugestão real da IA, métrica, decisão e
estado. As gravações locais usam arquivos temporários, fsync e troca atômica.
O GitHub preserva os checkpoints confirmados; o campo `pending` ajuda a detectar
uma rodada interrompida. Não repita uma rodada finalizada.

Os arquivos `data_v2.json` separam oito textos de calibração, oito problemas
de desenvolvimento e 24 testes novos. Somente desenvolvimento decide promoção.
O teste reservado é executado depois de congelar o estado e nunca escolhe pesos.

## Executar

Instale primeiro PyTorch CPU e dependências:

```bash
pip install torch==2.15.0+cpu --index-url https://download.pytorch.org/whl/cpu
pip install transformers==5.22.1 accelerate==1.15.0 safetensors==0.8.0 numpy
python download_model.py
python build_sensenova_port.py
```

Para reconstruir os ajustes algébricos desde o início, em vez do patch salvo:

```bash
python v2_adaptation/experiment.py teacher
python v2_adaptation/experiment.py adapt
```

Uma rodada é executada pelo controlador com uma receita explícita, por exemplo:

```bash
python rsi_cycle.py --round 1 --gain 0.05 --beta 0.025 --liquid-mix 0 --reason "Dividir a contribuição entre camadas originais e inseridas"
```

A numeração precisa coincidir com o checkpoint atual; use `rsi/status.json`.
Uma candidata só é promovida se reduzir a NLL média de desenvolvimento em mais
de 0,0001. Isso não garante melhora em perguntas novas. Sugestões do modelo são
dados para inspeção, não comandos que serão executados automaticamente.

O experimento roda em CPU durante a sessão. Este repositório não promete um
serviço de treinamento permanente nem dispara gastos ou APIs pagas.

## Fontes e licenças

Qwen e código SenseNova são Apache-2.0, conforme seus repositórios. A licença
e o aviso de atribuição estão incluídos. O LFM3 serve como referência de desenho:

- https://huggingface.co/Qwen/Qwen3.5-0.8B
- https://github.com/OpenSenseNova/SenseNova-Loop
- https://www.liquid.ai/blog/lfm3
- https://arxiv.org/abs/1511.05641 — transformações que preservam a função
- https://arxiv.org/abs/2605.23872 — amortecimento de computação em loops

As adaptações específicas deste repositório são experimentais. Resultados e
limitações devem ser lidos antes de alegar que o modelo melhorou.
