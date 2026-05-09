from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN = ROOT / "backend" / "app" / "main.py"


def replace_function(source: str, function_name: str, new_code: str) -> str:
    pattern = rf"^def {function_name}\(.*?\):\n(?:(?:    .*\n)|(?:\n))*"
    match = re.search(pattern, source, flags=re.MULTILINE)

    if not match:
        raise RuntimeError(f"Funzione non trovata: {function_name}")

    return source[:match.start()] + new_code.rstrip() + "\n\n" + source[match.end():]


def insert_after_function(source: str, function_name: str, insert_code: str, marker: str) -> str:
    if marker in source:
        return source

    pattern = rf"^def {function_name}\(.*?\):\n(?:(?:    .*\n)|(?:\n))*"
    match = re.search(pattern, source, flags=re.MULTILINE)

    if not match:
        raise RuntimeError(f"Funzione non trovata per inserimento: {function_name}")

    return source[:match.end()] + "\n\n" + insert_code.rstrip() + "\n\n" + source[match.end():]


HELPERS = r'''
def purchase_history(db):
    history = db.setdefault("purchase_history", [])
    return history if isinstance(history, list) else []


def raw_purchase_count(db, key, table="", name=""):
    count = 0
    display = str(name or "").strip().lower()

    for row in purchase_history(db):
        if table and row.get("table") != table:
            continue

        if key and row.get("key") == key:
            count += 1
            continue

        if display and str(row.get("name", "")).strip().lower() == display:
            count += 1

    return count


def raw_last_purchase(db, key, table="", name=""):
    rows = []
    display = str(name or "").strip().lower()

    for row in purchase_history(db):
        if table and row.get("table") != table:
            continue

        if key and row.get("key") == key:
            rows.append(row)
            continue

        if display and str(row.get("name", "")).strip().lower() == display:
            rows.append(row)

    if not rows:
        return None

    return sorted(rows, key=lambda x: str(x.get("date_iso", x.get("date", ""))))[-1]


def inventory_status(stock, cost, purchase_count=0, min_stock=0):
    stock = parse_float(stock)
    cost = parse_float(cost)
    purchase_count = int(parse_float(purchase_count))
    min_stock = parse_float(min_stock)

    if stock <= 0 and cost <= 0 and purchase_count <= 0:
        return {
            "status": "mai_acquistato",
            "badge": "mai acquistato",
            "color": "red",
            "usable_in_quote": False,
            "visible_operational": False,
        }

    if stock > 0 and cost <= 0:
        return {
            "status": "da_verificare",
            "badge": "da verificare",
            "color": "yellow",
            "usable_in_quote": False,
            "visible_operational": True,
        }

    if stock <= 0 and (cost > 0 or purchase_count > 0):
        return {
            "status": "esaurito",
            "badge": "esaurito",
            "color": "gray",
            "usable_in_quote": False,
            "visible_operational": True,
        }

    if min_stock > 0 and stock <= min_stock:
        return {
            "status": "sotto_scorta",
            "badge": "sotto scorta",
            "color": "orange",
            "usable_in_quote": True,
            "visible_operational": True,
        }

    if stock > 0 and cost > 0:
        return {
            "status": "attivo",
            "badge": "attivo",
            "color": "green",
            "usable_in_quote": True,
            "visible_operational": True,
        }

    return {
        "status": "da_verificare",
        "badge": "da verificare",
        "color": "yellow",
        "usable_in_quote": False,
        "visible_operational": True,
    }


def enrich_raw_item(db, table, key, info):
    name = display_name_from_key(key, info)
    stock = parse_float(info.get("stock"))
    cost = parse_float(info.get("weighted_average_cost", info.get("cost_per_unit")))
    purchases = raw_purchase_count(db, key, table, name)
    last = raw_last_purchase(db, key, table, name)

    if last:
        last_cost = parse_float(last.get("unit_cost"))
        last_supplier = last.get("supplier", info.get("supplier", ""))
        last_date = last.get("date", "")
    else:
        last_cost = parse_float(info.get("last_unit_cost", info.get("cost_per_unit")))
        last_supplier = info.get("last_supplier", info.get("supplier", ""))
        last_date = info.get("last_purchase_date", info.get("last_added", ""))

    min_stock = parse_float(info.get("min_stock"))
    state = inventory_status(stock, cost, purchases, min_stock)

    info["weighted_average_cost"] = cost
    info["cost_per_unit"] = cost
    info["purchase_count"] = purchases
    info["last_unit_cost"] = last_cost
    info["last_supplier"] = last_supplier
    info["last_purchase_date"] = last_date
    info["inventory_status"] = state["status"]
    info["inventory_badge"] = state["badge"]
    info["inventory_color"] = state["color"]
    info["usable_in_quote"] = state["usable_in_quote"]
    info["visible_operational"] = state["visible_operational"]

    return info
'''


