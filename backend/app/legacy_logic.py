from __future__ import annotations

import copy
import json
import os
import shutil
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any

APP_NAME = "MN Laser Lab Manager"
DB_FILE = "mn_laser_lab.db"
LEGACY_JSON_FILE = "laser_db.json"


def parse_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", ".").strip())
    except Exception:
        return default


def euro(value: Any) -> str:
    return f"{parse_float(value):.2f} €"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    return date.today().strftime("%d-%m-%Y")


def normalize_date(value: Any) -> str:
    if not value:
        return ""
    s = str(value).strip()
    if " " in s:
        s = s.split(" ")[0]
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%d-%m-%Y")
        except Exception:
            pass
    return s


def date_parts(value: Any):
    try:
        d, m, y = normalize_date(value).split("-")
        return d, m, y
    except Exception:
        return "", "", ""


def date_parts_match(value: Any, day="", month="", year="") -> bool:
    d, m, y = date_parts(value)
    return (not day or d == day) and (not month or m == month) and (not year or y == year)


def hours_minutes_to_decimal(hours_value=0, minutes_value=0) -> float:
    return max(0.0, parse_float(hours_value)) + max(0.0, parse_float(minutes_value)) / 60.0


def decimal_hours_to_hours_minutes(value):
    total = int(round(parse_float(value) * 60))
    return total // 60, total % 60


def user_data_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        path = Path(base) / APP_NAME
    else:
        path = Path.home() / ".mn_laser_lab_manager"
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> Path:
    return user_data_dir() / DB_FILE


def legacy_json_path() -> Path:
    return user_data_dir() / LEGACY_JSON_FILE


def connect():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def default_categories():
    return {
        "materials": {"Legname": ["Betulla", "Pioppo", "MDF", "Multistrato"], "Acrilico": ["Rosso", "Nero", "Giallo", "Blu", "Verde", "Bianco", "Trasparente", "Arancio"]},
        "components": {"Attrezzature": ["Pennelli", "Rulli"], "Vernici": ["Smalti", "Acrilici", "Acqua"], "Finiture": ["Flatting", "Cera", "Olio", "Trasparente"]},
        "products": {
            "Sottobicchieri": ["Classici", "Luminaria leccese", "Salento", "Personalizzati", "Set coordinati", "Tema mare", "Tema anime"],
            "Sottopiatti": ["Classici", "Luminaria leccese", "Decorativi", "Coordinati tavola", "Tema Salento", "Eventi"],
            "Orologi": ["Classici", "Custom", "Anime", "Decorativi", "Parete", "Tema mare", "Tema Salento"],
            "Decorazioni casa": ["Da parete", "Da tavolo", "Luminaria leccese", "Tema Salento", "Tema mare", "Minimal", "Rustiche"],
            "Centrotavola": ["Classici", "Decorativi", "Con specchio", "Con LED", "Tema pietra", "Tema legno"],
            "Targhe e insegne": ["Personalizzate", "Casa", "Attività commerciali", "Eventi", "Decorative"],
            "Portachiavi": ["Classici", "Personalizzati", "Acrilico", "Legno", "Tema Salento", "Tema anime"],
            "Idee regalo": ["Personalizzate", "Casa", "Eventi", "Turistiche", "Ricorrenze"],
        },
    }


def default_section_labels():
    return {"materials": "Falegnameria", "components": "Ferramenta", "products": "Prodotti Finiti / Semilavorati"}


def default_custom_sections():
    return ["Illuminazione"]


def default_product_custom_sections():
    return []


def default_thicknesses():
    base = [f"{i} mm" for i in range(1, 11)]
    return {"Legname": base.copy(), "Acrilico": base.copy()}


def default_formats():
    base = ["10x10", "20x20", "30x30", "40x40"]
    return {"Legname": base.copy(), "Acrilico": base.copy()}


def default_illumination_categories():
    return {
        "LED": ["Strisce LED", "Moduli LED", "LED touch", "LED COB", "LED neon flex", "Punti luce"],
        "Alimentatori": ["12V", "24V", "USB 5V", "Driver LED", "Trasformatori"],
        "Batterie": ["Portabatterie", "Batterie ricaricabili", "Power bank", "Moduli ricarica USB"],
        "Interruttori": ["Touch", "A pulsante", "A levetta", "Dimmer", "Sensori movimento"],
        "Cablaggio": ["Cavi", "Connettori", "Morsetti", "Prolunghe", "Saldature"],
        "Accessori luce": ["Diffusori", "Profili alluminio", "Coperture opaline", "Supporti", "Biadesivo termico"],
    }


def default_typologies():
    return {
        "Vernici": {"Smalti": ["Bomboletta", "Bottiglia"], "Acrilici": ["Bomboletta", "Bottiglia"], "Acqua": ["Bottiglia"]},
        "Finiture": {"Flatting": ["A mano", "Bomboletta"], "Cera": ["A mano"], "Olio": ["A mano"], "Trasparente": ["A mano", "Bomboletta"]},
        "Attrezzature": {"Pennelli": [], "Rulli": []},
        "LED": {"Strisce LED": ["Luce calda", "Luce fredda", "RGB", "COB", "Dimmerabile"], "Moduli LED": ["12V", "24V", "USB"], "LED touch": ["Tondo", "Incasso", "Adesivo"]},
        "Alimentatori": {"12V": ["Da presa", "Da incasso"], "24V": ["Da presa", "Da incasso"], "USB 5V": ["Cavo USB", "Modulo"]},
        "Batterie": {"Portabatterie": ["AA", "AAA", "18650"], "Batterie ricaricabili": ["Li-ion", "NiMH"], "Power bank": ["USB", "USB-C"]},
        "Interruttori": {"Touch": ["Capacitivo", "Dimmer"], "A pulsante": ["Mini", "Incasso"], "A levetta": ["Mini", "Standard"], "Dimmer": ["Rotativo", "Touch"]},
        "Cablaggio": {"Cavi": ["Rosso/Nero", "Trasparente", "USB"], "Connettori": ["Jack", "Morsetto rapido", "JST"], "Morsetti": ["2 poli", "3 poli"]},
        "Accessori luce": {"Diffusori": ["Opalino", "Trasparente"], "Profili alluminio": ["Piatto", "Angolare", "Incasso"], "Coperture opaline": ["Piatta", "Tonda"]},
    }


def default_product_links():
    return {
        "Sottobicchieri": {"Classici": ["Casa Classica", "Minimal Wood", "Rustic Wood"], "Luminaria leccese": ["Luminarie Leccesi", "Salento", "Lecce"], "Tema anime": ["Anime Wood", "Manga Style"]},
        "Orologi": {"Classici": ["Casa Classica", "Minimal Wood", "Rustic Wood"], "Custom": ["Regali Personalizzati", "Custom Wood"], "Anime": ["One Piece", "Dragon Ball", "Naruto", "Anime Wood", "Manga Style"], "Decorativi": ["Casa Decor", "LED Decor"]},
        "Centrotavola": {"Con specchio": ["Specchi e Pietra"], "Con LED": ["LED Decor", "Casa Decor"], "Tema pietra": ["Specchi e Pietra", "Rustic Wood"]},
        "Portachiavi": {"Personalizzati": ["Regali Personalizzati", "Custom Wood"], "Tema Salento": ["Salento", "Luminarie Leccesi"], "Tema anime": ["One Piece", "Dragon Ball", "Naruto", "Anime Wood"]},
    }


def empty_db():
    return {
        "materials": {}, "components": {}, "products": {}, "sales": [], "quotes": [], "customers": {}, "suppliers": {},
        "business_settings": default_business_settings(),
        "product_families": ["Home Decor", "Orologi", "Gadget", "Idee regalo", "Decorazioni", "Accessori tavola"],
        "product_types": ["Sottobicchiere", "Orologio da parete", "Targa", "Portachiavi", "Centrotavola", "Decorazione LED"],
        "product_styles": ["Luminaria", "Classico", "Anime", "Minimal", "Rustico", "Elegante", "Personalizzato"],
        "product_themes": ["Salento", "Lecce", "Mare", "One Piece", "Natale", "Matrimonio"],
        "product_collections": ["Luminarie Leccesi", "Casa Classica", "Casa Decor", "Salento", "Mare e Costa", "Anime Wood", "Tavola Coordinata", "Specchi e Pietra", "LED Decor", "Regali Personalizzati", "Eventi e Cerimonie", "Minimal Wood", "Rustic Wood"],
        "product_tags": ["turistico", "regalo", "legno inciso", "anime", "luminaria", "salento"],
        "product_collection_links": default_product_links(),
        "categories": default_categories(),
        "section_labels": default_section_labels(),
        "custom_sections": default_custom_sections(),
        "product_custom_sections": default_product_custom_sections(),
        "thicknesses": default_thicknesses(),
        "formats": default_formats(),
        "typologies": default_typologies(),
    }


