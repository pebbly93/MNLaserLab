from __future__ import annotations
from pathlib import Path

from typing import Any
from datetime import datetime
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .legacy_logic import *

app = FastAPI(title="MN Laser Lab Manager Web API", version="39.0-product-warehouse")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"http://(localhost|127\\.0\\.0\\.1|192\\.168\\.\\d+\\.\\d+|10\\.\\d+\\.\\d+\\.\\d+|172\\.(1[6-9]|2\\d|3[0-1])\\.\\d+\\.\\d+):(5173|8000)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Payload(BaseModel):
    data: dict[str, Any] = {}

@app.on_event("startup")
def startup():
    init_sqlite_db(); load_db()


def mutate(fn, *args, **kwargs):
    db = load_db()
    try:
        result = fn(db, *args, **kwargs)
        save_db(db)
        return result
    except ValueError as exc:
        raise HTTPException(400, str(exc))

# ---------------------------------------------------------------------------
# v41.3.9 - Runtime diagnostics
# ---------------------------------------------------------------------------

@app.get("/api/debug/runtime")
def debug_runtime_info():
    import os
    import sys
    import platform
    import inspect
    from pathlib import Path

    try:
        import app.legacy_logic as legacy_logic_module
        legacy_file = inspect.getfile(legacy_logic_module)
    except Exception as e:
        legacy_file = f"ERROR: {e}"

    try:
        main_file = __file__
    except Exception:
        main_file = "unknown"

    routes = []
    try:
        for r in app.routes:
            methods = sorted(list(getattr(r, "methods", []) or []))
            path = getattr(r, "path", "")
            if path:
                routes.append({"path": path, "methods": methods})
    except Exception as e:
        routes.append({"error": str(e)})

    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "frontend" / "dist",
        here.parents[1] / "frontend" / "dist",
        Path.cwd() / "frontend" / "dist",
        Path.cwd() / "dist",
        Path.cwd() / "resources" / "frontend" / "dist",
        Path.cwd() / "resources" / "app" / "frontend" / "dist",
    ]

    checked = []
    found = None
    for p in candidates:
        checked.append(str(p))
        if p.exists() and (p / "index.html").exists():
            found = p
            break

    return {
        "ok": True,
        "diagnostic": "v41.3.9",
        "cwd": os.getcwd(),
        "sys_executable": sys.executable,
        "platform": platform.platform(),
        "python_version": sys.version,
        "main_file": str(main_file),
        "legacy_logic_file": str(legacy_file),
        "frontend_dist_found": bool(found),
        "frontend_dist": str(found) if found else None,
        "checked_frontend_paths": checked,
        "routes_sample": routes[:200],
        "has_catalog_areas_get": any(r.get("path") == "/api/catalog/areas" and "GET" in r.get("methods", []) for r in routes if isinstance(r, dict)),
        "has_catalog_areas_post": any(r.get("path") == "/api/catalog/areas" and "POST" in r.get("methods", []) for r in routes if isinstance(r, dict)),
        "has_debug_static": any(r.get("path") == "/api/debug/static" for r in routes if isinstance(r, dict)),
    }

@app.get("/api/health")
def health(): return {"ok": True, "app": APP_NAME, "version": "39.0-product-warehouse", "db_path": str(db_path())}

@app.get("/api/state")
def state(): return load_db()

@app.post("/api/state")
def set_state(payload: Payload):
    save_db(normalize_db(payload.data)); return {"ok": True}

@app.get("/api/options")
def options():
    db = load_db()
    return {"raw_sections": get_catalog_areas(db), "product_sections": product_section_choices(db), "categories": db.get("categories", {}), "formats": db.get("formats", {}), "thicknesses": db.get("thicknesses", {}), "typologies": db.get("typologies", {}), "customers": sorted(db.get("customers", {}).keys()), "suppliers": sorted(db.get("suppliers", {}).keys()), "collections": sorted(db.get("product_collections", []))}

@app.get("/api/dashboard")
def dashboard():
    db=load_db(); raw=aggregated_raw_items(db); product_value=sum(parse_float(p.get("stock"))*product_unit_cost(db,n) for n,p in db.get("products",{}).items()); sales=sum(parse_float(s.get("total")) for s in db.get("sales",[]))
    return {"inventory_value": round(sum(x["value"] for x in raw),2), "raw_items": len(raw), "products": len(db.get("products",{})), "product_value": round(product_value,2), "sales": round(sales,2), "customers": len(db.get("customers",{})), "suppliers": len(db.get("suppliers",{}))}

@app.get("/api/inventory")
def inventory():
    try:
        rows = aggregated_raw_items(load_db())
        return rows if isinstance(rows, list) else []
    except Exception as exc:
        # La pagina Acquisti/Magazzino non deve mai bloccare tutta la web app.
        return []

@app.post("/api/purchase")
def purchase(payload: Payload): return mutate(add_purchase, payload.data)

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

@app.put("/api/raw/{table}/{key:path}")
def update_raw(table: str, key: str, payload: Payload):
    def fn(db):
        if table not in ("materials","components") or key not in db.get(table,{}): raise ValueError("Articolo non trovato")
        db[table][key].update(payload.data); return db[table][key]
    return mutate(fn)

@app.delete("/api/raw/{table}/{key:path}")
def delete_raw(table: str, key: str):
    def fn(db):
        if table not in ("materials","components") or key not in db.get(table,{}): raise ValueError("Articolo non trovato")
        db[table].pop(key); return {"ok": True}
    return mutate(fn)

@app.post("/api/presets/basic-materials")
def basic_presets(): return mutate(create_basic_material_presets)

@app.get("/api/products")
def products():
    db=load_db(); out=[]
    for name, info in db.get("products",{}).items():
        row={"name":name, **info, "material_unit_cost": product_material_unit_cost(db,name), "labor_unit_cost": product_labor_unit_cost(db,name), "unit_cost": product_unit_cost(db,name), "value": product_unit_cost(db,name)*parse_float(info.get("stock"))}
        out.append(row)
    return sorted(out, key=lambda x:x["name"].lower())

@app.post("/api/products")
def upsert_product(payload: Payload): return mutate(create_or_update_product, payload.data)

@app.delete("/api/products/{name:path}")
def delete_product(name: str):
    def fn(db):
        if name not in db.get("products",{}): raise ValueError("Prodotto non trovato")
        db["products"].pop(name); return {"ok": True}
    return mutate(fn)

