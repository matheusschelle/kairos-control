@echo off
title KAIROS // CONTROL
cd /d "%~dp0"

echo.
echo  =========================================
echo   KAIROS // CONTROL  -  starting bridge
echo  =========================================
echo.

REM Caminho do Python instalado
set PYTHON_EXE=C:\Users\Matheus\AppData\Local\Python\bin\python.exe

if not exist "%PYTHON_EXE%" (
    echo  ERRO: Python nao encontrado!
    echo  Rode install.bat primeiro.
    echo.
    pause
    exit /b 1
)

if not exist "server.py" (
    echo  ERRO: server.py nao encontrado!
    echo.
    pause
    exit /b 1
)

start "KAIROS BRIDGE" cmd /k ""%PYTHON_EXE%" server.py"

timeout /t 3 /nobreak >nul

start "" "http://localhost:8000"

echo.
echo  Dashboard:  http://localhost:8000
echo.
echo  Para parar tudo, feche a janela BRIDGE.
echo.
pause
