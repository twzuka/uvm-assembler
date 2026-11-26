@echo off
setlocal
cd /d "%~dp0"
if defined PYTHON (
    "%PYTHON%" -B -m src.uvm %*
) else (
    python -B -m src.uvm %*
)
exit /b %errorlevel%
