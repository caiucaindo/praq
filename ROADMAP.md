# ROADMAP - PRAQ

## Analise e Base

- [X] Auditar estrutura principal do projeto.
- [X] Ler `DESIGN_BASE.md`.
- [X] Conferir assets de logo, icone e referencia de interface.
- [X] Identificar referencias antigas de nome.
- [X] Identificar risco de chaves API em texto puro.

## Identidade e Organizacao

- [X] Padronizar nome visual para PRAQ.
- [X] Atualizar scripts de inicializacao e comentarios antigos.
- [X] Manter compatibilidade com o entrypoint atual.
- [X] Organizar responsabilidades entre UI, backend e configuracao.

## Configuracoes e Seguranca

- [X] Remover chaves API do `config.json`.
- [X] Criar armazenamento local protegido para segredos.
- [X] Criar tela de configuracoes para Gemini e Groq.
- [X] Mascarar campos sensiveis e permitir salvar/limpar chaves.
- [X] Bloquear chamadas de API quando a chave do provedor nao estiver configurada.

## Front-end

- [X] Refazer interface conforme `DESIGN_BASE.md`.
- [X] Aplicar logo PRAQ no topo conforme referencia visual.
- [X] Adicionar botao de configuracoes.
- [X] Corrigir referencia visual: remover moldura/barra interna da imagem exemplo.
- [X] Trocar texto do botao de configuracoes por icone de engrenagem.
- [X] Aumentar flexibilidade para telas grandes e fullscreen com limites saudaveis.
- [X] Aprimorar estados hover/pressed dos botoes.
- [X] Expandir layout horizontal para formato mais proximo de software de chat.
- [X] Corrigir travamento horizontal causado por alinhamento central usando `sizeHint`.
- [X] Definir abertura padrao no tamanho minimo da janela.
- [X] Remover container externo dos dropdowns.
- [X] Ajustar popup dos dropdowns para combinar com a interface.
- [X] Remover foco clicavel da caixa de resposta, mantendo apenas hover.
- [X] Adicionar hover visual na area de resposta e nos dropdowns.
- [X] Substituir engrenagem textual por icone SVG integrado ao design.
- [X] Remover card externo e label da area de resposta.
- [X] Remover divisao falsa dos dropdowns e restaurar seta visual unica.
- [X] Corrigir contorno pontilhado/foco visual nos botoes.
- [X] Criar navegacao entre tela principal e configuracoes.
- [X] Concentrar componentes para nao abrirem demais em telas grandes.
- [X] Limitar a area de resposta com largura/altura controladas.
- [X] Ajustar estados visuais para Groq e Gemini.
- [X] Aplicar o mesmo padrao base na tela de configuracoes.
- [X] Reorganizar tela de configuracoes com titulo centralizado e acoes agrupadas.
- [X] Adicionar estados visuais para chave pronta e chave invalida.
- [X] Mover mensagens de feedback para entre formulario e acoes.
- [X] Mover aviso de seguranca para o rodape da tela de configuracoes.

## Validacao

- [X] Validar sintaxe Python.
- [X] Validar inicializacao basica da UI.
- [X] Revisar referencias antigas restantes.

## Versao 0.1.0

- [X] Adicionar historico leve de respostas da sessao.
- [X] Limitar historico a 10 respostas, descartando a mais antiga ao adicionar a 11.
- [X] Apagar historico ao fechar a aplicacao.
- [X] Permitir navegar entre respostas com setas anterior/proxima.
- [X] Manter paginas antigas somente para leitura/copia.
- [X] Adicionar botao minimalista para excluir a resposta atual.
- [X] Corrigir animacao de abrir e fechar dropdowns.
- [X] Tornar possivel copiar texto da tela de resposta.
- [X] Corrigir comportamente de abertura e fechamento dos dropdown, deve ter uma animacao suave ao abrir, vindo de cima pra baixo, e ao fechar, encolher os itens de baixo pra cima.
- [X] Refinar fechamento dos dropdowns com recorte de conteudo e opacidade.
- [X] Fazer smoke test manual com Gemini, Groq, historico e configuracoes.
- [X] Aumentar ligeiramente o X do historico.
- [X] Ajustar engrenagem levemente para a direita.
- [X] Corrigir hover da caixa de resposta ao passar sobre X/setas.
- [X] Revisar assets finais de logo/icone da janela.
- [X] Criar `README.md` com proposta, uso, requisitos e configuracao de chaves.
- [X] Definir versao `0.1.0` nos metadados/scripts de build.
- [X] Preparar build distribuivel.
- [X] Criar repositorio remoto.
- [X] Publicar release inicial `0.1.0`.

