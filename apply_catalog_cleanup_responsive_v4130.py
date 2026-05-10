from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN = ROOT / "backend" / "app" / "main.py"
CSS = ROOT / "frontend" / "src" / "style.css"

TECHNICAL_AREAS = {"materials", "components", "products", "sales", "quotes", "customers", "suppliers", "categories", "formats", "thicknesses", "typologies"}


def patch_legacy_clean_areas():
    s = LEGACY.read_text(encoding="utf-8")

    # 1) Aggiunge helper per filtrare aree tecniche.
    if "def is_technical_catalog_area" not in s:
        helper = r'''

def is_technical_catalog_area(name):
    value = str(name or "").strip()
    return value.lower() in {
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


def clean_catalog_areas_list(values):
    cleaned = []
    for x in values or []:
        x = str(x or "").strip()
        if not x:
            continue
        if is_technical_catalog_area(x):
            continue
        if x not in cleaned:
            cleaned.append(x)
    return cleaned
'''
        s += "\n\n" + helper.strip() + "\n"

    # 2) Sostituisce get_catalog_areas con versione pulita.
    new_get_catalog_areas = r'''
def get_catalog_areas(db):
    areas = db.setdefault("catalog_areas", [])

    # Aree standard + aree utente. Non importiamo chiavi tecniche tipo materials/components/products.
    merged = []
    for x in default_catalog_areas() + list(areas):
        x = str(x or "").strip()
        if not x:
            continue
        if is_technical_catalog_area(x):
            continue
        if x not in merged:
            merged.append(x)

    # Integra solo chiavi categories che sembrano aree reali.
    for x in (db.get("categories", {}) or {}).keys():
        x = str(x or "").strip()
        if not x:
            continue
        if is_technical_catalog_area(x):
            continue
        if x not in merged:
            merged.append(x)

    db["catalog_areas"] = merged

    # Ogni area reale deve esistere anche come chiave categories.
    cats = db.setdefault("categories", {})
    for x in merged:
        cats.setdefault(x, {})

    # Rimuove eventuali chiavi tecniche finite per errore nel catalogo aree.
    for bad in list(cats.keys()):
        if is_technical_catalog_area(bad):
            # Rimuove solo se è una chiave vuota/non strutturata, per evitare perdita dati.
            value = cats.get(bad)
            if value in ({}, [], None, ""):
                cats.pop(bad, None)

    return merged
'''

    start = s.find("def get_catalog_areas(")
    if start == -1:
        raise RuntimeError("def get_catalog_areas non trovata")

    end = s.find("\ndef ", start + 1)
    if end == -1:
        end = len(s)

    s = s[:start] + new_get_catalog_areas.strip() + "\n\n" + s[end + 1:]

    # 3) Rende add_catalog_area più pulita.
    new_add_catalog_area = r'''
def add_catalog_area(db, payload):
    name = str((payload or {}).get("name", "")).strip()
    if not name:
        raise ValueError("Nome area obbligatorio")

    if is_technical_catalog_area(name):
        raise ValueError("Nome area riservato al sistema")

    areas = get_catalog_areas(db)
    if name not in areas:
        areas.append(name)

    db["catalog_areas"] = clean_catalog_areas_list(areas)
    db.setdefault("categories", {}).setdefault(name, {})

    return {"ok": True, "areas": db["catalog_areas"]}
'''

    start = s.find("def add_catalog_area(")
    if start == -1:
        raise RuntimeError("def add_catalog_area non trovata")

    end = s.find("\ndef ", start + 1)
    if end == -1:
        end = len(s)

    s = s[:start] + new_add_catalog_area.strip() + "\n\n" + s[end + 1:]

    # 4) Rende delete_catalog_area coerente e non blocca aree vuote.
    new_delete_catalog_area = r'''
def delete_catalog_area(db, name):
    name = str(name or "").strip()
    if not name:
        raise ValueError("Area non valida")

    if is_technical_catalog_area(name):
        # Non deve nemmeno comparire, ma se compare la puliamo.
        db["catalog_areas"] = [x for x in clean_catalog_areas_list(db.get("catalog_areas", [])) if x != name]
        db.setdefault("categories", {}).pop(name, None)
        return {"ok": True, "areas": get_catalog_areas(db)}

    used = False

    for section_key in ["materials", "components"]:
        for item in (db.get(section_key, {}) or {}).values():
            if isinstance(item, dict) and str(item.get("section", "")).strip() == name:
                used = True

    for supplier in (db.get("suppliers", {}) or {}).values():
        if isinstance(supplier, dict):
            if name in list(supplier.get("sections", []) or []):
                used = True

            for link in list(supplier.get("links", []) or []):
                if isinstance(link, dict) and str(link.get("section", "")).strip() == name:
                    used = True

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

    areas = [x for x in clean_catalog_areas_list(db.get("catalog_areas", [])) if str(x or "").strip() != name]
    db["catalog_areas"] = areas
    categories.pop(name, None)

    return {"ok": True, "areas": get_catalog_areas(db)}
'''

    start = s.find("def delete_catalog_area(")
    if start == -1:
        raise RuntimeError("def delete_catalog_area non trovata")

    end = s.find("\ndef ", start + 1)
    if end == -1:
        end = len(s)

    s = s[:start] + new_delete_catalog_area.strip() + "\n\n" + s[end + 1:]

    LEGACY.write_text(s, encoding="utf-8")
    print("Backend legacy: aree tecniche filtrate e gestione aree pulita.")


