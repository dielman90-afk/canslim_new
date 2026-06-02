# ============================================================
#  uninstall_scheduled_task.ps1
#  Entfernt den Windows-Aufgabenplaner-Task fuer den taeglichen
#  GitHub-Push der CANSLIM-Datei.
#
#  HINTERGRUND (Option 1):
#  Der taegliche Report-Lauf ist ab sofort der EINZIGE Schreiber
#  auf main. Der alte Absicherungs-Push hat die frischen Picks mit
#  einer veralteten lokalen canslim-picks.json ueberschrieben und
#  wird deshalb abgeschaltet.
#
#  Aufruf (einmalig):
#    Rechtsklick -> "Mit PowerShell ausfuehren"
#  oder im Terminal:
#    powershell -ExecutionPolicy Bypass -File uninstall_scheduled_task.ps1
# ============================================================

$ErrorActionPreference = "Stop"

$TaskName = "CANSLIM_Daily_GitHub_Push"

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Entferne Scheduled Task '$TaskName' ..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "OK -- Task '$TaskName' wurde entfernt." -ForegroundColor Green
    Write-Host "Der Report-Lauf ist jetzt der einzige Schreiber auf main." -ForegroundColor Cyan
} else {
    Write-Host "Task '$TaskName' ist nicht (mehr) registriert -- nichts zu tun." -ForegroundColor Green
}
