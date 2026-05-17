@echo off
title KAIROS // INSTALL
cd /d "%~dp0"

echo.
echo  =========================================
echo   KAIROS // CONTROL  -  installer
echo  =========================================
echo.

REM Caminho do Python instalado
set PYTHON_EXE=C:\Users\Matheus\AppData\Local\Python\bin\python.exe

REM Verifica se existe
if not exist "%PYTHON_EXE%" (
    echo  ERRO: Python nao encontrado em:
    echo  %PYTHON_EXE%
    echo.
    pause
    exit /b 1
)

echo  Python encontrado:
"%PYTHON_EXE%" --version
echo.

echo  Atualizando pip...
"%PYTHON_EXE%" -m pip install --upgrade pip

echo.
echo  Instalando dependencias (pode demorar alguns minutos)...
"%PYTHON_EXE%" -m pip install -r requirements.txt

echo.
echo  =========================================
echo   Instalacao completa!
echo  =========================================
echo.
echo  Agora execute start.bat para iniciar.
echo.
pause
