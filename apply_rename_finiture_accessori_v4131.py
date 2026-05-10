from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"

OLD = "Finiture"
NEW = "Accessori"


def patch_legacy_default_area():
    p = LEGACY
    s = p.read_text(encoding="utf-8")

    s = s.replace(
        'return ["Falegnameria", "Ferramenta", "Illuminazione", "Finiture"]',
        'return ["Falegnameria", "Ferramenta", "Illuminazione", "Accessori"]'
    )

    s = s.replace(
        '"Falegnameria", "Ferramenta", "Illuminazione", "Finiture"',
        '"Falegnameria", "Ferramenta", "Illuminazione", "Accessori"'
    )

    p.write_text(s, encoding="utf-8")
    print("Default area aggiornata: Finiture -> Accessori")


def find_json_files():
    candidates = []

    for pattern in [
        "backend/**/*.json",
        "data/**/*.json",
        "*.json",
    ]:
        candidates.extend(ROOT.glob(pattern))

    skip_names = {
        "package.json",
        "package-lock.json",
        "tsconfig.json",
        "vite.config.json",
    }

    result = []
    for p in candidates:
        if p.name in skip_names:
            continue
        if "node_modules" in p.parts or ".venv" in p.parts or "dist" in p.parts:
            continue
        result.append(p)

    return sorted(set(result))


def rename_value(obj):
    if isinstance(obj, dict):
        new_obj = {}

        for k, v in obj.items():
            nk = NEW if k == OLD else k
            new_obj[nk] = rename_value(v)

        return new_obj

    if isinstance(obj, list):
        return [rename_value(x) for x in obj]

    if isinstance(obj, str):
        return NEW if obj == OLD else obj

    return obj


def patch_json_data():
    changed = []

    for p in find_json_files():
        try:
            raw = p.read_text(encoding="utf-8")
            data = json.loads(raw)
        except Exception:
            continue

        new_data = rename_value(data)

        if new_data != data:
            p.write_text(json.dumps(new_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed.append(str(p.relative_to(ROOT)))

    if changed:
        print("File dati aggiornati:")
        for x in changed:
            print(" -", x)
    else:
        print("Nessun file dati JSON da migrare trovato o nessuna occorrenza presente.")


def main():
    patch_legacy_default_area()
    patch_json_data()
    print("Migrazione completata: Finiture rinominata in Accessori.")


if __name__ == "__main__":
    main()
