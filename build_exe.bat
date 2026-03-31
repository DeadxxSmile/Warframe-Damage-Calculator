@echo off
setlocal

cd /d "%~dp0"

echo [1/3] Creating fresh virtual environment is optional but recommended.
echo [2/3] Installing build dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :fail

echo [3/3] Building WDC with PyInstaller...
pyinstaller --clean --noconfirm WDC.spec
if errorlevel 1 goto :fail

echo.
echo Build complete.
echo EXE folder: %CD%\dist\WDC
exit /b 0

:fail
echo.
echo Build failed.
exit /b 1
