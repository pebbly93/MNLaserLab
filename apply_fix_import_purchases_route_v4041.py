from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "backend" / "app" / "main.py"
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"

LEGACY_FUNC = r'''

# ---------------------------------------------------------------------------
# v40.4.1 - Import CSV acquisti robusto
# ---------------------------------------------------------------------------

def import_purchase_rows(db, rows):
    if not isinstance(rows, list):
        raise ValueError("Formato import non valido")

    backup = backup_database("prima_import_csv_acquisti")
    imported = 0
    errors = []

    aliases = {
        "area": ["area", "section", "sezione"],
        "category": ["categoria", "category"],
        "subcategory": ["sottocategoria", "subcategory", "variante"],
        "size": ["formato", "tipo", "size"],
        "thickness": ["spessore", "thickness"],
        "unit": ["unita", "unità", "unit"],
        "supplier": ["fornitore", "supplier"],
        "quantity": ["quantita", "quantità", "qty", "quantity"],
        "total_cost": ["costo_totale", "costo totale", "total_cost", "totale"],
    }

    def pick(row, key, default=""):
        for name in aliases.get(key, [key]):
            if name in row:
                return row.get(name, default)
        return default

    for idx, row in enumerate(rows, start=1):
        try:
            if not isinstance(row, dict):
                raise ValueError("Riga non valida")

            payload = {
                "section": pick(row, "area") or section_label(db, "materials"),
                "category": pick(row, "category"),
                "subcategory": pick(row, "subcategory"),
                "size": pick(row, "size"),
                "thickness": pick(row, "thickness"),
                "unit": pick(row, "unit") or "pz",
                "supplier": pick(row, "supplier") or "Senza fornitore",
                "quantity": pick(row, "quantity"),
                "total_cost": pick(row, "total_cost"),
            }

            add_purchase(db, payload)
            imported += 1

        except Exception as exc:
            errors.append({
                "row": idx,
                "error": str(exc),
                "data": row,
            })

    return {
        "ok": not errors,
        "imported": imported,
        "errors": errors,
        "backup": backup,
    }
'''

API_ROUTE = r'''

@app.post("/api/maintenance/import-purchases")
def import_purchases_api(payload: Payload):
    try:
        rows = payload.data.get("rows", [])
        return mutate(import_purchase_rows, rows)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
'''

def main():
    legacy = LEGACY.read_text(encoding="utf-8")
    if "def import_purchase_rows" not in legacy:
        legacy += "\n\n" + LEGACY_FUNC.strip() + "\n"
        LEGACY.write_text(legacy, encoding="utf-8")
        print("Aggiunta funzione import_purchase_rows in legacy_logic.py")
    else:
        print("Funzione import_purchase_rows già presente.")

    main = MAIN.read_text(encoding="utf-8")

    # Rimuove eventuale route sbagliata GET/PUT con stesso path, se presente.
    main = main.replace('@app.get("/api/maintenance/import-purchases")', '@app.post("/api/maintenance/import-purchases")')
    main = main.replace('@app.put("/api/maintenance/import-purchases")', '@app.post("/api/maintenance/import-purchases")')

    if '@app.post("/api/maintenance/import-purchases")' not in main:
        # Inseriamo prima di maintenance/info se esiste, altrimenti in fondo.
        marker = '@app.get("/api/maintenance/info")'
        if marker in main:
            main = main.replace(marker, API_ROUTE.strip() + "\n\n" + marker, 1)
        else:
            main += "\n\n" + API_ROUTE.strip() + "\n"
        print("Aggiunta route POST /api/maintenance/import-purchases in main.py")
    else:
        print("Route POST import-purchases già presente.")

    MAIN.write_text(main, encoding="utf-8")
    print("Patch v40.4.1 completata.")

if __name__ == "__main__":
    main()
