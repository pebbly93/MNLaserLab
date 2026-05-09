from __future__ import annotations

from typing import Any
from datetime import datetime
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .legacy_logic import *

app = FastAPI(title="MN Laser Lab Manager Web API", version="39.0-product-warehouse")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

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
    return {"raw_sections": raw_section_choices(db), "product_sections": product_section_choices(db), "categories": db.get("categories", {}), "formats": db.get("formats", {}), "thicknesses": db.get("thicknesses", {}), "typologies": db.get("typologies", {}), "customers": sorted(db.get("customers", {}).keys()), "suppliers": sorted(db.get("suppliers", {}).keys()), "collections": sorted(db.get("product_collections", []))}

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
    return {"raw_tree": raw_tree, "product_tree": product_tree, "supplier_matrix": sorted(matrix, key=lambda x:(x["supplier"], x["section"], x["category"], x["subcategory"]))}

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
        'raw_sections': raw_section_choices(db),
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
