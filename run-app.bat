@echo off
title WhatsApp Chatbot RAG - Asia Visual Grafika

echo ============================================================
echo   WhatsApp Chatbot RAG - Asia Visual Grafika
echo   Auto-start: FastAPI + Ngrok (WhatsApp Fonnte)
echo ============================================================

set "ROOT=%~dp0"
set "ENV_FILE=%ROOT%.env"

echo [1/3] Membersihkan port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 "') do taskkill /PID %%a /F >nul 2>&1
timeout /t 1 /nobreak >nul

echo [2/3] Menjalankan FastAPI (port 8000)...
cd /d "%ROOT%"
start "FastAPI" cmd /k "title FastAPI && venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"

echo   Menunggu FastAPI siap...
timeout /t 5 /nobreak >nul

echo [3/3] Memeriksa konfigurasi ngrok...
set "NGROK_DOMAIN="
if not exist "%ENV_FILE%" goto RUN_DYNAMIC_NGROK

:: Ambil domain jika ada
for /f "tokens=2 delims==" %%i in ('findstr /I "NGROK_DOMAIN=" "%ENV_FILE%"') do set "NGROK_DOMAIN=%%i"

if "%NGROK_DOMAIN%"=="" goto RUN_DYNAMIC_NGROK

:RUN_STATIC_NGROK
echo [3/3] Menjalankan ngrok dengan static domain: %NGROK_DOMAIN%
start "Ngrok" cmd /k "title Ngrok && ngrok http --domain=%NGROK_DOMAIN% 8000"
goto DONE

:RUN_DYNAMIC_NGROK
echo [3/3] Menjalankan ngrok (dynamic URL)...
start "Ngrok" cmd /k "title Ngrok && ngrok http 8000"

:DONE
echo.
echo ============================================================
echo   ✅ WhatsApp Chatbot RAG Aktif!
echo   FastAPI   : http://localhost:8000
echo   Webhook   : https://%NGROK_DOMAIN%/chat/whatsapp
echo ============================================================
pause
