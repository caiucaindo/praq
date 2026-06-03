@echo off
REM Script para executar a aplicacao PRAQ com o ambiente virtual ativado

REM Ativa o ambiente virtual
call .\.venv\Scripts\activate.bat

REM Executa o script Python
python PRAQ.py

REM Se houver erro, mantem a janela aberta para ver a mensagem
pause
