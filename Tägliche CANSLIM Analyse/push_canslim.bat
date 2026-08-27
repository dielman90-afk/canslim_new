@echo off
REM ============================================================
REM  push_canslim.bat
REM  Pusht canslim-picks.json + canslim_verbesserungen.md
REM  ins GitHub-Repo dielman90-afk/CANSLIM-picks (Branch main).
REM
REM  Wird vom Windows-Aufgabenplaner taeglich aufgerufen als
REM  Absicherung, falls der Cowork-Push nicht durchgekommen ist.
REM
REM  Das Skript ist idempotent: wenn die Datei im Repo schon
REM  identisch ist, macht GitHub keinen neuen Commit.
REM
REM  WICHTIG: push_to_github.py prueft canslim-picks.json VOR dem
REM  Push gegen den Datenvertrag und gegen das Datum des bereits
REM  veroeffentlichten Standes. Exit-Code 3 = Pruefung fehlgeschlagen,
REM  es wurde NICHTS gepusht (Grund steht im Log). Das verhindert,
REM  dass dieser taegliche Task eine liegengebliebene alte Datei ueber
REM  den aktuellen Stand schreibt, wenn die Analyse-Routine aussetzt.
REM ============================================================

REM In den Projektordner wechseln (egal von wo gestartet)
cd /d "%~dp0"

REM Logfile mit Datum/Uhrzeit
set "LOGFILE=%~dp0push_canslim.log"

echo. >> "%LOGFILE%"
echo ===== %date% %time% ===== >> "%LOGFILE%"

REM Python aufrufen (versuche 'python' zuerst, dann 'py' als Fallback)
where python >nul 2>nul
if %errorlevel%==0 (
    python push_to_github.py canslim-picks.json canslim_verbesserungen.md >> "%LOGFILE%" 2>&1
    set "RC=%errorlevel%"
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        py -3 push_to_github.py canslim-picks.json canslim_verbesserungen.md >> "%LOGFILE%" 2>&1
        set "RC=%errorlevel%"
    ) else (
        echo FEHLER: Weder 'python' noch 'py' im PATH gefunden. >> "%LOGFILE%"
        set "RC=99"
    )
)

echo Exit-Code: %RC% >> "%LOGFILE%"
exit /b %RC%
