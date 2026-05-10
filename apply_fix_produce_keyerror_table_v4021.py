from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"


NEW_PRODUCE_PRODUCT = r'''
def produce_product(db, product_name, qty, substitutions=None):
    substitutions = substitutions or {}
    check = production_check(db, product_name, qty)
    deductions = []

    def resolve_material_ref(name_or_key, fallback_table="", fallback_key=""):
        """Ritorna (item, table, key) anche quando la BOM non contiene table/key."""
        if fallback_table and fallback_key and fallback_key in db.get(fallback_table, {}):
            return db[fallback_table][fallback_key], fallback_table, fallback_key

        item, table, key = get_raw_item(db, name_or_key)
        if item and table and key:
            return item, table, key

        # fallback: cerca per key esatta in entrambi i magazzini
        for table_name in ("materials", "components"):
            if name_or_key in db.get(table_name, {}):
                return db[table_name][name_or_key], table_name, name_or_key

        return None, "", ""

    for row in check["rows"]:
        needed = parse_float(row.get("needed"))

        if row.get("ok"):
            item, table, key = resolve_material_ref(
                row.get("key") or row.get("name"),
                row.get("table", ""),
                row.get("key", "")
            )

            if not item or not table or not key:
                raise ValueError(f"Materiale non risolvibile in distinta: {row.get('name', '')}")

            deductions.append((table, key, needed))
            continue

        sub = substitutions.get(str(row.get("index"))) or substitutions.get(row.get("index"))

        if not sub:
            raise ValueError(f"Materiale mancante non risolto: {row.get('name', '')}")

        # Supporto produzione mista:
        # substitutions[index] = {"mix": [{"table": "...", "key": "...", "qty": 1}, ...]}
        if isinstance(sub, dict) and isinstance(sub.get("mix"), list):
            total_mix = 0.0

            for part in sub.get("mix", []):
                part_qty = parse_float(part.get("qty"))
                if part_qty <= 0:
                    continue

                item, table, key = resolve_material_ref(
                    part.get("key") or part.get("name"),
                    part.get("table", ""),
                    part.get("key", "")
                )

                if not item or not table or not key:
                    raise ValueError(f"Materiale alternativo non risolvibile: {part.get('name') or part.get('key')}")

                deductions.append((table, key, part_qty))
                total_mix += part_qty

            if total_mix + 0.000001 < needed:
                raise ValueError(
                    f"Sostituzione parziale insufficiente per {row.get('name', '')}: "
                    f"richiesto {needed:.2f}, coperto {total_mix:.2f}"
                )

        else:
            item, table, key = resolve_material_ref(
                sub.get("key") or sub.get("name"),
                sub.get("table", ""),
                sub.get("key", "")
            )

            if not item or not table or not key:
                raise ValueError(f"Materiale alternativo non risolvibile: {sub.get('name') or sub.get('key')}")

            deductions.append((table, key, needed))

    # Aggrega eventuali scarichi doppi dello stesso materiale.
    aggregated = {}
    for table, key, need in deductions:
        if not table or not key:
            raise ValueError("Riferimento materiale incompleto durante la produzione")
        aggregated[(table, key)] = aggregated.get((table, key), 0.0) + parse_float(need)

    for (table, key), need in aggregated.items():
        if table not in db or key not in db.get(table, {}):
            raise ValueError(f"Materiale non trovato: {key}")

        available = parse_float(db[table][key].get("stock"))
        if available + 0.000001 < need:
            raise ValueError(
                f"Stock insufficiente per {display_name_from_key(key, db[table][key])}: "
                f"disponibile {available:.2f}, richiesto {need:.2f}"
            )

    for (table, key), need in aggregated.items():
        db[table][key]["stock"] = parse_float(db[table][key].get("stock")) - need

    if product_name not in db.get("products", {}):
        raise ValueError("Prodotto non trovato")

    db["products"][product_name]["stock"] = parse_float(db["products"][product_name].get("stock")) + qty

    return {
        "ok": True,
        "deductions": [
            {"table": table, "key": key, "qty": need}
            for (table, key), need in aggregated.items()
        ],
        "new_stock": db["products"][product_name]["stock"]
    }
'''


def replace_backend_function(source: str, name: str, new_code: str) -> str:
    start = source.find(f"def {name}(")
    if start == -1:
        raise RuntimeError(f"Funzione backend non trovata: {name}")

    next_def = source.find("\ndef ", start + 1)
    if next_def == -1:
        next_def = len(source)

    return source[:start] + new_code.rstrip() + "\n\n" + source[next_def + 1:]


def main():
    s = LEGACY.read_text(encoding="utf-8")
    s = replace_backend_function(s, "produce_product", NEW_PRODUCE_PRODUCT)
    LEGACY.write_text(s, encoding="utf-8")
    print("Patch v40.2.1 applicata: fix KeyError table in produzione.")


if __name__ == "__main__":
    main()
