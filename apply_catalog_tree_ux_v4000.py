from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


NEW_SETUP = r'''function Setup({ toast }) {
  const { data: tax, refresh: refreshTax } = useApi('/taxonomy', { raw_tree: [], product_tree: [], supplier_matrix: [] });
  const { data: sug, refresh: refreshSug } = useApi('/suggestions', {});

  const [mode, setMode] = useState('raw');
  const [q, setQ] = useState('');
  const [selectedArea, setSelectedArea] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSubcategory, setSelectedSubcategory] = useState('');

  const [rawDraft, setRawDraft] = useState({ category: '', subcategory: '' });
  const [formatDraft, setFormatDraft] = useState('');
  const [thicknessDraft, setThicknessDraft] = useState('');
  const [typologyDraft, setTypologyDraft] = useState('');
  const [productDraft, setProductDraft] = useState({ category: '', subcategory: '', collection: '' });

  const rawAreas = list(tax.raw_tree);
  const activeArea = rawAreas.find(a => a.scope === selectedArea || a.label === selectedArea) || rawAreas[0] || { scope: 'materials', label: 'Falegnameria', categories: [] };
  const areaScope = activeArea.scope;
  const areaLabel = activeArea.label;

  useEffect(() => {
    if (!selectedArea && rawAreas[0]) setSelectedArea(rawAreas[0].scope);
  }, [tax.raw_tree]);

  const activeCategories = list(activeArea.categories).filter(c => {
    const text = [areaLabel, c.name, ...(list(c.subcategories))].join(' ').toLowerCase();
    return !q || q.toLowerCase().split(/\s+/).every(part => text.includes(part));
  });

  const activeCategory = activeCategories.find(c => c.name === selectedCategory) || activeCategories[0] || null;
  const activeSubcategories = list(activeCategory?.subcategories);
  const activeSubcategory = selectedSubcategory || activeSubcategories[0] || '';

  const productRows = Object.entries(sug.collections_by_product_path || {}).flatMap(([cat, subMap]) =>
    Object.entries(subMap || {}).flatMap(([sub, cols]) =>
      list(cols).map(col => ({ category: cat, subcategory: sub, collection: col }))
    )
  ).filter(r => {
    const text = [r.category, r.subcategory, r.collection].join(' ').toLowerCase();
    return !q || q.toLowerCase().split(/\s+/).every(part => text.includes(part));
  });

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

  async function addRawCategory() {
    const payload = {
      scope: areaScope,
      category: rawDraft.category || selectedCategory,
      subcategory: rawDraft.subcategory
    };

    if (!payload.category) {
      toast('Inserisci una categoria', 'err');
      return;
    }

    await save('/categories', payload, 'Categoria salvata');
    setSelectedCategory(payload.category);
    setSelectedSubcategory(payload.subcategory || '');
    setRawDraft({ category: '', subcategory: '' });
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

      if (!subcategory && selectedCategory === category) {
        setSelectedCategory('');
        setSelectedSubcategory('');
      }

      if (subcategory && selectedSubcategory === subcategory) {
        setSelectedSubcategory('');
      }

      await reloadCatalog();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function addFormat() {
    const category = selectedCategory;
    if (!category || !formatDraft) {
      toast('Seleziona una categoria e inserisci un formato', 'err');
      return;
    }

    await save('/catalog/formats', { category, value: formatDraft }, 'Formato salvato');
    setFormatDraft('');
  }

  async function addThickness() {
    const category = selectedCategory;
    if (!category || !thicknessDraft) {
      toast('Seleziona una categoria e inserisci uno spessore', 'err');
      return;
    }

    await save('/catalog/thicknesses', { category, value: thicknessDraft }, 'Spessore salvato');
    setThicknessDraft('');
  }

  async function addTypology() {
    const category = selectedCategory;
    const subcategory = activeSubcategory;

    if (!category || !subcategory || !typologyDraft) {
      toast('Seleziona categoria/sottocategoria e inserisci una tipologia', 'err');
      return;
    }

    await save('/catalog/typologies', { category, subcategory, value: typologyDraft }, 'Tipologia salvata');
    setTypologyDraft('');
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

  async function addProductLink() {
    if (!productDraft.category || !productDraft.subcategory || !productDraft.collection) {
      toast('Categoria, sottocategoria e collezione prodotto sono richieste', 'err');
      return;
    }

    await save('/product-links', productDraft, 'Collezione prodotto salvata');
    setProductDraft({ category: '', subcategory: '', collection: '' });
  }

  async function removeProductLink(r) {
    if (!confirm(`Eliminare il collegamento "${r.category} → ${r.subcategory} → ${r.collection}"?`)) return;

    try {
      const params = new URLSearchParams({
        category: r.category,
        subcategory: r.subcategory,
        collection: r.collection,
      });
      await del('/product-links?' + params.toString());
      toast('Collegamento prodotto eliminato');
      await reloadCatalog();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  const categoryFormats = list(pick(sug, ['formats_by_category', selectedCategory], []));
  const categoryThicknesses = list(pick(sug, ['thicknesses_by_category', selectedCategory], []));
  const subTypologies = list(pick(sug, ['typologies_by_category_subcategory', selectedCategory, activeSubcategory], []));

  const areaStats = {
    categories: list(activeArea.categories).length,
    subcategories: list(activeArea.categories).reduce((a, c) => a + list(c.subcategories).length, 0),
  };

  return <>
    <PageTitle title="Catalogo" desc="Gestione guidata: scegli l’area, poi categoria e sottocategoria. Formati, spessori e tipologie restano collegati al contesto corretto." />

    <Card title="Gestione catalogo" icon={Settings2} sub="Struttura più ordinata per evitare valori fuori contesto, come 12V dentro Falegnameria/Legname.">
      <div className="catalog-topbar">
        <div className="catalog-mode-tabs">
          <button className={mode === 'raw' ? 'active' : ''} onClick={() => setMode('raw')}>Materiali e componenti</button>
          <button className={mode === 'products' ? 'active' : ''} onClick={() => setMode('products')}>Prodotti finiti</button>
        </div>
        <SearchBox value={q} onChange={setQ} placeholder="Cerca nel catalogo..." />
      </div>
    </Card>

    {mode === 'raw' && <div className="catalog-workbench">
      <section className="catalog-column catalog-areas">
        <div className="catalog-column-head">
          <span>1</span>
          <div>
            <b>Aree</b>
            <small>Ambito del materiale</small>
          </div>
        </div>

        <div className="catalog-list">
          {rawAreas.map(area => <button
            key={area.scope}
            className={(area.scope === areaScope || area.label === areaLabel) ? 'selected' : ''}
            onClick={() => {
              setSelectedArea(area.scope);
              setSelectedCategory('');
              setSelectedSubcategory('');
              setRawDraft({ category: '', subcategory: '' });
            }}
          >
            <b>{area.label}</b>
            <small>{list(area.categories).length} categorie</small>
          </button>)}
        </div>
      </section>

      <section className="catalog-column catalog-categories">
        <div className="catalog-column-head">
          <span>2</span>
          <div>
            <b>Categorie</b>
            <small>{areaLabel} · {areaStats.categories} categorie</small>
          </div>
        </div>

        <div className="catalog-create-box">
          <SmartInput label="Nuova categoria" options={rawCatsStrict ? rawCatsStrict(sug, areaScope) : rawCats(sug, areaScope)} value={rawDraft.category} onChange={e => setRawDraft({ ...rawDraft, category: e.target.value })} placeholder="Es. Legname, Acrilico, Alimentatori" />
          <SmartInput label="Sottocategoria opzionale" options={rawDraft.category ? (rawSubsStrict ? rawSubsStrict(sug, areaScope, rawDraft.category) : rawSubs(sug, areaScope, rawDraft.category)) : []} value={rawDraft.subcategory} onChange={e => setRawDraft({ ...rawDraft, subcategory: e.target.value })} placeholder="Es. Betulla, Pioppo, 12V" />
          <button className="primary" onClick={addRawCategory}><Plus /> Aggiungi</button>
        </div>

        <div className="catalog-list">
          {activeCategories.map(cat => <button
            key={cat.name}
            className={selectedCategory === cat.name || (!selectedCategory && activeCategory?.name === cat.name) ? 'selected' : ''}
            onClick={() => {
              setSelectedCategory(cat.name);
              setSelectedSubcategory('');
              setRawDraft({ category: cat.name, subcategory: '' });
            }}
          >
            <b>{cat.name}</b>
            <small>{list(cat.subcategories).length} sottocategorie · {cat.suppliers || 0} fornitori</small>
          </button>)}
          {!activeCategories.length && <Empty text="Nessuna categoria trovata" />}
        </div>
      </section>

      <section className="catalog-column catalog-subcategories">
        <div className="catalog-column-head">
          <span>3</span>
          <div>
            <b>Sottocategorie</b>
            <small>{activeCategory?.name || 'Seleziona categoria'}</small>
          </div>
        </div>

        <div className="catalog-selected-box">
          <span>Categoria selezionata</span>
          <b>{selectedCategory || activeCategory?.name || '—'}</b>
          {(selectedCategory || activeCategory?.name) && <button className="ghost danger" onClick={() => removeCategory(areaScope, selectedCategory || activeCategory?.name, '')}>Elimina categoria</button>}
        </div>

        <div className="catalog-list">
          {activeSubcategories.map(sub => <button
            key={sub}
            className={activeSubcategory === sub ? 'selected' : ''}
            onClick={() => setSelectedSubcategory(sub)}
          >
            <b>{sub}</b>
            <small>{selectedCategory || activeCategory?.name}</small>
          </button>)}
          {!activeSubcategories.length && <Empty text="Nessuna sottocategoria" />}
        </div>

        {activeSubcategory && <button className="ghost danger wide-action" onClick={() => removeCategory(areaScope, selectedCategory || activeCategory?.name, activeSubcategory)}>
          <Trash2 /> Elimina sottocategoria selezionata
        </button>}
      </section>

      <section className="catalog-column catalog-linked">
        <div className="catalog-column-head">
          <span>4</span>
          <div>
            <b>Configurazioni collegate</b>
            <small>{selectedCategory || activeCategory?.name || 'Nessuna categoria'}</small>
          </div>
        </div>

        <div className="catalog-config-card">
          <div className="catalog-config-head">
            <b>Formati</b>
            <small>Validi per la categoria</small>
          </div>
          <div className="catalog-inline-add">
            <SmartInput label="Aggiungi formato" options={formats(sug, selectedCategory || activeCategory?.name)} value={formatDraft} onChange={e => setFormatDraft(e.target.value)} placeholder="20x20, 40x40, Rotolo" />
            <button onClick={addFormat}><Plus /></button>
          </div>
          <div className="pill-list">
            {categoryFormats.map(v => <span key={v}>{v}<button onClick={() => removeFormat(selectedCategory || activeCategory?.name, v)}>×</button></span>)}
            {!categoryFormats.length && <small className="muted-cell">Nessun formato</small>}
          </div>
        </div>

        <div className="catalog-config-card">
          <div className="catalog-config-head">
            <b>Spessori</b>
            <small>Validi per la categoria</small>
          </div>
          <div className="catalog-inline-add">
            <SmartInput label="Aggiungi spessore" options={thicknesses(sug, selectedCategory || activeCategory?.name)} value={thicknessDraft} onChange={e => setThicknessDraft(e.target.value)} placeholder="2 mm, 4 mm, 10 mm" />
            <button onClick={addThickness}><Plus /></button>
          </div>
          <div className="pill-list">
            {categoryThicknesses.map(v => <span key={v}>{v}<button onClick={() => removeThickness(selectedCategory || activeCategory?.name, v)}>×</button></span>)}
            {!categoryThicknesses.length && <small className="muted-cell">Nessuno spessore</small>}
          </div>
        </div>

        <div className="catalog-config-card">
          <div className="catalog-config-head">
            <b>Tipologie</b>
            <small>Valide per la sottocategoria</small>
          </div>
          <div className="catalog-inline-add">
            <SmartInput label="Aggiungi tipologia" options={typologies(sug, selectedCategory || activeCategory?.name, activeSubcategory)} value={typologyDraft} onChange={e => setTypologyDraft(e.target.value)} placeholder="Da presa, Luce calda..." />
            <button onClick={addTypology}><Plus /></button>
          </div>
          <div className="pill-list">
            {subTypologies.map(v => <span key={v}>{v}<button onClick={() => removeTypology(selectedCategory || activeCategory?.name, activeSubcategory, v)}>×</button></span>)}
            {!subTypologies.length && <small className="muted-cell">Nessuna tipologia</small>}
          </div>
        </div>
      </section>
    </div>}

    {mode === 'products' && <div className="split-main">
      <Card title="Aggiungi collegamento prodotto" icon={Tags} sub="Esempio: Orologi → Anime → One Piece.">
        <div className="catalog-editor-grid">
          <SmartInput label="Categoria prodotto" options={sug.product_categories} value={productDraft.category} onChange={e=>setProductDraft({...productDraft,category:e.target.value,subcategory:'',collection:''})}/>
          <SmartInput label="Sottocategoria prodotto" options={prodSubs(sug, productDraft.category)} value={productDraft.subcategory} onChange={e=>setProductDraft({...productDraft,subcategory:e.target.value,collection:''})}/>
          <SmartInput label="Collezione / tema" options={collections(sug, productDraft.category, productDraft.subcategory)} value={productDraft.collection} onChange={e=>setProductDraft({...productDraft,collection:e.target.value})}/>
          <button className="primary" onClick={addProductLink}><Plus /> Salva</button>
        </div>
      </Card>

      <Card title="Categorie prodotti finiti" icon={Factory} sub={`${productRows.length} collegamenti visualizzati`}>
        <DataTable rows={productRows} empty="Nessuna categoria prodotto" columns={[
          {key:'category',label:'Categoria'},
          {key:'subcategory',label:'Sottocategoria'},
          {key:'collection',label:'Collezione'},
          {key:'act',label:'Azioni',render:r=><button className="ghost danger" onClick={()=>removeProductLink(r)}><Trash2 /> Elimina</button>}
        ]} />
      </Card>
    </div>}
  </>;
}'''


