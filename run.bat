@echo off
setlocal
cd /d "%~dp0"

where uv >nul 2>nul
if errorlevel 1 (
  echo uv not found. Install uv from https://github.com/astral-sh/uv then run again.
  echo You can also install Python and run: pip install uv
  pause
  exit /b 1
)

uv run python app.py
