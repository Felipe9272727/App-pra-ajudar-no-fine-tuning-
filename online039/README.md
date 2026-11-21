# Liquid Sense em ZeroGPU

O protótipo recupera o pacote de texto BF16 do APK 0.6.3 pelo SHA256. A carga confere
os 546 tensores e o plano de 32 camadas físicas com 56 execuções. O runtime inclui
os controladores mHC, a convolução temporal de largura 7 e as janelas de 256.

[Space Liquid Sense GPU](https://huggingface.co/spaces/Felipe0282829273/liquid-sense-gpu)

## Resultado do teste publicado

O Space passou na chamada real em `cuda:0`. Inicialmente, a GPU demorou cerca de
22,2 s para gerar os 64 tokens do teste de código. A revisão que pré-calcula as
saídas de 48 roteadores mHC reduziu a média de duas chamadas para 5,0 s de
inferência e de 22,6 s para 5,3 s de chamada completa. Esses roteadores têm matrizes
de entrada zeradas no pacote publicado. Os pesos, os valores de roteamento e as
56 execuções foram preservados. Todos os tokens coincidiram com a referência CPU
nos testes observados. A espera de fila e rede variou mais nas chamadas curtas.

Com limite de 160 tokens, a função terminou em 88 tokens e passou os 3 casos, com
saída idêntica entre CPU e GPU. O teste de 64 tokens terminou antes da função em
ambos. `reports/deployment.json` registra os commits e médias. Os relatórios por
chamada preservam os tempos e as saídas. Os resultados se limitam à amostra medida
no servidor. A integração Android depende da comparação com o motor Rust do APK.

O chat experimental aceita uma mensagem por vez e oferece thinking com orçamento
de até 512 tokens. O teste mede o tempo interno até a geração do primeiro token,
a velocidade de decodificação e o tempo total da requisição. Hoje a interface
apresenta a resposta quando a geração termina.

A referência CPU e o teste local do Gradio ficam em `reports/`. A porta PyTorch
produziu os mesmos tokens nos dois testes locais. A aritmética passou. O teste de
código consumiu os 64 tokens antes de concluir a função e passou 0 de 3 casos.
Esses testes curtos servem para comparar runtimes. Para medir qualidade e avançar
com o seletor Online/Local no Android, é necessária uma comparação maior com o
motor Rust do app e com orçamentos compatíveis com o uso real.

`space/` contém tudo que vai para o Space. O bootstrap recupera o pacote original
e verifica os hashes do release e do tokenizer. Na primeira inicialização, pode
baixar cerca de 2 GB no servidor. A GPU é alocada pelo ZeroGPU a cada chamada.
Consulte a [documentação do ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu)
para a cota de uso e condições da conta.

`deploy.py` usa a sessão Hugging Face ativa e cria um novo Space em ZeroGPU. O
script recusa sobrescrever uma repo existente. `compare_space.py` chama o endpoint
do Space e compara a sequência de tokens com a referência de CPU, usando os mesmos
prompts e limites. O avaliador local executa somente o código do teste em seu
processo isolado. O Space oferece geração de texto.
