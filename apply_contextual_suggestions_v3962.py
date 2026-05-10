from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"Blocco non trovato: {label}")
    return text.replace(old, new, 1)


def main():
    s = MAIN.read_text(encoding="utf-8")

    # 1. Rimuove il box testuale "Percorso logico di compilazione"
    logic_block = """      <div className="logic-path">
        <span>Percorso logico di compilazione</span>
        <b>Area</b><em>→</em><b>Fornitore</b><em>→</em><b>Categoria</b><em>→</em><b>Sottocategoria</b><em>→</em><b>Formato</b><em>→</em><b>Spessore</b>
      </div>
"""
    if logic_block in s:
        s = s.replace(logic_block, "", 1)

    # 2. Aggiunge helper robusti per suggerimenti contestuali
    marker = """const suppliersForRaw = (s, sec, cat, sub) => {
  const exact = pick(s, ['suppliers_by_raw_path', sec, cat, sub], []);
  const scoped = pick(s, ['suppliers_by_raw_scope', sec], []);
  return unique([...(exact || []), ...(scoped || []), ...(s?.suppliers || [])]);
};"""

    replacement = """const suppliersForRaw = (s, sec, cat, sub) => {
  const exact = pick(s, ['suppliers_by_raw_path', sec, cat, sub], []);
  const scoped = pick(s, ['suppliers_by_raw_scope', sec], []);
  return unique([...(exact || []), ...(scoped || []), ...(s?.suppliers || [])]);
};

const rawCatsStrict = (s, sec) => {
  if (!sec) return [];
  const scoped = pick(s, ['raw_categories_by_scope', sec], []);
  return unique(scoped);
};

const rawSubsStrict = (s, sec, cat) => {
  if (!sec || !cat) return [];
  const scoped = pick(s, ['raw_subcategories_by_scope_category', sec, cat], []);
  return unique(scoped);
};

const rawCatsForSupplierStrict = (s, supplier, sec) => {
  if (!sec) return [];
  const linked = pick(s, ['raw_categories_by_supplier_scope', supplier, sec], []);
  const scoped = rawCatsStrict(s, sec);
  if (supplier && linked.length) return unique(linked);
  return scoped;
};

const rawSubsForSupplierStrict = (s, supplier, sec, cat) => {
  if (!sec || !cat) return [];
  const linked = pick(s, ['raw_subcategories_by_supplier_scope_category', supplier, sec, cat], []);
  const scoped = rawSubsStrict(s, sec, cat);
  if (supplier && linked.length) return unique(linked);
  return scoped;
};"""

    if "const rawCatsStrict" not in s:
        s = replace_once(s, marker, replacement, "contextual suggestion helpers")

    # 3. Sostituisce i suggerimenti nella sezione Acquisti
    s = s.replace(
        "options={rawCatsForSupplier(sug, f.supplier, f.section)}",
        "options={rawCatsForSupplierStrict(sug, f.supplier, f.section)}"
    )

    s = s.replace(
        "options={rawSubsForSupplier(sug, f.supplier, f.section, f.category)}",
        "options={rawSubsForSupplierStrict(sug, f.supplier, f.section, f.category)}"
    )

    # 4. Migliora reset logico dei campi quando cambia Area/Fornitore/Categoria
    old_area = """<Select label="Area" value={f.section} onChange={e => setF({ ...f, section: e.target.value, category: '', subcategory: '', size: '', thickness: '' })}>"""
    new_area = """<Select label="Area" value={f.section} onChange={e => setF({ ...f, section: e.target.value, supplier: '', category: '', subcategory: '', size: '', thickness: '' })}>"""
    if old_area in s:
        s = s.replace(old_area, new_area, 1)

    old_supplier = """onChange={e => setF({ ...f, supplier: e.target.value, category: '', subcategory: '', size: '', thickness: '' })}"""
    new_supplier = """onChange={e => setF({ ...f, supplier: e.target.value, category: '', subcategory: '', size: '', thickness: '' })}"""
    # resta uguale, lo lasciamo per chiarezza

    # 5. Aggiorna hint: niente testo lungo invasivo
    s = s.replace(
        "hint={f.supplier ? `Categorie collegate a ${f.supplier}` : 'Scegli prima il fornitore per filtrare il catalogo'}",
        "hint={f.section ? `Categorie disponibili per ${f.section}` : 'Scegli prima l’area'}"
    )

    s = s.replace(
        "hint={f.supplier && f.category ? 'Sottocategorie filtrate per fornitore + categoria' : 'Seleziona categoria per filtrare'}",
        "hint={f.category ? `Sottocategorie di ${f.category}` : 'Scegli prima una categoria'}"
    )

    MAIN.write_text(s, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")

    # 6. Nasconde eventuale vecchio box logic-path se rimasto nel CSS/DOM
    if "/* v39.6.2 contextual suggestions */" not in css:
        css += """

/* v39.6.2 contextual suggestions */
.logic-path {
  display: none !important;
}

.compact-suggestions {
  margin-top: 5px;
  gap: 5px;
}

.compact-suggestions button {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.field small,
.field .hint {
  line-height: 1.25;
}
"""
        CSS.write_text(css, encoding="utf-8")

    print("Patch v39.6.2 suggerimenti contestuali completata.")


if __name__ == "__main__":
    main()