AGGREGATED_RAW_ITEMS = r'''
def aggregated_raw_items(db, table_filter=None, operational_only=False):
    groups = {}

    for table in ("materials", "components"):
        if table_filter and table != table_filter:
            continue

        table_data = db.get(table, {})
        if not isinstance(table_data, dict):
            continue

        for key, info in table_data.items():
            if not isinstance(info, dict):
                continue

            enrich_raw_item(db, table, key, info)

            if operational_only and not info.get("visible_operational", True):
                continue

            name = display_name_from_key(key, info)

            signature = (
                table,
                str(name).lower(),
                str(info.get("section", "")).lower(),
                str(info.get("category", "")).lower(),
                str(info.get("subcategory", "")).lower(),
                str(info.get("size", "")).lower(),
                str(info.get("thickness", "")).lower(),
                str(info.get("unit", "")).lower(),
            )

            g = groups.setdefault(signature, {
                "table": table,
                "key": key,
                "name": name,
                "section": info.get("section", ""),
                "category": info.get("category", ""),
                "subcategory": info.get("subcategory", ""),
                "size": info.get("size", ""),
                "thickness": info.get("thickness", ""),
                "unit": info.get("unit", ""),
                "stock": 0.0,
                "value": 0.0,
                "suppliers": [],
                "last_added": "",
                "last_purchase_date": "",
                "last_supplier": "",
                "last_unit_cost": 0.0,
                "purchase_count": 0,
                "min_stock": parse_float(info.get("min_stock")),
            })

            stock = parse_float(info.get("stock"))
            cpu = parse_float(info.get("weighted_average_cost", info.get("cost_per_unit")))
            value = stock * cpu

            g["stock"] += stock
            g["value"] += value
            g["purchase_count"] += int(parse_float(info.get("purchase_count")))
            g["min_stock"] = max(parse_float(g.get("min_stock")), parse_float(info.get("min_stock")))

            supplier = info.get("supplier") or "Senza fornitore"
            g["suppliers"].append(
                f"{supplier}: {stock:.2f} {info.get('unit','')} a {cpu:.2f} €/u"
            )

            if str(info.get("last_added", "")) > str(g.get("last_added", "")):
                g["last_added"] = info.get("last_added", "")

            if str(info.get("last_purchase_date", "")) > str(g.get("last_purchase_date", "")):
                g["last_purchase_date"] = info.get("last_purchase_date", "")
                g["last_supplier"] = info.get("last_supplier", info.get("supplier", ""))
                g["last_unit_cost"] = parse_float(info.get("last_unit_cost", cpu))

    out = []

    for g in groups.values():
        g["cost_per_unit"] = g["value"] / g["stock"] if g["stock"] else 0.0
        g["weighted_average_cost"] = g["cost_per_unit"]
        g["supplier_details"] = " | ".join(g["suppliers"])

        state = inventory_status(
            g["stock"],
            g["weighted_average_cost"],
            g["purchase_count"],
            g.get("min_stock", 0),
        )

        g["inventory_status"] = state["status"]
        g["inventory_badge"] = state["badge"]
        g["inventory_color"] = state["color"]
        g["usable_in_quote"] = state["usable_in_quote"]
        g["visible_operational"] = state["visible_operational"]

        out.append(g)

    return sorted(out, key=lambda x: (
        x.get("inventory_status") == "mai_acquistato",
        x.get("category", ""),
        x.get("subcategory", ""),
        x.get("name", ""),
    ))
'''