@app.post("/api/products/{name:path}/check-production")
def check_prod(name: str, payload: Payload):
    try: return production_check(load_db(), name, parse_float(payload.data.get("qty",1)))
    except ValueError as exc: raise HTTPException(400, str(exc))

@app.post("/api/products/{name:path}/produce")
def produce(name: str, payload: Payload):
    def fn(db):
        result = produce_product(db, name, parse_float(payload.data.get("qty",1)), payload.data.get("substitutions",{}))
        db.setdefault("product_movements", []).append({
            "date": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "product": name,
            "qty": parse_float(payload.data.get("qty",1)),
            "reason": "Produzione interna",
            "note": "Carico automatico da produzione"
        })
        return result
    return mutate(fn)

@app.post("/api/products/{name:path}/stock")
def product_stock(name: str, payload: Payload):
    def fn(db):
        if name not in db.get("products", {}):
            raise ValueError("Prodotto non trovato")
        qty = parse_float(payload.data.get("qty"))
        product = db["products"][name]
        current = parse_float(product.get("stock"))
        new_stock = current + qty
        if new_stock < 0:
            raise ValueError("Stock prodotto insufficiente per lo scarico richiesto")
        product["stock"] = new_stock
        db.setdefault("product_movements", []).append({
            "date": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "product": name,
            "qty": qty,
            "reason": payload.data.get("reason") or ("Carico manuale" if qty >= 0 else "Scarico manuale"),
            "note": payload.data.get("note", "")
        })
        return {"ok": True, "stock": new_stock}
    return mutate(fn)

@app.get("/api/products/movements")
def product_movements():
    return list(reversed(load_db().get("product_movements", [])))

@app.post("/api/quote/calculate")
def quote_calc(payload: Payload):
    try: return calculate_quote(load_db(), payload.data)
    except ValueError as exc: raise HTTPException(400, str(exc))

@app.post("/api/quote/sale")
def quote_sale(payload: Payload): return mutate(record_quote_sale, payload.data)

@app.get("/api/sales")
def sales(): return [{"id": i, **s, "date_normalized": normalize_date(s.get("date"))} for i,s in enumerate(load_db().get("sales",[]))]

@app.post("/api/sales")
def sale(payload: Payload): return mutate(record_product_sale, payload.data)

@app.delete("/api/sales/{idx}")
def delete_sale(idx:int, restore_stock: bool=True):
    def fn(db):
        sales=db.get("sales",[])
        if idx<0 or idx>=len(sales): raise ValueError("Vendita non trovata")
        s=sales[idx]
        if restore_stock and s.get("source")=="magazzino" and s.get("product") in db.get("products",{}): db["products"][s["product"]]["stock"] = parse_float(db["products"][s["product"]].get("stock"))+parse_float(s.get("qty"))
        del sales[idx]; return {"ok": True}
    return mutate(fn)

@app.get("/api/people")
def people():
    db=load_db(); return {"customers": db.get("customers",{}), "suppliers": db.get("suppliers",{})}

@app.post("/api/customers")
def customer(payload: Payload):
    def fn(db):
        name=(payload.data.get("name") or "").strip()
        if not name: raise ValueError("Inserisci il nome cliente")
        db.setdefault("customers",{})[name]={"name":name,"notes":payload.data.get("notes","")}; return db["customers"][name]
    return mutate(fn)

@app.delete("/api/customers/{name:path}")
def del_customer(name:str):
    def fn(db): db.get("customers",{}).pop(name,None); return {"ok":True}
    return mutate(fn)

@app.post("/api/suppliers")
def supplier(payload: Payload):
    def fn(db):
        name=(payload.data.get("name") or "").strip()
        section=(payload.data.get("section") or "").strip()
        category=(payload.data.get("category") or "").strip()
        subcategory=(payload.data.get("subcategory") or "").strip()
        if not name: raise ValueError("Inserisci il nome fornitore")
        old=db.setdefault("suppliers",{}).get(name,{"name":name,"sections":[],"links":[]})
        sections=list(old.get("sections",[]) or [])
        links=list(old.get("links",[]) or [])
        if section and section not in sections: sections.append(section)
        if section and category:
            link={"section":section,"category":category,"subcategory":subcategory}
            if link not in links: links.append(link)
            ensure_category(db, scope_from_display(db, section), category, subcategory)
        db["suppliers"][name]={"name":name,"sections":sections,"links":links}
        return db["suppliers"][name]
    return mutate(fn)

@app.delete("/api/suppliers/{name:path}")
def del_supplier(name:str):
    def fn(db): db.get("suppliers",{}).pop(name,None); return {"ok":True}
    return mutate(fn)

# ---------------------------------------------------------------------------
# v41.3.8 - Forced catalog areas routes before SPA/static fallback
# ---------------------------------------------------------------------------

@app.get("/api/catalog/areas")
def forced_catalog_areas_api():
    db = load_db()
    return get_catalog_areas(db)


@app.post("/api/catalog/areas")
def forced_add_catalog_area_api(payload: Payload):
    def fn(db):
        return add_catalog_area(db, payload.data)
    return mutate(fn)


@app.delete("/api/catalog/areas/{name:path}")
def forced_delete_catalog_area_api(name: str):
    def fn(db):
        return delete_catalog_area(db, name)
    return mutate(fn)


@app.get("/api/debug/static")
def forced_debug_static_assets_api():
    from pathlib import Path
    import os

    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "frontend" / "dist",
        here.parents[1] / "frontend" / "dist",
        Path.cwd() / "frontend" / "dist",
        Path.cwd() / "dist",
        Path.cwd() / "resources" / "frontend" / "dist",
        Path.cwd() / "resources" / "app" / "frontend" / "dist",
    ]

    checked = []
    found = None

    for p in candidates:
        checked.append(str(p))
        if p.exists() and (p / "index.html").exists():
            found = p
            break

    assets = []
    if found and (found / "assets").exists():
        assets = sorted([x.name for x in (found / "assets").glob("*")])

    return {
        "ok": True,
        "frontend_dist_found": bool(found),
        "frontend_dist": str(found) if found else None,
        "cwd": os.getcwd(),
        "checked_paths": checked,
        "index_exists": bool(found and (found / "index.html").exists()),
        "assets_count": len(assets),
        "assets_sample": assets[:30],
    }

