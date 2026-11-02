@echo off
rem SPHEREx Motion Explorer - one-click public URL launcher (no account, no card).
rem Starts the local server + a Cloudflare quick tunnel, then shows the public URL.
title SPHEREx Motion Explorer - public tunnel
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [setup] First run: creating the Python environment...
  python -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements.txt
)

if not exist "cloudflared.exe" (
  echo [setup] Downloading the Cloudflare tunnel client...
  curl -sL -o cloudflared.exe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
)

echo [1/2] Starting the app on http://127.0.0.1:8000 ...
start "SPHEREx server" /min .venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
timeout /t 4 /nobreak >nul

echo [2/2] Opening the public tunnel. Your shareable URL appears below
echo       (it stays valid while this window stays open; a new run gives a new URL).
echo.
"C:\Users\HP\Downloads\cloudflared.exe" tunnel --url http://127.0.0.1:8000 --no-autoupdate
pause
