from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"

def patch_add_catalog_area(s: str) -> str:
    start = s.find("def add_catalog_area")
    if start == -1:
        raise RuntimeError("def add_catalog_area non trovata")

    end = s.find("\ndef ", start + 1)
    if end == -1:
        end = len(s)

    block = s[start:end]

    if 'db.setdefault("categories", {}).setdefault(name, {})' not in block:
        marker = 'db["catalog_areas"] = areas'
        if marker in block:
            block = block.replace(
                marker,
                'db.setdefault("categories", {}).setdefault(name, {})\n    ' + marker,
                1
            )
        else:
            block = block.replace(
                "return {",
                'db.setdefault("categories", {}).setdefault(name, {})\n    return {',
                1
            )

    return s[:start] + block + s[end:]


def patch_get_catalog_areas(s: str) -> str:
    start = s.find("def get_catalog_areas")
    if start == -1:
        raise RuntimeError("def get_catalog_areas non trovata")

    end = s.find("\ndef ", start + 1)
    if end == -1:
        end = len(s)

    block = s[start:end]

    if "db.setdefault(\"categories\", {}).setdefault(x, {})" not in block:
        old = 'db["catalog_areas"] = merged\n    return merged'
        new = '''db["catalog_areas"] = merged

    # Ogni area deve esistere anche come chiave categories,
    # altrimenti non compare nella gestione categorie figlie.
    cats = db.setdefault("categories", {})
    for x in merged:
        cats.setdefault(x, {})

    return merged'''
        if old in block:
            block = block.replace(old, new, 1)
        else:
            block = block.replace("return merged", '''cats = db.setdefault("categories", {})
    for x in merged:
        cats.setdefault(x, {})

    return merged''', 1)

    return s[:start] + block + s[end:]


def patch_taxonomy_builders(s: str) -> str:
    """
    Se raw_tree viene costruito solo da db['categories'], ora basta che get_catalog_areas()
    abbia creato le chiavi vuote. Però forziamo anche le funzioni più probabili a chiamarlo.
    """
    for fn in ["taxonomy_data", "build_taxonomy", "taxonomy_summary", "get_taxonomy"]:
        start = s.find(f"def {fn}")
        if start == -1:
            continue

        end = s.find("\ndef ", start + 1)
        if end == -1:
            end = len(s)

        block = s[start:end]

        if "get_catalog_areas(db)" not in block:
            first_nl = block.find("\n")
            block = block[:first_nl + 1] + "    get_catalog_areas(db)\n" + block[first_nl + 1:]
            s = s[:start] + block + s[end:]

    return s


def main():
    s = LEGACY.read_text(encoding="utf-8")
    s = patch_get_catalog_areas(s)
    s = patch_add_catalog_area(s)
    s = patch_taxonomy_builders(s)
    LEGACY.write_text(s, encoding="utf-8")
    print("Fix aree vuote applicato: le nuove aree saranno visibili anche prima di creare categorie figlie.")

if __name__ == "__main__":
    main()
