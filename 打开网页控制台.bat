@echo off
chcp 65001 >nul

set "PYTHON3=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
set "SCRIPT_DIR=%~dp0"
set "PORT=8765"
set "URL=http://127.0.0.1:%PORT%/"

REM Check if server is already running
powershell -Command "try { $r = Invoke-WebRequest -Uri '%URL%' -TimeoutSec 2 -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% == 0 (
    echo Console is already running at %URL%
    start "" "%URL%"
    goto :end
)

echo Starting benchmark verification console at %URL% ...

if exist "%PYTHON3%" (
    "%PYTHON3%" -m verification_console.server --port %PORT% --open-browser
) else (
    python -m verification_console.server --port %PORT% --open-browser
)

:end
pause