def replace_setup(source: str) -> str:
    start = source.find("function Setup")
    end = source.find("\nfunction People", start)

    if start == -1 or end == -1:
        raise RuntimeError("Funzione Setup non trovata")

    return source[:start] + NEW_SETUP + "\n\n" + source[end + 1:]


def main():
    s = FRONTEND.read_text(encoding="utf-8")
    s = replace_setup(s)
    FRONTEND.write_text(s, encoding="utf-8")
    print("Setup catalogo UX definitivo applicato.")

    css = CSS.read_text(encoding="utf-8")
    if "/* v40 catalog workbench */" not in css:
        css += """

/* v40 catalog workbench */
.catalog-topbar {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 14px;
  align-items: center;
}

.catalog-mode-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.catalog-mode-tabs button {
  border: 1px solid rgba(148, 163, 184, .22);
  background: rgba(255,255,255,.055);
  color: var(--muted);
  border-radius: 999px;
  padding: 10px 14px;
  cursor: pointer;
  font-weight: 900;
}

.catalog-mode-tabs button.active {
  background: rgba(34, 211, 238, .14);
  border-color: rgba(34, 211, 238, .45);
  color: var(--text);
}

.catalog-workbench {
  display: grid;
  grid-template-columns: 220px minmax(220px, .9fr) minmax(220px, .9fr) minmax(320px, 1.3fr);
  gap: 14px;
  align-items: start;
}

.catalog-column {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  border-radius: 24px;
  padding: 14px;
  min-height: 520px;
}

.catalog-column-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(148, 163, 184, .14);
  margin-bottom: 12px;
}

.catalog-column-head > span {
  width: 30px;
  height: 30px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(34, 211, 238, .14);
  border: 1px solid rgba(34, 211, 238, .35);
  font-weight: 900;
  color: #67e8f9;
}

.catalog-column-head b {
  display: block;
}

.catalog-column-head small {
  display: block;
  color: var(--muted);
  margin-top: 2px;
}

.catalog-list {
  display: grid;
  gap: 8px;
}

.catalog-list button {
  text-align: left;
  border: 1px solid rgba(148, 163, 184, .15);
  background: rgba(255,255,255,.045);
  color: var(--text);
  border-radius: 16px;
  padding: 11px;
  cursor: pointer;
}

.catalog-list button:hover {
  border-color: rgba(34, 211, 238, .38);
  background: rgba(34, 211, 238, .075);
}

.catalog-list button.selected {
  border-color: rgba(34, 211, 238, .58);
  background: rgba(34, 211, 238, .13);
}

.catalog-list button b,
.catalog-list button small {
  display: block;
}

.catalog-list button small {
  color: var(--muted);
  margin-top: 4px;
}

.catalog-create-box,
.catalog-selected-box,
.catalog-config-card {
  border: 1px solid rgba(148, 163, 184, .14);
  background: rgba(2, 6, 23, .18);
  border-radius: 18px;
  padding: 12px;
  margin-bottom: 12px;
}

.catalog-create-box {
  display: grid;
  gap: 10px;
}

.catalog-selected-box span,
.catalog-selected-box b {
  display: block;
}

.catalog-selected-box span {
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .06em;
}

.catalog-selected-box b {
  margin: 4px 0 10px;
}

.wide-action {
  width: 100%;
  justify-content: center;
  margin-top: 12px;
}

.catalog-config-card {
  display: grid;
  gap: 10px;
}

.catalog-config-head b,
.catalog-config-head small {
  display: block;
}

.catalog-config-head small {
  color: var(--muted);
  margin-top: 2px;
}

.catalog-inline-add {
  display: grid;
  grid-template-columns: 1fr 42px;
  gap: 8px;
  align-items: end;
}

.catalog-inline-add button {
  height: 42px;
  display: grid;
  place-items: center;
}

.pill-list {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.pill-list > span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(148, 163, 184, .22);
  background: rgba(255,255,255,.055);
  border-radius: 999px;
  padding: 7px 9px;
  font-size: 12px;
}

.pill-list > span button {
  border: 0;
  background: rgba(239, 68, 68, .14);
  color: #fecaca;
  width: 18px;
  height: 18px;
  border-radius: 999px;
  cursor: pointer;
}

@media (max-width: 1280px) {
  .catalog-workbench {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 850px) {
  .catalog-topbar,
  .catalog-workbench {
    grid-template-columns: 1fr;
  }

  .catalog-column {
    min-height: auto;
  }
}
"""
        CSS.write_text(css, encoding="utf-8")
        print("CSS catalogo UX definitivo aggiunto.")

    print("Patch v40.0.0 catalogo UX definitivo completata.")


if __name__ == "__main__":
    main()
