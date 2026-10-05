@echo off
chcp 65001 >nul
setlocal EnableExtensions

REM ============================================================
REM  Domel Konin - codzienna aktualizacja promocji dnia (GT B2B)
REM  Cena na stronie = Cena BRUTTO + 200 zl
REM
REM  1. Uzupelnij EMAIL i HASLO ponizej ALBO ustaw zmienne systemowe
REM  2. Uruchom recznie albo dodaj do Harmonogramu zadan Windows
REM ============================================================

REM --- KONFIGURACJA ---
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

REM Login B2B - WYPELNIJ (nie wrzucaj tego pliku z haslem na GitHub!)
if not defined GT_B2B_EMAIL set "GT_B2B_EMAIL=domel@domel.kalisz.pl"
if not defined GT_B2B_PASSWORD set "GT_B2B_PASSWORD=Domel12345@"

set "LOG_FILE=%PROJECT_DIR%promocje_update.log"
set "MARGIN=200"

echo ========================================>> "%LOG_FILE%"
echo Start: %DATE% %TIME%>> "%LOG_FILE%"
echo Katalog: %PROJECT_DIR%>> "%LOG_FILE%"

echo.
echo [Domel] Aktualizacja promocji dnia...
echo Katalog: %PROJECT_DIR%
echo.

REM Sprawdz Python
where python >nul 2>&1
if errorlevel 1 (
    echo BLAD: Brak polecenia "python" w PATH.
    echo BLAD: Brak python>> "%LOG_FILE%"
    pause
    exit /b 1
)

REM Sprawdz czy nie zostalo domyslne haslo
echo %GT_B2B_EMAIL% | findstr /I "WPROWADZ_EMAIL" >nul
if not errorlevel 1 (
    echo BLAD: Uzupelnij GT_B2B_EMAIL i GT_B2B_PASSWORD w pliku aktualizuj_promocje.bat
    echo        albo ustaw zmienne srodowiskowe przed uruchomieniem.
    echo BLAD: brak danych logowania>> "%LOG_FILE%"
    pause
    exit /b 1
)

echo [1/3] Pobieranie z B2B GT...
python download_promocje_b2b.py --margin %MARGIN% >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo BLAD przy pobieraniu. Szczegoly w: %LOG_FILE%
    echo Sprobuj: python download_promocje_b2b.py --headed
    echo BLAD download>> "%LOG_FILE%"
    pause
    exit /b 2
)

echo [2/3] Generowanie promocje.html...
python regenerate_promocje_html.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo BLAD przy generowaniu HTML. Szczegoly w: %LOG_FILE%
    echo BLAD regenerate>> "%LOG_FILE%"
    pause
    exit /b 3
)

echo [3/3] Git push na GitHub (jesli repozytorium git)...
where git >nul 2>&1
if errorlevel 1 (
    echo Brak git - pominieto push. Wrzuć pliki recznie na GitHub.
    echo Brak git>> "%LOG_FILE%"
    goto DONE
)

if not exist "%PROJECT_DIR%.git\" (
    echo To nie jest repozytorium git - pominieto push.
    echo Brak .git>> "%LOG_FILE%"
    goto DONE
)

git add promocje.json promocje.html images/promocje 2>> "%LOG_FILE%"
git diff --staged --quiet
if errorlevel 1 (
    git commit -m "Automatyczna aktualizacja promocji dnia %DATE%" >> "%LOG_FILE%" 2>&1
    git push >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo UWAGA: git push nie powiodl sie. Zaloguj sie / sprawdz remote.
        echo git push FAIL>> "%LOG_FILE%"
    ) else (
        echo Push OK - strona na GitHub Pages powinna sie odswiezyc za 1-2 min.
        echo Push OK>> "%LOG_FILE%"
    )
) else (
    echo Brak zmian w promocjach - commit pominiety.
    echo Brak zmian>> "%LOG_FILE%"
)

:DONE
echo.
echo Gotowe. Log: %LOG_FILE%
echo Koniec: %DATE% %TIME%>> "%LOG_FILE%"
echo ========================================>> "%LOG_FILE%"
echo.
REM Przy uruchomieniu z Harmonogramu zadan zakomentuj nastepna linie (pause):
pause
endlocal
exit /b 0
