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

## Versao 1.1 - Nova Interface Web e Polimento Visual

### Decisao Tecnica e Linha de Base

- [X] Corrigir distancia dos botoes de acao quando a area de resposta atinge a altura maxima na interface atual.
- [X] Remover zonas mortas entre opcoes dos dropdowns na interface atual.
- [X] Registrar a linha de base local da interface PySide6: abertura em 4,62 s, 131,1 MB em uso e executavel de 66,1 MB.
- [ ] Medir o tempo ate a primeira resposta com APIs reais antes da troca definitiva.
- [X] Adotar React, TypeScript e Vite para a interface, embarcados em `pywebview` com WebView2.
- [X] Manter Python como backend nativo para DPAPI, hotkeys, clipboard, screenshots e clientes Gemini/Groq.
- [X] Manter a interface PySide6 utilizavel ate a nova interface atingir paridade funcional e passar pelos criterios de aceite.

### Refatoracao do Backend Antes da Troca de Interface

- [X] Extrair de `MainWindow` um servico de aplicacao independente de UI para configuracao, provider/modelo ativo, processamento, historico e captura.
- [ ] Remover `QThread` e `Signal` do backend, substituindo-os por concorrencia Python com estado protegido, eventos e encerramento limitado por timeout.
- [X] Definir uma unica politica para requisicoes simultaneas, impedindo duplicidade por hotkeys e resultados fora de ordem.
- [X] Associar cada operacao a um identificador e a um snapshot de provider/modelo para que trocas na interface nao alterem requisicoes em andamento.
- [X] Definir uma bridge minima e tipada entre TypeScript e Python para comandos, estados, resultados e erros.
- [X] Garantir que chaves descriptografadas e imagens capturadas nunca sejam retornadas ao frontend, gravadas em logs ou armazenadas no navegador.
- [X] Preservar o formato atual de `%APPDATA%\PRAQ\secrets.json` para manter compatibilidade com as chaves DPAPI existentes.

### Fundacao Visual

- [ ] Criar tokens centralizados de cor, tipografia, espacamento, borda, raio, foco, elevacao e movimento.
- [X] Aplicar app shell escuro e utilitario baseado em zinc-950/zinc-900 com destaque indigo, contraste forte e densidade moderada.
- [X] Criar header compacto com identidade PRAQ, status discreto e acesso claro a configuracoes.
- [X] Substituir a titlebar do Windows por uma barra integrada com arraste, resize pelas bordas e maximizacao limitada a area de trabalho.
- [X] Usar uma area de trabalho ampla, sem cards aninhados, sombras pesadas, gradientes decorativos ou espacos excessivos em fullscreen.
- [ ] Criar componentes reutilizaveis para botoes, selects, campos secretos, status, tooltips, dialogs, toasts e atalhos.
- [ ] Usar icones consistentes e alvos interativos de pelo menos 40 x 40 px, preservando os assets finais de logo e icone.

### Paridade Funcional Obrigatoria

- [ ] Recriar os seletores de API e modelo com popup moderno, selecao clara, fechamento suave e suporte completo a mouse e teclado.
- [X] Recriar a area de resposta somente leitura, copiavel, com scroll interno, largura/altura controladas e estados de hover, foco e processamento.
- [X] Preservar Groq como padrao, texto via F2 e ocultar sem deixar espacos mortos as acoes F8/F9 indisponiveis no Groq.
- [X] Preservar Gemini para texto, print unico e print com scroll pelas acoes visuais e hotkeys F2/F8/F9.
- [X] Preservar historico temporario de ate 10 respostas, navegacao anterior/proxima, exclusao atual e controles corretamente desabilitados nos limites.
- [X] Recriar a tela de configuracoes com navegacao de ida/volta, campos mascarados, validacao, estados pronto/invalido e feedback entre formulario e acoes.
- [X] Confirmar internamente limpeza e substituicao de chaves sem usar dialogs genericos do Windows.
- [X] Preservar salvamento e limpeza de chaves por DPAPI e manter o aviso de protecao local no rodape.
- [X] Preservar responsividade, concentracao do conteudo em telas grandes, abertura em tamanho minimo e layout sem overflow externo.
- [X] Equalizar as acoes Gemini e expandir a acao Groq junto com a area de resposta.

### Experiencia, Acessibilidade e Movimento

