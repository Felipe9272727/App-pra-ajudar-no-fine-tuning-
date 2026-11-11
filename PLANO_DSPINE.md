# DSpine — viabilidade separada da capacidade

Fontes oficiais consultadas em11/11/2026: Tencent/DSpine e cartão
tencent/Qwen3.8-27B-DSpine-b16. Cópias de consulta e URLs em review013/sources/.
O README identifica um drafter paralelo com Adjacent Causal Injection, código
de treino em SpecForge e inferência SGLang0.5.22/Python3.11+/CUDA. Há também uma
implementação Apple Silicon/MLX, sem aplicação a este executor LinuxCPU.

O cartão reporta2,71x/3,13x/3,84x no throughput Code/Web/Office, em BF16,
FlashAttention3 e concorrência8. São resultados dos autores para outro modelo,
hardware e carga, não medições nossas nem aumento de acurácia/raciocínio.
Comprimento médio de aceitação em HumanEval/MBPP/LCB não equivale a pass@1.

Executor atual: semGPU,8GiBRAM, cotaCPU equivalente a2núcleos, quatro threads
PyTorch e aproximadamente1,7GiB livres em disco na retomada. Um drafter de
aproximadamente2B consome perto de4GB só em BF16, além do nosso target~2GB,
caches, ativações e runtime. Seus pesos não cabem no disco livre. Não há drafter
publicado compatível com o port híbrido Liquid Sense: tokenizer, features,
dimensões, caches por visita e verificação precisam de adaptação e treinamento.

Decisão: não baixar nem integrar esse drafter agora. Não há protótipo DSpine ou
aceleração medida neste estudo. Primeiro resolver aprendizado/qualidade e medir
latência serial real, tokens gerados e tokens/s nos relatórios comparáveis.
Esses números NÃO são TTFT, concorrência8, energia ou throughput de servidor.
Uma trilha futura precisará de drafter muito menor, prova de equivalência da
verificação, perfil de memória e comparação completa incluindo overhead.

CCORE: conferidos o cartão do modelo Apache2.0 e o dataset MIT, revisão
276821245d5714b95571465569ed5b844ac6adc7. A configuração `conversations` tem
3501treinos/417validações, colunas id,title,domain,messages; cada mensagem tem
role,content,reasoning_content. A tentativa inicial config=default retornou404;
config=conversations funcionou e o schema real foi salvo. Também há configurações
previews/meshes. Renderização e validação de GLBs são alegações do mantenedor,
não uma auditoria independente nossa. As árvores públicas consultadas não
continham o pipeline completo executável de treinamento; não o inventamos.
O piloto Python próprio usa a lição de validar artefatos, sem copiar o treino
3D ou afirmar reproduzir o SFT da CCORE.
