@echo off
setlocal
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo Ambiente ausente. Execute scripts\setup.ps1 primeiro.
  pause
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0ai-farm-agent\main.py"
if errorlevel 1 pause
