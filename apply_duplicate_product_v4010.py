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

    # 1. ProductWarehouse riceve onDuplicate
    s = s.replace(
        "function ProductWarehouse({ products, refresh, toast, onEdit, onDelete })",
        "function ProductWarehouse({ products, refresh, toast, onEdit, onDelete, onDuplicate })"
    )

    # 2. Aggiunge pulsante Duplica vicino a Modifica/Elimina.
    candidates = [
        """<button className="ghost" onClick={() => onEdit(r)}>Modifica</button>
          <button className="ghost danger" onClick={() => onDelete(r.name)}>Elimina</button>""",
        """<button className="ghost" onClick={() => onEdit(r)}>Modifica scheda</button>
          <button className="ghost danger" onClick={() => onDelete(r.name)}>Elimina</button>""",
        """<button className="ghost" onClick={() => onEdit(r)}>Modifica</button>"""
    ]

    replaced = False
    for old in candidates:
        if old in s and "onDuplicate(r)" not in s:
            if "Elimina" in old:
                new = old.replace(
                    '<button className="ghost" onClick={() => onEdit(r)}>',
                    '<button className="ghost" onClick={() => onDuplicate(r)}>Duplica</button>\n          <button className="ghost" onClick={() => onEdit(r)}>'
                )
            else:
                new = """<button className="ghost" onClick={() => onDuplicate(r)}>Duplica</button>
          <button className="ghost" onClick={() => onEdit(r)}>Modifica</button>"""
            s = s.replace(old, new, 1)
            replaced = True
            break

    if not replaced and "onDuplicate(r)" not in s:
        # fallback: prova a inserire in una table-actions dei prodotti
        marker = """<button className="ghost" onClick={() => openProductDetail(r.name)}>Dettaglio</button>"""
        if marker in s:
            s = s.replace(marker, marker + "\n          <button className=\"ghost\" onClick={() => onDuplicate(r)}>Duplica</button>", 1)
            replaced = True

    if not replaced:
        print("Avviso: pulsante Duplica non inserito automaticamente. Controllare azioni ProductWarehouse.")

    # 3. Stato e funzioni duplicate dentro Products
    if "duplicateProduct" not in s:
        old = """  const [bom, setBom] = useState({ name: '', qty: '1' });"""
        new = """  const [bom, setBom] = useState({ name: '', qty: '1' });
  const [duplicateProduct, setDuplicateProduct] = useState(null);
  const [duplicateName, setDuplicateName] = useState('');"""
        s = replace_once(s, old, new, "duplicate state")

    if "function openDuplicateProduct" not in s:
        old = """  function editProduct(r) { setP({ ...r, old_name: r.name, bom: r.bom || [], stock: String(r.stock ?? '') }); setArea('sheet'); window.scrollTo({ top: 0, behavior: 'smooth' }); }"""
        new = """  function editProduct(r) { setP({ ...r, old_name: r.name, bom: r.bom || [], stock: String(r.stock ?? '') }); setArea('sheet'); window.scrollTo({ top: 0, behavior: 'smooth' }); }

  function openDuplicateProduct(r) {
    setDuplicateProduct(r);
    setDuplicateName(`${r.name} - variante`);
  }

  async function saveDuplicateProduct() {
    if (!duplicateProduct || !duplicateName.trim()) {
      toast('Inserisci il nome della variante', 'err');
      return;
    }

    const payload = {
      ...duplicateProduct,
      old_name: duplicateName.trim(),
      name: duplicateName.trim(),
      stock: 0,
      bom: duplicateProduct.bom || [],
      description: duplicateProduct.description || '',
    };

    delete payload.value;
    delete payload.unit_cost;
    delete payload.material_unit_cost;
    delete payload.labor_unit_cost;

    try {
      await postJSON('/products', payload);
      toast('Variante prodotto creata');
      setDuplicateProduct(null);
      setDuplicateName('');
      await refresh();
      await refreshSug();
      setArea('sheet');
    } catch (e) {
      toast(e.message, 'err');
    }
  }"""
        s = replace_once(s, old, new, "duplicate functions")

    # 4. Passa onDuplicate a ProductWarehouse
    old = """<ProductWarehouse products={products} refresh={() => { refresh(); refreshMovements(); }} toast={toast} onEdit={editProduct} onDelete={remove} />"""
    new = """<ProductWarehouse products={products} refresh={() => { refresh(); refreshMovements(); }} toast={toast} onEdit={editProduct} onDelete={remove} onDuplicate={openDuplicateProduct} />"""
    if old in s:
        s = s.replace(old, new, 1)
    elif "onDuplicate={openDuplicateProduct}" not in s:
        old2 = """<ProductWarehouse products={products} refresh={() => { refresh(); refreshMovements(); }} toast={toast} onEdit={editProduct} />"""
        new2 = """<ProductWarehouse products={products} refresh={() => { refresh(); refreshMovements(); }} toast={toast} onEdit={editProduct} onDelete={remove} onDuplicate={openDuplicateProduct} />"""
        if old2 in s:
            s = s.replace(old2, new2, 1)
        else:
            print("Avviso: ProductWarehouse props non aggiornate automaticamente.")

    # 5. Modal duplica prodotto prima del return finale Products
    if "Crea variante prodotto" not in s:
        marker = """    {area !== 'warehouse' && <Card title="Catalogo produzione" """
        insert = """    {duplicateProduct && <DetailModal title="Crea variante prodotto" subtitle="Duplica una scheda esistente mantenendo categoria, collezione, costi e distinta base. Lo stock iniziale della variante sarà 0." icon={PackagePlus} onClose={() => setDuplicateProduct(null)}>
      <div className="duplicate-product-modal">
        <div className="detail-hero">
          <div>
            <span>Prodotto origine</span>
            <strong>{duplicateProduct.name}</strong>
            <small>{[duplicateProduct.category, duplicateProduct.subcategory, duplicateProduct.collection].filter(Boolean).join(' · ') || 'Scheda prodotto'}</small>
          </div>
          <span className="quote-status sent">variante</span>
        </div>

        <div className="form-grid">
          <Input label="Nome nuova variante" value={duplicateName} onChange={e => setDuplicateName(e.target.value)} />
          <Input label="Stock iniziale" value="0" disabled />
        </div>

        <div className="duplicate-summary">
          <div><span>Categoria</span><b>{duplicateProduct.category || '—'}</b></div>
          <div><span>Sottocategoria</span><b>{duplicateProduct.subcategory || '—'}</b></div>
          <div><span>Collezione</span><b>{duplicateProduct.collection || '—'}</b></div>
          <div><span>Materiali BOM</span><b>{list(duplicateProduct.bom).length}</b></div>
        </div>

        <div className="notice">
          <CheckCircle2 />
          La variante copierà distinta base, costi lavoro, costi extra, categoria e collezione. Potrai modificarla subito dopo dalla scheda prodotto.
        </div>

        <div className="quick-actions">
          <button className="primary" onClick={saveDuplicateProduct}><Save /> Crea variante</button>
          <button className="ghost" onClick={() => setDuplicateProduct(null)}>Annulla</button>
        </div>
      </div>
    </DetailModal>}

"""
        if marker in s:
            s = s.replace(marker, insert + marker, 1)
        else:
            print("Avviso: punto inserimento modal duplica non trovato.")

    MAIN.write_text(s, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    if "/* v40.1 duplicate product */" not in css:
        css += """

/* v40.1 duplicate product */
.duplicate-product-modal {
  display: grid;
  gap: 18px;
}

.duplicate-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.duplicate-summary > div {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.055);
  border-radius: 18px;
  padding: 14px;
  min-height: 84px;
}

.duplicate-summary span {
  display: block;
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .06em;
  margin-bottom: 6px;
}

.duplicate-summary b {
  display: block;
  line-height: 1.25;
  word-break: break-word;
}

@media (max-width: 950px) {
  .duplicate-summary {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 620px) {
  .duplicate-summary {
    grid-template-columns: 1fr;
  }
}
"""
        CSS.write_text(css, encoding="utf-8")

    print("Patch v40.1.0 duplica prodotto completata.")


if __name__ == "__main__":
    main()
