# Tägliche CANSLIM-Analyse — Producer

Dieser Ordner ist der **Producer** der CANSLIM-Datenkette:

```
canslim_new              CANSLIM-picks            dashboard_new
(hier)             --->  (Datenstand)      --->   (Anzeige)
schreibt + pusht         canslim-picks.json       laedt per raw.githubusercontent
```

## Ablauf

1. Die Analyse-Routine schreibt `canslim-picks.json` in diesen Ordner.
2. `push_canslim.bat` (Windows-Aufgabenplaner, Mo-Fr 09:30) ruft
   `push_to_github.py` auf.
3. `push_to_github.py` **prueft die Datei und pusht nur, wenn sie besteht**.

## Die Pruefung vor dem Push

Zwei Stufen, beide blockierend:

1. **Datenvertrag** — Struktur gegen `canslim-picks.schema.json`
   (`validate_picks.py`). Falsche Feldnamen landen nicht mehr im Repo und
   damit nicht als halb leeres Widget im Dashboard.
2. **Rueckschritt-Schutz** — das `updated`-Datum der lokalen Datei darf
   nicht aelter sein als das der bereits veroeffentlichten.

Stufe 2 ist der wichtigere Schutz: Der Windows-Task laeuft taeglich,
unabhaengig davon ob die Analyse-Routine vorher etwas Neues geschrieben
hat. Ohne diese Sperre wuerde er eine liegengebliebene alte Datei ueber
den aktuellen Stand pushen, sobald die Routine einmal aussetzt. Genau das
drohte: die hier eingecheckte Datei stand auf dem Stand vom 07.05.2026,
waehrend im Repo bereits der 17.08.2026 lag.

Schlaegt eine Pruefung fehl, bricht das Skript mit **Exit-Code 3** ab und
pusht **nichts**. Der Grund steht im Log (`push_canslim.log`).

## Verwendung

```
python3 push_to_github.py                    # pruefen und pushen
python3 push_to_github.py --dry-run          # nur pruefen, nichts pushen
python3 push_to_github.py --force            # Pruefung uebergehen (Notfall)
python3 validate_picks.py canslim-picks.json # nur pruefen
```

## Dateien

| Datei | Zweck |
|---|---|
| `canslim-picks.json` | Ergebnis des letzten Laufs (wird gepusht) |
| `push_to_github.py` | Pruefung + Push per GitHub Contents API |
| `validate_picks.py` | Pruef-Logik (Kopie aus `CANSLIM-picks`) |
| `canslim-picks.schema.json` | Datenvertrag (Kopie; wird vor jedem Push frisch aus dem Repo geholt) |
| `push_canslim.bat` | Einstiegspunkt fuer den Windows-Aufgabenplaner |
| `install_scheduled_task.ps1` | Registriert den Task (einmalig) |
| `push_canslim.log` | Log jedes Laufs |

**Massgeblich ist immer `SCHEMA.md` im Repo `CANSLIM-picks`.** Die
Schema-Kopie hier ist nur der Offline-Rueckfall; `push_to_github.py`
zieht das Schema vor jedem Push frisch von GitHub.
