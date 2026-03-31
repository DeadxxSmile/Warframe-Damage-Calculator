@echo off
setlocal

cd /d "%~dp0"

set "ISCC_DEFAULT=C:\Users\%USERNAME%\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_DEFAULT=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_DEFAULT=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if not exist "%CD%\dist\WDC\WDC.exe" (
    echo PyInstaller output not found. Building EXE first...
    call build_exe.bat
    if errorlevel 1 goto :fail
)

if not exist "%ISCC_DEFAULT%" (
    echo Inno Setup compiler was not found automatically.
    echo Edit build_installer.bat and set ISCC_DEFAULT to your ISCC.exe path.
    exit /b 1
)

echo Building installer with Inno Setup...
"%ISCC_DEFAULT%" installer\WDC.iss
if errorlevel 1 goto :fail

echo.
echo Installer build complete.
echo Output folder: %CD%\installer_output
exit /b 0

:fail
echo.
echo Installer build failed.
exit /b 1
