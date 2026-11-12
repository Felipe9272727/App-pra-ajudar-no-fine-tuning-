Chat offline do Liquid Sense, com motor de inferência em Rust e interface nativa Android.
O modelo de texto acompanha o APK: não há download adicional de pesos, API externa ou permissão de internet.

ARM64, Android 9 ou mais recente. Preparado para teste no Snapdragon 7s Gen 2 com16GB de RAM. O APK tem aproximadamente1,61GB; reserve cerca de4GB de armazenamento para download e instalação.

Usa os546tensores de texto do checkpoint geral preservado, em BF16 com auxiliares FP32, sem quantização. Mantém32camadas físicas,56execuções, duas visitas do loop, mHC e os operadores temporais inspirados na Liquid. A visão não faz parte deste chat de texto.

Há histórico local, nova conversa, seleção/cópia de texto e botão Parar. A execução usa quatro threads de CPU; o tempo de resposta depende do aparelho e do tamanho da conversa. Contexto máximo2048tokens e respostas de até192tokens na interface.

Esta é uma prévia experimental assinada. Foram verificados compilação, assinatura, payloads dos pesos, tokenizer, operadores e geração real no host. Ainda não houve execução deste APK em Android físico ou emulador. O port tem diferenças numéricas em relação ao PyTorch e não representa uma melhoria de inteligência ou dos pesos. Não houve promoção das candidatas rejeitadas.

O certificado desta prévia é gerado durante a compilação; outra compilação pode exigir desinstalar a anterior. A conversa fica apenas no armazenamento privado do app; desinstalar remove esse histórico.
