# ============================================================
#  install_scheduled_task.ps1
#  Registriert den Windows-Aufgabenplaner-Task fuer den
#  taeglichen GitHub-Push der CANSLIM-Datei.
#
#  Aufruf (einmalig):
#    Rechtsklick -> "Mit PowerShell ausfuehren"
#  oder im Terminal:
#    powershell -ExecutionPolicy Bypass -File install_scheduled_task.ps1
#
#  Der Task laeuft danach Mo-Fr um 09:30 (also 20 Minuten nach
#  dem Cowork-Lauf) und ist die Absicherung, falls der
#  Cowork-Push nicht durchgekommen ist.
# ============================================================

$ErrorActionPreference = "Stop"

$TaskName = "CANSLIM_Daily_GitHub_Push"
$TaskDescription = "Tägliche Absicherung: pusht canslim-picks.json und canslim_verbesserungen.md ins GitHub-Repo dielman90-afk/CANSLIM-picks. Idempotent."

# Pfad zum .bat-Skript (liegt im selben Ordner wie dieses PS-Skript)
$BatPath = Join-Path $PSScriptRoot "push_canslim.bat"

if (-not (Test-Path $BatPath)) {
    Write-Host "FEHLER: push_canslim.bat nicht gefunden unter $BatPath" -ForegroundColor Red
    Write-Host "Stelle sicher, dass dieses Skript im selben Ordner wie push_canslim.bat liegt." -ForegroundColor Yellow
    exit 1
}

Write-Host "Registriere Windows-Aufgabenplaner-Task '$TaskName' ..." -ForegroundColor Cyan
Write-Host "  Skript: $BatPath"
Write-Host "  Zeitplan: Montag bis Freitag um 09:30 Uhr"
Write-Host ""

# Existierenden Task entfernen, falls schon vorhanden
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "  Entferne existierenden Task ..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Action: das .bat-Skript starten
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$BatPath`"" `
    -WorkingDirectory $PSScriptRoot

# Trigger: Mo-Fr um 09:30
$trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday `
    -At 09:30

# Settings: nicht parallel laufen lassen, im Hintergrund, max 5 min
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -MultipleInstances IgnoreNew

# Principal: als aktueller User, hoechste Rechte NICHT noetig
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

# Task registrieren
Register-ScheduledTask `
    -TaskName $TaskName `
    -Description $TaskDescription `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal | Out-Null

Write-Host ""
Write-Host "OK -- Task '$TaskName' wurde registriert." -ForegroundColor Green
Write-Host ""
Write-Host "Naechster automatischer Lauf:" -ForegroundColor Cyan
$task = Get-ScheduledTask -TaskName $TaskName
$info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host "  $($info.NextRunTime)" -ForegroundColor White
Write-Host ""
Write-Host "Sofort-Test (manuell anstoßen):" -ForegroundColor Cyan
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
Write-Host ""
Write-Host "Logs nach jedem Lauf in:" -ForegroundColor Cyan
Write-Host "  $(Join-Path $PSScriptRoot 'push_canslim.log')" -ForegroundColor White
Write-Host ""
Write-Host "Task entfernen (falls jemals noetig):" -ForegroundColor Cyan
Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor White
Write-Host ""
