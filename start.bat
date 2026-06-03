@echo off
setlocal EnableDelayedExpansion
title Job Detector - Monitor
color 0A

echo ================================================
echo   Job Detector - Is Ilanlari Monitoru
echo ================================================
echo.

:: Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi. Lutfen Python 3.11+ yukleyin.
    pause & exit /b 1
)

:: Sanal ortam yoksa olustur
if not exist ".venv\Scripts\activate.bat" (
    echo [*] Sanal ortam olusturuluyor...
    python -m venv .venv
    if errorlevel 1 ( echo [HATA] Sanal ortam olusturulamadi. & pause & exit /b 1 )
)

:: Sanal ortami aktifle
call .venv\Scripts\activate.bat

:: Bagimliliklar
echo [*] Bagimliliklar kontrol ediliyor...
pip install -q -r requirements.txt
if errorlevel 1 ( echo [HATA] Bagimliliklar yuklenemedi. & pause & exit /b 1 )

:: Playwright Chromium
echo [*] Playwright Chromium kontrol ediliyor...
playwright install chromium >nul 2>&1

:: .env dosyasindan degiskenleri yukle
if exist ".env" (
    echo [*] .env dosyasi yukleniyor...
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        set "line=%%A"
        if not "!line:~0,1!"=="#" (
            if not "%%A"=="" (
                set "%%A=%%B"
            )
        )
    )
)

echo.

:: Eksik degiskenleri sor
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
echo     LinkedIn : %LI_EMAIL%
echo     Interval : 15 dakika
echo ================================================
echo.

python run_loop.py

echo.
echo [*] Monitor durduruldu.
pause
endlocal