@app.get("/api/categories")
def cats():
    db=load_db(); return {"categories": db.get("categories",{}), "product_collection_links": db.get("product_collection_links",{}), "formats": db.get("formats",{}), "thicknesses": db.get("thicknesses",{})}

@app.post("/api/categories")
def add_cat(payload: Payload):
    def fn(db):
        scope=payload.data.get("scope") or "materials"; category=payload.data.get("category",""); sub=payload.data.get("subcategory","")
        ensure_category(db, scope_from_display(db, scope), category, sub); return {"ok":True}
    return mutate(fn)

@app.delete("/api/categories")
def del_cat(scope:str, category:str, subcategory:str=""):
    def fn(db):
        s=scope_from_display(db, scope); cats=db.get("categories",{}).get(s,{})
        if category in cats:
            if subcategory:
                if subcategory in cats[category]: cats[category].remove(subcategory)
                if not cats[category]: cats.pop(category,None)
            else: cats.pop(category,None)
        return {"ok":True}
    return mutate(fn)

@app.post("/api/product-links")
def add_product_link(payload: Payload):
    def fn(db):
        c=payload.data.get("category","").strip(); s=payload.data.get("subcategory","").strip(); col=payload.data.get("collection","").strip()
        if not c or not s or not col: raise ValueError("Categoria, sottocategoria e collezione richieste")
        ensure_category(db,"products",c,s); db.setdefault("product_collection_links",{}).setdefault(c,{}).setdefault(s,[])
        if col not in db["product_collection_links"][c][s]: db["product_collection_links"][c][s].append(col)
        if col not in db.setdefault("product_collections",[]): db["product_collections"].append(col)
        return {"ok":True}
    return mutate(fn)

@app.post("/api/presets")
def add_preset(payload: Payload):
    def fn(db):
        category=payload.data.get("category","").strip(); typ=payload.data.get("type","format"); value=payload.data.get("value","").strip()
        if not category or not value: raise ValueError("Categoria e valore richiesti")
        key="formats" if typ=="format" else "thicknesses"; db.setdefault(key,{}).setdefault(category,[])
        if value not in db[key][category]: db[key][category].append(value)
        return {"ok":True}
    return mutate(fn)


def ensure_custom_areas_in_taxonomy(db, result):
    """
    Garantisce che /api/taxonomy includa anche le aree catalogo vuote.
    Filtra chiavi tecniche come materials/components/products.
    """
    if not isinstance(result, dict):
        return result

    technical = {
        "materials",
        "components",
        "products",
        "sales",
        "quotes",
        "customers",
        "suppliers",
        "categories",
        "formats",
        "thicknesses",
        "typologies",
    }

    raw_tree = result.setdefault("raw_tree", [])

    cleaned_tree = []
    seen = set()

    for sec in raw_tree:
        if not isinstance(sec, dict):
            continue

        label = str(sec.get("label") or sec.get("name") or sec.get("section") or sec.get("key") or "").strip()
        if not label:
            continue

        if label.lower() in technical:
            continue

        if label in seen:
            continue

        sec["label"] = label
        sec["name"] = sec.get("name") or label
        sec["categories"] = sec.get("categories") or []
        cleaned_tree.append(sec)
        seen.add(label)

    areas = []
    for a in db.get("catalog_areas", []) or []:
        a = str(a or "").strip()
        if not a or a.lower() in technical:
            continue
        if a not in areas:
            areas.append(a)

    for a in (db.get("categories", {}) or {}).keys():
        a = str(a or "").strip()
        if not a or a.lower() in technical:
            continue
        if a not in areas:
            areas.append(a)

    for area in areas:
        if area in seen:
            continue

        cleaned_tree.append({
            "key": area,
            "label": area,
            "name": area,
            "section": area,
            "categories": [],
        })
        seen.add(area)

    result["raw_tree"] = cleaned_tree
    return result


@app.get("/api/taxonomy")
def taxonomy():
    db = load_db()
    labels = {"materials": section_label(db,"materials"), "components": section_label(db,"components"), "products": section_label(db,"products")}

    # Albero materie prime/componenti: categorie tecniche + fornitori realmente presenti in stock.
    raw_tree = []
    for scope in ["materials", "components"] + [x for x in db.get("custom_sections", []) if x not in db.get("product_custom_sections", [])]:
        cats = db.get("categories", {}).get(scope, {})
        if not isinstance(cats, dict):
            continue
        cat_rows = []
        for category, subs in sorted(cats.items()):
            suppliers = set()
            for table in ("materials", "components"):
                for info in db.get(table, {}).values():
                    if info.get("category") == category and (scope in ("materials","components") or info.get("section") == scope):
                        if info.get("supplier"): suppliers.add(info.get("supplier"))
            cat_rows.append({"name": category, "subcategories": subs if isinstance(subs, list) else [], "suppliers": len(suppliers)})
        raw_tree.append({"scope": scope, "label": labels.get(scope, scope), "categories": cat_rows})

    product_tree = []
    links = db.get("product_collection_links", {})
    for category, subs in sorted(db.get("categories", {}).get("products", {}).items()):
        subrows=[]
        for sub in (subs if isinstance(subs, list) else []):
            subrows.append({"name": sub, "collections": links.get(category, {}).get(sub, [])})
        product_tree.append({"category": category, "subcategories": subrows})

    # Matrice fornitori: unione tra collegamenti registrati e dati dedotti dagli acquisti reali.
    matrix = []
    seen = set()
    for supplier, info in db.get("suppliers", {}).items():
        for link in info.get("links", []) or []:
            row = {"supplier": supplier, "section": link.get("section",""), "category": link.get("category",""), "subcategory": link.get("subcategory",""), "source": "registrato"}
            key = tuple(row.values())
            if key not in seen:
                seen.add(key); matrix.append(row)
    for table in ("materials", "components"):
        for info in db.get(table, {}).values():
            supplier = info.get("supplier") or "Senza fornitore"
            row = {"supplier": supplier, "section": info.get("section", labels.get(table, table)), "category": info.get("category",""), "subcategory": info.get("subcategory",""), "source": "da acquisti"}
            key = tuple(row.values())
            if row["category"] and key not in seen:
                seen.add(key); matrix.append(row)
    result = {"raw_tree": raw_tree, "product_tree": product_tree, "supplier_matrix": sorted(matrix, key=lambda x:(x["supplier"], x["section"], x["category"], x["subcategory"]))}
    return ensure_custom_areas_in_taxonomy(db, result)
