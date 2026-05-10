from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN = ROOT / "backend" / "app" / "main.py"


WORKFLOW_HELPERS = r'''

# ---------------------------------------------------------------------------
# Workflow avanzato v39.5 - Preventivi, impostazioni, ricerca globale, dettagli
# ---------------------------------------------------------------------------

def default_business_settings():
    return {
        "hourly_rate": 20.0,
        "default_margin": 50.0,
        "default_commission": 0.0,
        "default_discount": 0.0,
        "default_packaging": 0.0,
        "default_energy": 1.0,
        "default_wear": 1.0,
        "quote_validity_days": 15,
        "marketplaces": {
            "Vendita diretta": {"commission": 0.0},
            "Instagram": {"commission": 0.0},
            "Vinted": {"commission": 5.0},
            "Etsy": {"commission": 12.0},
            "Shopify": {"commission": 3.0},
        },
    }


def business_settings(db):
    settings = db.setdefault("business_settings", default_business_settings())
    base = default_business_settings()

    for key, value in base.items():
        if key not in settings:
            settings[key] = value

    settings.setdefault("marketplaces", {})
    for key, value in base["marketplaces"].items():
        settings["marketplaces"].setdefault(key, value)

    return settings


def update_business_settings(db, payload):
    settings = business_settings(db)

    numeric_fields = [
        "hourly_rate",
        "default_margin",
        "default_commission",
        "default_discount",
        "default_packaging",
        "default_energy",
        "default_wear",
        "quote_validity_days",
    ]

    for key in numeric_fields:
        if key in payload:
            settings[key] = parse_float(payload.get(key))

    marketplaces = payload.get("marketplaces")
    if isinstance(marketplaces, dict):
        settings["marketplaces"] = marketplaces

    return settings


def quote_rows_cost(rows):
    return sum(parse_float(row.get("cost")) for row in rows or [])


def quote_status_label(status):
    labels = {
        "draft": "bozza",
        "sent": "inviato",
        "accepted": "accettato",
        "rejected": "rifiutato",
        "expired": "scaduto",
    }
    return labels.get(status, status or "bozza")


def quote_status_color(status):
    colors = {
        "draft": "gray",
        "sent": "blue",
        "accepted": "green",
        "rejected": "red",
        "expired": "orange",
    }
    return colors.get(status, "gray")


def next_quote_id(db):
    existing = db.setdefault("quotes", [])
    return f"Q-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(existing) + 1}"


def save_quote(db, payload):
    name = (payload.get("name") or payload.get("title") or "Preventivo senza nome").strip()
    customer = (payload.get("customer") or "").strip()
    status = payload.get("status") or "draft"
    rows = payload.get("rows", []) or []

    calc_payload = {
        **payload,
        "rows": rows,
        "estimates": payload.get("estimates", payload.get("estimated_materials", [])) or [],
    }

    result = calculate_quote(db, calc_payload)

    quote_id = payload.get("id") or next_quote_id(db)
    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    quote = {
        "id": quote_id,
        "date": payload.get("date") or now,
        "date_iso": payload.get("date_iso") or now_iso,
        "updated_at": now,
        "customer": customer,
        "name": name,
        "description": payload.get("description", ""),
        "status": status,
        "status_label": quote_status_label(status),
        "status_color": quote_status_color(status),
        "rows": rows,
        "estimates": payload.get("estimates", payload.get("estimated_materials", [])) or [],
        "hours": parse_float(payload.get("hours")),
        "rate": parse_float(payload.get("rate")),
        "packaging": parse_float(payload.get("packaging")),
        "energy": parse_float(payload.get("energy")),
        "wear": parse_float(payload.get("wear")),
        "commission": parse_float(payload.get("commission")),
        "margin": parse_float(payload.get("margin")),
        "discount": parse_float(payload.get("discount")),
        "marketplace": payload.get("marketplace", "Vendita diretta"),
        "notes": payload.get("notes", ""),
        "result": result,
        "real": result.get("real", result.get("real_cost", 0)),
        "min": result.get("min", result.get("min_price", 0)),
        "recommended": result.get("recommended", 0),
        "discounted": result.get("discounted", 0),
        "premium": result.get("premium", 0),
        "potential_value": result.get("discounted") or result.get("recommended") or 0,
    }

    quotes = db.setdefault("quotes", [])
    replaced = False

    for index, existing in enumerate(quotes):
        if existing.get("id") == quote_id:
            quotes[index] = {**existing, **quote}
            replaced = True
            break

    if not replaced:
        quotes.append(quote)

    return quote


def list_quotes(db):
    quotes = db.setdefault("quotes", [])
    for quote in quotes:
        status = quote.get("status", "draft")
        quote["status_label"] = quote_status_label(status)
        quote["status_color"] = quote_status_color(status)
    return sorted(quotes, key=lambda x: x.get("date_iso", x.get("date", "")), reverse=True)


def get_quote(db, quote_id):
    for quote in db.setdefault("quotes", []):
        if quote.get("id") == quote_id:
            status = quote.get("status", "draft")
            quote["status_label"] = quote_status_label(status)
            quote["status_color"] = quote_status_color(status)
            return quote
    raise ValueError("Preventivo non trovato")


def update_quote_status(db, quote_id, status):
    quote = get_quote(db, quote_id)
    quote["status"] = status
    quote["status_label"] = quote_status_label(status)
    quote["status_color"] = quote_status_color(status)
    quote["updated_at"] = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    return quote


def quote_to_product(db, quote_id, payload=None):
    payload = payload or {}
    quote = get_quote(db, quote_id)

    product_name = (
        payload.get("name")
        or quote.get("name")
        or "Prodotto da preventivo"
    ).strip()

    if not product_name:
        raise ValueError("Nome prodotto richiesto")

    bom = []
    for row in quote.get("rows", []) or []:
        material_name = row.get("name") or row.get("key") or row.get("label")
        if not material_name:
            continue
        bom.append({
            "name": material_name,
            "qty": parse_float(row.get("qty")),
            "unit": row.get("unit", ""),
            "label": row.get("label", material_name),
        })

    product_payload = {
        "name": product_name,
        "section": payload.get("section") or section_label(db, "products"),
        "category": payload.get("category") or payload.get("product_category") or "Prodotti da preventivo",
        "subcategory": payload.get("subcategory") or "Da preventivo",
        "collection": payload.get("collection") or "Custom Wood",
        "tags": payload.get("tags") or "preventivo, custom",
        "unit": payload.get("unit") or "pz",
        "labor_hours": parse_float(quote.get("hours")),
        "hourly_rate": parse_float(quote.get("rate")),
        "extra_unit_cost": parse_float(quote.get("packaging")) + parse_float(quote.get("energy")) + parse_float(quote.get("wear")),
        "stock": parse_float(payload.get("stock", 0)),
        "bom": bom,
        "description": payload.get("description") or f"Creato dal preventivo {quote_id}",
    }

    product = create_or_update_product(db, product_payload)

    quote["converted_to_product"] = product_name
    quote["status"] = "accepted"
    quote["status_label"] = quote_status_label("accepted")
    quote["status_color"] = quote_status_color("accepted")
    quote["updated_at"] = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    return {
        "ok": True,
        "quote": quote,
        "product_name": product_name,
        "product": product,
    }


def raw_detail(db, table, key):
    if table not in ("materials", "components"):
        raise ValueError("Tipo articolo non valido")

    info = db.get(table, {}).get(key)
    if not isinstance(info, dict):
        raise ValueError("Articolo non trovato")

    enrich_raw_item(db, table, key, info)

    name = display_name_from_key(key, info)
    history = []

    for row in purchase_history(db):
        if row.get("key") == key or str(row.get("name", "")).strip().lower() == str(name).strip().lower():
            history.append(row)

    used_in_products = []
    for product_name, product in db.get("products", {}).items():
        for bom_row in product.get("bom", []) or []:
            bom_name = bom_row.get("name", "")
            if bom_name == key or bom_name == name:
                used_in_products.append({
                    "product": product_name,
                    "qty": parse_float(bom_row.get("qty")),
                    "unit": bom_row.get("unit", info.get("unit", "")),
                })

    return {
        "table": table,
        "key": key,
        "name": name,
        "item": info,
        "purchase_history": sorted(history, key=lambda x: x.get("date_iso", x.get("date", "")), reverse=True),
        "used_in_products": used_in_products,
        "stock_value": parse_float(info.get("stock")) * parse_float(info.get("weighted_average_cost", info.get("cost_per_unit"))),
    }


def global_search(db, query):
    q = str(query or "").strip().lower()
    if not q:
        return {
            "materials": [],
            "products": [],
            "customers": [],
            "suppliers": [],
            "quotes": [],
            "sales": [],
        }

    def match(*values):
        return q in " ".join(str(v or "") for v in values).lower()

    materials = []
    for table in ("materials", "components"):
        for key, info in db.get(table, {}).items():
            if not isinstance(info, dict):
                continue
            name = display_name_from_key(key, info)
            if match(name, info.get("section"), info.get("category"), info.get("subcategory"), info.get("supplier"), info.get("size"), info.get("thickness")):
                enrich_raw_item(db, table, key, info)
                materials.append({
                    "type": "material",
                    "table": table,
                    "key": key,
                    "name": name,
                    "subtitle": " · ".join([x for x in [info.get("section"), info.get("category"), info.get("subcategory"), info.get("supplier")] if x]),
                    "status": info.get("inventory_badge", ""),
                })

    products = []
    for name, info in db.get("products", {}).items():
        if match(name, info.get("category"), info.get("subcategory"), info.get("collection"), info.get("tags")):
            products.append({
                "type": "product",
                "name": name,
                "subtitle": " · ".join([x for x in [info.get("category"), info.get("subcategory"), info.get("collection")] if x]),
                "stock": parse_float(info.get("stock")),
            })

    customers = []
    for name, info in db.get("customers", {}).items():
        if match(name, info.get("notes")):
            customers.append({"type": "customer", "name": name, "subtitle": info.get("notes", "")})

    suppliers = []
    for name, info in db.get("suppliers", {}).items():
        if match(name, info.get("sections"), info.get("links")):
            suppliers.append({"type": "supplier", "name": name, "subtitle": ", ".join(info.get("sections", []) or [])})

    quotes = []
    for quote in db.get("quotes", []) or []:
        if match(quote.get("id"), quote.get("name"), quote.get("customer"), quote.get("status_label")):
            quotes.append({
                "type": "quote",
                "id": quote.get("id"),
                "name": quote.get("name"),
                "subtitle": f"{quote.get('customer','')} · {quote.get('status_label','bozza')}",
                "value": quote.get("potential_value", quote.get("recommended", 0)),
            })

    sales = []
    for index, sale in enumerate(db.get("sales", []) or []):
        if match(sale.get("product"), sale.get("customer"), sale.get("source"), sale.get("date")):
            sales.append({
                "type": "sale",
                "id": index,
                "name": sale.get("product"),
                "subtitle": f"{sale.get('customer','')} · {sale.get('date','')}",
                "value": parse_float(sale.get("total")),
            })

    return {
        "materials": materials[:20],
        "products": products[:20],
        "customers": customers[:20],
        "suppliers": suppliers[:20],
        "quotes": quotes[:20],
        "sales": sales[:20],
    }


def workflow_alerts(db):
    quality_rows = aggregated_raw_items(db)
    quotes = db.get("quotes", []) or []
    products = db.get("products", {}) or {}

    to_check = [x for x in quality_rows if x.get("inventory_status") == "da_verificare"]
    never = [x for x in quality_rows if x.get("inventory_status") == "mai_acquistato"]
    low = [x for x in quality_rows if x.get("inventory_status") == "sotto_scorta"]
    open_quotes = [q for q in quotes if q.get("status", "draft") in ("draft", "sent")]

    low_product_stock = []
    for name, info in products.items():
        if parse_float(info.get("stock")) <= 0:
            low_product_stock.append({"name": name, "stock": parse_float(info.get("stock"))})

    return {
        "materials_to_check": len(to_check),
        "never_purchased": len(never),
        "low_stock_materials": len(low),
        "open_quotes": len(open_quotes),
        "low_product_stock": len(low_product_stock),
        "potential_quotes_value": round(sum(parse_float(q.get("potential_value", q.get("recommended", 0))) for q in open_quotes), 2),
        "items": {
            "materials_to_check": to_check[:8],
            "low_stock_materials": low[:8],
            "open_quotes": open_quotes[:8],
            "low_product_stock": low_product_stock[:8],
        }
    }
'''


