from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
MAIN = ROOT / "backend" / "app" / "main.py"
CSS = ROOT / "frontend" / "src" / "style.css"


def remove_raw_tree_frontend_patch():
    s = FRONTEND.read_text(encoding="utf-8")

    # Rimuove hook catalogAreas inserito dentro Setup, se presente.
    s = re.sub(
        r"\n\s*const\s+\{\s*data:\s*catalogAreas,\s*refresh:\s*refreshAreas\s*\}\s*=\s*useApi\('/catalog/areas',\s*\[\]\);\s*",
        "\n",
        s
    )

    # Rimuove tutto il blocco const rawTreeWithAreas = (() => { ... })();
    s = re.sub(
        r"\n\s*const\s+rawTreeWithAreas\s*=\s*\(\(\)\s*=>\s*\{.*?\n\s*\}\)\(\);\s*\n",
        "\n",
        s,
        flags=re.DOTALL
    )

    # Ripristina tutte le letture al tax.raw_tree originale.
    s = s.replace("list(rawTreeWithAreas)", "list(tax.raw_tree)")
    s = s.replace("(rawTreeWithAreas || [])", "(tax.raw_tree || [])")
    s = s.replace("rawTreeWithAreas || []", "tax.raw_tree || []")

    # Rimuove refreshAreas inseriti dove non esiste più.
    s = re.sub(r"\n\s*refreshAreas\?\.\(\);\s*", "\n", s)

    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend ripristinato: rimossa patch rawTreeWithAreas che causava pagina bianca.")


def add_taxonomy_area_helper():
    s = MAIN.read_text(encoding="utf-8")

    if "def ensure_custom_areas_in_taxonomy" not in s:
        helper = r'''

def ensure_custom_areas_in_taxonomy(db, result):
    """
    Garantisce che /api/taxonomy includa anche le aree catalogo vuote.
    Serve per farle comparire nella colonna 'Aree' prima di creare categorie figlie.
    """
    if not isinstance(result, dict):
        return result

    raw_tree = result.setdefault("raw_tree", [])

    seen = set()
    for sec in raw_tree:
        if not isinstance(sec, dict):
            continue
        label = str(sec.get("label") or sec.get("name") or sec.get("section") or sec.get("key") or "").strip()
        if label:
            seen.add(label)

    areas = []
    for a in db.get("catalog_areas", []) or []:
        a = str(a or "").strip()
        if a and a not in areas:
            areas.append(a)

    # Integra anche eventuali chiavi già presenti in categories.
    for a in (db.get("categories", {}) or {}).keys():
        a = str(a or "").strip()
        if a and a not in areas:
            areas.append(a)

    for area in areas:
        if area in seen:
            continue

        raw_tree.append({
            "key": area,
            "label": area,
            "name": area,
            "section": area,
            "categories": [],
        })
        seen.add(area)

    return result
'''
        # Inserisce helper prima della route taxonomy se possibile.
        marker = '@app.get("/api/taxonomy")'
        if marker in s:
            s = s.replace(marker, helper.strip() + "\n\n" + marker, 1)
        else:
            s += "\n\n" + helper.strip() + "\n"

    # Patch della funzione taxonomy: intercetta il return e avvolge il risultato.
    if "ensure_custom_areas_in_taxonomy" in s and "return ensure_custom_areas_in_taxonomy" not in s:
        start = s.find('def taxonomy():')
        if start == -1:
            raise RuntimeError("def taxonomy() non trovata in backend/app/main.py")

        end = s.find("\n@app.", start + 1)
        if end == -1:
            end = s.find("\ndef ", start + 1)
        if end == -1:
            end = len(s)

        block = s[start:end]

        # Se non c'è db = load_db(), lo aggiungiamo.
        if "db = load_db()" not in block:
            first_nl = block.find("\n")
            block = block[:first_nl + 1] + "    db = load_db()\n" + block[first_nl + 1:]

        # Cambia return <expr> in result = <expr>; return ensure...
        lines = block.splitlines()
        new_lines = []
        patched_return = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("return ") and not patched_return:
                expr = stripped[len("return "):]
                expr = expr.replace("load_db()", "db")
                indent = line[:len(line) - len(line.lstrip())]
                new_lines.append(indent + "result = " + expr)
                new_lines.append(indent + "return ensure_custom_areas_in_taxonomy(db, result)")
                patched_return = True
            else:
                new_lines.append(line)

        block = "\n".join(new_lines)

        s = s[:start] + block + s[end:]

    MAIN.write_text(s, encoding="utf-8")
    print("Backend taxonomy patchato: include aree catalogo vuote.")


