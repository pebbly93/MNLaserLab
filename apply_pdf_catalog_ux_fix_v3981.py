from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"Blocco non trovato: {label}")
    return text.replace(old, new, 1)


NEW_SETUP = r'''function Setup({ toast }) {
  const { data: tax, refresh: refreshTax } = useApi('/taxonomy', { raw_tree: [], product_tree: [], supplier_matrix: [] });
  const { data: sug, refresh: refreshSug } = useApi('/suggestions', {});

  const [tab, setTab] = useState('raw');
  const [q, setQ] = useState('');
  const [scopeFilter, setScopeFilter] = useState('all');

  const [raw, setRaw] = useState({ scope: 'materials', category: '', subcategory: '' });
  const [prod, setProd] = useState({ category: '', subcategory: '', collection: '' });
  const [fmt, setFmt] = useState({ category: '', value: '' });
  const [thk, setThk] = useState({ category: '', value: '' });
  const [typ, setTyp] = useState({ category: '', subcategory: '', value: '' });

  async function reloadCatalog() {
    await refreshTax();
    await refreshSug();
  }

  async function save(path, obj, msg) {
    try {
      await postJSON(path, obj);
      toast(msg);
      await reloadCatalog();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function removeCategory(scope, category, subcategory = '') {
    const label = subcategory
      ? `Eliminare la sottocategoria "${subcategory}" da "${category}"?`
      : `Eliminare tutta la categoria "${category}"?`;

    if (!confirm(label)) return;

    try {
      const params = new URLSearchParams({ scope, category, subcategory });
      await del('/categories?' + params.toString());
      toast(subcategory ? 'Sottocategoria eliminata' : 'Categoria eliminata');
      await reloadCatalog();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function removeProductLink(r) {
    if (!confirm(`Eliminare il collegamento "${r.category} → ${r.subcategory} → ${r.collection}"?`)) return;
    try {
      const params = new URLSearchParams({ category: r.category, subcategory: r.subcategory, collection: r.collection });
      await del('/product-links?' + params.toString());
      toast('Collegamento prodotto eliminato');
      await reloadCatalog();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function saveFormat() {
    await save('/catalog/formats', fmt, 'Formato salvato');
    setFmt(v => ({ ...v, value: '' }));
  }

  async function saveThickness() {
    await save('/catalog/thicknesses', thk, 'Spessore salvato');
    setThk(v => ({ ...v, value: '' }));
  }

  async function saveTypology() {
    await save('/catalog/typologies', typ, 'Tipologia salvata');
    setTyp(v => ({ ...v, value: '' }));
  }

  async function removeFormat(category, value) {
    if (!confirm(`Eliminare formato "${value}" da "${category}"?`)) return;
    try {
      const params = new URLSearchParams({ category, value });
      await del('/catalog/formats?' + params.toString());
      toast('Formato eliminato');
      await reloadCatalog();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function removeThickness(category, value) {
    if (!confirm(`Eliminare spessore "${value}" da "${category}"?`)) return;
    try {
      const params = new URLSearchParams({ category, value });
      await del('/catalog/thicknesses?' + params.toString());
      toast('Spessore eliminato');
      await reloadCatalog();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function removeTypology(category, subcategory, value) {
    if (!confirm(`Eliminare tipologia "${value}" da "${category} → ${subcategory}"?`)) return;
    try {
      const params = new URLSearchParams({ category, subcategory, value });
      await del('/catalog/typologies?' + params.toString());
      toast('Tipologia eliminata');
      await reloadCatalog();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  const rawRowsAll = list(tax.raw_tree).flatMap(sec =>
    list(sec.categories).flatMap(c =>
      list(c.subcategories).length
        ? list(c.subcategories).map(sub => ({
            scope: sec.scope,
            area: sec.label,
            category: c.name,
            subcategory: sub,
            suppliers: c.suppliers
          }))
        : [{
            scope: sec.scope,
            area: sec.label,
            category: c.name,
            subcategory: '',
            suppliers: c.suppliers
          }]
    )
  );

  const prodRowsAll = Object.entries(sug.collections_by_product_path || {}).flatMap(([cat, subMap]) =>
    Object.entries(subMap || {}).flatMap(([sub, cols]) =>
      list(cols).map(col => ({ category: cat, subcategory: sub, collection: col }))
    )
  );

  const formatRowsAll = Object.entries(sug.formats_by_category || {}).flatMap(([category, values]) =>
    list(values).map(value => ({ category, value }))
  );

  const thicknessRowsAll = Object.entries(sug.thicknesses_by_category || {}).flatMap(([category, values]) =>
    list(values).map(value => ({ category, value }))
  );

  const typologyRowsAll = Object.entries(sug.typologies_by_category_subcategory || {}).flatMap(([category, subMap]) =>
    Object.entries(subMap || {}).flatMap(([subcategory, values]) =>
      list(values).map(value => ({ category, subcategory, value }))
    )
  );

  const allRawCategories = unique([...list(sug.raw_categories), ...rawRowsAll.map(r => r.category)]);
  const areaChoices = list(tax.raw_tree).map(x => ({ scope: x.scope, label: x.label }));

  const textMatch = row => {
    const t = Object.values(row || {}).join(' ').toLowerCase();
    return !q || q.toLowerCase().split(/\s+/).every(part => t.includes(part));
  };

  const rawRows = rawRowsAll
    .filter(r => scopeFilter === 'all' || r.scope === scopeFilter || r.area === scopeFilter)
    .filter(textMatch);

  const prodRows = prodRowsAll.filter(textMatch);
  const formatRows = formatRowsAll.filter(textMatch);
  const thicknessRows = thicknessRowsAll.filter(textMatch);
  const typologyRows = typologyRowsAll.filter(textMatch);

  const typSubcategories = typ.category
    ? unique(rawRowsAll.filter(r => r.category === typ.category).map(r => r.subcategory).filter(Boolean))
    : [];

  const formCategoryOptions = scopeFilter === 'all'
    ? allRawCategories
    : unique(rawRowsAll.filter(r => r.scope === scopeFilter || r.area === scopeFilter).map(r => r.category));

  return <>
    <PageTitle title="Catalogo" desc="Gestisci categorie, formati, spessori e tipologie senza mischiare aree diverse come Falegnameria e Illuminazione." />

    <Card title="Centro catalogo" icon={Settings2} sub="Scegli cosa vuoi configurare, filtra per area e cerca velocemente ciò che vuoi modificare.">
      <div className="catalog-toolbar">
        <div className="catalog-tabs">
          <button className={tab === 'raw' ? 'active' : ''} onClick={() => setTab('raw')}>Materiali</button>
          <button className={tab === 'formats' ? 'active' : ''} onClick={() => setTab('formats')}>Formati</button>
          <button className={tab === 'thicknesses' ? 'active' : ''} onClick={() => setTab('thicknesses')}>Spessori</button>
          <button className={tab === 'typologies' ? 'active' : ''} onClick={() => setTab('typologies')}>Tipologie</button>
          <button className={tab === 'products' ? 'active' : ''} onClick={() => setTab('products')}>Prodotti</button>
        </div>

        <div className="catalog-filters">
          <select value={scopeFilter} onChange={e => setScopeFilter(e.target.value)}>
            <option value="all">Tutte le aree</option>
            {areaChoices.map(a => <option key={a.scope} value={a.scope}>{a.label}</option>)}
          </select>
          <SearchBox value={q} onChange={setQ} placeholder="Cerca categoria, sottocategoria, formato..." />
        </div>
      </div>
    </Card>

    {tab === 'raw' && <>
      <Card title="Aggiungi categoria materiale" icon={Truck} sub="Esempio: Falegnameria → Legname → Betulla. Illuminazione resta separata da Legname.">
        <div className="catalog-editor-grid">
          <Select label="Area" value={raw.scope} onChange={e=>setRaw({...raw,scope:e.target.value,category:'',subcategory:''})}>
            {areaChoices.map(a => <option key={a.scope} value={a.scope}>{a.label}</option>)}
          </Select>
          <SmartInput label="Categoria" options={rawCatsStrict ? rawCatsStrict(sug, raw.scope) : rawCats(sug, raw.scope)} value={raw.category} onChange={e=>setRaw({...raw,category:e.target.value,subcategory:''})}/>
          <SmartInput label="Sottocategoria" options={rawSubsStrict ? rawSubsStrict(sug, raw.scope, raw.category) : rawSubs(sug, raw.scope, raw.category)} value={raw.subcategory} onChange={e=>setRaw({...raw,subcategory:e.target.value})}/>
          <button className="primary" onClick={() => save('/categories', raw, 'Categoria materiale salvata')}><Plus /> Salva</button>
        </div>
      </Card>

      <Card title="Categorie materiali" icon={Layers3} sub={`${rawRows.length} elementi visualizzati`}>
        <DataTable rows={rawRows} empty="Nessuna categoria materiale" columns={[
          {key:'area',label:'Area'},
          {key:'category',label:'Categoria'},
          {key:'subcategory',label:'Sottocategoria',render:r=>r.subcategory || '—'},
          {key:'suppliers',label:'Fornitori',render:r=>r.suppliers || 0},
          {key:'act',label:'Azioni',render:r=><div className="table-actions">
            {r.subcategory && <button className="ghost danger" onClick={()=>removeCategory(r.scope, r.category, r.subcategory)}>Elimina sottocategoria</button>}
            <button className="ghost danger" onClick={()=>removeCategory(r.scope, r.category, '')}>Elimina categoria</button>
          </div>}
        ]} />
      </Card>
    </>}

    {tab === 'formats' && <>
      <Card title="Aggiungi formato" icon={Layers3} sub="Associa i formati solo alla categoria corretta. Esempio: Legname → 20x20, 40x40.">
        <div className="catalog-editor-grid">
          <SmartInput label="Categoria" options={formCategoryOptions} value={fmt.category} onChange={e=>setFmt({...fmt,category:e.target.value})}/>
          <SmartInput label="Formato / tipo" options={formats(sug, fmt.category)} value={fmt.value} onChange={e=>setFmt({...fmt,value:e.target.value})} placeholder="Es. 20x20, 40x40, Rotolo"/>
          <button className="primary" onClick={saveFormat}><Plus /> Aggiungi</button>
        </div>
      </Card>

      <Card title="Formati configurati" icon={Layers3} sub={`${formatRows.length} elementi visualizzati`}>
        <DataTable rows={formatRows} empty="Nessun formato configurato" columns={[
          {key:'category',label:'Categoria'},
          {key:'value',label:'Formato'},
          {key:'act',label:'Azioni',render:r=><button className="ghost danger" onClick={()=>removeFormat(r.category, r.value)}><Trash2 /> Elimina</button>}
        ]} />
      </Card>
    </>}

    {tab === 'thicknesses' && <>
      <Card title="Aggiungi spessore" icon={Layers3} sub="Associa gli spessori alle categorie corrette. Esempio: Legname → 2 mm, 4 mm, 10 mm.">
        <div className="catalog-editor-grid">
          <SmartInput label="Categoria" options={formCategoryOptions} value={thk.category} onChange={e=>setThk({...thk,category:e.target.value})}/>
          <SmartInput label="Spessore" options={thicknesses(sug, thk.category)} value={thk.value} onChange={e=>setThk({...thk,value:e.target.value})} placeholder="Es. 2 mm, 4 mm, 10 mm"/>
          <button className="primary" onClick={saveThickness}><Plus /> Aggiungi</button>
        </div>
      </Card>

      <Card title="Spessori configurati" icon={Layers3} sub={`${thicknessRows.length} elementi visualizzati`}>
        <DataTable rows={thicknessRows} empty="Nessuno spessore configurato" columns={[
          {key:'category',label:'Categoria'},
          {key:'value',label:'Spessore'},
          {key:'act',label:'Azioni',render:r=><button className="ghost danger" onClick={()=>removeThickness(r.category, r.value)}><Trash2 /> Elimina</button>}
        ]} />
      </Card>
    </>}

    {tab === 'typologies' && <>
      <Card title="Aggiungi tipologia" icon={Settings2} sub="Esempio: Illuminazione → Alimentatori → 12V → Da presa.">
        <div className="catalog-editor-grid">
          <SmartInput label="Categoria" options={formCategoryOptions} value={typ.category} onChange={e=>setTyp({...typ,category:e.target.value,subcategory:'',value:''})}/>
          <SmartInput label="Sottocategoria" options={typSubcategories} value={typ.subcategory} onChange={e=>setTyp({...typ,subcategory:e.target.value,value:''})}/>
          <SmartInput label="Tipologia" options={typologies(sug, typ.category, typ.subcategory)} value={typ.value} onChange={e=>setTyp({...typ,value:e.target.value})} placeholder="Es. Da presa, Da incasso, Luce calda"/>
          <button className="primary" onClick={saveTypology}><Plus /> Aggiungi</button>
        </div>
      </Card>

      <Card title="Tipologie configurate" icon={Settings2} sub={`${typologyRows.length} elementi visualizzati`}>
        <DataTable rows={typologyRows} empty="Nessuna tipologia configurata" columns={[
          {key:'category',label:'Categoria'},
          {key:'subcategory',label:'Sottocategoria'},
          {key:'value',label:'Tipologia'},
          {key:'act',label:'Azioni',render:r=><button className="ghost danger" onClick={()=>removeTypology(r.category, r.subcategory, r.value)}><Trash2 /> Elimina</button>}
        ]} />
      </Card>
    </>}

    {tab === 'products' && <>
      <Card title="Aggiungi collegamento prodotto" icon={Tags} sub="Esempio: Orologi → Anime → One Piece.">
        <div className="catalog-editor-grid">
          <SmartInput label="Categoria prodotto" options={sug.product_categories} value={prod.category} onChange={e=>setProd({...prod,category:e.target.value,subcategory:'',collection:''})}/>
          <SmartInput label="Sottocategoria prodotto" options={prodSubs(sug, prod.category)} value={prod.subcategory} onChange={e=>setProd({...prod,subcategory:e.target.value,collection:''})}/>
          <SmartInput label="Collezione / tema" options={collections(sug, prod.category, prod.subcategory)} value={prod.collection} onChange={e=>setProd({...prod,collection:e.target.value})}/>
          <button className="primary" onClick={() => save('/product-links', prod, 'Collezione prodotto salvata')}><Plus /> Salva</button>
        </div>
      </Card>

      <Card title="Categorie prodotti" icon={Factory} sub={`${prodRows.length} elementi visualizzati`}>
        <DataTable rows={prodRows} empty="Nessuna categoria prodotto" columns={[
          {key:'category',label:'Categoria'},
          {key:'subcategory',label:'Sottocategoria'},
          {key:'collection',label:'Collezione'},
          {key:'act',label:'Azioni',render:r=><button className="ghost danger" onClick={()=>removeProductLink(r)}><Trash2 /> Elimina</button>}
        ]} />
      </Card>
    </>}
  </>;
}'''