## Versao 1.1 - Polimento Visual

- [X] Corrigir distancia dos botoes de acao quando a area de resposta atinge a altura maxima.
- [X] Remover zonas mortas entre opcoes dos dropdowns.
- [ ] Corrigir erros ortograficos em todos os textos.
- [ ] Analisar textos e mensagens pensando em opcoes melhores.
- [ ] Adicionar botoes de redirecionamento para paginas de API key de cada API.
- [ ] Adicionar indicador discreto de que o Groq tem uso gratuito.
- [ ] Revisar suavidade final do fechamento dos dropdowns em ambiente local.
- [ ] Suavizar bordas finas principais.
- [ ] Revisar suavidade das bordas finas em ambiente local.
- [ ] Diminuir tamanho minimo da tela, redimensionando escala e/ou espacamento de componentes.
- [ ] Diminuir espaçamento/distanciamento maximo, na janela cheia ta tudo muito grande
- [ ] Testar inverter a cor de fundo pela cor da caixa de resposta e vice-versa.
- [ ] Adicionar transparencia aos dropdowns.
- [ ] Adicionar animacao (API que vou passar) aos botoes de acao.
- [ ] Avaliar migracao do front para TypeScript para melhorar design, elementos e animacoes.

## Versao 1.2 - Modelos e Flexibilidade

- [ ] Testar prompt mais flexivel para questoes que nao sejam de multipla escolha.
- [ ] Talvez desativar o hover da caixa de resposta, deixando ativo so quando o modelo estiver pensando/carregando e, na v0.2, quando estiver no modo de escrita.
- [ ] Definir formato de configuracao para modelos ativados/desativados por API.
- [ ] Criar componentes base da janela de modelos na tela de configuracoes.
- [ ] Listar modelos disponiveis por API em modo somente leitura na janela.
- [ ] Permitir ativar/desativar modelos com limite maximo de selecionados.
- [ ] Aplicar modelos selecionados no dropdown de modelos da tela principal.
- [ ] Adicionar indicadores simples de contexto, custo e qualidade dos modelos.
- [ ] Evoluir indicadores para icones/tags com tooltip especifico.

## Versao 2.0 - Chat Minimalista

- [ ] Definir estrutura interna de conversa por pagina do historico.
- [ ] Transformar a caixa de resposta em area editavel quando o usuario clicar/digitar.
- [ ] Permitir chat apenas na ultima pagina/questao do historico.
- [ ] Trocar `Analisar F2` para `Enviar` quando houver texto manual escrito.
- [ ] Enviar mensagem manual com `Enter`.
- [ ] Usar prompt de chat simples, sem o prompt rigido de questao.
- [ ] Orientar o modelo a responder direto, sem bajulacao, sem inventar e avisando incerteza.
- [ ] Exibir a pergunta do usuario no topo da conversa.
- [ ] Exibir resposta do modelo logo abaixo da pergunta.
- [ ] Diferenciar visualmente mensagem do usuario com cor discreta.
- [ ] Prefixar mensagens com `>` para indicar inicio de mensagem.
- [ ] Ao criar nova questao, iniciar contexto novo e independente para o modelo.
- [ ] Manter paginas antigas do historico como leitura/copia, sem envio de novas mensagens.
- [ ] Preservar conversa da pagina anterior apenas como texto navegavel no historico.

## Planos Futuros - Linux

- [ ] Criar camada multiplataforma para armazenamento seguro de chaves.
- [ ] Substituir ou adaptar atalhos globais para Linux.
- [ ] Adaptar captura de tela/clipboard para ambientes Linux e Wayland/X11.
- [ ] Criar script de build Linux separado, gerado no proprio Linux.
- [ ] Validar empacotamento Linux com PyInstaller ou alternativa equivalente.