@app.post("/api/supplier-links")
def supplier_link(payload: Payload):
    def fn(db):
        supplier=(payload.data.get("supplier") or "").strip()
        section=(payload.data.get("section") or "").strip()
        category=(payload.data.get("category") or "").strip()
        subcategory=(payload.data.get("subcategory") or "").strip()
        if not supplier or not section or not category:
            raise ValueError("Fornitore, sezione e categoria sono richiesti")
        info=db.setdefault("suppliers",{}).setdefault(supplier,{"name":supplier,"sections":[],"links":[]})
        if section not in info.setdefault("sections",[]): info["sections"].append(section)
        link={"section":section,"category":category,"subcategory":subcategory}
        if link not in info.setdefault("links",[]): info["links"].append(link)
        return {"ok": True, "link": link}
    return mutate(fn)


def _push_unique(values, value):
    value = str(value or '').strip()
    if value and value not in values:
        values.append(value)

def _flatten_category_suggestions(db, scope=None, category=None):
    categories = []
    subcategories = []
    scopes = [scope] if scope else list(db.get('categories', {}).keys())
    for sc in scopes:
        cats = db.get('categories', {}).get(sc, {})
        if not isinstance(cats, dict):
            continue
        for cat, subs in cats.items():
            _push_unique(categories, cat)
            if category and str(cat).strip().lower() != str(category).strip().lower():
                continue
            for sub in (subs or []):
                _push_unique(subcategories, sub)
    return sorted(categories), sorted(subcategories)

