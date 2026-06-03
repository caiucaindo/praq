# Prompt de Design

Use este guia para aplicar um visual semelhante ao do caiucaindo/pqp em outro projeto.

## Direcao Visual

Crie uma interface desktop/web app escura, utilitaria e elegante, com foco em ferramentas de produtividade. O visual deve parecer uma aplicacao de trabalho moderna, nao uma landing page. Priorize densidade moderada, leitura rapida, botoes claros e areas de trabalho funcionais.

## Paleta

- Fundo principal: quase preto, em torno de `#09090b` / zinc-950.
- Superficies: `#18181b` / zinc-900, com variacoes em `#27272a` / zinc-800.
- Bordas: `#27272a` a `#3f3f46`, discretas.
- Texto principal: zinc-100 / zinc-200.
- Texto secundario: zinc-400 / zinc-500.
- Destaque primario: indigo, especialmente `indigo-600` para acoes e estados ativos.
- Destaques por funcao:
  - Editor: emerald-600.
  - Mesclar: indigo-600.
  - Separar: amber-600.

Evite fundos brancos ou cinzas muito claros em overlays. Em uma interface escura, overlays de drag/drop devem usar fundo escuro translucido, como `bg-indigo-950/65`, borda dashed indigo e texto claro.

## Layout

- Use app shell direto, sem hero marketing.
- Header superior fixo/sticky com blur leve, borda inferior sutil e altura compacta.
- Botao voltar no canto esquerdo, com titulo alinhado ao conteudo principal da tela.
- Conteudo principal com largura maxima fluida: centralizado em telas grandes, mas respeitando uma margem minima para nao conflitar com o botao voltar.
- Cards e caixas de upload com raio moderado, no maximo `rounded-2xl` para dropzones e `rounded-lg` para itens.
- Evite cards dentro de cards. Ferramentas repetidas podem ser cards; secoes da pagina devem ser layouts simples.

## Componentes

### Botoes

- Use botoes compactos, com icone quando possivel.
- Acoes principais usam cor da tela: emerald/indigo/amber.
- Acoes destrutivas usam vermelho apenas em hover ou estados sutis.
- Botoes fantasmas devem ser discretos: texto zinc-400, hover para a cor da funcao.

### Dropzones

- Fundo zinc-900, borda dashed zinc-700.
- Hover: borda zinc-600 e leve aumento de contraste no fundo.
- Durante drag: borda na cor da funcao e fundo translucido da mesma cor, por exemplo `bg-indigo-500/10`.
- A area que aceita arquivos pode ser a tela inteira, mas o indicador visual deve continuar centralizado na zona de upload ou area de trabalho.

### Switches

- Evite switch ligado branco em tema escuro.
- Estado desligado: zinc/input escuro.
- Estado ligado: `indigo-600`.
- Thumb: zinc-100.

### Camadas/Listas

- Lista compacta com itens em zinc-900/zinc-800.
- Item selecionado: fundo `indigo-500/15`, borda `indigo-500/30`, texto `indigo-200`.
- Itens ocultos ou desativados podem usar `opacity-55`.
- Reordenacao deve funcionar por botoes pequenos e tambem drag-and-drop quando fizer sentido.

## Tipografia

- Use fonte sans-serif de sistema.
- Titulos de tela: `text-lg font-semibold`, sem exagero.
- Labels de grupos: `text-xs uppercase tracking-wider text-zinc-500`.
- Textos auxiliares: `text-sm text-zinc-500`.
- Evite letter spacing negativo.

## Interacao

- Prefira feedback minimalista: borda, opacidade, cor de icone e hover.
- Overlays devem ser escuros, translucidos e coerentes com o tema.
- Acoes de arquivo devem prevenir o comportamento padrao do navegador ao arrastar PDFs.
- Em ferramentas com canvas/documento, a area de trabalho deve poder rolar internamente sem aumentar a pagina inteira.

## Exemplo de Tailwind

```tsx
<div className="min-h-screen bg-background text-foreground font-sans">
  <header className="sticky top-0 z-10 h-14 border-b border-zinc-800 backdrop-blur">
    <div className="h-full flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="rounded-lg bg-indigo-600 p-1.5">
          <Icon className="h-5 w-5 text-white" />
        </div>
        <h1 className="text-lg font-semibold tracking-tight">Titulo</h1>
      </div>
    </div>
  </header>

  <main className="mx-auto max-w-3xl px-4 py-8">
    <div className="rounded-2xl border-2 border-dashed border-zinc-700 bg-zinc-900 p-8 text-center transition-colors hover:border-zinc-600 hover:bg-zinc-800/60">
      <p className="text-base font-medium text-zinc-200">Arraste arquivos ou clique para escolher</p>
      <p className="mt-1 text-sm text-zinc-500">Texto auxiliar</p>
    </div>
  </main>
</div>
```