def main():
    s = MAIN.read_text(encoding="utf-8")

    # Fix PDF: usa URL assoluto verso backend.
    old = """  function openQuotePdf(q, type = 'customer') {
    if (!q?.id) {
      toast('Salva prima il preventivo', 'err');
      return;
    }
    const url = `/api/quotes/${encodeURIComponent(q.id)}/pdf/${type}`;
    window.open(url, '_blank');
  }"""

    new = """  function openQuotePdf(q, type = 'customer') {
    if (!q?.id) {
      toast('Salva prima il preventivo', 'err');
      return;
    }

    const backendBase =
      window.location.protocol === 'file:'
        ? 'http://127.0.0.1:8000'
        : window.location.origin.includes('5173')
          ? 'http://127.0.0.1:8000'
          : window.location.origin;

    const url = `${backendBase}/api/quotes/${encodeURIComponent(q.id)}/pdf/${type}`;

    const popup = window.open(url, '_blank', 'noopener,noreferrer');

    if (!popup) {
      window.location.href = url;
    }
  }"""

    if old in s:
        s = s.replace(old, new, 1)

    # Sostituisce interamente Setup con versione più ordinata.
    start = s.find("function Setup")
    end = s.find("\nfunction People", start)

    if start == -1 or end == -1:
        raise RuntimeError("Funzione Setup non trovata")

    s = s[:start] + NEW_SETUP + "\n\n" + s[end + 1:]

    MAIN.write_text(s, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    if "/* v39.8.1 catalog ux */" not in css:
        css += """

/* v39.8.1 catalog ux */
.catalog-toolbar {
  display: grid;
  gap: 14px;
}

.catalog-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.catalog-tabs button {
  border: 1px solid rgba(148, 163, 184, .22);
  background: rgba(255,255,255,.055);
  color: var(--muted);
  border-radius: 999px;
  padding: 10px 14px;
  cursor: pointer;
  font-weight: 800;
}

.catalog-tabs button.active {
  background: rgba(34, 211, 238, .14);
  border-color: rgba(34, 211, 238, .45);
  color: var(--text);
}

.catalog-filters {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 12px;
  align-items: center;
}

.catalog-filters select {
  min-height: 42px;
}

.catalog-editor-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) auto;
  gap: 12px;
  align-items: end;
}

.catalog-editor-grid button {
  min-height: 42px;
  white-space: nowrap;
}

@media (max-width: 1050px) {
  .catalog-filters,
  .catalog-editor-grid {
    grid-template-columns: 1fr;
  }
}
"""
        CSS.write_text(css, encoding="utf-8")

    print("Patch v39.8.1 PDF URL + catalogo UX applicata.")


if __name__ == "__main__":
    main()