@app.get('/api/suggestions')
def suggestions(section: str = '', category: str = '', subcategory: str = '', mode: str = 'all', q: str = ''):
    db = load_db()
    raw_scope = scope_from_display(db, section) if section else ''
    product_scope = 'products'

    raw_categories, raw_subcategories = _flatten_category_suggestions(db, raw_scope or None, category or None)
    product_categories, product_subcategories = _flatten_category_suggestions(db, product_scope, category or None)

    suppliers = []
    customers = []
    units = ['pz', 'mq', 'ml', 'm', 'cm', 'kg', 'g', 'set', 'kit', 'rotolo', 'lastra', 'barattolo']
    formats = []
    thicknesses = []
    typologies = []
    raw_names = []
    product_names = []
    collections = []
    sections = []

    for x in raw_section_choices(db):
        _push_unique(sections, x)
    for x in product_section_choices(db):
        _push_unique(sections, x)

    for name in db.get('suppliers', {}).keys():
        _push_unique(suppliers, name)
    for name in db.get('customers', {}).keys():
        _push_unique(customers, name)

    for cat, vals in db.get('formats', {}).items():
        if not category or cat == category:
            for v in vals: _push_unique(formats, v)
    for cat, vals in db.get('thicknesses', {}).items():
        if not category or cat == category:
            for v in vals: _push_unique(thicknesses, v)

    typ_data = db.get('typologies', {})
    if category and category in typ_data:
        for sub, vals in typ_data.get(category, {}).items():
            if not subcategory or sub == subcategory:
                for v in vals: _push_unique(typologies, v)
    else:
        for submap in typ_data.values():
            if isinstance(submap, dict):
                for vals in submap.values():
                    for v in vals: _push_unique(typologies, v)

    for table in ('materials', 'components'):
        for key, info in db.get(table, {}).items():
            if section and info.get('section') != section and raw_scope not in (table, ''):
                pass
            _push_unique(raw_names, display_name_from_key(key, info))
            _push_unique(suppliers, info.get('supplier'))
            _push_unique(raw_categories, info.get('category'))
            if not category or info.get('category') == category:
                _push_unique(raw_subcategories, info.get('subcategory'))
            _push_unique(formats, info.get('size'))
            _push_unique(thicknesses, info.get('thickness'))
            _push_unique(units, info.get('unit'))

    links = db.get('product_collection_links', {})
    for name, info in db.get('products', {}).items():
        _push_unique(product_names, name)
        _push_unique(product_categories, info.get('category'))
        if not category or info.get('category') == category:
            _push_unique(product_subcategories, info.get('subcategory'))
        _push_unique(collections, info.get('collection'))
        _push_unique(units, info.get('unit'))
    for cat, submap in links.items():
        _push_unique(product_categories, cat)
        for sub, cols in (submap or {}).items():
            if not category or cat == category:
                _push_unique(product_subcategories, sub)
            if (not category or cat == category) and (not subcategory or sub == subcategory):
                for col in cols or []: _push_unique(collections, col)
    for col in db.get('product_collections', []):
        _push_unique(collections, col)

    # Mappe contestuali per campi intelligenti dipendenti.
    raw_categories_by_scope = {}
    raw_subcategories_by_scope_category = {}
    all_raw_scopes = ['materials', 'components'] + [x for x in db.get('custom_sections', []) if x not in db.get('product_custom_sections', [])]
    for sc in all_raw_scopes:
        cats = db.get('categories', {}).get(sc, {})
        if not isinstance(cats, dict):
            continue
        display_scope = section_label(db, sc) if sc in ('materials', 'components', 'products') else sc
        raw_categories_by_scope.setdefault(display_scope, [])
        raw_categories_by_scope.setdefault(sc, [])
        raw_subcategories_by_scope_category.setdefault(display_scope, {})
        raw_subcategories_by_scope_category.setdefault(sc, {})
        for cat, subs in cats.items():
            _push_unique(raw_categories_by_scope[display_scope], cat)
            _push_unique(raw_categories_by_scope[sc], cat)
            raw_subcategories_by_scope_category[display_scope].setdefault(cat, [])
            raw_subcategories_by_scope_category[sc].setdefault(cat, [])
            for sub in (subs or []):
                _push_unique(raw_subcategories_by_scope_category[display_scope][cat], sub)
                _push_unique(raw_subcategories_by_scope_category[sc][cat], sub)

    product_subcategories_by_category = {}
    for cat, subs in db.get('categories', {}).get('products', {}).items():
        product_subcategories_by_category.setdefault(cat, [])
        for sub in (subs or []): _push_unique(product_subcategories_by_category[cat], sub)

    collections_by_product_path = {}
    for cat, submap in db.get('product_collection_links', {}).items():
        collections_by_product_path.setdefault(cat, {})
        for sub, cols in (submap or {}).items():
            collections_by_product_path[cat].setdefault(sub, [])
            for col in (cols or []): _push_unique(collections_by_product_path[cat][sub], col)

    formats_by_category = {k: sorted(list(dict.fromkeys(v or []))) for k, v in db.get('formats', {}).items()}
    thicknesses_by_category = {k: sorted(list(dict.fromkeys(v or []))) for k, v in db.get('thicknesses', {}).items()}
    typologies_by_category_subcategory = {}
    for cat, submap in db.get('typologies', {}).items():
        typologies_by_category_subcategory.setdefault(cat, {})
        for sub, vals in (submap or {}).items():
            typologies_by_category_subcategory[cat][sub] = sorted(list(dict.fromkeys(vals or [])))

    suppliers_by_raw_path = {}
    suppliers_by_raw_scope = {}
    raw_categories_by_supplier_scope = {}
    raw_subcategories_by_supplier_scope_category = {}

    def add_supplier_context(supplier, sec, cat='', sub=''):
        supplier = (supplier or '').strip(); sec = (sec or '').strip(); cat = (cat or '').strip(); sub = (sub or '').strip()
        if not supplier or not sec:
            return
        _push_unique(suppliers_by_raw_scope.setdefault(sec, []), supplier)
        if cat:
            _push_unique(raw_categories_by_supplier_scope.setdefault(supplier, {}).setdefault(sec, []), cat)
            raw_subcategories_by_supplier_scope_category.setdefault(supplier, {}).setdefault(sec, {}).setdefault(cat, [])
            if sub:
                _push_unique(raw_subcategories_by_supplier_scope_category[supplier][sec][cat], sub)
                suppliers_by_raw_path.setdefault(sec, {}).setdefault(cat, {}).setdefault(sub, [])
                _push_unique(suppliers_by_raw_path[sec][cat][sub], supplier)

    # Collegamenti espliciti salvati nella scheda fornitore.
    for supplier_name, supplier_info in db.get('suppliers', {}).items():
        for link in supplier_info.get('links', []) or []:
            if isinstance(link, dict):
                add_supplier_context(supplier_name, link.get('section'), link.get('category'), link.get('subcategory'))
        # Se il fornitore ha solo area ma nessuna categoria, resta disponibile come fornitore per quell'area.
        for sec in supplier_info.get('sections', []) or []:
            _push_unique(suppliers_by_raw_scope.setdefault(sec, []), supplier_name)

    # Collegamenti dedotti automaticamente dagli acquisti già registrati.
    for table in ('materials', 'components'):
        for info in db.get(table, {}).values():
            sec = info.get('section') or section_label(db, table)
            add_supplier_context(info.get('supplier'), sec, info.get('category'), info.get('subcategory'))

    result = {
        'sections': sorted(sections),
        'raw_sections': get_catalog_areas(db),
        'product_sections': product_section_choices(db),
        'suppliers': sorted(suppliers),
        'customers': sorted(customers),
        'units': sorted(units),
        'raw_categories': sorted(raw_categories),
        'raw_subcategories': sorted(raw_subcategories),
        'product_categories': sorted(product_categories),
        'product_subcategories': sorted(product_subcategories),
        'formats': sorted(formats),
        'thicknesses': sorted(thicknesses),
        'typologies': sorted(typologies),
        'raw_names': sorted(raw_names),
        'product_names': sorted(product_names),
        'collections': sorted(collections),
        'raw_categories_by_scope': raw_categories_by_scope,
        'raw_subcategories_by_scope_category': raw_subcategories_by_scope_category,
        'product_subcategories_by_category': product_subcategories_by_category,
        'collections_by_product_path': collections_by_product_path,
        'formats_by_category': formats_by_category,
        'thicknesses_by_category': thicknesses_by_category,
        'typologies_by_category_subcategory': typologies_by_category_subcategory,
        'suppliers_by_raw_path': suppliers_by_raw_path,
        'suppliers_by_raw_scope': suppliers_by_raw_scope,
        'raw_categories_by_supplier_scope': raw_categories_by_supplier_scope,
        'raw_subcategories_by_supplier_scope_category': raw_subcategories_by_supplier_scope_category,
    }

    q = (q or '').strip().lower()
    if q:
        for key, values in list(result.items()):
            if isinstance(values, list):
                result[key] = [v for v in values if q in str(v).lower()][:40]
    return result

@app.get("/api/report")
def report_api(): return report(load_db())

@app.post("/api/maintenance/cleanup")
def cleanup():
    def fn(db):
        b=backup_database("prima_pulizia"); normalize_db(db); return {"ok":True,"backup":b}
    return mutate(fn)

@app.post("/api/maintenance/backup")
def backup(): return {"backup": backup_database("manuale")}

@app.post("/api/maintenance/reset")
def reset():
    b=backup_database("prima_reset"); save_db(empty_db()); return {"ok":True,"backup":b}


@app.get("/api/maintenance/info")
def maintenance_info():
    return {
        "ok": True,
        "db_path": str(db_path()),
        "data_dir": str(user_data_dir()),
        "checked_at": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    }

@app.get("/api/maintenance/export")
def export_archive():
    data = load_db()
    return {
        "filename": f"mn_laser_lab_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "data": data,
    }

@app.post("/api/maintenance/import")
def import_archive(payload: Payload):
    incoming = payload.data
    if not isinstance(incoming, dict):
        raise HTTPException(400, "Formato import non valido")
    backup = backup_database("prima_import")
    save_db(normalize_db(incoming))
    return {"ok": True, "backup": backup}


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


@app.get("/api/products/{name:path}/detail")
def product_detail_api(name: str):
    try:
        return product_detail(load_db(), name)
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@app.post("/api/catalog/formats")
def add_catalog_format_api(payload: Payload):
    return mutate(add_catalog_format, payload.data)


@app.delete("/api/catalog/formats")
def delete_catalog_format_api(category: str, value: str):
    return mutate(delete_catalog_format, category, value)