ADD_PURCHASE = r'''
def add_purchase(db, payload):
    selected_section = payload.get("section") or section_label(db, "materials")
    scope = scope_from_display(db, selected_section)
    table = "materials" if scope == "materials" else "components"

    category = (payload.get("category") or "").strip()
    subcategory = (payload.get("subcategory") or "").strip()
    size = (payload.get("size") or "").strip()
    thickness = (payload.get("thickness") or "").strip()
    unit = (payload.get("unit") or "pz").strip() or "pz"

    name = (
        payload.get("name")
        or build_purchase_item_name(db, selected_section, category, subcategory, size, thickness)
    ).strip()

    qty = parse_float(payload.get("quantity"))
    total = parse_float(payload.get("total_cost"))
    supplier = (payload.get("supplier") or "Senza fornitore").strip()
    note = payload.get("note", payload.get("notes", ""))

    if not name:
        raise ValueError("Nome articolo non generabile: compila almeno categoria/sottocategoria/formato.")

    if qty <= 0 or total <= 0:
        raise ValueError("Quantità e costo totale devono essere maggiori di zero.")

    unit_cost = total / qty

    supplier_info = db.setdefault("suppliers", {}).setdefault(
        supplier,
        {"name": supplier, "sections": [], "links": []}
    )

    if selected_section not in supplier_info.setdefault("sections", []):
        supplier_info["sections"].append(selected_section)

    if category:
        link = {
            "section": selected_section,
            "category": category,
            "subcategory": subcategory
        }

        if link not in supplier_info.setdefault("links", []):
            supplier_info["links"].append(link)

    key = (
        find_supplier_item_key(
            db,
            table,
            name,
            selected_section,
            category,
            subcategory,
            size,
            thickness,
            supplier,
        )
        or supplier_item_key(
            name,
            selected_section,
            category,
            subcategory,
            size,
            thickness,
            supplier,
        )
    )

    entry = db.setdefault(table, {}).get(key, {
        "display_name": name,
        "unit": unit,
        "cost_per_unit": unit_cost,
        "weighted_average_cost": unit_cost,
        "stock": 0,
        "category": category,
        "subcategory": subcategory,
        "size": size,
        "thickness": thickness,
        "section": selected_section,
        "supplier": supplier,
        "last_added": "",
        "last_unit_cost": 0.0,
        "last_supplier": "",
        "last_purchase_date": "",
        "purchase_count": 0,
        "min_stock": 0.0,
    })

    old_qty = parse_float(entry.get("stock"))
    old_cost = parse_float(entry.get("weighted_average_cost", entry.get("cost_per_unit")))
    old_value = old_qty * old_cost
    new_qty = old_qty + qty
    new_average_cost = (old_value + total) / new_qty if new_qty else 0.0

    purchase_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    purchase_date_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry.update({
        "display_name": name,
        "unit": unit,
        "category": category,
        "subcategory": subcategory,
        "size": size,
        "thickness": thickness,
        "section": selected_section,
        "supplier": supplier,
        "stock": new_qty,
        "cost_per_unit": new_average_cost,
        "weighted_average_cost": new_average_cost,
        "last_unit_cost": unit_cost,
        "last_supplier": supplier,
        "last_purchase_date": purchase_date,
        "last_added": purchase_date,
        "purchase_count": int(parse_float(entry.get("purchase_count"))) + 1,
    })

    db[table][key] = entry

    history_row = {
        "id": f"PUR-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "date": purchase_date,
        "date_iso": purchase_date_iso,
        "table": table,
        "key": key,
        "name": name,
        "section": selected_section,
        "category": category,
        "subcategory": subcategory,
        "size": size,
        "thickness": thickness,
        "unit": unit,
        "quantity": qty,
        "total_cost": total,
        "unit_cost": unit_cost,
        "supplier": supplier,
        "note": note,
    }

    db.setdefault("purchase_history", []).append(history_row)

    ensure_category(db, scope, category, subcategory)
    enrich_raw_item(db, table, key, entry)

    return {
        "table": table,
        "key": key,
        "item": entry,
        "purchase": history_row,
    }
'''


CALCULATE_QUOTE = r'''
def calculate_quote(db, payload):
    rows = payload.get("rows", []) or []
    estimates = payload.get("estimates", []) or []

    checked_rows = []
    blocked = []

    for row in rows:
        row_name = row.get("name") or row.get("material") or row.get("item") or ""
        item, table, key = get_raw_item(db, row_name)

        if item:
            enrich_raw_item(db, table, key, item)

            if not item.get("usable_in_quote"):
                blocked.append({
                    "name": display_name_from_key(key, item),
                    "reason": "stock o costo medio non valorizzato",
                    "stock": parse_float(item.get("stock")),
                    "weighted_average_cost": parse_float(
                        item.get("weighted_average_cost", item.get("cost_per_unit"))
                    ),
                    "badge": item.get("inventory_badge", "da verificare"),
                })

            qty = parse_float(row.get("qty", row.get("quantity", 1)))
            row["unit_cost"] = parse_float(
                item.get("weighted_average_cost", item.get("cost_per_unit"))
            )
            row["cost"] = qty * row["unit_cost"]

        checked_rows.append(row)

    if blocked:
        names = ", ".join([x["name"] for x in blocked[:5]])
        raise ValueError(
            "Non puoi usare nei preventivi articoli con stock 0 o costo medio 0. "
            f"Articoli da verificare: {names}"
        )

    base = (
        sum(parse_float(x.get("cost")) for x in checked_rows)
        + sum(
            parse_float(
                x.get(
                    "cost",
                    parse_float(x.get("qty")) * parse_float(x.get("unit_cost"))
                )
            )
            for x in estimates
        )
    )

    base += parse_float(payload.get("hours")) * parse_float(payload.get("rate"))
    base += (
        parse_float(payload.get("packaging"))
        + parse_float(payload.get("energy"))
        + parse_float(payload.get("wear"))
    )

    commission = parse_float(payload.get("commission")) / 100
    margin = parse_float(payload.get("margin", 30)) / 100
    discount = parse_float(payload.get("discount")) / 100

    if commission + margin >= 1:
        raise ValueError("Margine e commissioni sono troppo alti.")

    if discount >= 1:
        raise ValueError("Lo sconto deve essere inferiore al 100%.")

    min_price = base / (1 - commission) if commission < 1 else base
    recommended = base / (1 - commission - margin)
    discounted = recommended * (1 - discount)
    premium = recommended * 1.2

    return {
        "real": round(base, 2),
        "min": round(min_price, 2),
        "recommended": round(recommended, 2),
        "discounted": round(discounted, 2),
        "premium": round(premium, 2),
        "rows": checked_rows,
        "blocked": blocked,
    }
'''


