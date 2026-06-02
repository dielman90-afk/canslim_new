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

Funktioniert idempotent: Wenn die Datei im Repo schon existiert, wird sie
mit dem aktuellen SHA aktualisiert; sonst neu erstellt.
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_OWNER = "dielman90-afk"
REPO_NAME = "CANSLIM-picks"
BRANCH = "main"

API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents"


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


def main() -> int:
    project_dir = Path(__file__).parent.resolve()
    files = sys.argv[1:] or ["canslim-picks.json"]

    # ------------------------------------------------------------------
    # DEAKTIVIERT (Option 1): Der taegliche Report-Lauf ist ab sofort der
    # EINZIGE Schreiber auf main. Dieser Absicherungs-Push wuerde sonst die
    # frischen Picks mit einer veralteten lokalen canslim-picks.json
    # ueberschreiben. Zum bewussten Reaktivieren: CANSLIM_ENABLE_PUSH=1 setzen.
    # ------------------------------------------------------------------
    if os.environ.get("CANSLIM_ENABLE_PUSH") != "1":
        print(
            "DEAKTIVIERT: Daily-Push uebersprungen -- der Report-Lauf ist der "
            "einzige Schreiber auf main. Zum Reaktivieren CANSLIM_ENABLE_PUSH=1 setzen."
        )
        return 0

    try:
        token = load_token(project_dir)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1

    from datetime import datetime
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
