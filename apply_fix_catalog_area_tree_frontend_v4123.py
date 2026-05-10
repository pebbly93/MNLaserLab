from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"

def find_setup_bounds(s: str):
    start = s.find("function Setup({ toast })")
    if start == -1:
        raise RuntimeError("function Setup({ toast }) non trovata")

    end = s.find("\nfunction ", start + 1)
    if end == -1:
        end = len(s)

    return start, end

def main():
    s = FRONTEND.read_text(encoding="utf-8")
    start, end = find_setup_bounds(s)
    block = s[start:end]

    # 1. Aggiunge hook aree dentro Setup, se manca.
    if "catalogAreas" not in block:
        tax_line_match = re.search(r"const\s+\{\s*data:\s*tax[^;]+;\n", block)
        if not tax_line_match:
            raise RuntimeError("Hook tax /taxonomy non trovato dentro Setup")

        insert = tax_line_match.group(0) + "  const { data: catalogAreas, refresh: refreshAreas } = useApi('/catalog/areas', []);\n"
        block = block[:tax_line_match.start()] + insert + block[tax_line_match.end():]

    # 2. Crea rawTreeWithAreas: tax.raw_tree + aree vuote da /catalog/areas.
    if "const rawTreeWithAreas =" not in block:
        anchor = "const [raw,"
        pos = block.find(anchor)
        if pos == -1:
            # fallback: dopo gli hook iniziali
            pos = block.find("async function")
            if pos == -1:
                raise RuntimeError("Punto inserimento rawTreeWithAreas non trovato")

        helper = r'''
  const rawTreeWithAreas = (() => {
    const base = list(tax.raw_tree).map(sec => ({
      ...sec,
      label: sec.label || sec.name || sec.section || sec.key || '',
      name: sec.name || sec.label || sec.section || sec.key || '',
      categories: list(sec.categories),
    }));

    const seen = new Set(base.map(sec => String(sec.label || sec.name || '').trim()).filter(Boolean));

    for (const area of list(catalogAreas)) {
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

    # 3. Dentro Setup, sostituisce le letture dirette di tax.raw_tree con rawTreeWithAreas,
    # ma lascia intatta la dichiarazione originale useApi('/taxonomy', { raw_tree: ... }).
    block = block.replace("list(tax.raw_tree)", "list(rawTreeWithAreas)")
    block = block.replace("(tax.raw_tree || [])", "(rawTreeWithAreas || [])")
    block = block.replace("tax.raw_tree || []", "rawTreeWithAreas || []")

    # Evita sostituzione errata nella useApi default, se capitata.
    block = block.replace("useApi('/taxonomy', { rawTreeWithAreas:", "useApi('/taxonomy', { raw_tree:")

    # 4. Quando salvo/eliminio area devo aggiornare anche refreshAreas.
    block = block.replace("refreshTax?.();", "refreshTax?.();\n      refreshAreas?.();")
    block = block.replace("refreshTax();", "refreshTax();\n      refreshAreas?.();")

    # Rimuove eventuali duplicati causati da patch ripetute.
    block = block.replace("refreshAreas?.();\n      refreshAreas?.();", "refreshAreas?.();")

    s = s[:start] + block + s[end:]
    FRONTEND.write_text(s, encoding="utf-8")
    print("Fix applicato: le aree personalizzate vengono unite al raw_tree nella gestione catalogo.")

if __name__ == "__main__":
    main()
