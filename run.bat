@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    set "APP_PYTHON=.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [错误] 未找到 Python。请安装 Python 3.12 或创建 .venv。
        pause
        exit /b 1
    )
    set "APP_PYTHON=python"
)
"%APP_PYTHON%" main.py
if errorlevel 1 pause
endlocal