MAIN_ENDPOINTS = r'''

@app.get("/api/settings/business")
def get_business_settings():
    return business_settings(load_db())


@app.post("/api/settings/business")
def set_business_settings(payload: Payload):
    return mutate(update_business_settings, payload.data)


@app.get("/api/quotes")
def quotes_api():
    return list_quotes(load_db())


@app.post("/api/quotes")
def save_quote_api(payload: Payload):
    return mutate(save_quote, payload.data)


@app.get("/api/quotes/{quote_id:path}")
def get_quote_api(quote_id: str):
    try:
        return get_quote(load_db(), quote_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@app.post("/api/quotes/{quote_id:path}/status")
def quote_status_api(quote_id: str, payload: Payload):
    status = payload.data.get("status") or "draft"
    return mutate(update_quote_status, quote_id, status)


@app.post("/api/quotes/{quote_id:path}/to-product")
def quote_to_product_api(quote_id: str, payload: Payload):
    return mutate(quote_to_product, quote_id, payload.data)


@app.get("/api/raw-detail/{table}/{key:path}")
def raw_detail_api(table: str, key: str):
    try:
        return raw_detail(load_db(), table, key)
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@app.get("/api/global-search")
def global_search_api(q: str = ""):
    return global_search(load_db(), q)


@app.get("/api/workflow/alerts")
def workflow_alerts_api():
    return workflow_alerts(load_db())
'''