- [ ] Modelar estados explicitos de inicializacao, sem chave, carregamento de modelos, captura, envio, analise, sucesso, resposta vazia, erro recuperavel e erro fatal.
- [X] Manter a resposta anterior visivel durante novo processamento e apresentar progresso sem deslocamentos abruptos de layout.
- [ ] Exibir erros com causa, impacto e uma acao recuperavel como configurar chave, tentar novamente ou trocar modelo.
- [X] Separar o nome das acoes de seus atalhos, exibindo F2/F8/F9 em badges discretos.
- [X] Implementar navegacao completa por teclado, ordem de tab previsivel, foco visivel e textos acessiveis para controles com icone.
- [ ] Nao depender apenas de cor para status e respeitar contraste, escala de texto do Windows e `prefers-reduced-motion`.
- [X] Aplicar transicoes funcionais de 100-220 ms em telas, status, selects e botoes, sem animacoes que atrasem a operacao.
- [ ] Integrar a animacao de botoes que sera fornecida, adaptando-a ao tema e desativando-a com movimento reduzido.

### Polimento de Conteudo e Layout

- [ ] Corrigir erros ortograficos e revisar todos os textos, labels, tooltips, mensagens e chamadas para acao.
- [X] Adicionar links seguros para as paginas oficiais de criacao das chaves Gemini e Groq.
- [ ] Adicionar indicador discreto de disponibilidade gratuita do Groq sem competir com a acao principal.
- [X] Definir o tamanho minimo em 640 x 598 mantendo legibilidade, scroll interno e controles acessiveis.
- [X] Limitar largura e espacamentos em telas grandes para evitar que a interface fique dispersa.
- [ ] Comparar fundo principal e superficie da resposta nas duas combinacoes propostas e manter a de melhor hierarquia e contraste.
- [ ] Avaliar transparencia leve nos dropdowns somente se nao prejudicar contraste, leitura ou desempenho.
- [ ] Suavizar bordas finas e validar o resultado no WebView2 em diferentes escalas de DPI.

### Performance, Seguranca e Distribuicao

- [X] Carregar apenas o bundle local de producao do Vite, com CSP restritiva, origem validada, navegacao externa bloqueada e DevTools desabilitado no build final.
- [ ] Exigir o runtime WebView2 (`edgechromium`) e apresentar recuperacao clara se ele nao estiver disponivel, sem fallback para MSHTML.
- [ ] Comparar `onefile` e `onedir` e adotar o formato com melhor abertura e menor incidencia de bloqueio por antivirus; priorizar instalador unico com app `onedir` interno.
- [X] Criar build web separado que compila o frontend antes do PyInstaller e impede a inclusao acidental de PySide6/PyQt, sem substituir o build estavel.
- [X] Preservar `config.json`, assets, metadados de versao e dados de `%APPDATA%\PRAQ` no executavel web.
- [ ] Adicionar logs locais sem segredos e garantir que hotkeys, threads e processos sejam encerrados mesmo durante requisicoes lentas.
- [ ] Remover PySide6, `ui.py` e o empacotamento Qt somente depois da aprovacao da nova interface e da paridade completa.

### Validacao e Criterios de Aceite

- [X] Adicionar testes unitarios para configuracao, estado, chaves e limite do historico e manter typecheck no build Vite.
- [X] Gerar `dist\PRAQ-Web.exe` e confirmar abertura responsiva do WebView2 sem remover `dist\PRAQ.exe`.
- [ ] Validar build limpo no Windows 10 e 11 sem Python ou Node instalados e com usuario sem privilegios administrativos.
- [ ] Testar F2/F8/F9, repeticao rapida, troca de provider/modelo durante requisicao, ausencia de internet, rate limit e fechamento durante processamento.
- [ ] Testar clipboard de texto e outros formatos, multiplos monitores e escalas de DPI de 100%, 125%, 150% e 200%.
- [ ] Validar Gemini e Groq com chave ausente, valida, invalida, arquivo DPAPI corrompido e chave criada pela versao anterior.
- [ ] Garantir funcionamento sem mouse, foco previsivel, status anunciaveis e animacoes reduzidas quando solicitado pelo sistema.
- [X] Garantir ausencia de overflow externo em 640 x 598; apenas a resposta e configuracoes podem rolar internamente.
- [ ] Confirmar historico de no maximo 10 itens, estados corretos dos controles e nenhuma regressao dos requisitos de frontend ja concluidos.
- [X] Comparar o prototipo com a linha de base: abertura em 3,43 s, 139,4 MB em uso e executavel de 32,8 MB; validar APIs reais antes da decisao final.
- [ ] Realizar smoke test final do executavel/instalador e aprovar visualmente a nova interface antes de remover a implementacao PySide6.

## Versao 1.2 - Modelos e Flexibilidade

- [ ] Testar prompt mais flexivel para questoes que nao sejam de multipla escolha.
- [ ] Talvez desativar o hover da caixa de resposta, deixando ativo so quando o modelo estiver pensando/carregando e, na v0.2, quando estiver no modo de escrita.
- [ ] Adicionar API Cerebras Inference
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