def patch_main_taxonomy_filter():
    s = MAIN.read_text(encoding="utf-8")

    # Rafforza ensure_custom_areas_in_taxonomy filtrando aree tecniche.
    if "def ensure_custom_areas_in_taxonomy" in s:
        start = s.find("def ensure_custom_areas_in_taxonomy")
        end = s.find("\n@app.", start + 1)
        if end == -1:
            end = s.find("\ndef ", start + 1)
        if end == -1:
            end = len(s)

        new_func = r'''
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
'''
        s = s[:start] + new_func.strip() + "\n\n" + s[end:]

    MAIN.write_text(s, encoding="utf-8")
    print("Backend main: taxonomy filtrata da aree tecniche.")


def patch_css_design_system():
    css = CSS.read_text(encoding="utf-8")

    if "/* v41.3 professional responsive normalization */" not in css:
        css += r'''

/* v41.3 professional responsive normalization */

/* Base: layout più coerente su 21:9, 16:9, tablet e mobile */
:root {
  --mn-card-radius: 22px;
  --mn-card-pad: clamp(14px, 1.1vw, 20px);
  --mn-gap: clamp(12px, 1vw, 18px);
  --mn-field-h: 44px;
  --mn-row-h: 64px;
}

/* Evita che testi e cards collassino */
* {
  min-width: 0;
}

.card,
.panel,
.table-card,
[class*="card"] {
  box-sizing: border-box;
}

/* Card più regolari */
.card,
.panel,
.table-card {
  border-radius: var(--mn-card-radius) !important;
}

.card-head,
.panel-head,
.table-head,
[class*="head"] {
  min-width: 0;
}

/* Titoli e sottotitoli leggibili */
.card h3,
.panel h3,
.table-card h3,
.card-title,
.panel-title {
  line-height: 1.15 !important;
  overflow-wrap: anywhere;
}

.card small,
.panel small,
.muted,
.muted-cell {
  line-height: 1.35 !important;
}

/* Form: campi stessa altezza */
input,
select,
textarea {
  min-height: var(--mn-field-h) !important;
  line-height: 1.35 !important;
}

button {
  min-height: 38px;
  line-height: 1.2;
}

/* Liste/righe: altezza minima coerente */
.category-pill,
.catalog-pill,
.area-pill,
.subcategory-pill,
.treatment-row,
.area-table-row,
.option-row,
.list-row {
  min-height: var(--mn-row-h);
  align-items: center !important;
}

/* Fix specifico bottoni categorie/sottocategorie: stessa altezza */
.category-manager-grid button,
.setup-catalog-grid button,
.catalog-grid button,
.catalog-board button {
  line-height: 1.2 !important;
}

.category-manager-grid .pill,
.setup-catalog-grid .pill,
.catalog-grid .pill,
.catalog-board .pill,
.category-manager-grid [class*="item"],
.setup-catalog-grid [class*="item"] {
  min-height: 58px;
}

/* Se un bottone contiene titolo + sottotitolo, mantienilo ordinato */
.category-manager-grid button b,
.category-manager-grid button span,
.category-manager-grid button small,
.setup-catalog-grid button b,
.setup-catalog-grid button span,
.setup-catalog-grid button small,
.catalog-grid button b,
.catalog-grid button span,
.catalog-grid button small {
  display: block;
  line-height: 1.25 !important;
}

/* Evita righe più basse solo perché il testo è corto */
.category-manager-grid button,
.setup-catalog-grid button,
.catalog-grid button,
.catalog-board button {
  justify-content: center;
}

/* Griglia categorie: colonne equilibrate desktop */
.category-manager-grid,
.setup-catalog-grid,
.catalog-grid,
.catalog-board {
  gap: var(--mn-gap) !important;
  align-items: stretch !important;
}

/* Colonne catalogo con altezza controllata */
.category-manager-grid > *,
.setup-catalog-grid > *,
.catalog-grid > *,
.catalog-board > * {
  min-height: 0 !important;
  height: auto;
}

/* Card 4 configurazioni: scroll vero e area utile maggiore */
.category-manager-grid > *:nth-child(4),
.setup-catalog-grid > *:nth-child(4),
.catalog-grid > *:nth-child(4),
.catalog-board > *:nth-child(4) {
  max-height: min(72vh, 760px) !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  padding-right: 8px;
}

/* Anche i blocchi interni della card 4 devono scrollare bene */
.config-linked-card,
.linked-config-card,
.catalog-config-card,
.setup-config-card,
.config-panel,
.config-list {
  max-height: min(72vh, 760px) !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
}

/* Normalizza chips e microbottoni */
.area-chip,
.badge,
.tag,
.chip,
.pill {
  line-height: 1.15 !important;
  white-space: nowrap;
}

/* Tabelle più stabili */
.table-wrap {
  max-width: 100%;
  overflow-x: auto !important;
}

table {
  width: 100%;
  table-layout: auto;
}

th,
td {
  vertical-align: middle !important;
  line-height: 1.35 !important;
}

/* Desktop grande / 21:9 */
@media (min-width: 1800px) {
  .main,
  .content,
  .app-main {
    max-width: 1680px;
    margin-left: auto;
    margin-right: auto;
  }

  .category-manager-grid,
  .setup-catalog-grid,
  .catalog-grid,
  .catalog-board {
    grid-template-columns: .75fr 1.05fr 1.05fr 1.45fr !important;
  }
}

/* Desktop normale */
@media (max-width: 1500px) {
  .category-manager-grid,
  .setup-catalog-grid,
  .catalog-grid,
  .catalog-board {
    grid-template-columns: .85fr 1.1fr 1.1fr 1.35fr !important;
  }
}

/* Laptop/tablet landscape */
@media (max-width: 1180px) {
  .category-manager-grid,
  .setup-catalog-grid,
  .catalog-grid,
  .catalog-board {
    grid-template-columns: 1fr 1fr !important;
  }

  .category-manager-grid > *:nth-child(4),
  .setup-catalog-grid > *:nth-child(4),
  .catalog-grid > *:nth-child(4),
  .catalog-board > *:nth-child(4) {
    max-height: 520px !important;
  }
}

/* Tablet/mobile */
@media (max-width: 820px) {
  .main,
  .content,
  .app-main {
    padding: 12px !important;
  }

  .category-manager-grid,
  .setup-catalog-grid,
  .catalog-grid,
  .catalog-board,
  .split-main,
  .form-grid,
  .area-manager-layout {
    grid-template-columns: 1fr !important;
  }

  .card,
  .panel,
  .table-card {
    border-radius: 18px !important;
  }

  .category-manager-grid > *:nth-child(4),
  .setup-catalog-grid > *:nth-child(4),
  .catalog-grid > *:nth-child(4),
  .catalog-board > *:nth-child(4),
  .config-linked-card,
  .linked-config-card,
  .catalog-config-card,
  .setup-config-card,
  .config-panel,
  .config-list {
    max-height: none !important;
    overflow-y: visible !important;
  }

  input,
  select,
  textarea {
    font-size: 16px !important;
  }

  table {
    min-width: 720px;
  }
}

/* Mobile stretto 9:16 */
@media (max-width: 520px) {
  .hero h1,
  .page-title h1,
  .page-hero h1 {
    font-size: 28px !important;
  }

  .card,
  .panel,
  .table-card {
    padding: 14px !important;
  }

  button {
    min-height: 42px;
  }

  .area-create-row,
  .area-table-row,
  .treatment-row {
    grid-template-columns: 1fr !important;
  }

  .area-create-row button,
  .area-table-row button {
    width: 100%;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")
        print("CSS: normalizzazione responsive professionale applicata.")


def main():
    patch_legacy_clean_areas()
    patch_main_taxonomy_filter()
    patch_css_design_system()
    print("Patch v41.3.0 completata: cleanup aree tecniche + responsive/UI normalization.")

if __name__ == "__main__":
    main()
