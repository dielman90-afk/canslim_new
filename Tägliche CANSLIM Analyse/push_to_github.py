#!/usr/bin/env python3
"""
push_to_github.py

Pusht canslim-picks.json (und optional weitere Dateien) per GitHub Contents API
ins Repo dielman90-afk/CANSLIM-picks (Branch main).

Liest den Personal Access Token aus .github_token.txt im selben Ordner.
Wird vom Scheduled Task automatisch nach dem JSON-Schreiben aufgerufen.

Verwendung:
    python3 push_to_github.py canslim-picks.json
    python3 push_to_github.py canslim-picks.json canslim_verbesserungen.md
    python3 push_to_github.py --dry-run          # nur pruefen, nichts pushen
    python3 push_to_github.py --force            # Pruefung uebergehen (Notfall)

Funktioniert idempotent: Wenn die Datei im Repo schon existiert, wird sie
mit dem aktuellen SHA aktualisiert; sonst neu erstellt.

SCHUTZ VOR DATENVERLUST (seit 2026-08-27):
canslim-picks.json wird VOR dem Push geprueft, und zwar zweifach:

  1. Datenvertrag — Struktur gegen SCHEMA.md / canslim-picks.schema.json
     (validate_picks.py). Ein Lauf mit falschen Feldnamen landet nicht mehr
     im Repo und damit nicht als halb leeres Widget im Dashboard.

  2. Rueckschritt-Schutz — das `updated`-Datum der lokalen Datei darf nicht
     aelter sein als das der bereits veroeffentlichten. Ohne diesen Schutz
     wuerde der Windows-Task (Mo-Fr 09:30) eine alte, liegengebliebene
     Datei ueber den aktuellen Stand schreiben, sobald die Analyse-Routine
     einmal nicht gelaufen ist. Genau das war der Fall: die hier
     eingecheckte Datei stand monatelang auf dem Stand vom 07.05.2026.

Schlaegt eine Pruefung fehl, bricht das Skript mit Exit-Code 3 ab und
pusht NICHTS. --force uebergeht das bewusst.
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

REPO_OWNER = "dielman90-afk"
REPO_NAME = "CANSLIM-picks"
BRANCH = "main"

API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents"

# Der Datenvertrag liegt im CANSLIM-picks-Repo und ist dort die einzige
# Quelle der Wahrheit. Wir ziehen ihn vor dem Push frisch, damit hier keine
# veraltete Kopie mitlaeuft.
SCHEMA_RAW_URL = (
    f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/canslim-picks.schema.json"
)
PICKS_DATEI = "canslim-picks.json"


def load_token(project_dir: Path) -> str:
    for name in (".github_token", ".github_token.txt"):
        path = project_dir / name
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
    raise FileNotFoundError(
        f"Kein Token gefunden. Lege .github_token oder .github_token.txt in {project_dir} an."
    )


def gh_request(url: str, token: str, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "canslim-daily-push",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"raw": body}


def get_existing_sha(token: str, repo_path: str) -> str | None:
    url = f"{API_BASE}/{repo_path}?ref={BRANCH}"
    status, data = gh_request(url, token)
    if status == 200 and isinstance(data, dict):
        return data.get("sha")
    return None


def push_file(token: str, local_file: Path, repo_path: str, commit_message: str) -> bool:
    if not local_file.is_file():
        print(f"  SKIP: {local_file} existiert nicht.")
        return False

    content_b64 = base64.b64encode(local_file.read_bytes()).decode("ascii")

    payload: dict = {
        "message": commit_message,
        "content": content_b64,
        "branch": BRANCH,
    }
    sha = get_existing_sha(token, repo_path)
    if sha:
        payload["sha"] = sha

    url = f"{API_BASE}/{repo_path}"
    status, data = gh_request(url, token, method="PUT", payload=payload)

    if status in (200, 201):
        commit = data.get("commit", {}) if isinstance(data, dict) else {}
        sha_short = commit.get("sha", "")[:7]
        action = "updated" if sha else "created"
        print(f"  OK ({action}): {repo_path} -> commit {sha_short}")
        return True
    else:
        msg = data.get("message", data) if isinstance(data, dict) else data
        print(f"  FAIL ({status}): {repo_path} -> {msg}")
        return False


def hole_veroeffentlichtes_datum(token: str) -> str | None:
    """`updated` der aktuell im Repo liegenden canslim-picks.json (oder None)."""
    url = f"{API_BASE}/{PICKS_DATEI}?ref={BRANCH}"
    status, data = gh_request(url, token)
    if status != 200 or not isinstance(data, dict):
        return None
    try:
        roh = base64.b64decode(data.get("content", "")).decode("utf-8")
        return json.loads(roh).get("updated")
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def hole_schema(project_dir: Path) -> Path | None:
    """Schema aus dem Repo ziehen; faellt auf eine lokale Kopie zurueck."""
    lokal = project_dir / "canslim-picks.schema.json"
    try:
        req = urllib.request.Request(
            SCHEMA_RAW_URL, headers={"User-Agent": "canslim-daily-push"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            inhalt = resp.read().decode("utf-8")
        json.loads(inhalt)  # nur uebernehmen, wenn es gueltiges JSON ist
        lokal.write_text(inhalt, encoding="utf-8")
        return lokal
    except (urllib.error.URLError, json.JSONDecodeError, OSError, TimeoutError) as e:
        print(f"  Hinweis: Schema nicht abrufbar ({e}).", end=" ")
        if lokal.is_file():
            print("Nutze lokale Kopie.")
            return lokal
        print("Pruefe nur die Struktur.")
        return None


def pruefe_picks(project_dir: Path, token: str) -> bool:
    """Datenvertrag + Rueckschritt-Schutz. True = Push erlaubt."""
    datei = project_dir / PICKS_DATEI
    if not datei.is_file():
        print(f"  SKIP-PRUEFUNG: {PICKS_DATEI} liegt nicht vor.")
        return True

    try:
        from validate_picks import pruefe, pruefe_mit_schema
    except ImportError:
        print("  WARNUNG: validate_picks.py fehlt — Pruefung uebersprungen.")
        return True

    try:
        daten = json.loads(datei.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  FEHLER: {PICKS_DATEI} ist kein gueltiges JSON — {e}")
        return False

    veroeffentlicht = hole_veroeffentlichtes_datum(token)
    min_datum = None
    if veroeffentlicht:
        try:
            min_datum = datetime.strptime(veroeffentlicht, "%Y-%m-%d").date()
        except ValueError:
            pass

    fehler, warnungen = pruefe(daten, min_datum)
    schema_pfad = hole_schema(project_dir)
    schema_fehler = pruefe_mit_schema(daten, schema_pfad) if schema_pfad else None
    if schema_fehler:
        fehler.extend(f"Schema — {m}" for m in schema_fehler)

    print(f"  Pruefe {PICKS_DATEI}: Stand {daten.get('updated')}, Lauf {daten.get('run')}, "
          f"{len(daten.get('picks') or [])} Picks / {len(daten.get('watchlist') or [])} Watchlist"
          + (f" (im Repo: {veroeffentlicht})" if veroeffentlicht else ""))
    for w in warnungen:
        print(f"  WARNUNG: {w}")
    for f in fehler:
        print(f"  FEHLER:  {f}")
    return not fehler


def main() -> int:
    project_dir = Path(__file__).parent.resolve()
    sys.path.insert(0, str(project_dir))

    argumente = sys.argv[1:]
    dry_run = "--dry-run" in argumente
    force = "--force" in argumente
    files = [a for a in argumente if not a.startswith("--")] or [PICKS_DATEI]

    try:
        token = load_token(project_dir)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1

    if PICKS_DATEI in files:
        if not pruefe_picks(project_dir, token):
            if force:
                print("  --force gesetzt: Push trotz Vertragsverletzung.")
            else:
                print("\nABBRUCH: Datenvertrag verletzt, es wurde NICHTS gepusht.")
                print("Siehe SCHEMA.md im Repo CANSLIM-picks. Notfall-Override: --force")
                return 3
        else:
            print("  Pruefung in Ordnung.")

    if dry_run:
        print("\n--dry-run: kein Push ausgefuehrt.")
        return 0

    today = datetime.now().strftime("%Y-%m-%d")

    success = True
    for filename in files:
        local = project_dir / filename
        repo_path = filename
        msg = f"Daily CANSLIM update {today} ({filename})"
        if not push_file(token, local, repo_path, msg):
            success = False

    return 0 if success else 2


if __name__ == "__main__":
    sys.exit(main())