def patch_empty_db(source: str) -> str:
    if '"quotes": []' in source and '"business_settings": default_business_settings()' in source:
        return source

    old = '''        "materials": {}, "components": {}, "products": {}, "sales": [], "customers": {}, "suppliers": {},'''
    new = '''        "materials": {}, "components": {}, "products": {}, "sales": [], "quotes": [], "customers": {}, "suppliers": {},
        "business_settings": default_business_settings(),'''

    if old not in source:
        raise RuntimeError("Blocco empty_db non trovato")

    return source.replace(old, new, 1)


def patch_normalize_db(source: str) -> str:
    if 'data.setdefault("quotes", [])' in source and 'business_settings(data)' in source:
        return source

    marker = "    return data\n"
    insert = '''    data.setdefault("quotes", [])
    business_settings(data)

'''
    idx = source.find(marker, source.find("def normalize_db"))
    if idx == -1:
        raise RuntimeError("return data di normalize_db non trovato")

    return source[:idx] + insert + source[idx:]


def patch_report(source: str) -> str:
    if '"quotes_open": len([q for q in db.get("quotes", [])' in source:
        return source

    marker = '''        "low_stock": low_stock[:20],
    }'''
    replacement = '''        "low_stock": low_stock[:20],
        "quotes_open": len([q for q in db.get("quotes", []) if q.get("status", "draft") in ("draft", "sent")]),
        "quotes_value": round(sum(parse_float(q.get("potential_value", q.get("recommended", 0))) for q in db.get("quotes", []) if q.get("status", "draft") in ("draft", "sent")), 2),
    }'''

    if marker not in source:
        raise RuntimeError("Blocco finale report non trovato")

    return source.replace(marker, replacement, 1)


def patch_legacy():
    source = LEGACY.read_text(encoding="utf-8")

    if "Workflow avanzato v39.5" not in source:
        source += "\n\n" + WORKFLOW_HELPERS.strip() + "\n"

    source = patch_empty_db(source)
    source = patch_normalize_db(source)
    source = patch_report(source)

    LEGACY.write_text(source, encoding="utf-8")


def patch_main():
    source = MAIN.read_text(encoding="utf-8")

    if "def get_business_settings" not in source:
        source += "\n\n" + MAIN_ENDPOINTS.strip() + "\n"

    MAIN.write_text(source, encoding="utf-8")


def main():
    patch_legacy()
    patch_main()
    print("Patch backend workflow avanzato completata.")
    print(f"Aggiornato: {LEGACY}")
    print(f"Aggiornato: {MAIN}")


if __name__ == "__main__":
    main()
