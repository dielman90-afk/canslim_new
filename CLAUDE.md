# CANSLIM Tägliche Analyse – Claude Code Setup

## Aufgabe

Jeden Werktag (Mo–Fr) analysierst du den US-Aktienmarkt nach der CANSLIM-Methode von William O'Neil und erstellst eine tagesaktuelle Zusammenfassung mit den besten Picks.

---

## CANSLIM-Kriterien (Kurzreferenz)

| Kürzel | Bedeutung | Schwellwert |
|--------|-----------|-------------|
| C | Current Earnings | EPS aktuelles Quartal +25% YoY |
| A | Annual Earnings | EPS letzte 3 Jahre +25% p.a. |
| N | New product/service/management | Neues Produkt, Führung oder ATH |
| S | Supply & Demand | Steigende Volumen beim Kurs-Anstieg |
| L | Leader | RS-Rating > 80 (Marktführer) |
| I | Institutional Sponsorship | Institutionelle Käufer erkennbar |
| M | Market Direction | Gesamtmarkt im Aufwärtstrend |

---

## Täglicher Ablauf (in dieser Reihenfolge)

### 1. Marktanalyse
- Nutze WebSearch für aktuelle S&P 500 und Nasdaq Kurse, Volumen, Marktbreite
- Bestimme die Marktampel: `GREEN` (klarer Aufwärtstrend), `YELLOW` (unentschieden/Warnung), `RED` (Distribution/Baisse)
- Schreibe eine kurze `market_note` (1-3 Sätze, ASCII-only, keine Umlaute)

### 2. CANSLIM-Aktienauswahl
- Recherchiere via WebSearch aktuelle Top-Kandidaten (Earnings-Beats, neue ATHs, Volumen-Breakouts)
- Wähle bis zu 5 Aktien die ALLE 7 CANSLIM-Kriterien erfüllen
- Bei Marktampel RED: Maximal 2 Picks, defensive Sektoren bevorzugen
- Aktien mit Earnings innerhalb der nächsten 3 Wochen vermeiden (Earnings-Risiko)

### 3. JSON schreiben
Schreibe das Ergebnis in `canslim-picks.json` im Root des Repos (Datei überschreiben):

```json
{
  "updated": "YYYY-MM-DD",
  "market_signal": "GREEN|YELLOW|RED",
  "market_note": "Kurze Marktbeschreibung ASCII-only",
  "picks": [
    {
      "ticker": "TICKER",
      "name": "Vollständiger Firmenname",
      "price": 123.45,
      "chart_pattern": "z.B. Cup with Handle Breakout",
      "signal": "GREEN|YELLOW|RED",
      "canslim": {
        "C": true,
        "A": true,
        "N": true,
        "S": true,
        "L": true,
        "I": true,
        "M": true
      },
      "note": "Kurzanalyse ASCII-only, max 3 Saetze"
    }
  ]
}
```

### 4. Slack-Direktnachricht
Sende eine Direktnachricht an den konfigurierten Empfänger (siehe `SLACK_USER_ID` unten).

**Format (ASCII-only, ~3.000–3.500 Zeichen):**
```
===== CANSLIM DAILY [DATUM] =====
Markt: [GREEN/YELLOW/RED] -- [market_note]

--- PICKS ---
#1 TICKER -- Firmenname [$Kurs] [chart_pattern]
   Signal: [GREEN/YELLOW/RED]
   CANSLIM: C+ A+ N+ S+ L+ I+ M+
   [note]

#2 ...

--- ENDE ---
Naechster Lauf: [naechster Werktag] 09:10
```

Verwende das Slack MCP Tool `slack_send_message`.

### 5. GitHub-Push
Pushe folgende Dateien ins Repo `dielman90-afk/canslim_new` (Branch `main`):
- `canslim-picks.json`
- `canslim_verbesserungen.md`

Verwende das GitHub MCP Tool `push_files` mit Commit-Message:
`Daily CANSLIM update YYYY-MM-DD`

### 6. Verbesserungslog aktualisieren
Füge oben in `canslim_verbesserungen.md` einen neuen Abschnitt ein:

```markdown
## Lauf [N] -- [Datum] ([Wochentag])

### Was gut lief
- [Punkte]

### Probleme
- [Punkte oder "Keine"]
```

---

## Konfiguration

```
SLACK_USER_ID = [HIER_USER_ID_EINTRAGEN]
GITHUB_REPO   = dielman90-afk/canslim_new
GITHUB_BRANCH = main
LAUF_NUMMER   = 22
```

> Erhöhe `LAUF_NUMMER` nach jedem erfolgreichen Lauf um 1.

---

## Cron-Job einrichten (einmalig, auf dem Server)

Das Skript `run_canslim.sh` startet Claude Code automatisch täglich um 09:10:

```bash
# Cron-Eintrag hinzufügen (einmalig ausführen):
(crontab -l 2>/dev/null; echo "10 9 * * 1-5 /home/user/canslim_new/run_canslim.sh") | crontab -

# Prüfen:
crontab -l

# Logs ansehen:
tail -f /home/user/canslim_new/canslim_cron.log
```

---

## Wichtige Regeln

1. **ASCII-only** in allen Ausgaben – keine Umlaute (ä→ae, ö→oe, ü→ue, ß→ss)
2. **Earnings-Filter**: Keine Aktien mit Earnings in den nächsten 3 Wochen
3. **Maximale Picks**: 5 bei GREEN, 3 bei YELLOW, 2 bei RED
4. **Keine Wiederholung**: Picks aus der Vorwoche nur halten wenn Chart-Muster intakt
5. **Reihenfolge einhalten**: Markt → JSON → Slack → GitHub → Log
