SET BINPATH=%~dp0
set VENV_DIR=%BINPATH%..\venv\Scripts
%VENV_DIR%\python %BINPATH%..\main.py %1 %2 %3 %4
RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters