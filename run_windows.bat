@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
 echo Python launcher was not found. Install Python 3.11 or 3.12 from python.org.
 pause
 exit /b 1
)
if not exist .venv (
 py -3.12 -m venv .venv 2>nul
 if errorlevel 1 py -3.11 -m venv .venv
)
if not exist .venv\Scripts\activate.bat (
 echo Python 3.11 or 3.12 could not be found.
 pause
 exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 (
 echo Package installation failed. Check your internet connection and Python version.
 pause
 exit /b 1
)
start "" http://127.0.0.1:8000
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
endlocal