@app.post("/api/catalog/thicknesses")
def add_catalog_thickness_api(payload: Payload):
    return mutate(add_catalog_thickness, payload.data)


@app.delete("/api/catalog/thicknesses")
def delete_catalog_thickness_api(category: str, value: str):
    return mutate(delete_catalog_thickness, category, value)


@app.post("/api/catalog/typologies")
def add_catalog_typology_api(payload: Payload):
    return mutate(add_catalog_typology, payload.data)


@app.delete("/api/catalog/typologies")
def delete_catalog_typology_api(category: str, subcategory: str, value: str):
    return mutate(delete_catalog_typology, category, subcategory, value)


@app.delete("/api/product-links")
def delete_product_link_api(category: str, subcategory: str, collection: str):
    return mutate(delete_product_collection_link, category, subcategory, collection)


from fastapi.responses import HTMLResponse


@app.get("/api/quotes/{quote_id:path}/pdf/customer", response_class=HTMLResponse)
def quote_customer_pdf_api(quote_id: str):
    try:
        return HTMLResponse(quote_customer_html(load_db(), quote_id))
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@app.get("/api/quotes/{quote_id:path}/pdf/internal", response_class=HTMLResponse)
def quote_internal_pdf_api(quote_id: str):
    try:
        return HTMLResponse(quote_internal_html(load_db(), quote_id))
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@app.get("/api/quote-pdf/customer", response_class=HTMLResponse)
def quote_customer_pdf_query_api(id: str):
    try:
        db = load_db()
        quote = get_quote_flexible(db, id)
        return HTMLResponse(quote_customer_html(db, quote.get("id", id)))
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@app.get("/api/quote-pdf/internal", response_class=HTMLResponse)
def quote_internal_pdf_query_api(id: str):
    try:
        db = load_db()
        quote = get_quote_flexible(db, id)
        return HTMLResponse(quote_internal_html(db, quote.get("id", id)))
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@app.get("/api/maintenance/backups")
def maintenance_backups():
    return {"backups": list_backups()}


@app.post("/api/maintenance/backup-named")
def backup_named(payload: Payload):
    name = payload.data.get("name") or "manuale"
    return {"backup": backup_database_named(name), "backups": list_backups()}


@app.post("/api/maintenance/restore")
def restore_backup(payload: Payload):
    try:
        filename = payload.data.get("filename") or ""
        return restore_database_from_backup(filename)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.post("/api/maintenance/import-purchases")
def import_purchases_api(payload: Payload):
    try:
        rows = payload.data.get("rows", [])
        return mutate(import_purchase_rows, rows)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.get("/api/operations")
def operations_api():
    return operational_dashboard(load_db())


@app.get("/api/quotes/workflow")
def quote_workflow_api():
    return quote_workflow_summary(load_db())


@app.post("/api/quotes/{quote_id:path}/status")
def quote_status_api(quote_id: str, payload: Payload):
    def fn(db):
        return update_quote_status(db, quote_id, payload.data.get("status"))
    return mutate(fn)


@app.post("/api/quotes/{quote_id:path}/duplicate")
def quote_duplicate_api(quote_id: str, payload: Payload):
    def fn(db):
        return duplicate_quote(db, quote_id, payload.data.get("name", ""))
    return mutate(fn)


@app.get("/api/settings/pdf")
def get_pdf_settings_api():
    return get_pdf_settings(load_db())


@app.post("/api/settings/pdf")
def update_pdf_settings_api(payload: Payload):
    def fn(db):
        return update_pdf_settings(db, payload.data)
    return mutate(fn)


@app.get("/api/settings/pdf/export")
def export_pdf_settings_api():
    return export_pdf_settings(load_db())


@app.post("/api/settings/pdf/import")
def import_pdf_settings_api(payload: Payload):
    def fn(db):
        return import_pdf_settings(db, payload.data)
    return mutate(fn)


@app.post("/api/quotes/{quote_id:path}/start-production")
def quote_start_production_api(quote_id: str):
    def fn(db):
        return quote_start_production(db, quote_id)
    return mutate(fn)


@app.post("/api/quotes/{quote_id:path}/register-sale")
def quote_register_sale_api(quote_id: str, payload: Payload):
    def fn(db):
        return quote_register_sale(db, quote_id, payload.data)
    return mutate(fn)


@app.post("/api/quotes/{quote_id:path}/mark-delivered")
def quote_mark_delivered_api(quote_id: str):
    def fn(db):
        return quote_mark_delivered(db, quote_id)
    return mutate(fn)


@app.get("/api/catalog/areas")
def catalog_areas_api():
    return get_catalog_areas(load_db())


@app.post("/api/catalog/areas")
def add_catalog_area_api(payload: Payload):
    def fn(db):
        return add_catalog_area(db, payload.data)
    return mutate(fn)


@app.delete("/api/catalog/areas/{name:path}")
def delete_catalog_area_api(name: str):
    def fn(db):
        return delete_catalog_area(db, name)
    return mutate(fn)


@app.get("/api/catalog/wood-treatments")
def wood_treatments_api():
    return get_wood_treatments(load_db())


@app.post("/api/catalog/wood-treatments")
def save_wood_treatment_api(payload: Payload):
    def fn(db):
        return save_wood_treatment(db, payload.data)
    return mutate(fn)


@app.delete("/api/catalog/wood-treatments/{name:path}")
def delete_wood_treatment_api(name: str):
    def fn(db):
        return delete_wood_treatment(db, name)
    return mutate(fn)


# ---------------------------------------------------------------------------
# v41.3.2 - Static assets hardening for Electron/browser
# Evita pagina bianca da Strict MIME type checking:
# /assets/*.js o /assets/*.css non devono mai ricevere index.html.
# ---------------------------------------------------------------------------

from fastapi import Request
from fastapi.responses import FileResponse, Response, JSONResponse
import mimetypes

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("image/png", ".png")
mimetypes.add_type("image/x-icon", ".ico")
mimetypes.add_type("application/wasm", ".wasm")


def _frontend_dist_dir():
    here = Path(__file__).resolve()

    candidates = [
        here.parents[2] / "frontend" / "dist",
        here.parents[1] / "frontend" / "dist",
        here.parents[2] / "dist",
        here.parents[1] / "dist",
        Path.cwd() / "frontend" / "dist",
        Path.cwd() / "dist",
        Path.cwd() / "resources" / "frontend" / "dist",
        Path.cwd() / "resources" / "app" / "frontend" / "dist",
    ]

    for p in candidates:
        if p.exists() and (p / "index.html").exists():
            return p

    return None


