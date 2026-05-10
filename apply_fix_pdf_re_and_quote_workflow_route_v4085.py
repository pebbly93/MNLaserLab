from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN = ROOT / "backend" / "app" / "main.py"

def ensure_import_re():
    s = LEGACY.read_text(encoding="utf-8")

    if "import re" not in s.split("\n")[:40]:
        lines = s.splitlines()

        insert_at = 0
        for i, line in enumerate(lines[:40]):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = i + 1

        lines.insert(insert_at, "import re")
        s = "\n".join(lines) + "\n"
        LEGACY.write_text(s, encoding="utf-8")
        print("Aggiunto import re in legacy_logic.py")
    else:
        print("import re già presente")

def ensure_quote_workflow_route():
    s = MAIN.read_text(encoding="utf-8")

    if '@app.get("/api/quotes/workflow")' not in s:
        route = '''

@app.get("/api/quotes/workflow")
def quote_workflow_api():
    return quote_workflow_summary(load_db())
'''
        marker = '@app.get("/api/quotes")'
        if marker in s:
            s = s.replace(marker, route.strip() + "\\n\\n" + marker, 1)
        else:
            s += "\\n\\n" + route.strip() + "\\n"

        MAIN.write_text(s, encoding="utf-8")
        print("Aggiunta route /api/quotes/workflow in main.py")
    else:
        print("Route /api/quotes/workflow già presente")

def ensure_quote_workflow_function():
    s = LEGACY.read_text(encoding="utf-8")

    if "def quote_workflow_summary" not in s:
        helper = r'''

QUOTE_STATUSES = [
    "bozza",
    "inviato",
    "da_modificare",
    "accettato",
    "in_produzione",
    "consegnato",
    "rifiutato",
    "scaduto",
]

def normalize_quote_status(status):
    status = str(status or "bozza").strip().lower().replace(" ", "_")
    aliases = {
        "draft": "bozza",
        "sent": "inviato",
        "accepted": "accettato",
        "rejected": "rifiutato",
        "production": "in_produzione",
        "delivered": "consegnato",
    }
    status = aliases.get(status, status)
    return status if status in QUOTE_STATUSES else "bozza"

def quote_workflow_summary(db):
    quotes = db.get("quotes", []) or []
    counts = {s: 0 for s in QUOTE_STATUSES}
    rows = []

    for q in quotes:
        if not isinstance(q, dict):
            continue

        status = normalize_quote_status(q.get("status"))
        q["status"] = status
        counts[status] = counts.get(status, 0) + 1

        rows.append({
            "id": q.get("id", ""),
            "name": q.get("name", ""),
            "customer": q.get("customer", ""),
            "status": status,
            "date": q.get("date", ""),
            "total": q.get("discounted") or q.get("recommended") or q.get("total") or q.get("unit_price") or 0,
            "margin": q.get("margin_total", 0),
        })

    return {
        "statuses": QUOTE_STATUSES,
        "counts": counts,
        "quotes": rows,
    }
'''
        s += "\n\n" + helper.strip() + "\n"
        LEGACY.write_text(s, encoding="utf-8")
        print("Aggiunta funzione quote_workflow_summary in legacy_logic.py")
    else:
        print("quote_workflow_summary già presente")

def main():
    ensure_import_re()
    ensure_quote_workflow_function()
    ensure_quote_workflow_route()
    print("Fix v40.8.5 completato.")

if __name__ == "__main__":
    main()
