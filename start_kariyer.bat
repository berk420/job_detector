@echo off
setlocal EnableDelayedExpansion
title Kariyer.net CV Guncelleyici
color 0B

echo ================================================
echo   Kariyer.net CV Guncelleyici (her 5 dakika)
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

:: Ilk giris icin uyari
if not exist "data\kariyer_cookies.json" (
    echo [!] Kaydedilmis oturum bulunamadi.
    echo [!] Ilk calistirmada tarayici gorunerek acilacak.
    echo [!] Lutfen CAPTCHA'yi cozup giris yapin.
    echo.
    set HEADLESS=false
)

:: Kariyer email kontrolu
if "%KARIYER_EMAIL%"=="" (
    echo [*] .env dosyasina KARIYER_EMAIL ve KARIYER_PASSWORD ekleyin.
    echo     (Giris icin zorunlu degil, cookies kullaniliyor)
    echo.
)

set PYTHONIOENCODING=utf-8
echo [*] CV Guncelleyici baslatiliyor...
echo     Interval : 5 dakika
echo     Cookies  : data\kariyer_cookies.json
echo ================================================
echo.
echo Durdurmak icin Ctrl+C'ye basin.
echo.

python kariyer_guncelle.py

echo.
echo [*] Guncelleyici durduruldu.
pause
endlocal