@app.middleware("http")
async def static_asset_mime_guard(request: Request, call_next):
    path = request.url.path

    # Se il frontend chiede un asset Vite, servilo come file reale.
    # Se manca, restituisci 404 testuale, NON index.html.
    if path.startswith("/assets/"):
        dist = _frontend_dist_dir()
        if not dist:
            return Response("Frontend dist not found", status_code=404, media_type="text/plain")

        file_path = (dist / path.lstrip("/")).resolve()

        try:
            file_path.relative_to(dist.resolve())
        except Exception:
            return Response("Invalid asset path", status_code=403, media_type="text/plain")

        if not file_path.exists() or not file_path.is_file():
            return Response(f"Asset not found: {path}", status_code=404, media_type="text/plain")

        media_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        return FileResponse(
            file_path,
            media_type=media_type,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
            },
        )

    response = await call_next(request)

    # Evita cache aggressiva sull'HTML principale.
    if path in ("", "/") or path.endswith("index.html"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"

    return response


@app.get("/api/debug/static")
def debug_static_assets():
    dist = _frontend_dist_dir()
    assets = []

    if dist and (dist / "assets").exists():
        assets = sorted([p.name for p in (dist / "assets").glob("*")])[:50]

    return {
        "frontend_dist_found": bool(dist),
        "frontend_dist": str(dist) if dist else None,
        "index_exists": bool(dist and (dist / "index.html").exists()),
        "assets_count": len(assets),
        "assets_sample": assets,
    }


@app.get("/api/system/status")
def system_status_api():
    return system_status_info(load_db())



# ---------------------------------------------------------------------------

from fastapi import Request
from fastapi.responses import FileResponse, Response
import mimetypes

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("image/png", ".png")
mimetypes.add_type("image/x-icon", ".ico")
mimetypes.add_type("application/wasm", ".wasm")


def browser_frontend_dist_dir():
    here = Path(__file__).resolve()

    candidates = [
        here.parents[2] / "frontend" / "dist",
        here.parents[1] / "frontend" / "dist",
        Path.cwd() / "frontend" / "dist",
        Path.cwd() / "dist",
        Path.cwd() / "resources" / "frontend" / "dist",
        Path.cwd() / "resources" / "app" / "frontend" / "dist",
        Path(getattr(sys, "_MEIPASS", "")) / "frontend" / "dist" if hasattr(sys, "_MEIPASS") else None,
    ]

    for p in candidates:
        if not p:
            continue
        try:
            if p.exists() and (p / "index.html").exists():
                return p
        except Exception:
            pass

    return None





# ---------------------------------------------------------------------------

def safe_browser_frontend_dist_dir():
    import sys
    from pathlib import Path

    here = Path(__file__).resolve()

    candidates = [
        here.parents[2] / "frontend" / "dist",
        here.parents[1] / "frontend" / "dist",
        Path.cwd() / "frontend" / "dist",
        Path.cwd() / "dist",
        Path.cwd() / "resources" / "frontend" / "dist",
        Path.cwd() / "resources" / "app" / "frontend" / "dist",
    ]

    if hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "frontend" / "dist")
        candidates.append(Path(sys._MEIPASS) / "dist")

    checked = []

    for p in candidates:
        try:
            checked.append(str(p))
            if p.exists() and (p / "index.html").exists():
                return p, checked
        except Exception as e:
            checked.append(f"{p} -> ERROR {e}")

    return None, checked



@app.get("/browser-health")
def browser_health_api():
    return {"ok": True, "mode": "browser-edition", "route": "browser-health"}

# ---------------------------------------------------------------------------
# v42.0.4 - Single safe frontend route for Browser Edition
# ---------------------------------------------------------------------------

def mn_browser_dist():
    import sys
    from pathlib import Path

    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "frontend" / "dist",
        here.parents[1] / "frontend" / "dist",
        Path.cwd() / "frontend" / "dist",
        Path.cwd() / "dist",
    ]

    if hasattr(sys, "_MEIPASS"):
        candidates += [
            Path(sys._MEIPASS) / "frontend" / "dist",
            Path(sys._MEIPASS) / "dist",
        ]

    checked = []
    for p in candidates:
        try:
            checked.append(str(p))
            if p.exists() and (p / "index.html").exists():
                return p, checked
        except Exception as e:
            checked.append(f"{p} ERROR {e}")

    return None, checked


@app.get("/api/debug/browser-dist")
def mn_debug_browser_dist():
    dist, checked = mn_browser_dist()
    assets = []
    if dist and (dist / "assets").exists():
        assets = sorted([p.name for p in (dist / "assets").glob("*")])

    return {
        "ok": True,
        "dist_found": bool(dist),
        "dist": str(dist) if dist else None,
        "checked": checked,
        "assets_count": len(assets),
        "assets_sample": assets[:30],
    }


@app.get("/assets/{asset_path:path}")
def mn_browser_assets(asset_path: str):
    from fastapi.responses import FileResponse, Response
    import mimetypes

    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("text/css", ".css")

    dist, checked = mn_browser_dist()
    if not dist:
        return Response("frontend/dist non trovato\n" + "\n".join(checked), status_code=404, media_type="text/plain")

    file_path = (dist / "assets" / asset_path).resolve()
    assets_dir = (dist / "assets").resolve()

    try:
        file_path.relative_to(assets_dir)
    except Exception:
        return Response("invalid asset path", status_code=403, media_type="text/plain")

    if not file_path.exists():
        return Response(f"asset not found: {asset_path}", status_code=404, media_type="text/plain")

    media_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    return FileResponse(file_path, media_type=media_type)


@app.get("/")
def mn_browser_index():
    from fastapi.responses import FileResponse, Response

    dist, checked = mn_browser_dist()
    if not dist:
        return Response(
            "frontend/dist non trovato.\n\nPercorsi controllati:\n" + "\n".join(checked),
            status_code=404,
            media_type="text/plain",
        )

    index = dist / "index.html"
    if not index.exists():
        return Response(f"index.html non trovato in {dist}", status_code=404, media_type="text/plain")

    return FileResponse(index, media_type="text/html")


