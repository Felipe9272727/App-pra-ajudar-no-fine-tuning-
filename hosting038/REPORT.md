# Hospedagem e velocidade — pesquisa de16/11/2026

O usuário confirmou que a instalação finalmente funcionou após o reparador0.3.
Isso fecha a pendência de instalação física como sucesso informado pelo usuário.
Não é medição automática de velocidade/qualidade ou confirmação dos bugs de teclado.
Os resultados anteriores permanecem preservados no histórico.

Antes de retomar o treinamento, o usuário perguntou se existe hospedagem gratuita
que deixe o Liquid Sense mais rápido. Não foi feito deploy nem treino nesta etapa.

## Opções verificadas em fontes oficiais

| Serviço | Oferta atual | Limites relevantes |
| --- | --- | --- |
| Hugging Face ZeroGPU | Até2Spaces Gradio em conta pessoal gratuita elegível | E-mail verificado, conta com mais de30dias/em boa situação;5minutosGPU/dia por contaFree; fila compartilhada. Modelo emPyTorch compatível e funções GPU decoradas. Não é GPU dedicada24/7. |
| Modal Starter | $30mensais em créditos de computação | Exige método de pagamento; acima dos créditos há cobrança. CPU/RAM/armazenamento podem consumir orçamento além da GPU. Definir limite de uso/gasto antes de qualquer implantação. Oferece funções e endpoints para código/modelo próprios. |
| Colab gratuito | Recursos para notebooks interativos, com disponibilidade variável | A FAQ restringe usos que contornam o notebook para interação principal viawebUI; não é indicado como backend permanente do app. |

Fontes consultadas:
- https://huggingface.co/docs/hub/spaces-zerogpu — elegibilidade,5min/dia, filas,
  Gradio/PyTorch, GPU temporária e limites. O tempo de GPU não é tempo de sessão
  de chat; fila e rede também entram na espera. Não há garantia de latência.
- https://huggingface.co/docs/hub/spaces-overview — novas SpacesGradio/Docker
  exigem plano pago, com exceçãoZeroGPUpara contas pessoais elegíveis.
- https://modal.com/pricing — Starter$30créditos/mês e custos por recurso.
- https://modal.com/docs/guide/billing — método de pagamento obrigatório.
- https://modal.com/docs/guide/budgets — limites de uso e gastos; o limite padrão
  pode permitir cobrança acima dos créditos. Nada foi contratado/configurado.
- https://research.google.com/colaboratory/faq.html — recursos não garantidos e
  restrições de uso do plano gratuito como serviço externo persistente.

Não confundir armazenar pesos/APKs em GitHub/HFHub com executar inferência emGPU.
Uma VM gratuita apenasCPU não tem ganho garantido sobre o Snapdragon do usuário.
As opções acima não garantem GPU dedicada gratuita e sempre disponível.

## Adequação ao Liquid Sense

O runtime do APK é RustCPU, com32camadas físicas/56execuções, mHC e operadores
temporais. O Cargo existente não inclui backendCUDA. Hospedar esse executável em
máquina comGPU não o torna um programaGPU automaticamente. Há implementações
PyTorch no projeto, mas os caminhos de carga/inferência foram usados emCPU e
contêm alocações específicas de dispositivo; ainda precisam de adaptação e testes.
Não foi demonstrada compatibilidade atual do checkpoint completo comZeroGPU.

O candidato experimental029época2teve divergência conhecida de geração entre
Python e Rust apesar de tensores ativos equivalentes (caso antigo de dividir
listas: Python5/5, Rust1/5). Isso impede prometer qualidade idêntica em uma porta
GPU só porque os pesos são iguais. Ver android_epochs030/README.md.

Hospedagem pode melhorar velocidade de geração se o motor usarGPU corretamente;
não demonstra aumento de inteligência nem corrige sozinho erros de raciocínio.
Fila, inicialização a frio e rede podem reduzir o ganho percebido. Não há medição
online nem comparação com o aparelho nesta etapa; nenhum fator de velocidade é
atribuído ao projeto.

## Próximo trabalho tecnicamente indicado

Primeiro um protótipo isoladoZeroGPU, se a conta atender à elegibilidade, ou
Modal com crédito/limite explícito caso o usuário escolha essa alternativa.
Restaurar o mesmo checkpoint geral selecionado e loop/controladores completos,
com opções experimentais separadas. Não trocar por Qwen original nem eliminar
passagens para parecer mais rápido.

Separar porte e otimização de novos treinos. Comparar prompts/contexto/tokenbudget
iguais, controle de geração, testes de código executáveis e controles gerais,
com diferenças de precisão/backend registradas. Medir tempo até primeiro token,
tokens/s, tempo total, cold/warm e fila/rede; só então integrar modoOnline opcional
no app, mantendoLocal e histórico. Fluxo de ferramentas web/Python deve ter
contrato explícito; não expor chaves de conta noAPK. GPU e publicação só depois
de escolher conta/host e estabelecer limite de custo.

Pedido amplo de melhorar o modelo permanece como objetivo posterior. A frase
“antes de continuar” prioriza esta decisão de hospedagem; não autoriza fingir que
um modelo novo foi treinado ou um endpoint já foi implantado nesta pesquisa.