def init_sqlite_db():
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS app_state(key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        INSERT OR IGNORE INTO meta(key,value) VALUES('schema_version','37_1_web_full_logic');
        """)


def normalize_db(data: Any) -> dict:
    if not isinstance(data, dict):
        data = empty_db()
    if "consumables" in data and "components" not in data:
        data["components"] = data.get("consumables", {})
    base = empty_db()
    for key, val in base.items():
        data.setdefault(key, copy.deepcopy(val))

    # merge defaults without deleting user additions
    for scope, cats in default_categories().items():
        data.setdefault("categories", {}).setdefault(scope, {})
        for cat, subs in cats.items():
            data["categories"][scope].setdefault(cat, [])
            for sub in subs:
                if sub not in data["categories"][scope][cat]:
                    data["categories"][scope][cat].append(sub)
    data.setdefault("categories", {}).setdefault("Illuminazione", {})
    for cat, subs in default_illumination_categories().items():
        data["categories"]["Illuminazione"].setdefault(cat, [])
        for sub in subs:
            if sub not in data["categories"]["Illuminazione"][cat]:
                data["categories"]["Illuminazione"][cat].append(sub)
    for sec in default_custom_sections():
        if sec not in data.setdefault("custom_sections", []):
            data["custom_sections"].append(sec)
    data["custom_sections"] = [x for x in data.get("custom_sections", []) if x not in ("materials", "components", "products")]
    for k, vals in default_formats().items():
        data.setdefault("formats", {}).setdefault(k, [])
        for v in vals:
            if v not in data["formats"][k]: data["formats"][k].append(v)
    for k, vals in default_thicknesses().items():
        data.setdefault("thicknesses", {}).setdefault(k, [])
        for v in vals:
            if v not in data["thicknesses"][k]: data["thicknesses"][k].append(v)
    data.setdefault("typologies", {}).update({k: data.get("typologies", {}).get(k, v) for k, v in default_typologies().items()})
    labels = data.setdefault("section_labels", default_section_labels())
    for k, v in default_section_labels().items():
        if labels.get(k) in ("", k, None): labels[k] = v
    for name, info in list(data.get("customers", {}).items()):
        if not isinstance(info, dict): data["customers"][name] = {"name": name, "notes": str(info)}
        else:
            info.setdefault("name", name); info.setdefault("notes", info.get("note", ""))
    for name, info in list(data.get("suppliers", {}).items()):
        if not isinstance(info, dict): data["suppliers"][name] = {"name": name, "sections": []}
        else:
            info.setdefault("name", name)
            if isinstance(info.get("sections", []), str): info["sections"] = [info["sections"]] if info["sections"] else []
            info.setdefault("sections", [])

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

    data.setdefault("quotes", [])
    business_settings(data)

    return data


def load_legacy_json_if_available():
    p = legacy_json_path()
    if not p.exists(): return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_db() -> dict:
    init_sqlite_db()
    with connect() as conn:
        row = conn.execute("SELECT value FROM app_state WHERE key='main'").fetchone()
    if row and row["value"]:
        try:
            return normalize_db(json.loads(row["value"]))
        except Exception:
            pass
    legacy = load_legacy_json_if_available()
    data = normalize_db(legacy if legacy is not None else empty_db())
    save_db(data)
    return data


def save_db(db: dict):
    init_sqlite_db()
    with connect() as conn:
        conn.execute("INSERT INTO app_state(key,value,updated_at) VALUES('main',?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at", (json.dumps(normalize_db(db), ensure_ascii=False), now_str()))


def section_label(db, scope):
    return db.get("section_labels", {}).get(scope, default_section_labels().get(scope, scope))


def scope_from_display(db, display):
    labels = db.get("section_labels", {})
    for scope in ("materials", "components", "products"):
        if display == labels.get(scope, default_section_labels().get(scope)):
            return scope
    return display


def raw_section_choices(db):
    product_sections = set(db.get("product_custom_sections", []))
    choices = [section_label(db, "materials"), section_label(db, "components")]
    choices += [x for x in db.get("custom_sections", []) if x not in product_sections and x != section_label(db, "products")]
    return list(dict.fromkeys(choices))


def product_section_choices(db):
    raw = set([section_label(db, "materials"), section_label(db, "components")] + db.get("custom_sections", []))
    choices = [section_label(db, "products")] + [x for x in db.get("product_custom_sections", []) if x not in raw]
    return list(dict.fromkeys(choices))


def category_names(db, scope):
    return sorted(db.get("categories", {}).get(scope, {}).keys())


def subcategory_names(db, scope, category):
    return sorted(db.get("categories", {}).get(scope, {}).get(category, []))


def ensure_category(db, scope, category, subcategory=""):
    category = (category or "").strip(); subcategory = (subcategory or "").strip()
    if not category: return
    db.setdefault("categories", {}).setdefault(scope, {}).setdefault(category, [])
    if subcategory and subcategory not in db["categories"][scope][category]:
        db["categories"][scope][category].append(subcategory)


def display_name_from_key(key, info=None):
    if info and info.get("display_name"): return info["display_name"]
    return str(key).split("__", 1)[0] if "__" in str(key) else str(key)


def supplier_item_key(name, section, category, subcategory, size, thickness, supplier):
    raw = "|".join(str(x).strip().lower() for x in (name, section, category, subcategory, size, thickness, supplier))
    safe = "".join(ch if ch.isalnum() else "_" for ch in raw)
    return f"{name}__{safe}"


def find_supplier_item_key(db, table, name, section, category, subcategory, size, thickness, supplier):
    target = tuple(str(x).strip().lower() for x in (name, section, category, subcategory, size, thickness, supplier))
    for key, info in db.get(table, {}).items():
        current = tuple(str(x).strip().lower() for x in (display_name_from_key(key, info), info.get("section", ""), info.get("category", ""), info.get("subcategory", ""), info.get("size", ""), info.get("thickness", ""), info.get("supplier", "")))
        if current == target: return key
    return None


def get_raw_item(db, name):
    for table in ("materials", "components"):
        table_data = db.get(table, {})
        if not isinstance(table_data, dict):
            continue
        if name in table_data and isinstance(table_data[name], dict):
            return table_data[name], table, name
        for k, info in table_data.items():
            if isinstance(info, dict) and display_name_from_key(k, info) == name:
                return info, table, k
    return None, None, None





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

def build_purchase_item_name(db, section, category, subcategory, size, thickness):
    parts = []
    if section == section_label(db, "materials"):
        parts.append(subcategory or category)
        if size: parts.append(size)
        if thickness: parts.append(thickness)
    else:
        if category: parts.append(category)
        if subcategory and subcategory.lower() != category.lower(): parts.append(subcategory)
        if size: parts.append(size)
        if thickness: parts.append(thickness)
    return " ".join([p for p in parts if p]).strip()



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

def product_material_unit_cost(db, name):
    product = db.get("products", {}).get(name) or {}; total = 0.0
    for row in product.get("bom", []):
        item, _, _ = get_raw_item(db, row.get("name", ""))
        if item: total += parse_float(item.get("cost_per_unit")) * parse_float(row.get("qty"))
    return total


def product_labor_unit_cost(db, name):
    p = db.get("products", {}).get(name) or {}
    return parse_float(p.get("labor_hours")) * parse_float(p.get("hourly_rate"))


def product_unit_cost(db, name):
    p = db.get("products", {}).get(name) or {}
    return product_material_unit_cost(db, name) + product_labor_unit_cost(db, name) + parse_float(p.get("extra_unit_cost"))


def product_collection_choices(db, category=None, subcategory=None):
    links = db.setdefault("product_collection_links", {})
    if category and subcategory:
        linked = sorted(links.get(category, {}).get(subcategory, []))
        if linked: return linked
    vals = set(db.get("product_collections", []))
    for sub_map in links.values():
        if isinstance(sub_map, dict):
            for collections in sub_map.values(): vals.update(collections)
    return sorted(vals)


def create_or_update_product(db, payload):
    name = (payload.get("name") or "").strip()
    if not name: raise ValueError("Inserisci il nome prodotto.")
    old_name = payload.get("old_name") or name
    section = payload.get("section") or section_label(db, "products")
    product = db.setdefault("products", {}).get(old_name, {}) if old_name in db.setdefault("products", {}) else {}
    if old_name != name and old_name in db["products"]: db["products"].pop(old_name, None)
    product.update({
        "section": section, "category": payload.get("category", ""), "subcategory": payload.get("subcategory", ""),
        "collection": payload.get("collection", ""), "tags": payload.get("tags", ""), "unit": payload.get("unit", "pz") or "pz",
        "labor_hours": max(0.0, parse_float(payload.get("labor_hours"))), "hourly_rate": max(0.0, parse_float(payload.get("hourly_rate"))),
        "extra_unit_cost": max(0.0, parse_float(payload.get("extra_unit_cost"))), "stock": max(0.0, parse_float(payload.get("stock", product.get("stock", 0)))),
        "bom": payload.get("bom", product.get("bom", [])) or [], "description": payload.get("description", product.get("description", "")),
    })
    db["products"][name] = product
    ensure_category(db, scope_from_display(db, section), product.get("category", ""), product.get("subcategory", ""))
    return product



def find_material_variants(db, item_name, needed_qty=0):
    item, table, key = get_raw_item(db, item_name)
    if not item:
        return []

    category = item.get("category", "")
    subcategory = item.get("subcategory", "")
    size = item.get("size", "")
    thickness = item.get("thickness", "")
    section = item.get("section", "")

    candidates = []

    for table_name in ("materials", "components"):
        for cand_key, info in db.get(table_name, {}).items():
            if cand_key == key:
                continue

            if not isinstance(info, dict):
                continue

            stock = parse_float(info.get("stock"))
            if stock <= 0:
                continue

            cand_category = info.get("category", "")
            cand_subcategory = info.get("subcategory", "")
            cand_size = info.get("size", "")
            cand_thickness = info.get("thickness", "")
            cand_section = info.get("section", "")

            same_section = section and cand_section == section
            same_category = category and cand_category == category
            same_sub = subcategory and cand_subcategory == subcategory
            same_size = size and cand_size == size
            same_thick = thickness and cand_thickness == thickness

            # Non mischiare aree/categorie senza logica.
            # Esempio: Legname può proporre Pioppo/MDF/Betulla, ma non LED/12V.
            if category == "Legname":
                if cand_category != "Legname":
                    continue
            else:
                # Per componenti/illuminazione serve almeno stessa categoria,
                # oppure stessa area + sottocategoria molto simile.
                if not same_category:
                    continue

            score = 0
            notes = []

            if same_section:
                score += 2
                notes.append("stessa area")

            if same_category:
                score += 8
                notes.append("stessa categoria")

            if same_sub:
                score += 8
                notes.append("stessa sottocategoria/essenza")
            elif cand_subcategory:
                score += 2
                notes.append(f"alternativa: {cand_subcategory}")

            if same_size:
                score += 6
                notes.append("stesso formato")
            elif cand_size:
                score += 1
                notes.append(f"formato diverso: {cand_size}")

            if same_thick:
                score += 6
                notes.append("stesso spessore")
            elif cand_thickness:
                score += 1
                notes.append(f"spessore diverso: {cand_thickness}")

            if stock >= needed_qty:
                score += 5
                notes.append("stock sufficiente")
            else:
                notes.append("stock parziale")

            # Priorità esempi:
            # Betulla 4 mancante → Pioppo 4 molto alto
            # Betulla 4 mancante → Betulla 6 alto
            # Betulla 4 mancante → Pioppo 6 medio
            if category == "Legname":
                if same_size and same_thick:
                    score += 8
                elif same_sub and same_size:
                    score += 5
                elif same_size or same_thick:
                    score += 3

            unit_cost = parse_float(info.get("weighted_average_cost", info.get("cost_per_unit")))

            candidates.append({
                "key": cand_key,
                "table": table_name,
                "name": display_name_from_key(cand_key, info),
                "stock": stock,
                "unit": info.get("unit", ""),
                "category": cand_category,
                "subcategory": cand_subcategory,
                "size": cand_size,
                "thickness": cand_thickness,
                "supplier": info.get("supplier", ""),
                "unit_cost": unit_cost,
                "score": score,
                "can_cover": stock >= needed_qty,
                "notes": ", ".join(notes),
            })

    return sorted(
        candidates,
        key=lambda x: (
            x.get("can_cover", False),
            x.get("score", 0),
            x.get("stock", 0)
        ),
        reverse=True
    )[:10]

def production_check(db, product_name, qty):
    product = db.get("products", {}).get(product_name)
    if not product: raise ValueError("Prodotto non trovato.")
    rows = []
    for idx, row in enumerate(product.get("bom", [])):
        item_name = row.get("name", ""); need = parse_float(row.get("qty")) * qty
        item, table, key = get_raw_item(db, item_name)
        if not item:
            rows.append({"index": idx, "ok": False, "name": item_name or "Voce senza nome", "key": item_name, "table": "", "needed": need, "available": 0, "missing": need, "unit": "", "reason": "Articolo non trovato", "variants": []})
            continue
        available = parse_float(item.get("stock")); ok = available >= need
        rows.append({"index": idx, "ok": ok, "name": display_name_from_key(key, item), "key": key, "table": table, "needed": need, "available": available, "missing": max(0, need-available), "unit": item.get("unit", ""), "reason": "Disponibile" if ok else "Stock insufficiente", "variants": [] if ok else find_material_variants(db, key, need)})
    return {"can_produce": all(r["ok"] for r in rows), "rows": rows}




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

def calculate_quote(db, payload):
    project_fee = parse_float(payload.get("project_fee"))
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
def record_product_sale(db, payload):
    name = payload.get("product") or payload.get("name")
    qty = parse_float(payload.get("qty")); price = parse_float(payload.get("unit_price"))
    product = db.get("products", {}).get(name)
    if not product: raise ValueError("Prodotto non trovato.")
    if qty <= 0 or price <= 0: raise ValueError("Quantità e prezzo devono essere maggiori di zero.")
    stock = parse_float(product.get("stock"))
    if stock < qty: raise ValueError(f"Stock insufficiente. Disponibile {stock:.2f}, richiesto {qty:.2f}.")
    material = product_material_unit_cost(db, name); labor = product_labor_unit_cost(db, name); extra = parse_float(product.get("extra_unit_cost")); total_unit = material+labor+extra
    product["stock"] = stock - qty
    sale = {"date": today_str(), "customer": payload.get("customer", ""), "product": name, "qty": qty, "unit_price": price, "total": qty*price, "source": "magazzino", "material_unit_cost": material, "labor_unit_cost": labor, "extra_unit_cost": extra, "total_unit_cost": total_unit, "margin_total": (price-total_unit)*qty}
    db.setdefault("sales", []).append(sale)
    return sale


def record_quote_sale(db, payload):
    qty = parse_float(payload.get("qty", 1)); price = parse_float(payload.get("unit_price")); name = payload.get("name") or "Vendita da preventivo"
    if qty <= 0 or price <= 0: raise ValueError("Quantità e prezzo unitario validi richiesti.")
    quote_material_total = sum(parse_float(x.get("cost")) for x in payload.get("rows", []))
    quote_labor_total = parse_float(payload.get("hours")) * parse_float(payload.get("rate"))
    quote_extra_total = parse_float(payload.get("packaging")) + parse_float(payload.get("energy")) + parse_float(payload.get("wear"))
    material = quote_material_total/qty if qty else 0; labor = quote_labor_total/qty if qty else 0; extra = quote_extra_total/qty if qty else 0; total_unit = material+labor+extra
    sale = {"date": today_str(), "customer": payload.get("customer", ""), "product": name, "qty": qty, "unit_price": price, "total": qty*price, "source": "preventivo", "discount_percent": parse_float(payload.get("discount")), "material_unit_cost": material, "labor_unit_cost": labor, "extra_unit_cost": extra, "total_unit_cost": total_unit, "margin_total": (price-total_unit)*qty, "estimated_materials": payload.get("estimates", [])}
    db.setdefault("sales", []).append(sale)
    return sale


def sale_cost_breakdown(db, sale):
    product = sale.get("product", ""); qty = parse_float(sale.get("qty")); unit_price = parse_float(sale.get("unit_price")); revenue = parse_float(sale.get("total")) or unit_price*qty
    material = parse_float(sale.get("material_unit_cost", product_material_unit_cost(db, product)))
    labor = parse_float(sale.get("labor_unit_cost", product_labor_unit_cost(db, product)))
    extra = parse_float(sale.get("extra_unit_cost", parse_float((db.get("products", {}).get(product) or {}).get("extra_unit_cost"))))
    total_unit = material+labor+extra
    margin = parse_float(sale.get("margin_total", revenue-total_unit*qty))
    return material, labor, extra, total_unit, margin, revenue



def _date_to_iso(value):
    """Converte date italiane o ISO in YYYY-MM-DD per ordinamenti/report."""
    s = str(value or "").strip()
    if not s:
        return ""
    if " " in s:
        s = s.split(" ")[0]
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return s


def _month_label(value):
    iso = _date_to_iso(value)
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%Y-%m")
    except Exception:
        return "Senza data"


def _sum_row(target, **values):
    for key, value in values.items():
        target[key] = parse_float(target.get(key)) + parse_float(value)


def report(db):
    """Report gestionale avanzato per dashboard, pivot e grafici.

    Mantiene i campi storici usati dal frontend e aggiunge dataset pronti per grafici:
    - sales_by_month
    - sales_by_source
    - stock_by_section
    - stock_by_category
    - margin_by_product
    - pivot_product_month
    - pivot_source_month
    - top_products
    - low_stock
    """
    raw_total = 0.0
    section_map = {}
    category_map = {}
    low_stock = []

    for table, fallback in (("materials", section_label(db, "materials")), ("components", section_label(db, "components"))):
        for key, info in db.get(table, {}).items():
            if not isinstance(info, dict):
                continue
            qty = parse_float(info.get("stock"))
            cost = parse_float(info.get("cost_per_unit"))
            val = qty * cost
            raw_total += val
            sec = info.get("section", fallback) or fallback
            cat = info.get("category", "Senza categoria") or "Senza categoria"
            sub = info.get("subcategory", "") or ""
            supplier = info.get("supplier", "") or "Senza fornitore"
            name = display_name_from_key(key, info)

            d = section_map.setdefault(sec, {"items": 0, "qty": 0.0, "value": 0.0})
            d["items"] += 1; d["qty"] += qty; d["value"] += val

            c = category_map.setdefault(cat, {"category": cat, "items": 0, "qty": 0.0, "value": 0.0})
            c["items"] += 1; c["qty"] += qty; c["value"] += val

            if qty <= 1:
                low_stock.append({
                    "name": name, "section": sec, "category": cat, "subcategory": sub,
                    "supplier": supplier, "qty": qty, "unit": info.get("unit", ""), "value": val
                })

    product_total = 0.0
    product_stock_rows = []
    for name, info in db.get("products", {}).items():
        if not isinstance(info, dict):
            continue
        stock = parse_float(info.get("stock"))
        unit_cost = product_unit_cost(db, name)
        value = stock * unit_cost
        product_total += value
        product_stock_rows.append({
            "product": name,
            "category": info.get("category", "") or "Senza categoria",
            "subcategory": info.get("subcategory", "") or "",
            "stock": stock,
            "unit_cost": unit_cost,
            "value": value,
        })

    sales_total = 0.0
    margin_total = 0.0
    product_map = {}
    month_map = {}
    source_map = {}
    source_month_map = {}
    product_month_map = {}
    details = []

    for sale in db.get("sales", []):
        if not isinstance(sale, dict):
            continue
        material, labor, extra, total_unit, margin, revenue = sale_cost_breakdown(db, sale)
        qty = parse_float(sale.get("qty"))
        product = sale.get("product", "Senza prodotto") or "Senza prodotto"
        source = sale.get("source", "manuale") or "manuale"
        date_raw = sale.get("date", "")
        date_iso = _date_to_iso(date_raw)
        month = _month_label(date_raw)
        cost_total = total_unit * qty

        sales_total += revenue
        margin_total += margin

        row = product_map.setdefault(product, {"product": product, "qty": 0.0, "revenue": 0.0, "materials": 0.0, "labor": 0.0, "extra": 0.0, "cost": 0.0, "margin": 0.0})
        row["qty"] += qty; row["revenue"] += revenue; row["materials"] += material * qty; row["labor"] += labor * qty; row["extra"] += extra * qty; row["cost"] += cost_total; row["margin"] += margin

        m = month_map.setdefault(month, {"month": month, "revenue": 0.0, "cost": 0.0, "margin": 0.0, "qty": 0.0, "sales": 0})
        m["revenue"] += revenue; m["cost"] += cost_total; m["margin"] += margin; m["qty"] += qty; m["sales"] += 1

        src = source_map.setdefault(source, {"source": source, "revenue": 0.0, "cost": 0.0, "margin": 0.0, "qty": 0.0, "sales": 0})
        src["revenue"] += revenue; src["cost"] += cost_total; src["margin"] += margin; src["qty"] += qty; src["sales"] += 1

        sm_key = (source, month)
        sm = source_month_map.setdefault(sm_key, {"source": source, "month": month, "revenue": 0.0, "margin": 0.0, "qty": 0.0})
        sm["revenue"] += revenue; sm["margin"] += margin; sm["qty"] += qty

        pm_key = (product, month)
        pm = product_month_map.setdefault(pm_key, {"product": product, "month": month, "revenue": 0.0, "margin": 0.0, "qty": 0.0})
        pm["revenue"] += revenue; pm["margin"] += margin; pm["qty"] += qty

        details.append({
            "date": normalize_date(date_raw), "date_iso": date_iso, "month": month,
            "product": product, "source": source, "customer": sale.get("customer", ""),
            "qty": qty, "unit_price": parse_float(sale.get("unit_price")), "revenue": revenue,
            "material_unit": material, "labor_unit": labor, "extra_unit": extra,
            "total_unit_cost": total_unit, "cost_total": cost_total, "margin": margin,
            "margin_pct": (margin / revenue * 100 if revenue else 0),
        })

    products = []
    for row in product_map.values():
        row["margin_pct"] = row["margin"] / row["revenue"] * 100 if row["revenue"] else 0
        products.append(row)

    sections = [{"section": k, **v} for k, v in section_map.items()]
    sections.sort(key=lambda x: x.get("value", 0), reverse=True)
    stock_by_category = sorted(category_map.values(), key=lambda x: x.get("value", 0), reverse=True)
    sales_by_month = sorted(month_map.values(), key=lambda x: x.get("month", ""))
    sales_by_source = sorted(source_map.values(), key=lambda x: x.get("revenue", 0), reverse=True)
    pivot_product_month = sorted(product_month_map.values(), key=lambda x: (x.get("product", ""), x.get("month", "")))
    pivot_source_month = sorted(source_month_map.values(), key=lambda x: (x.get("source", ""), x.get("month", "")))
    details.sort(key=lambda x: x.get("date_iso", ""), reverse=True)
    products.sort(key=lambda x: x.get("margin", 0), reverse=True)
    product_stock_rows.sort(key=lambda x: x.get("value", 0), reverse=True)
    low_stock.sort(key=lambda x: x.get("qty", 0))

    return {
        "raw_total": raw_total,
        "product_total": product_total,
        "sales_total": sales_total,
        "margin_total": margin_total,
        "margin_pct": (margin_total / sales_total * 100 if sales_total else 0),
        "sections": sections,
        "products": products,
        "margins_by_product": products,
        "sales_detail": details,
        "sales_by_month": sales_by_month,
        "sales_by_source": sales_by_source,
        "stock_by_section": sections,
        "stock_by_category": stock_by_category,
        "product_stock": product_stock_rows,
        "pivot_product_month": pivot_product_month,
        "pivot_source_month": pivot_source_month,
        "top_products": products[:8],
        "low_stock": low_stock[:20],
        "quotes_open": len([q for q in db.get("quotes", []) if q.get("status", "draft") in ("draft", "sent")]),
        "quotes_value": round(sum(parse_float(q.get("potential_value", q.get("recommended", 0))) for q in db.get("quotes", []) if q.get("status", "draft") in ("draft", "sent")), 2),
    }


def create_basic_material_presets(db):
    created = 0; updated = 0; section = section_label(db,"materials"); db.setdefault("materials", {})
    for category, names in {"Legname":["Betulla","Pioppo","MDF","Multistrato"], "Acrilico":["Rosso","Nero","Giallo","Blu","Verde","Bianco","Trasparente","Arancio"]}.items():
        formats = db.get("formats", {}).get(category, ["10x10","20x20","30x30","40x40"]); thicks = db.get("thicknesses", {}).get(category, [f"{i} mm" for i in range(1,11)])
        ensure_category(db,"materials",category)
        for sub in names:
            ensure_category(db,"materials",category,sub)
            for fmt in formats:
                for th in thicks:
                    name = f"{sub} {fmt} {th}" if category == "Legname" else f"Acrilico {sub} {fmt} {th}"
                    key = supplier_item_key(name, section, category, sub, fmt, th, "Preset")
                    if key in db["materials"]: updated += 1
                    else: created += 1
                    db["materials"].setdefault(key, {"display_name": name, "section": section, "category": category, "subcategory": sub, "size": fmt, "thickness": th, "unit": "pz", "supplier": "Preset", "cost_per_unit": 0.0, "stock": 0.0, "last_added": today_str()})
    return {"created": created, "updated": updated}


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

    quote["project_fee"] = parse_float(payload.get("project_fee"))
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


# ---------------------------------------------------------------------------
# v39.6.0 - Dettaglio prodotti finiti
# ---------------------------------------------------------------------------

def product_detail(db, name):
    product = db.get("products", {}).get(name)
    if not isinstance(product, dict):
        raise ValueError("Prodotto non trovato")

    material_cost = product_material_unit_cost(db, name)
    labor_cost = product_labor_unit_cost(db, name)
    extra_cost = parse_float(product.get("extra_unit_cost"))
    unit_cost = product_unit_cost(db, name)
    stock = parse_float(product.get("stock"))
    value = stock * unit_cost

    bom_rows = []
    for row in product.get("bom", []) or []:
        raw_name = row.get("name", "")
        item, table, key = get_raw_item(db, raw_name)
        unit_cost_raw = 0.0
        available = 0.0
        item_label = raw_name

        if item:
            enrich_raw_item(db, table, key, item)
            unit_cost_raw = parse_float(item.get("weighted_average_cost", item.get("cost_per_unit")))
            available = parse_float(item.get("stock"))
            item_label = display_name_from_key(key, item)

        qty = parse_float(row.get("qty"))

        bom_rows.append({
            "name": raw_name,
            "label": item_label,
            "qty": qty,
            "unit": row.get("unit", item.get("unit", "") if item else ""),
            "unit_cost": unit_cost_raw,
            "cost": qty * unit_cost_raw,
            "available": available,
            "ok": available >= qty if item else False,
        })

    movements = [
        x for x in db.get("product_movements", [])
        if x.get("product") == name
    ]

    sales = [
        x for x in db.get("sales", [])
        if x.get("product") == name
    ]

    return {
        "name": name,
        "product": product,
        "stock": stock,
        "unit_cost": unit_cost,
        "material_cost": material_cost,
        "labor_cost": labor_cost,
        "extra_cost": extra_cost,
        "value": value,
        "bom": bom_rows,
        "movements": list(reversed(movements)),
        "sales": list(reversed(sales)),
    }


# ---------------------------------------------------------------------------
# v39.7.0 - Catalogo avanzato formati, spessori e tipologie
# ---------------------------------------------------------------------------

def add_catalog_format(db, payload):
    category = (payload.get("category") or "").strip()
    value = (payload.get("value") or "").strip()

    if not category or not value:
        raise ValueError("Categoria e formato richiesti")

    values = db.setdefault("formats", {}).setdefault(category, [])
    if value not in values:
        values.append(value)

    return {"ok": True, "category": category, "value": value}


def delete_catalog_format(db, category, value):
    category = (category or "").strip()
    value = (value or "").strip()

    values = db.setdefault("formats", {}).setdefault(category, [])
    if value in values:
        values.remove(value)

    return {"ok": True}


def add_catalog_thickness(db, payload):
    category = (payload.get("category") or "").strip()
    value = (payload.get("value") or "").strip()

    if not category or not value:
        raise ValueError("Categoria e spessore richiesti")

    values = db.setdefault("thicknesses", {}).setdefault(category, [])
    if value not in values:
        values.append(value)

    return {"ok": True, "category": category, "value": value}


def delete_catalog_thickness(db, category, value):
    category = (category or "").strip()
    value = (value or "").strip()

    values = db.setdefault("thicknesses", {}).setdefault(category, [])
    if value in values:
        values.remove(value)

    return {"ok": True}


def add_catalog_typology(db, payload):
    category = (payload.get("category") or "").strip()
    subcategory = (payload.get("subcategory") or "").strip()
    value = (payload.get("value") or "").strip()

    if not category or not subcategory or not value:
        raise ValueError("Categoria, sottocategoria e tipologia richieste")

    values = db.setdefault("typologies", {}).setdefault(category, {}).setdefault(subcategory, [])
    if value not in values:
        values.append(value)

    return {
        "ok": True,
        "category": category,
        "subcategory": subcategory,
        "value": value,
    }


def delete_catalog_typology(db, category, subcategory, value):
    category = (category or "").strip()
    subcategory = (subcategory or "").strip()
    value = (value or "").strip()

    values = db.setdefault("typologies", {}).setdefault(category, {}).setdefault(subcategory, [])
    if value in values:
        values.remove(value)

    return {"ok": True}


def delete_product_collection_link(db, category, subcategory, collection):
    category = (category or "").strip()
    subcategory = (subcategory or "").strip()
    collection = (collection or "").strip()

    links = db.setdefault("product_collection_links", {})
    values = links.setdefault(category, {}).setdefault(subcategory, [])

    if collection in values:
        values.remove(collection)

    if category in links and subcategory in links[category] and not links[category][subcategory]:
        links[category].pop(subcategory, None)

    if category in links and not links[category]:
        links.pop(category, None)

    return {"ok": True}


# ---------------------------------------------------------------------------
# v39.8.0 - Preventivi stampabili / PDF cliente e interno
# ---------------------------------------------------------------------------

def _html_escape(value):
    return (
        str(value if value is not None else "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _money_html(value):
    return f"€ {parse_float(value):.2f}"


def _quote_price_value(quote):
    result = quote.get("result") or {}
    return (
        quote.get("discounted")
        or result.get("discounted")
        or quote.get("recommended")
        or result.get("recommended")
        or quote.get("potential_value")
        or 0
    )


def quote_customer_html(db, quote_id):
    quote = get_quote(db, quote_id)
    result = quote.get("result") or {}

    title = quote.get("name") or "Preventivo"
    customer = quote.get("customer") or "Cliente"
    notes = quote.get("notes") or quote.get("description") or ""
    price = _quote_price_value(quote)
    date = quote.get("date") or today_str()
    validity_days = business_settings(db).get("quote_validity_days", 15)

    rows_html = ""
    public_rows = quote.get("rows", []) or []
    for row in public_rows:
        label = row.get("label") or row.get("name") or "Voce"
        qty = parse_float(row.get("qty", 1))
        unit = row.get("unit", "")
        rows_html += f"""
          <tr>
            <td>{_html_escape(label)}</td>
            <td class="right">{qty:.2f} {_html_escape(unit)}</td>
          </tr>
        """

    if not rows_html:
        rows_html = """
          <tr>
            <td>Realizzazione personalizzata MN Laser Lab</td>
            <td class="right">1</td>
          </tr>
        """

    html = f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <title>Preventivo cliente - {_html_escape(title)}</title>
  <style>
    @page {{ size: A4; margin: 18mm; }}
    body {{
      font-family: Arial, Helvetica, sans-serif;
      color: #111827;
      margin: 0;
      background: #ffffff;
    }}
    .page {{
      max-width: 780px;
      margin: 0 auto;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 3px solid #058482;
      padding-bottom: 18px;
      margin-bottom: 28px;
    }}
    .brand h1 {{
      margin: 0;
      font-size: 28px;
      letter-spacing: -0.03em;
    }}
    .brand p {{
      margin: 5px 0 0;
      color: #4b5563;
      font-size: 13px;
    }}
    .doc-badge {{
      text-align: right;
      font-size: 12px;
      color: #4b5563;
    }}
    .doc-badge b {{
      display: block;
      color: #058482;
      font-size: 18px;
      margin-bottom: 4px;
    }}
    .box {{
      border: 1px solid #e5e7eb;
      border-radius: 16px;
      padding: 18px;
      margin-bottom: 18px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }}
    .label {{
      display: block;
      color: #6b7280;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: .08em;
      margin-bottom: 4px;
    }}
    .value {{
      font-weight: 700;
      font-size: 15px;
    }}
    h2 {{
      margin: 0 0 12px;
      font-size: 22px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
    }}
    th {{
      background: #f3f4f6;
      text-align: left;
      font-size: 12px;
      color: #374151;
      padding: 10px;
    }}
    td {{
      border-bottom: 1px solid #e5e7eb;
      padding: 10px;
      font-size: 13px;
    }}
    .right {{
      text-align: right;
    }}
    .price {{
      margin-top: 26px;
      border-radius: 18px;
      background: linear-gradient(135deg, #058482, #0f766e);
      color: white;
      padding: 22px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .price span {{
      font-size: 13px;
      opacity: .9;
    }}
    .price b {{
      font-size: 30px;
    }}
    .notes {{
      color: #374151;
      line-height: 1.55;
      white-space: pre-wrap;
    }}
    .footer {{
      margin-top: 30px;
      padding-top: 14px;
      border-top: 1px solid #e5e7eb;
      color: #6b7280;
      font-size: 12px;
      display: flex;
      justify-content: space-between;
      gap: 18px;
    }}
    .print-btn {{
      position: fixed;
      right: 20px;
      top: 20px;
      border: 0;
      background: #058482;
      color: white;
      border-radius: 999px;
      padding: 12px 18px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 12px 30px rgba(0,0,0,.18);
    }}
    @media print {{
      .print-btn {{ display: none; }}
      body {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
    }}
  </style>
</head>
<body>
  <button class="print-btn" onclick="window.print()">Stampa / Salva PDF</button>
  <main class="page">
    <section class="header">
      <div class="brand">
        <h1>MN Laser Lab</h1>
        <p>Creazioni artigianali in legno · Taglio e incisione laser</p>
        <p>Filippo Lolli · filippololli1@gmail.com</p>
      </div>
      <div class="doc-badge">
        <b>Preventivo</b>
        <span>{_html_escape(date)}</span><br>
        <span>ID: {_html_escape(quote.get("id", ""))}</span>
      </div>
    </section>

    <section class="box grid">
      <div>
        <span class="label">Cliente</span>
        <span class="value">{_html_escape(customer)}</span>
      </div>
      <div>
        <span class="label">Validità preventivo</span>
        <span class="value">{int(parse_float(validity_days, 15))} giorni</span>
      </div>
    </section>

    <section class="box">
      <h2>{_html_escape(title)}</h2>
      <div class="notes">{_html_escape(notes or "Realizzazione personalizzata secondo specifiche concordate.")}</div>

      <table>
        <thead>
          <tr>
            <th>Descrizione</th>
            <th class="right">Quantità</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        {quote_project_fee_html(quote)}
</tbody>
      </table>
    </section>

    <section class="price">
      <span>Totale preventivo</span>
      <b>{_money_html(price)}</b>
    </section>

    <section class="footer">
      <span>Preventivo generato con MN Laser Lab Manager.</span>
      <span>Il presente documento non include dettagli interni di costo.</span>
    </section>
  </main>
</body>
</html>"""
    return apply_pdf_brand_to_html(db, html, 'customer', quote)


def quote_internal_html(db, quote_id):
    quote = get_quote(db, quote_id)
    result = quote.get("result") or {}
    title = quote.get("name") or "Preventivo"
    rows = quote.get("rows", []) or []

    material_rows = ""
    for row in rows:
        label = row.get("label") or row.get("name") or "Voce"
        qty = parse_float(row.get("qty", 1))
        unit = row.get("unit", "")
        unit_cost = parse_float(row.get("unit_cost", row.get("cost_per_unit", row.get("weighted_average_cost", 0))))
        cost = parse_float(row.get("cost", qty * unit_cost))

        material_rows += f"""
          <tr>
            <td>{_html_escape(label)}</td>
            <td class="right">{qty:.2f} {_html_escape(unit)}</td>
            <td class="right">{_money_html(unit_cost)}</td>
            <td class="right">{_money_html(cost)}</td>
          </tr>
        """

    if not material_rows:
        material_rows = """
          <tr>
            <td colspan="4">Nessun materiale collegato</td>
          </tr>
        """

    real = result.get("real", result.get("real_cost", quote.get("real", 0)))
    min_price = result.get("min", result.get("min_price", quote.get("min", 0)))
    recommended = result.get("recommended", quote.get("recommended", 0))
    discounted = result.get("discounted", quote.get("discounted", 0))
    premium = result.get("premium", quote.get("premium", 0))

    html = f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <title>PDF interno - {_html_escape(title)}</title>
  <style>
    @page {{ size: A4; margin: 14mm; }}
    body {{
      font-family: Arial, Helvetica, sans-serif;
      color: #111827;
      margin: 0;
      background: #ffffff;
    }}
    .page {{
      max-width: 820px;
      margin: 0 auto;
    }}
    .header {{
      border-bottom: 3px solid #111827;
      padding-bottom: 14px;
      margin-bottom: 20px;
    }}
    h1 {{
      margin: 0;
      font-size: 25px;
    }}
    .muted {{
      color: #6b7280;
      font-size: 12px;
    }}
    .box {{
      border: 1px solid #e5e7eb;
      border-radius: 14px;
      padding: 14px;
      margin-bottom: 14px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }}
    .kpi {{
      background: #f9fafb;
      border-radius: 12px;
      padding: 12px;
    }}
    .kpi span {{
      display: block;
      color: #6b7280;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: .06em;
    }}
    .kpi b {{
      display: block;
      margin-top: 5px;
      font-size: 17px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th {{
      background: #f3f4f6;
      text-align: left;
      padding: 9px;
      font-size: 12px;
    }}
    td {{
      padding: 9px;
      border-bottom: 1px solid #e5e7eb;
      font-size: 12px;
    }}
    .right {{
      text-align: right;
    }}
    .print-btn {{
      position: fixed;
      right: 20px;
      top: 20px;
      border: 0;
      background: #111827;
      color: white;
      border-radius: 999px;
      padding: 12px 18px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 12px 30px rgba(0,0,0,.18);
    }}
    @media print {{
      .print-btn {{ display: none; }}
      body {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
    }}
  </style>
</head>
<body>
  <button class="print-btn" onclick="window.print()">Stampa / Salva PDF</button>
  <main class="page">
    <section class="header">
      <h1>Analisi interna preventivo</h1>
      <div class="muted">MN Laser Lab Manager · Filippo Lolli · filippololli1@gmail.com</div>
      <div class="muted">ID: {_html_escape(quote.get("id", ""))} · Data: {_html_escape(quote.get("date", ""))}</div>
    </section>

    <section class="box">
      <h2>{_html_escape(title)}</h2>
      <p class="muted">Cliente: {_html_escape(quote.get("customer", "—"))}</p>
      <p class="muted">{_html_escape(quote.get("notes", ""))}</p>
    </section>

    <section class="box grid">
      <div class="kpi"><span>Costo reale</span><b>{_money_html(real)}</b></div>
      <div class="kpi"><span>Prezzo minimo</span><b>{_money_html(min_price)}</b></div>
      <div class="kpi"><span>Consigliato</span><b>{_money_html(recommended)}</b></div>
      <div class="kpi"><span>Premium</span><b>{_money_html(premium)}</b></div>
    </section>

    <section class="box grid">
      <div class="kpi"><span>Ore lavoro</span><b>{parse_float(quote.get("hours")):.2f}</b></div>
      <div class="kpi"><span>Tariffa/h</span><b>{_money_html(quote.get("rate"))}</b></div>
      <div class="kpi"><span>Margine</span><b>{parse_float(quote.get("margin")):.2f}%</b></div>
      <div class="kpi"><span>Sconto</span><b>{parse_float(quote.get("discount")):.2f}%</b></div>
    </section>

    <section class="box">
      <h2>Materiali</h2>
      <table>
        <thead>
          <tr>
            <th>Materiale</th>
            <th class="right">Quantità</th>
            <th class="right">Costo/u</th>
            <th class="right">Totale</th>
          </tr>
        </thead>
        <tbody>
          {material_rows}
        {quote_project_fee_html(quote)}
</tbody>
      </table>
    </section>

    <section class="box grid">
      <div class="kpi"><span>Packaging</span><b>{_money_html(quote.get("packaging"))}</b></div>
      <div class="kpi"><span>Energia</span><b>{_money_html(quote.get("energy"))}</b></div>
      <div class="kpi"><span>Usura</span><b>{_money_html(quote.get("wear"))}</b></div>
      <div class="kpi"><span>Commissioni</span><b>{parse_float(quote.get("commission")):.2f}%</b></div>
    </section>
  </main>
</body>
</html>"""
    return apply_pdf_brand_to_html(db, html, 'internal', quote)


# ---------------------------------------------------------------------------
# v39.8.2 - Ricerca robusta preventivi per PDF
# ---------------------------------------------------------------------------

def get_quote_flexible(db, quote_id):
    quotes = db.get("quotes", []) or []

    for q in quotes:
        if str(q.get("id", "")) == str(quote_id):
            return q

    # fallback: alcune versioni vecchie possono avere id salvati come indice/stringa
    try:
        idx = int(str(quote_id))
        if 0 <= idx < len(quotes):
            return quotes[idx]
    except Exception:
        pass

    # fallback: se arriva un id parziale o codificato diversamente
    qid = str(quote_id or "").strip()
    for q in quotes:
        current = str(q.get("id", "")).strip()
        if current and (current.endswith(qid) or qid.endswith(current)):
            return q

    raise ValueError("Preventivo non trovato")


# ---------------------------------------------------------------------------
# v40.3.0 - Backup avanzato e ripristino
# ---------------------------------------------------------------------------

def list_backups():
    root = user_data_dir()
    rows = []

    for p in sorted(root.glob("mn_laser_lab_*_*.db"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            stat = p.stat()
            rows.append({
                "filename": p.name,
                "path": str(p),
                "size": stat.st_size,
                "updated_at": datetime.fromtimestamp(stat.st_mtime).strftime("%d-%m-%Y %H:%M:%S"),
            })
        except Exception:
            pass

    return rows


def backup_database_named(name="manuale"):
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in str(name or "manuale").strip())
    safe = safe or "manuale"
    return backup_database(safe)




# ---------------------------------------------------------------------------
# v40.3.1 - SQLite WAL safe backup/restore
# ---------------------------------------------------------------------------

def sqlite_checkpoint():
    """Forza SQLite a scrivere il WAL nel file .db principale."""
    try:
        with connect() as conn:
            conn.execute("PRAGMA wal_checkpoint(FULL)")
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        pass


def sqlite_sidecar_paths(path):
    p = Path(path)
    return [
        Path(str(p) + "-wal"),
        Path(str(p) + "-shm"),
    ]


def remove_sqlite_sidecars(path):
    for p in sqlite_sidecar_paths(path):
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass


def backup_database(suffix="backup"):
    sqlite_checkpoint()

    source = db_path()
    if not source.exists():
        return ""

    dest = user_data_dir() / f"mn_laser_lab_{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(source, dest)
    return str(dest)


def restore_database_from_backup(filename):
    filename = str(filename or "").strip()
    if not filename:
        raise ValueError("Nome backup mancante")

    root = user_data_dir()
    source = root / filename

    if not source.exists() or source.suffix.lower() != ".db":
        raise ValueError("Backup non trovato")

    sqlite_checkpoint()

    # Backup di sicurezza prima del ripristino.
    safety = backup_database("prima_ripristino")

    target = db_path()

    # Fondamentale con journal_mode=WAL:
    # rimuove i file sidecar vecchi, altrimenti SQLite può leggere dati non ripristinati.
    remove_sqlite_sidecars(target)

    shutil.copy2(source, target)

    # Dopo la copia, elimina eventuali sidecar generati prima della prossima apertura.
    remove_sqlite_sidecars(target)

    # Riapre e normalizza il db ripristinato.
    restored_data = load_db()
    save_db(restored_data)

    return {
        "ok": True,
        "restored": str(source),
        "safety_backup": safety,
        "db_path": str(target),
        "items": {
            "materials": len(restored_data.get("materials", {})),
            "components": len(restored_data.get("components", {})),
            "products": len(restored_data.get("products", {})),
            "sales": len(restored_data.get("sales", [])),
            "quotes": len(restored_data.get("quotes", [])),
        }
    }


# ---------------------------------------------------------------------------
# v40.4.0 - Import CSV acquisti
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


# ---------------------------------------------------------------------------
# v40.5.0 - Dashboard operativa intelligente
# ---------------------------------------------------------------------------

def operational_dashboard(db):
    raw_items = aggregated_raw_items(db)

    zero_cost = []
    low_stock = []
    never_purchased = []

    for item in raw_items:
        stock = parse_float(item.get("stock"))
        cost = parse_float(item.get("cost_per_unit", item.get("weighted_average_cost", 0)))
        status = item.get("inventory_status", "")

        if stock > 0 and cost <= 0:
            zero_cost.append(item)

        if stock <= 1 and stock > 0:
            low_stock.append(item)

        if stock <= 0 and cost <= 0 or status == "mai_acquistato":
            never_purchased.append(item)

    products = []
    products_without_bom = []
    products_low_stock = []

    for name, info in db.get("products", {}).items():
        if not isinstance(info, dict):
            continue

        stock = parse_float(info.get("stock"))
        bom = info.get("bom", []) or []
        unit_cost = product_unit_cost(db, name)

        row = {
            "name": name,
            "category": info.get("category", ""),
            "subcategory": info.get("subcategory", ""),
            "collection": info.get("collection", ""),
            "stock": stock,
            "unit_cost": unit_cost,
            "bom_count": len(bom),
        }

        products.append(row)

        if not bom:
            products_without_bom.append(row)

        if stock <= 1:
            products_low_stock.append(row)

    quotes = db.get("quotes", []) or []
    quote_stats = {}
    quote_rows = []

    for q in quotes:
        if not isinstance(q, dict):
            continue

        status = q.get("status", "bozza") or "bozza"
        quote_stats[status] = quote_stats.get(status, 0) + 1

        if status in ("bozza", "inviato", "accettato", "da_modificare"):
            quote_rows.append({
                "id": q.get("id", ""),
                "name": q.get("name", ""),
                "customer": q.get("customer", ""),
                "status": status,
                "total": q.get("recommended") or q.get("discounted") or q.get("total") or 0,
                "date": q.get("date", ""),
            })

    sales_total = sum(parse_float(s.get("total")) for s in db.get("sales", []) if isinstance(s, dict))
    raw_value = sum(parse_float(x.get("value")) for x in raw_items)
    product_value = sum(parse_float(p.get("stock")) * product_unit_cost(db, name) for name, p in db.get("products", {}).items() if isinstance(p, dict))

    tasks = []

    def add_task(priority, title, detail, target, count=0):
        if count:
            tasks.append({
                "priority": priority,
                "title": title,
                "detail": detail,
                "target": target,
                "count": count,
            })

    add_task("alta", "Materiali con costo mancante", "Stock presente ma costo medio pari a zero", "materials", len(zero_cost))
    add_task("alta", "Prodotti senza distinta base", "Prodotti creati ma senza materiali collegati", "products", len(products_without_bom))
    add_task("media", "Materiali sotto scorta", "Stock basso o da ricontrollare", "materials", len(low_stock))
    add_task("media", "Prodotti con stock basso", "Prodotti finiti con disponibilità ≤ 1", "products", len(products_low_stock))
    add_task("bassa", "Preset mai acquistati", "Articoli presenti da catalogo ma non ancora valorizzati", "materials", len(never_purchased))
    add_task("media", "Preventivi accettati", "Da trasformare in produzione/consegna", "quote", quote_stats.get("accettato", 0))

    priority_order = {"alta": 0, "media": 1, "bassa": 2}
    tasks.sort(key=lambda x: (priority_order.get(x.get("priority"), 9), -x.get("count", 0)))

    return {
        "summary": {
            "raw_value": round(raw_value, 2),
            "product_value": round(product_value, 2),
            "sales_total": round(sales_total, 2),
            "raw_items": len(raw_items),
            "products": len(products),
            "quotes": len(quotes),
        },
        "tasks": tasks[:8],
        "zero_cost": zero_cost[:10],
        "low_stock": low_stock[:10],
        "products_without_bom": products_without_bom[:10],
        "products_low_stock": products_low_stock[:10],
        "quotes": quote_rows[:10],
        "quote_stats": quote_stats,
    }


# ---------------------------------------------------------------------------
# v40.6.0 - Workflow preventivi avanzato
# ---------------------------------------------------------------------------

QUOTE_STATUSES = [
    "bozza",
    "inviato",
    "da_modificare",
    "accettato",
    "in_produzione",
    "consegnato",
    "rifiutato",
    "scaduto",
]


def normalize_quote_status(status):
    status = str(status or "bozza").strip().lower().replace(" ", "_")
    aliases = {
        "draft": "bozza",
        "sent": "inviato",
        "accepted": "accettato",
        "rejected": "rifiutato",
        "production": "in_produzione",
        "delivered": "consegnato",
    }
    status = aliases.get(status, status)
    return status if status in QUOTE_STATUSES else "bozza"


def quote_workflow_summary(db):
    quotes = db.get("quotes", []) or []
    counts = {s: 0 for s in QUOTE_STATUSES}

    rows = []
    for q in quotes:
        if not isinstance(q, dict):
            continue

        status = normalize_quote_status(q.get("status"))
        q["status"] = status
        counts[status] = counts.get(status, 0) + 1

        rows.append({
            "id": q.get("id", ""),
            "name": q.get("name", ""),
            "customer": q.get("customer", ""),
            "status": status,
            "date": q.get("date", ""),
            "total": q.get("discounted") or q.get("recommended") or q.get("total") or q.get("unit_price") or 0,
            "margin": q.get("margin_total", 0),
        })

    return {
        "statuses": QUOTE_STATUSES,
        "counts": counts,
        "quotes": rows,
    }


def update_quote_status(db, quote_id, status):
    status = normalize_quote_status(status)
    quote = get_quote_flexible(db, quote_id)

    quote["status"] = status
    quote["status_updated_at"] = now_str()

    quote.setdefault("history", []).append({
        "date": now_str(),
        "event": "Cambio stato",
        "status": status,
    })

    return {
        "ok": True,
        "id": quote.get("id", quote_id),
        "status": status,
    }


def duplicate_quote(db, quote_id, name=""):
    quote = get_quote_flexible(db, quote_id)
    quotes = db.setdefault("quotes", [])

    new_quote = copy.deepcopy(quote)
    new_id = f"Q{datetime.now().strftime('%Y%m%d%H%M%S')}"
    new_quote["id"] = new_id
    new_quote["name"] = (name or f"{quote.get('name', 'Preventivo')} - copia").strip()
    new_quote["status"] = "bozza"
    new_quote["date"] = today_str()
    new_quote["created_at"] = now_str()
    new_quote["status_updated_at"] = now_str()
    new_quote["history"] = [{
        "date": now_str(),
        "event": "Duplicato da preventivo",
        "source_id": quote.get("id", quote_id),
        "status": "bozza",
    }]

    quotes.append(new_quote)

    return {
        "ok": True,
        "quote": new_quote,
    }


# ---------------------------------------------------------------------------
# v40.7.0 - Impostazioni modello PDF / brand
# ---------------------------------------------------------------------------

def default_pdf_settings():
    return {
        "company_name": "MN Laser Lab",
        "author": "Filippo Lolli",
        "email": "filippololli1@gmail.com",
        "phone": "",
        "address": "",
        "website": "",
        "vat": "",
        "logo_data_url": "",
        "primary_color": "#058482",
        "customer_title": "Preventivo cliente",
        "internal_title": "Scheda interna preventivo",
        "intro_text": "Grazie per averci contattato. Di seguito trovi il riepilogo del preventivo richiesto.",
        "terms": "Il preventivo è valido salvo disponibilità materiali e conferma finale della lavorazione.",
        "footer": "MN Laser Lab - Creazioni artigianali in legno e taglio laser",
    }


def get_pdf_settings(db):
    settings = db.setdefault("pdf_settings", {})
    base = default_pdf_settings()
    for k, v in base.items():
        settings.setdefault(k, v)
    return settings


def update_pdf_settings(db, payload):
    settings = get_pdf_settings(db)
    allowed = set(default_pdf_settings().keys())

    for key, value in (payload or {}).items():
        if key in allowed:
            settings[key] = str(value or "")

    db["pdf_settings"] = settings
    return settings


def export_pdf_settings(db):
    return {
        "filename": f"mn_laser_lab_pdf_template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "data": get_pdf_settings(db),
    }


def import_pdf_settings(db, payload):
    if not isinstance(payload, dict):
        raise ValueError("Modello PDF non valido")
    return update_pdf_settings(db, payload)


def _pdf_brand_block(db):
    s = get_pdf_settings(db)
    logo = s.get("logo_data_url", "")
    logo_html = f'<img class="brand-logo" src="{logo}" alt="Logo" />' if logo else ""
    return f"""
    <div class="brand-head">
      <div>
        {logo_html}
      </div>
      <div class="brand-company">
        <h1>{s.get('company_name','MN Laser Lab')}</h1>
        <p>{s.get('author','')}</p>
        <p>{s.get('email','')} {s.get('phone','')}</p>
        <p>{s.get('address','')}</p>
        <p>{s.get('website','')} {s.get('vat','')}</p>
      </div>
    </div>
    """


def _pdf_brand_css(db):
    s = get_pdf_settings(db)
    color = s.get("primary_color", "#058482") or "#058482"
    return f"""
    <style>
      :root {{ --brand: {color}; }}
      .brand-head {{
        display: flex;
        justify-content: space-between;
        gap: 24px;
        align-items: flex-start;
        border-bottom: 3px solid var(--brand);
        padding-bottom: 18px;
        margin-bottom: 24px;
      }}
      .brand-logo {{
        max-width: 150px;
        max-height: 80px;
        object-fit: contain;
      }}
      .brand-company {{
        text-align: right;
        font-size: 12px;
        color: #475569;
      }}
      .brand-company h1 {{
        margin: 0 0 6px;
        color: #0f172a;
        font-size: 24px;
      }}
      .brand-company p {{
        margin: 2px 0;
      }}
      .pdf-intro {{
        border-left: 4px solid var(--brand);
        padding: 10px 14px;
        background: #f8fafc;
        margin: 18px 0;
        color: #334155;
      }}
      .pdf-terms {{
        margin-top: 28px;
        padding: 14px;
        background: #f8fafc;
        border-radius: 10px;
        color: #475569;
        font-size: 12px;
      }}
      .pdf-footer {{
        margin-top: 28px;
        border-top: 1px solid #e2e8f0;
        padding-top: 12px;
        font-size: 11px;
        color: #64748b;
        text-align: center;
      }}
    </style>
    """


# ---------------------------------------------------------------------------
# v40.7.2b - Applicazione sicura modello PDF senza doppia intestazione
# ---------------------------------------------------------------------------

def apply_pdf_brand_to_html(db, html, kind="customer", quote=None):
    settings = get_pdf_settings(db)
    quote = quote or {}

    company = settings.get("company_name", "MN Laser Lab") or "MN Laser Lab"
    author = settings.get("author", "Filippo Lolli") or "Filippo Lolli"
    email = settings.get("email", "filippololli1@gmail.com") or "filippololli1@gmail.com"
    phone = settings.get("phone", "") or ""
    address = settings.get("address", "") or ""
    website = settings.get("website", "") or ""
    vat = settings.get("vat", "") or ""
    color = settings.get("primary_color", "#058482") or "#058482"
    footer = settings.get("footer", "MN Laser Lab - Creazioni artigianali in legno e taglio laser") or ""
    terms = settings.get("terms", "") or ""
    intro = settings.get("intro_text", "") or ""
    logo = settings.get("logo_data_url", "") or ""

    project_fee = parse_float(quote.get("project_fee"))

    # Logo fallback MN se non è stato caricato un logo nelle impostazioni.
    if not logo:
        logo = (
            "data:image/svg+xml;utf8,"
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 160 160'>"
            "<rect width='160' height='160' rx='34' fill='%23f8fafc'/>"
            "<circle cx='80' cy='80' r='62' fill='white' stroke='%23058482' stroke-width='6'/>"
            "<text x='80' y='76' text-anchor='middle' font-family='Arial, Helvetica, sans-serif' font-size='34' font-weight='900' fill='%230f172a'>MN</text>"
            "<text x='80' y='103' text-anchor='middle' font-family='Arial, Helvetica, sans-serif' font-size='13' font-weight='700' fill='%23058482'>LASER LAB</text>"
            "</svg>"
        )

    contact_bits = [x for x in [author, email, phone, address, website, vat] if str(x or "").strip()]
    contact_line = " · ".join(contact_bits)

    # Pulizia residui patch precedenti.
    html = html.replace("{_pdf_brand_css(db)}", "")
    html = html.replace("{_pdf_brand_block(db)}", "")

    # Sostituzioni dinamiche.
    html = html.replace("#058482", color)
    html = html.replace("MN Laser Lab", company)

    old_contacts = [
        "Filippo Lolli - filippololli1@gmail.com",
        "Filippo Lolli · filippololli1@gmail.com",
        "Filippo Lolli - filippololli@gmail.com",
        "Filippo Lolli · filippololli@gmail.com",
        "Mauro Nocco · mnlaserlab@gmail.com",
        "Mauro Nocco - mnlaserlab@gmail.com",
        "mnlaserlab@gmail.com",
        "filippololli@gmail.com",
        "filippololli1@gmail.com",
    ]

    for old in old_contacts:
        html = html.replace(old, contact_line or old)

    old_subtitles = [
        "Creazioni artigianali in legno · Taglio e incisione laser",
        "Creazioni artigianali in legno - Taglio e incisione laser",
        "Creazioni artigianali in legno e taglio laser",
        "MN Laser Lab - Creazioni artigianali in legno e taglio laser",
    ]

    business_subtitle = footer or "Creazioni artigianali in legno e taglio laser"
    for old in old_subtitles:
        html = html.replace(old, business_subtitle)

    if intro:
        html = html.replace(
            "Grazie per averci contattato. Di seguito trovi il riepilogo del preventivo richiesto.",
            intro
        )

    if terms:
        html = html.replace(
            "Il preventivo è valido salvo disponibilità materiali e conferma finale della lavorazione.",
            terms
        )

    if footer:
        html = html.replace("Preventivo generato con MN Laser Lab Manager.", footer)

    # Rimuove eventuale testata duplicata nata dalle patch precedenti.
    html = re.sub(
        r"<div class=['\"]brand-head['\"].*?</div>\s*</div>",
        "",
        html,
        flags=re.DOTALL
    )

    # Inserisce il logo nella testata esistente.
    if "pdf-brand-logo-inline" not in html:
        logo_html = f"<img class='pdf-brand-logo-inline' src='{logo}' alt='Logo MN Laser Lab' />"
        html = html.replace(
            f"<h1>{company}</h1>",
            f"<div class='pdf-brand-title-row'>{logo_html}<div><h1>{company}</h1><p class='pdf-dynamic-contact'>{contact_line}</p></div></div>",
            1
        )

    # Se il contatto non è entrato, lo aggiunge sotto il titolo.
    if contact_line and contact_line not in html:
        html = html.replace(
            f"<h1>{company}</h1>",
            f"<h1>{company}</h1><p class='pdf-dynamic-contact'>{contact_line}</p>",
            1
        )

    # Spese di progetto: voce separata nel PDF solo se > 0.
    if project_fee > 0 and "pdf-project-fee" not in html:
        project_fee_html = f"""
        <div class="pdf-project-fee">
          <span>Spese di progetto</span>
          <strong>€ {project_fee:.2f}</strong>
        </div>
        """

        if "Totale preventivo" in html:
            html = html.replace("Totale preventivo", project_fee_html + "\nTotale preventivo", 1)
        else:
            html = html.replace("</body>", project_fee_html + "\n</body>", 1)

    # CSS professionale PDF.
    extra_css = f"""
    <style>
      :root {{
        --brand: {color};
        --ink: #0f172a;
        --muted: #64748b;
        --line: #e2e8f0;
        --soft: #f8fafc;
      }}

      body {{
        background: #f1f5f9 !important;
        color: var(--ink) !important;
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif !important;
        margin: 0 !important;
        padding: 34px 0 44px !important;
      }}

      .page, main, .document, .quote-page {{
        width: min(920px, calc(100vw - 64px)) !important;
        margin: 0 auto !important;
        background: #ffffff !important;
      }}

      .pdf-brand-title-row {{
        display: flex !important;
        align-items: center !important;
        gap: 16px !important;
      }}

      .pdf-brand-logo-inline {{
        width: 74px !important;
        height: 74px !important;
        object-fit: contain !important;
        display: block !important;
        flex: 0 0 auto !important;
      }}

      .pdf-dynamic-contact {{
        margin: 5px 0 0 !important;
        color: var(--muted) !important;
        font-size: 13px !important;
        line-height: 1.35 !important;
        font-weight: 600 !important;
      }}

      h1 {{
        margin: 0 !important;
        font-size: 28px !important;
        line-height: 1.05 !important;
        letter-spacing: -0.04em !important;
      }}

      h2, h3 {{
        letter-spacing: -0.025em !important;
      }}

      table {{
        width: 100% !important;
        border-collapse: collapse !important;
        table-layout: fixed !important;
      }}

      th {{
        background: #f1f5f9 !important;
        color: #475569 !important;
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: .06em !important;
        padding: 12px 13px !important;
      }}

      td {{
        padding: 13px !important;
        border-bottom: 1px solid #e5e7eb !important;
        color: #1e293b !important;
        font-size: 13px !important;
        line-height: 1.35 !important;
      }}

      td:last-child,
      th:last-child,
      .right {{
        text-align: right !important;
      }}

      .pdf-project-fee {{
        margin: 18px 0 10px !important;
        border: 1px solid rgba(5, 132, 130, .22) !important;
        background: linear-gradient(135deg, rgba(5,132,130,.08), rgba(5,132,130,.03)) !important;
        border-radius: 16px !important;
        padding: 15px 18px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 18px !important;
        color: var(--ink) !important;
      }}

      .pdf-project-fee span {{
        font-size: 13px !important;
        font-weight: 800 !important;
        color: #334155 !important;
      }}

      .pdf-project-fee strong {{
        font-size: 22px !important;
        color: var(--brand) !important;
      }}

      .print-button,
      .print-actions,
      button {{
        position: fixed;
        top: 24px;
        right: 24px;
      }}

      @media print {{
        body {{
          background: white !important;
          padding: 0 !important;
        }}

        .page, main, .document, .quote-page {{
          width: 100% !important;
          margin: 0 !important;
          box-shadow: none !important;
        }}

        .print-button, .print-actions, button {{
          display: none !important;
        }}
      }}
    </style>
    """

    if "</head>" in html:
        html = html.replace("</head>", extra_css + "\n</head>", 1)

    return html

def quote_register_sale(db, quote_id, payload=None):
    payload = payload or {}
    quote = get_quote_flexible(db, quote_id)

    name = payload.get("name") or quote.get("name") or "Vendita da preventivo"
    customer = payload.get("customer") or quote.get("customer") or ""
    qty = parse_float(payload.get("qty", 1)) or 1

    unit_price = (
        parse_float(payload.get("unit_price"))
        or parse_float(quote.get("discounted"))
        or parse_float(quote.get("recommended"))
        or parse_float(quote.get("total"))
        or parse_float(quote.get("unit_price"))
    )

    rows = quote.get("rows", []) or []
    estimated_materials = quote.get("estimated_materials", []) or []

    sale_payload = {
        "name": name,
        "customer": customer,
        "qty": qty,
        "unit_price": unit_price,
        "rows": rows,
        "estimated_materials": estimated_materials,
        "hours": quote.get("hours", 0),
        "rate": quote.get("rate", 0),
        "packaging": quote.get("packaging", 0),
        "energy": quote.get("energy", 0),
        "wear": quote.get("wear", 0),
        "commission": quote.get("commission", 0),
        "margin": quote.get("margin", 0),
        "discount": quote.get("discount", 0),
        "source": "preventivo",
        "quote_id": quote.get("id", quote_id),
    }

    result = record_quote_sale(db, sale_payload)

    quote["status"] = "consegnato"
    quote["status_updated_at"] = now_str()
    quote.setdefault("history", []).append({
        "date": now_str(),
        "event": "Vendita registrata da preventivo",
        "status": "consegnato",
    })

    return {
        "ok": True,
        "sale": result,
        "quote_status": quote["status"],
    }


def quote_start_production(db, quote_id):
    quote = get_quote_flexible(db, quote_id)

    quote["status"] = "in_produzione"
    quote["status_updated_at"] = now_str()
    quote.setdefault("history", []).append({
        "date": now_str(),
        "event": "Preventivo avviato in produzione",
        "status": "in_produzione",
    })

    return {
        "ok": True,
        "id": quote.get("id", quote_id),
        "status": "in_produzione",
    }


def quote_mark_delivered(db, quote_id):
    quote = get_quote_flexible(db, quote_id)

    quote["status"] = "consegnato"
    quote["status_updated_at"] = now_str()
    quote.setdefault("history", []).append({
        "date": now_str(),
        "event": "Preventivo segnato come consegnato",
        "status": "consegnato",
    })

    return {
        "ok": True,
        "id": quote.get("id", quote_id),
        "status": "consegnato",
    }


def quote_project_fee_html(quote):
    fee = parse_float((quote or {}).get("project_fee"))
    if fee <= 0:
        return ""
    return f"""
      <tr>
        <td>Spese di progetto</td>
        <td class="right">1.00 pz</td>
        <td class="right">€ {fee:.2f}</td>
      </tr>
    """
