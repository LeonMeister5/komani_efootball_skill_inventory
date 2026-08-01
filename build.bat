@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    set "BUILD_PYTHON=.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [错误] 未找到 Python。
        pause
        exit /b 1
    )
    set "BUILD_PYTHON=python"
)
"%BUILD_PYTHON%" -m PyInstaller --version >nul 2>nul
if errorlevel 1 "%BUILD_PYTHON%" -m pip install pyinstaller
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
"%BUILD_PYTHON%" -m PyInstaller --noconfirm --clean --noconsole --name "实况足球技能仓库" --collect-all customtkinter main.py
if errorlevel 1 (
    echo [错误] 构建失败。
    pause
    exit /b 1
)
echo 构建完成：%CD%\dist\实况足球技能仓库\实况足球技能仓库.exe
pause
endlocal