# ---------------------------------------------------------------------------
# v42.0.5 - Browser Edition logo/static public files
# ---------------------------------------------------------------------------

def mn_find_public_file(filename):
    from pathlib import Path
    import sys

    here = Path(__file__).resolve()

    candidates = [
        here.parents[2] / "frontend" / "dist" / filename,
        here.parents[2] / "frontend" / "public" / filename,
        here.parents[2] / "desktop" / "assets" / filename,
        here.parents[1] / "frontend" / "dist" / filename,
        here.parents[1] / "frontend" / "public" / filename,
        Path.cwd() / "frontend" / "dist" / filename,
        Path.cwd() / "frontend" / "public" / filename,
        Path.cwd() / "desktop" / "assets" / filename,
        Path.cwd() / filename,
    ]

    if hasattr(sys, "_MEIPASS"):
        candidates += [
            Path(sys._MEIPASS) / "frontend" / "dist" / filename,
            Path(sys._MEIPASS) / "frontend" / "public" / filename,
            Path(sys._MEIPASS) / "desktop" / "assets" / filename,
            Path(sys._MEIPASS) / filename,
        ]

    for p in candidates:
        try:
            if p.exists() and p.is_file():
                return p
        except Exception:
            pass

    return None






# ---------------------------------------------------------------------------
# v42.2.2 - Safe logo and system APIs before SPA fallback
# ---------------------------------------------------------------------------

@app.get("/api/system/version")
def mn_system_version_api_safe():
    return {
        "ok": True,
        "current_version": "42.2.2",
        "channel": "browser-edition",
        "automatic_updates": False,
        "message": "Aggiornamenti automatici non ancora attivi. Usa il pacchetto Browser Edition aggiornato dalla release GitHub.",
    }


@app.get("/api/system/status")
def mn_system_status_api_safe():
    import os
    import sys
    import socket
    import platform
    from datetime import datetime

    def get_lan_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    db = load_db()
    port = int(os.environ.get("MN_BACKEND_PORT", "8000"))
    lan_ip = get_lan_ip()

    return {
        "ok": True,
        "app": "MN Laser Lab Manager",
        "edition": "Browser Edition",
        "version": "42.2.2",
        "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "port": port,
        "local_url": f"http://127.0.0.1:{port}/",
        "lan_ip": lan_ip,
        "lan_url": f"http://{lan_ip}:{port}/",
        "db_counts": {
            "materials": len(db.get("materials", {}) or {}),
            "components": len(db.get("components", {}) or {}),
            "products": len(db.get("products", {}) or {}),
            "quotes": len(db.get("quotes", []) or []),
            "customers": len(db.get("customers", {}) or {}),
            "suppliers": len(db.get("suppliers", {}) or {}),
            "sales": len(db.get("sales", []) or []),
        },
    }


def mn_logo_svg_response():
    from fastapi.responses import Response

    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
      <rect width="120" height="120" rx="28" fill="#ffffff"/>
      <circle cx="60" cy="60" r="45" fill="none" stroke="#0f172a" stroke-width="4" opacity=".16"/>
      <path d="M24 72V43h12l12 16 12-16h12v34H60V60L50 73h-5L36 60v17H24z" fill="#0f172a"/>
      <path d="M76 43h22v11H88v23H76z" fill="#058482"/>
      <path d="M30 86c15 8 48 8 62-2" fill="none" stroke="#058482" stroke-width="6" stroke-linecap="round"/>
    </svg>"""

    return Response(
        svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )





# ---------------------------------------------------------------------------
# v42.2.4 - Force real PNG logo
# ---------------------------------------------------------------------------

def mn_real_png_logo_path():
    from pathlib import Path
    import sys

    here = Path(__file__).resolve()

    candidates = [
        here.parents[2] / "frontend" / "public" / "mn_laser_lab_logo.png",
        here.parents[2] / "frontend" / "dist" / "mn_laser_lab_logo.png",
        here.parents[2] / "desktop" / "assets" / "mn_laser_lab_logo.png",
        Path.cwd() / "frontend" / "public" / "mn_laser_lab_logo.png",
        Path.cwd() / "frontend" / "dist" / "mn_laser_lab_logo.png",
        Path.cwd() / "desktop" / "assets" / "mn_laser_lab_logo.png",
    ]

    if hasattr(sys, "_MEIPASS"):
        candidates += [
            Path(sys._MEIPASS) / "frontend" / "dist" / "mn_laser_lab_logo.png",
            Path(sys._MEIPASS) / "frontend" / "public" / "mn_laser_lab_logo.png",
            Path(sys._MEIPASS) / "desktop" / "assets" / "mn_laser_lab_logo.png",
        ]

    for p in candidates:
        try:
            if p.exists() and p.is_file() and p.stat().st_size > 100:
                return p
        except Exception:
            pass

    return None


@app.get("/mn_laser_lab_logo.png")
def mn_laser_lab_logo_real_png():
    from fastapi.responses import FileResponse, Response

    p = mn_real_png_logo_path()
    if p:
        return FileResponse(
            p,
            media_type="image/png",
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
            },
        )

    return Response("MN Laser Lab logo PNG not found", status_code=404, media_type="text/plain")


@app.get("/logo.png")
def mn_laser_lab_logo_real_png_alias():
    return mn_laser_lab_logo_real_png()


@app.get("/api/debug/logo")
def mn_laser_lab_logo_debug():
    p = mn_real_png_logo_path()
    return {
        "ok": True,
        "real_logo_found": bool(p),
        "path": str(p) if p else None,
        "mode": "real-png" if p else "missing",
        "url": "/mn_laser_lab_logo.png",
    }

@app.get("/{full_path:path}")
def mn_browser_spa(full_path: str):
    from fastapi.responses import FileResponse, Response

    if full_path.startswith("api/"):
        return Response("api route not found", status_code=404, media_type="text/plain")

    if full_path.startswith("assets/"):
        return Response(f"asset not found: {full_path}", status_code=404, media_type="text/plain")

    dist, checked = mn_browser_dist()
    if not dist:
        return Response(
            "frontend/dist non trovato.\n\nPercorsi controllati:\n" + "\n".join(checked),
            status_code=404,
            media_type="text/plain",
        )

    return FileResponse(dist / "index.html", media_type="text/html")
