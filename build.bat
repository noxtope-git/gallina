@echo off
cd /d "%~dp0"
echo ========================================
echo  Compilando Gallina AI - Ejecutable
echo ========================================
echo.

call .venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo activar el entorno virtual .venv
    pause
    exit /b 1
)

echo [1/3] Limpiando builds anteriores...
if exist dist rmdir /s /q dist >nul 2>&1
if exist build rmdir /s /q build >nul 2>&1

echo [2/3] Compilando con PyInstaller (esto puede tardar varios minutos)...
python -m PyInstaller --onefile --console --name gallina main.py --noconfirm
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la compilacion. Revisa los errores arriba.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  COMPILACION EXITOSA
echo ========================================
echo.
echo  El ejecutable se encuentra en:
echo  %~dp0dist\gallina.exe
echo.
echo  Peso aproximado: 2.5 GB (incluye PyTorch + CUDA)
echo.
pause
