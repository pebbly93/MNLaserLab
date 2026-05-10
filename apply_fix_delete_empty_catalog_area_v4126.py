from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"

NEW_FUNC = r'''
def delete_catalog_area(db, name):
    name = str(name or "").strip()
    if not name:
        raise ValueError("Area non valida")

    used = False

    # Materiali/componenti realmente collegati all'area.
    for section_key in ["materials", "components"]:
        for item in (db.get(section_key, {}) or {}).values():
            if isinstance(item, dict) and str(item.get("section", "")).strip() == name:
                used = True

    # Fornitori realmente collegati all'area.
    for supplier in (db.get("suppliers", {}) or {}).values():
        if isinstance(supplier, dict):
            if name in list(supplier.get("sections", []) or []):
                used = True

            for link in list(supplier.get("links", []) or []):
                if isinstance(link, dict) and str(link.get("section", "")).strip() == name:
                    used = True

    # Categorie figlie reali.
    # La sola chiave categories[name] vuota NON deve bloccare l'eliminazione.
    categories = db.setdefault("categories", {})
    area_categories = categories.get(name, {})

    if isinstance(area_categories, dict) and len(area_categories.keys()) > 0:
        used = True
    elif isinstance(area_categories, list) and len(area_categories) > 0:
        used = True
    elif area_categories and not isinstance(area_categories, (dict, list)):
        used = True

    if used:
        raise ValueError("Area già usata: elimina prima categorie, materiali o collegamenti fornitori")

    areas = [x for x in get_catalog_areas(db) if str(x or "").strip() != name]
    db["catalog_areas"] = areas

    # Ora posso rimuovere anche la chiave vuota dalle categorie.
    categories.pop(name, None)

    return {"ok": True, "areas": areas}
'''

def replace_function(source: str, name: str, new_code: str) -> str:
    start = source.find(f"def {name}(")
    if start == -1:
        raise RuntimeError(f"Funzione non trovata: {name}")

    end = source.find("\ndef ", start + 1)
    if end == -1:
        end = len(source)

    return source[:start] + new_code.strip() + "\n\n" + source[end + 1:]

def main():
    s = LEGACY.read_text(encoding="utf-8")
    s = replace_function(s, "delete_catalog_area", NEW_FUNC)
    LEGACY.write_text(s, encoding="utf-8")
    print("Fix applicato: le aree vuote ora si possono eliminare.")

if __name__ == "__main__":
    main()