def patch_scroll_card4():
    css = CSS.read_text(encoding="utf-8")

    if "/* v41.2.5 hard scroll category config card */" not in css:
        css += r'''

/* v41.2.5 hard scroll category config card */

/* La pagina categorie deve poter scorrere sempre */
body,
html,
#root {
  min-height: 100%;
}

.main,
.content,
.page,
.app-main {
  overflow-y: auto;
}

/* Card 4: Configurazioni collegate */
.catalog-board > *:nth-child(4),
.catalog-grid > *:nth-child(4),
.setup-catalog-grid > *:nth-child(4),
.category-manager-grid > *:nth-child(4),
[class*="catalog"] > *:nth-child(4),
[class*="category"] > *:nth-child(4) {
  max-height: 650px !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  min-height: 0 !important;
}

/* Contenuti interni della card 4 */
.catalog-board > *:nth-child(4) *,
.catalog-grid > *:nth-child(4) *,
.setup-catalog-grid > *:nth-child(4) *,
.category-manager-grid > *:nth-child(4) * {
  min-width: 0;
}

/* Se la quarta card contiene configurazioni lunghe, abilita scroll anche sui blocchi interni */
.config-linked-card,
.linked-config-card,
.catalog-config-card,
.setup-config-card,
.config-panel,
.config-list {
  max-height: 650px !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
}

/* Scrollbar visibile ma discreta */
.catalog-board > *:nth-child(4)::-webkit-scrollbar,
.catalog-grid > *:nth-child(4)::-webkit-scrollbar,
.setup-catalog-grid > *:nth-child(4)::-webkit-scrollbar,
.category-manager-grid > *:nth-child(4)::-webkit-scrollbar,
.config-linked-card::-webkit-scrollbar,
.linked-config-card::-webkit-scrollbar,
.catalog-config-card::-webkit-scrollbar,
.setup-config-card::-webkit-scrollbar {
  width: 8px;
}

.catalog-board > *:nth-child(4)::-webkit-scrollbar-thumb,
.catalog-grid > *:nth-child(4)::-webkit-scrollbar-thumb,
.setup-catalog-grid > *:nth-child(4)::-webkit-scrollbar-thumb,
.category-manager-grid > *:nth-child(4)::-webkit-scrollbar-thumb,
.config-linked-card::-webkit-scrollbar-thumb,
.linked-config-card::-webkit-scrollbar-thumb,
.catalog-config-card::-webkit-scrollbar-thumb,
.setup-config-card::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, .38);
  border-radius: 999px;
}

@media (max-width: 900px) {
  .catalog-board > *:nth-child(4),
  .catalog-grid > *:nth-child(4),
  .setup-catalog-grid > *:nth-child(4),
  .category-manager-grid > *:nth-child(4),
  [class*="catalog"] > *:nth-child(4),
  [class*="category"] > *:nth-child(4) {
    max-height: none !important;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")
        print("CSS scroll card 4 applicato.")


def main():
    remove_raw_tree_frontend_patch()
    add_taxonomy_area_helper()
    patch_scroll_card4()
    print("Patch v41.2.5 completata.")

if __name__ == "__main__":
    main()
