# PRAQ

Pra Responder Atividade Quieto

É uma aplicacao desktop para auxiliar respostas de questoes de multipla escolha com modelos de IA. A interface foi desenhada para uso rapido: selecionar API/modelo, enviar texto selecionado por atalho e navegar por um historico leve da sessao.


## Recursos

- Suporte a Groq para analise de texto.
- Suporte a Gemini para texto e imagens.
- Atalhos para capturar texto selecionado e prints.
- Historico temporario de ate 10 respostas.
- Configuracao local de chaves Gemini e Groq.
- Chaves protegidas no Windows via DPAPI, fora do `config.json`.

## Requisitos

- Windows 10 ou superior.
- Python 3.12 recomendado para rodar pelo codigo-fonte.
- Chave API Gemini e/ou Groq.

## Rodar pelo codigo-fonte

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe PRAQ.py
```

Tambem e possivel usar `PRAQ.bat` ou `PRAQ.vbs` depois que o ambiente virtual estiver configurado.

## Configurar chaves

Abra a tela de configuracoes pelo icone de engrenagem e informe as chaves de API. O aplicativo nao grava chaves no `config.json`; elas sao salvas localmente com protecao do usuario do Windows.

## Gerar build Windows

O build usa PyInstaller em modo executavel unico.

```powershell
.\scripts\build.ps1
```

O executavel esperado sera gerado em:

```text
dist\PRAQ.exe
```

Para validar e limpar saidas sem gerar executavel:

```powershell
.\scripts\build.ps1 -CleanOnly
```

## Versao

Versao atual: `0.1.0`.

## Observacao sobre Linux

A versao `0.1.0` e focada em Windows. A interface PySide6 e portavel em parte, mas armazenamento seguro de chaves, atalhos globais, captura de tela e scripts de inicializacao precisam de adaptacao para Linux.
