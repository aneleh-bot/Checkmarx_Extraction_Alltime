import requests
import time
import os
import pandas as pd
from datetime import datetime, timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import HTTPError, ChunkedEncodingError, ConnectionError

# =========================================================
# CONFIGURAÇÃO (PREENCHA)
# =========================================================

TENANT_NAME   = " " # adicionar o tenant
CLIENT_ID     = " " # adicionar o client id
CLIENT_SECRET = " " # adicionar o secret (OAuth Checkmarx One)

AST_API_BASE  = "https://eu.ast.checkmarx.net" # substituir (us,us2,eu,eu2)
IAM_BASE      = "https://eu.iam.checkmarx.net" # substituir (us,us2,eu,eu2)

AUTH_URL     = f"{IAM_BASE}/auth/realms/{TENANT_NAME}/protocol/openid-connect/token"
PROJECTS_URL = f"{AST_API_BASE}/api/projects"
SCANS_URL    = f"{AST_API_BASE}/api/scans"
RESULTS_URL  = f"{AST_API_BASE}/api/results"

PAGE_SIZE = 4000

# =========================================================
# SESSION + RETRY
# =========================================================

session = requests.Session()
session.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
    )
)

# =========================================================
# AUTH
# =========================================================

def get_headers():
    r = session.post(
        AUTH_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        },
        timeout=(5, 30)
    )
    r.raise_for_status()
    token = r.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json;v=1.0"
    }

# =========================================================
# API HELPERS
# =========================================================

def list_projects(headers):
    acc, off = [], 0
    while True:
        r = session.get(
            PROJECTS_URL,
            headers=headers,
            params={"limit": PAGE_SIZE, "offset": off},
            timeout=(5, 30)
        )
        r.raise_for_status()
        batch = r.json().get("projects", [])
        if not batch:
            break
        acc += batch
        off += PAGE_SIZE
    return acc

def list_scans_for_project(headers, project_id):
    acc, off = [], 0
    while True:
        try:
            r = session.get(
                SCANS_URL,
                headers=headers,
                params={
                    "project-id": project_id,
                    "limit": PAGE_SIZE,
                    "offset": off
                },
                timeout=(5, 30)
            )
            r.raise_for_status()
            batch = r.json().get("scans", [])
        except HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                print(f"[WARN] Sem acesso ao projeto {project_id}, pulando.")
                return []
            raise
        if not batch:
            break
        acc += batch
        off += PAGE_SIZE
    return acc

def get_results_for_scan(headers, project_id, scan_id):
    acc, off = [], 0
    while True:
        try:
            r = session.get(
                RESULTS_URL,
                headers=headers,
                params={
                    "project-id": project_id,   # <<< OBRIGATÓRIO
                    "scan-id": scan_id,
                    "limit": PAGE_SIZE,
                    "offset": off
                },
                timeout=(5, 30)
            )
            r.raise_for_status()
            batch = r.json().get("results", [])
        except (ChunkedEncodingError, ConnectionError):
            print(f"[WARN] Retry results scan={scan_id} offset={off}")
            time.sleep(2)
            continue

        if not batch:
            break

        acc += batch
        off += PAGE_SIZE

    return acc

# =========================================================
# MAIN
# =========================================================

def collect_all_vulnerabilities() -> pd.DataFrame:
    headers = get_headers()
    projects = list_projects(headers)
    print(f"[+] Projetos encontrados: {len(projects)}")

    rows = []

    for proj in projects:
        headers = get_headers()  # token fresh
        pid = proj.get("id")
        pname = proj.get("name", "<unknown>")

        scans = list_scans_for_project(headers, pid)
        print(f"[+] Projeto '{pname}' ({pid}) - scans: {len(scans)}")

        for scan in scans:
            sid = scan.get("id")
            scan_type = scan.get("type")
            scan_date = scan.get("createdAt") or scan.get("scanDate")

            results = get_results_for_scan(headers, pid, sid)

            for res in results:
                rows.append({
                    "Project Name": pname,
                    "Project Id": pid,
                    "Scan Id": sid,
                    "Scan Type": scan_type,
                    "Severity": res.get("severity"),
                    "Vulnerability Type": res.get("type"),
                    "Result Id": res.get("id"),
                    "First Found At": res.get("firstFoundAt"),
                    "Last Found At": (
                        res.get("foundAt")
                        or res.get("lastFoundAt")
                        or res.get("updatedAt")
                    ),
                    "Scan Date": scan_date
                })

    return pd.DataFrame(rows)

# =========================================================
# EXPORT
# =========================================================

def export_report(df: pd.DataFrame):
    if df.empty:
        print("Nenhuma vulnerabilidade encontrada.")
        return

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    excel = f"cxone_vulnerabilities_full_history_{ts}.xlsx"
    csv = f"cxone_vulnerabilities_full_history_{ts}.csv"

    df.to_excel(excel, index=False)
    df.to_csv(csv, index=False)

    print(f"[✓] Excel gerado: {excel}")
    print(f"[✓] CSV gerado:   {csv}")

# =========================================================
if __name__ == "__main__":
    df = collect_all_vulnerabilities()
    export_report(df)
