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
- [ ] Publicar release inicial `0.1.0`.

## Versao 0.1.1 - Polimento Visual

- [ ] Adicionar animacao (API que vou passar) aos botoes de acao.
- [ ] Suavizar bordas finas principais.
- [ ] Adicionar transparencia aos dropdowns.
- [ ] Revisar suavidade final do fechamento dos dropdowns em ambiente local.
- [ ] Revisar suavidade das bordas finas em ambiente local.
- [ ] Diminuir tamanho minimo da tela, redimensionando escala e/ou espacamento de componentes.
- [ ] testar inverter a cor de fundo pela cor da caixa de resposta e vice-versa.
- [ ] botoes de redirecionamento que levam as paginas de API KEY de cada API,
- [ ] indicador que o Groq é gratuito?

### V0.1.2

- [ ] talvez desativar o hover da caixa resposta, e deixar ele ativo so quando o modelo estiver pensando/carregando, e na v0.2, quando estiver no modo de escrita.
- [ ] adicionar nova janela, na tela de configurações, uma janela que aparece atraves de um botao em cada API e lista os modelos disponiveis, e o usuario pode ativar/desativar uma quantidade maxima, esses selecionados serão os que aparecem no dropdown de modelos ta tela principal.
- [ ] na nova janela de modelos, deve ter algum indicador de qualidade/uso, minhas ideias sao: ou o basico, valor de tokens e de contexto; ou simbolos que representariam tags, seriam simbolos pequenos e simples, provavelmente eu procuraria algum pack de icone online pra isso. Cada simbolo representariam uma tag, e cada modelo teria pelo menos dois simbolos, um referente a qualidade de resposta e o outro referente ao custo. Ao colocar o mouse em cima do simbolo, um hover especifico que vou trazer deve ser ativado com a palavra que define aquela tag, tipo "rapido", "burro", "excelente", etc. Esse processo deve ser feito em etapas de incrementação, criando componentes primeiro, aplicando suas funcionalidades, só depois criar e posicionar na janela.

## Versao 0.2.0 - Chat Minimalista

- [ ] Transformar a caixa de resposta em area editavel quando o usuario clicar/digitar.
- [ ] Trocar `Analisar F2` para `Enviar` quando houver texto manual escrito.
- [ ] Enviar mensagem manual com `Enter`.
- [ ] Exibir a pergunta do usuario no topo da conversa.
- [ ] Exibir resposta do modelo logo abaixo da pergunta.
- [ ] Prefixar mensagens com `>` para indicar inicio de mensagem.
- [ ] Diferenciar visualmente mensagem do usuario com cor discreta.
- [ ] Usar prompt de chat simples, sem o prompt rigido de questao.
- [ ] Orientar o modelo a responder direto, sem bajulacao, sem inventar e avisando incerteza.
- [ ] Permitir chat apenas na ultima pagina/questao do historico.
- [ ] Manter paginas antigas do historico como leitura/copia, sem envio de novas mensagens.
- [ ] Ao criar nova questao, iniciar contexto novo e independente para o modelo.
- [ ] Preservar conversa da pagina anterior apenas como texto navegavel no historico.

## Planos Futuros - Linux

- [ ] Criar camada multiplataforma para armazenamento seguro de chaves.
- [ ] Substituir ou adaptar atalhos globais para Linux.
- [ ] Adaptar captura de tela/clipboard para ambientes Linux e Wayland/X11.
- [ ] Criar script de build Linux separado, gerado no proprio Linux.
- [ ] Validar empacotamento Linux com PyInstaller ou alternativa equivalente.
