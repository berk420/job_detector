@echo off
setlocal EnableDelayedExpansion
title LinkedIn Job Monitor - Browser Mode
color 0A

echo ================================================
echo   LinkedIn Job Monitor - Browser Mode
echo ================================================
echo.

:: Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi.
    pause & exit /b 1
)

:: Sanal ortam
if not exist ".venv\Scripts\activate.bat" (
    echo [*] Sanal ortam olusturuluyor...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

:: Bagimliliklar
echo [*] Bagimliliklar yukleniyor...
pip install -q -r requirements.txt
if errorlevel 1 ( echo [HATA] pip install basarisiz. & pause & exit /b 1 )

:: Playwright browser
echo [*] Playwright Chromium kontrol ediliyor...
playwright install chromium >nul 2>&1

echo.

:: Kimlik bilgileri
if "%LI_EMAIL%"=="" (
    set /p LI_EMAIL="LinkedIn Email: "
)
if "%LI_PASSWORD%"=="" (
    set /p LI_PASSWORD="LinkedIn Sifre: "
)
if "%TELEGRAM_BOT_TOKEN%"=="" (
    set /p TELEGRAM_BOT_TOKEN="Telegram Bot Token: "
)
if "%TELEGRAM_CHAT_ID%"=="" (
    set /p TELEGRAM_CHAT_ID="Telegram Chat ID: "
)

echo.
echo [*] Monitor baslatiliyor...
echo ================================================
echo.

python run_loop.py

echo.
pause
endlocal
