@echo off
chcp 65001 >nul
if "%1"=="hidden" goto :run_hidden

REM First run: relaunch hidden
set "script_path=%~dp0"
set "script_name=%~nx0"
powershell -WindowStyle Hidden -Command "Start-Process '%~f0' -ArgumentList 'hidden' -WindowStyle Hidden"
exit

:run_hidden
REM Hidden run: execute Python
set "PYTHON3=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
set "SCRIPT_DIR=%~dp0"

if exist "%PYTHON3%" (
    "%PYTHON3%" "%SCRIPT_DIR%benchmark_gui.py"
) else (
    python "%SCRIPT_DIR%benchmark_gui.py"
)
