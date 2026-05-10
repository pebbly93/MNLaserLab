from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
MAIN = ROOT / "backend" / "app" / "main.py"
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    start = s.find("function Setup({ toast })")
    if start == -1:
        raise RuntimeError("function Setup({ toast }) non trovata")

    end = s.find("\nfunction ", start + 1)
    if end == -1:
        end = len(s)

    block = s[start:end]

    # 1) Ripara autoref nel rawTreeWithAreas.
    block = block.replace("const base = list(rawTreeWithAreas).map(sec => ({", "const base = list(tax.raw_tree).map(sec => ({")
    block = block.replace("const base = list(rawTreeWithAreas || []).map(sec => ({", "const base = list(tax.raw_tree || []).map(sec => ({")

    # 2) Se non esiste, aggiunge hook /catalog/areas dopo /taxonomy.
    if "data: catalogAreas" not in block:
        m = re.search(r"const\s+\{\s*data:\s*tax[^;]+;\n", block)
        if not m:
            raise RuntimeError("Hook /taxonomy non trovato dentro Setup")

        hook = m.group(0) + "  const { data: catalogAreas, refresh: refreshAreas } = useApi('/catalog/areas', []);\n"
        block = block[:m.start()] + hook + block[m.end():]

    # 3) Se non esiste, crea rawTreeWithAreas dopo gli hook iniziali e prima degli state.
    if "const rawTreeWithAreas =" not in block:
        pos = block.find("const [raw,")
        if pos == -1:
            pos = block.find("const [scope")
        if pos == -1:
            pos = block.find("async function")
        if pos == -1:
            raise RuntimeError("Punto inserimento rawTreeWithAreas non trovato")

        helper = r'''
  const rawTreeWithAreas = (() => {
    const base = list(tax.raw_tree || []).map(sec => ({
      ...sec,
      label: sec.label || sec.name || sec.section || sec.key || '',
      name: sec.name || sec.label || sec.section || sec.key || '',
      categories: list(sec.categories),
    }));

    const seen = new Set(base.map(sec => String(sec.label || sec.name || '').trim()).filter(Boolean));

    for (const area of list(catalogAreas || [])) {
      const name = String(area || '').trim();
      if (!name || seen.has(name)) continue;

      base.push({
        key: name,
        label: name,
        name,
        section: name,
        categories: [],
      });

      seen.add(name);
    }

    return base;
  })();

'''
        block = block[:pos] + helper + block[pos:]

    # 4) Usa rawTreeWithAreas SOLO nella UI, non dentro la sua stessa definizione.
    # Prima normalizza eventuali sostituzioni sbagliate.
    block = re.sub(
        r"const base = list\(rawTreeWithAreas(?: \|\| \[\])?\)\.map\(sec => \(\{",
        "const base = list(tax.raw_tree || []).map(sec => ({",
        block
    )

    # Sostituisce occorrenze successive, escludendo il blocco helper con una sostituzione controllata.
    helper_start = block.find("const rawTreeWithAreas =")
    helper_end = block.find("})();", helper_start)
    if helper_start != -1 and helper_end != -1:
        helper_end += len("})();")
        before = block[:helper_start]
        helper = block[helper_start:helper_end]
        after = block[helper_end:]

        after = after.replace("list(tax.raw_tree)", "list(rawTreeWithAreas)")
        after = after.replace("(tax.raw_tree || [])", "(rawTreeWithAreas || [])")
        after = after.replace("tax.raw_tree || []", "rawTreeWithAreas || []")

        # Però evita di corrompere default useApi se per caso fosse dopo.
        after = after.replace("useApi('/taxonomy', { rawTreeWithAreas:", "useApi('/taxonomy', { raw_tree:")

        block = before + helper + after

    # 5) Se salvi area, aggiorna anche /catalog/areas.
    block = block.replace("refreshTax?.();\n      refreshAreas?.();\n      refreshAreas?.();", "refreshTax?.();\n      refreshAreas?.();")
    block = block.replace("refreshTax();\n      refreshAreas?.();\n      refreshAreas?.();", "refreshTax();\n      refreshAreas?.();")

    s = s[:start] + block + s[end:]
    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend categorie riparato: rawTreeWithAreas non è più autoreferenziale.")


def patch_workflow_backend():
    legacy = LEGACY.read_text(encoding="utf-8")

    if "def quote_workflow_summary" not in legacy:
        legacy += r'''

def quote_workflow_summary(db):
    quotes = db.get("quotes", []) or []
    statuses = ["bozza", "inviato", "accettato", "rifiutato", "in_produzione", "consegnato"]
    counts = {s: 0 for s in statuses}
    rows = []

    for q in quotes:
        if not isinstance(q, dict):
            continue

        status = str(q.get("status", "bozza") or "bozza").lower()
        aliases = {
            "draft": "bozza",
            "sent": "inviato",
            "accepted": "accettato",
            "rejected": "rifiutato",
            "production": "in_produzione",
            "delivered": "consegnato",
        }
        status = aliases.get(status, status)
        if status not in counts:
            counts[status] = 0
        counts[status] += 1

        result = q.get("result") or {}
        rows.append({
            "id": q.get("id", ""),
            "date": q.get("date", q.get("date_iso", "")),
            "name": q.get("name", ""),
            "customer": q.get("customer", ""),
            "status": status,
            "total": q.get("discounted") or result.get("discounted") or q.get("recommended") or result.get("recommended") or 0,
        })

    return {
        "statuses": statuses,
        "counts": counts,
        "quotes": rows,
    }
'''
        LEGACY.write_text(legacy, encoding="utf-8")
        print("Aggiunta quote_workflow_summary")

    main = MAIN.read_text(encoding="utf-8")

    if '@app.get("/api/quotes/workflow")' not in main:
        route = r'''

@app.get("/api/quotes/workflow")
def quote_workflow_api():
    return quote_workflow_summary(load_db())
'''
        marker = '@app.get("/api/quotes")'
        if marker in main:
            main = main.replace(marker, route.strip() + "\n\n" + marker, 1)
        else:
            main += "\n\n" + route.strip() + "\n"

        MAIN.write_text(main, encoding="utf-8")
        print("Aggiunta route /api/quotes/workflow")
    else:
        print("Route /api/quotes/workflow già presente")


def main():
    patch_frontend()
    patch_workflow_backend()
    print("Patch v41.2.4 completata.")

if __name__ == "__main__":
    main()
