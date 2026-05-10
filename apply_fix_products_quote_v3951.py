from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN = ROOT / "frontend" / "src" / "main.jsx"


NEW_CALCULATE_QUOTE = r'''
def calculate_quote(db, payload):
    rows = payload.get("rows", []) or []
    estimates = payload.get("estimates", payload.get("estimated_materials", [])) or []

    checked_rows = []
    blocked = []

    for row in rows:
        row = dict(row or {})
        row_name = row.get("name") or row.get("material") or row.get("item") or row.get("key") or ""
        qty = parse_float(row.get("qty", row.get("quantity", 1)))

        frontend_unit_cost = parse_float(
            row.get("unit_cost", row.get("cost_per_unit", row.get("weighted_average_cost", 0)))
        )
        frontend_stock = parse_float(row.get("stock", row.get("available", 0)))

        # Se il frontend passa costo e stock dalla riga aggregata, usiamo quelli.
        # Questo evita falsi blocchi quando il key aggregato non coincide con la riga raw originale.
        if frontend_unit_cost > 0:
            if frontend_stock > 0 and qty > frontend_stock:
                blocked.append({
                    "name": row.get("label") or row_name,
                    "reason": "stock insufficiente",
                    "stock": frontend_stock,
                    "weighted_average_cost": frontend_unit_cost,
                    "badge": "stock insufficiente",
                })

            row["unit_cost"] = frontend_unit_cost
            row["cost_per_unit"] = frontend_unit_cost
            row["weighted_average_cost"] = frontend_unit_cost
            row["cost"] = qty * frontend_unit_cost
            checked_rows.append(row)
            continue

        item, table, key = get_raw_item(db, row_name)

        if item:
            enrich_raw_item(db, table, key, item)

            unit_cost = parse_float(item.get("weighted_average_cost", item.get("cost_per_unit")))
            stock = parse_float(item.get("stock"))

            if stock <= 0 or unit_cost <= 0:
                blocked.append({
                    "name": display_name_from_key(key, item),
                    "reason": "stock o costo medio non valorizzato",
                    "stock": stock,
                    "weighted_average_cost": unit_cost,
                    "badge": item.get("inventory_badge", "da verificare"),
                })

            if stock > 0 and qty > stock:
                blocked.append({
                    "name": display_name_from_key(key, item),
                    "reason": "stock insufficiente",
                    "stock": stock,
                    "weighted_average_cost": unit_cost,
                    "badge": "stock insufficiente",
                })

            row["unit_cost"] = unit_cost
            row["cost_per_unit"] = unit_cost
            row["weighted_average_cost"] = unit_cost
            row["cost"] = qty * unit_cost
            row.setdefault("label", display_name_from_key(key, item))
        else:
            manual_cost = parse_float(row.get("cost"))
            if manual_cost <= 0:
                blocked.append({
                    "name": row.get("label") or row_name or "Riga senza nome",
                    "reason": "materiale non trovato e costo non valorizzato",
                    "stock": 0,
                    "weighted_average_cost": 0,
                    "badge": "da verificare",
                })

        checked_rows.append(row)

    if blocked:
        names = ", ".join([x["name"] for x in blocked[:5]])
        raise ValueError(
            "Non puoi usare nei preventivi articoli con stock 0, costo medio 0 o stock insufficiente. "
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
        "real_cost": round(base, 2),
        "min": round(min_price, 2),
        "min_price": round(min_price, 2),
        "recommended": round(recommended, 2),
        "discounted": round(discounted, 2),
        "premium": round(premium, 2),
        "rows": checked_rows,
        "blocked": blocked,
    }
'''


def replace_function(source: str, function_name: str, new_code: str) -> str:
    pattern = rf"^def {function_name}\(.*?\):\n(?:(?:    .*\n)|(?:\n))*"
    match = re.search(pattern, source, flags=re.MULTILINE)

    if not match:
        raise RuntimeError(f"Funzione non trovata: {function_name}")

    return source[:match.start()] + new_code.rstrip() + "\n\n" + source[match.end():]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Blocco non trovato: {label}")
    return text.replace(old, new, 1)


def patch_backend():
    source = LEGACY.read_text(encoding="utf-8")
    source = replace_function(source, "calculate_quote", NEW_CALCULATE_QUOTE)
    LEGACY.write_text(source, encoding="utf-8")
    print("Backend: calculate_quote corretto.")


def patch_frontend():
    s = MAIN.read_text(encoding="utf-8")

    old = """function ProductWarehouse({ products, refresh, toast, onEdit }) {"""
    new = """function ProductWarehouse({ products, refresh, toast, onEdit, onDelete }) {"""
    if old in s:
        s = s.replace(old, new, 1)

    old = """        { key: 'act', label: '', render: r => <button onClick={() => onEdit(r)}>Modifica scheda</button> }"""
    new = """        { key: 'act', label: 'Azioni', render: r => <div className="table-actions">
          <button className="ghost" onClick={() => onEdit(r)}>Modifica</button>
          <button className="ghost danger" onClick={() => onDelete(r.name)}>Elimina</button>
        </div> }"""
    if old in s:
        s = s.replace(old, new, 1)
    elif "onDelete(r.name)" not in s:
        raise RuntimeError("Colonna azioni prodotti non trovata")

    old = """    {area === 'warehouse' && <ProductWarehouse products={products} refresh={() => { refresh(); refreshMovements(); }} toast={toast} onEdit={editProduct} />}"""
    new = """    {area === 'warehouse' && <ProductWarehouse products={products} refresh={() => { refresh(); refreshMovements(); }} toast={toast} onEdit={editProduct} onDelete={remove} />}"""
    if old in s:
        s = s.replace(old, new, 1)

    old = """    setRows(v => [...v, {
      name: materialKey,
      qty: qn,
      cost: qn * Number((it.weighted_average_cost ?? it.cost_per_unit) || 0),
      label: it.name,
      unit: it.unit || '',
      category: it.category || '',
      supplier: it.supplier_details || '',
    }]);"""

    new = """    const unitCost = Number((it.weighted_average_cost ?? it.cost_per_unit) || 0);
    setRows(v => [...v, {
      name: materialKey,
      key: materialKey,
      qty: qn,
      stock: Number(it.stock || 0),
      unit_cost: unitCost,
      cost_per_unit: unitCost,
      weighted_average_cost: unitCost,
      cost: qn * unitCost,
      label: it.name,
      unit: it.unit || '',
      category: it.category || '',
      supplier: it.supplier_details || '',
    }]);"""

    if old in s:
        s = s.replace(old, new, 1)
    elif "unit_cost: unitCost" not in s:
        raise RuntimeError("Blocco addMaterial preventivo non trovato")

    MAIN.write_text(s, encoding="utf-8")
    print("Frontend: azioni prodotti e righe preventivo corrette.")


def main():
    patch_backend()
    patch_frontend()
    print("Patch v39.5.1 completata.")


if __name__ == "__main__":
    main()
