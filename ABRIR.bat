@echo off
REM Abre o Contas TikTok (auto-atualizavel) SEM terminal, via launcher.
set "PW=%LOCALAPPDATA%\Python\pythoncore-3.14-64\pythonw.exe"
if not exist "%PW%" set "PW=pythonw"
start "" "%PW%" "%~dp0launcher.py"