INVENTORY_ENDPOINTS = r'''
@app.get("/api/purchase-history")
def purchase_history_api():
    db = load_db()
    rows = db.get("purchase_history", [])
    if not isinstance(rows, list):
        return []
    return list(reversed(rows))


@app.get("/api/inventory/active")
def active_inventory():
    db = load_db()
    return [
        x
        for x in aggregated_raw_items(db, operational_only=True)
        if x.get("usable_in_quote")
    ]


@app.get("/api/inventory/quality")
def inventory_quality():
    db = load_db()
    rows = aggregated_raw_items(db)

    counters = {
        "total": len(rows),
        "active": 0,
        "never_purchased": 0,
        "to_check": 0,
        "out_of_stock": 0,
        "low_stock": 0,
        "real_value": 0.0,
    }

    for row in rows:
        status = row.get("inventory_status")

        if status == "attivo":
            counters["active"] += 1
        elif status == "mai_acquistato":
            counters["never_purchased"] += 1
        elif status == "da_verificare":
            counters["to_check"] += 1
        elif status == "esaurito":
            counters["out_of_stock"] += 1
        elif status == "sotto_scorta":
            counters["low_stock"] += 1

        if row.get("usable_in_quote"):
            counters["real_value"] += parse_float(row.get("value"))

    counters["real_value"] = round(counters["real_value"], 2)
    return counters
'''


def patch_normalize_db(source: str) -> str:
    if 'data.setdefault("purchase_history", [])' in source:
        return source

    insert = r'''
    data.setdefault("purchase_history", [])

    for table in ("materials", "components"):
        table_data = data.setdefault(table, {})
        if not isinstance(table_data, dict):
            data[table] = {}
            continue

        for key, info in list(table_data.items()):
            if not isinstance(info, dict):
                table_data.pop(key, None)
                continue

            info.setdefault("display_name", display_name_from_key(key, info))
            info.setdefault("stock", 0.0)
            info.setdefault("cost_per_unit", 0.0)
            info.setdefault("weighted_average_cost", info.get("cost_per_unit", 0.0))
            info.setdefault("last_unit_cost", info.get("cost_per_unit", 0.0))
            info.setdefault("last_supplier", info.get("supplier", ""))
            info.setdefault("last_purchase_date", info.get("last_added", ""))
            info.setdefault("purchase_count", 0)
            info.setdefault("min_stock", 0.0)

            enrich_raw_item(data, table, key, info)

'''

    pattern = r"(def normalize_db\(data: Any\) -> dict:\n(?:(?:    .*\n)|(?:\n))*?)(    return data\n)"
    match = re.search(pattern, source, flags=re.MULTILINE)

    if not match:
        raise RuntimeError("normalize_db non trovata o non patchabile")

    return source[:match.start()] + match.group(1) + insert + match.group(2) + source[match.end():]


def patch_main_endpoints(source: str) -> str:
    if 'def purchase_history_api' in source:
        return source

    target = '@app.post("/api/purchase")\ndef purchase(payload: Payload): return mutate(add_purchase, payload.data)\n'
    if target not in source:
        raise RuntimeError("Endpoint /api/purchase non trovato nella forma prevista")

    return source.replace(target, target + "\n" + INVENTORY_ENDPOINTS.strip() + "\n")


def main():
    legacy = LEGACY.read_text(encoding="utf-8")
    main_py = MAIN.read_text(encoding="utf-8")

    legacy = insert_after_function(
        legacy,
        "get_raw_item",
        HELPERS,
        "def inventory_status("
    )

    legacy = patch_normalize_db(legacy)
    legacy = replace_function(legacy, "aggregated_raw_items", AGGREGATED_RAW_ITEMS)
    legacy = replace_function(legacy, "add_purchase", ADD_PURCHASE)
    legacy = replace_function(legacy, "calculate_quote", CALCULATE_QUOTE)

    main_py = patch_main_endpoints(main_py)

    LEGACY.write_text(legacy, encoding="utf-8")
    MAIN.write_text(main_py, encoding="utf-8")

    print("Patch completata.")
    print(f"Aggiornato: {LEGACY}")
    print(f"Aggiornato: {MAIN}")


if __name__ == "__main__":
    main()
