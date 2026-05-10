from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN_API = ROOT / "backend" / "app" / "main.py"
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"Blocco non trovato: {label}")
    return text.replace(old, new, 1)


BACKEND_HELPERS = r'''

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
'''


API_ENDPOINTS = r'''

@app.post("/api/catalog/formats")
def add_catalog_format_api(payload: Payload):
    return mutate(add_catalog_format, payload.data)


@app.delete("/api/catalog/formats")
def delete_catalog_format_api(category: str, value: str):
    return mutate(delete_catalog_format, category, value)


@app.post("/api/catalog/thicknesses")
def add_catalog_thickness_api(payload: Payload):
    return mutate(add_catalog_thickness, payload.data)


@app.delete("/api/catalog/thicknesses")
def delete_catalog_thickness_api(category: str, value: str):
    return mutate(delete_catalog_thickness, category, value)


@app.post("/api/catalog/typologies")
def add_catalog_typology_api(payload: Payload):
    return mutate(add_catalog_typology, payload.data)


@app.delete("/api/catalog/typologies")
def delete_catalog_typology_api(category: str, subcategory: str, value: str):
    return mutate(delete_catalog_typology, category, subcategory, value)


@app.delete("/api/product-links")
def delete_product_link_api(category: str, subcategory: str, collection: str):
    return mutate(delete_product_collection_link, category, subcategory, collection)
'''


NEW_SETUP = r'''function Setup({ toast }) {
  const { data: tax, refresh: refreshTax } = useApi('/taxonomy', { raw_tree: [], product_tree: [], supplier_matrix: [] });
  const { data: sug, refresh: refreshSug } = useApi('/suggestions', {});

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

  const rawRows = list(tax.raw_tree).flatMap(sec =>
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

  const prodRows = Object.entries(sug.collections_by_product_path || {}).flatMap(([cat, subMap]) =>
    Object.entries(subMap || {}).flatMap(([sub, cols]) =>
      list(cols).map(col => ({ category: cat, subcategory: sub, collection: col }))
    )
  );

  const formatRows = Object.entries(sug.formats_by_category || {}).flatMap(([category, values]) =>
    list(values).map(value => ({ category, value }))
  );

  const thicknessRows = Object.entries(sug.thicknesses_by_category || {}).flatMap(([category, values]) =>
    list(values).map(value => ({ category, value }))
  );

  const typologyRows = Object.entries(sug.typologies_by_category_subcategory || {}).flatMap(([category, subMap]) =>
    Object.entries(subMap || {}).flatMap(([subcategory, values]) =>
      list(values).map(value => ({ category, subcategory, value }))
    )
  );

  const allRawCategories = unique([
    ...list(sug.raw_categories),
    ...rawRows.map(r => r.category),
  ]);

  const typSubcategories = typ.category
    ? unique(rawRows.filter(r => r.category === typ.category).map(r => r.subcategory).filter(Boolean))
    : [];

  return <>
    <PageTitle title="Catalogo" desc="Gestisci aree, categorie, sottocategorie, formati, spessori e tipologie collegate al flusso acquisti e prodotti." />

    <div className="split-main">
      <Card title="Catalogo materiali" icon={Truck} sub="Struttura logica per acquisti e magazzino. Esempio: Falegnameria → Legname → Betulla." action={<button onClick={() => save('/categories', raw, 'Categoria materiale salvata')}><Plus /> Salva</button>}>
        <div className="form-grid">
          <Select label="Area" value={raw.scope} onChange={e=>setRaw({...raw,scope:e.target.value,category:'',subcategory:''})}>
            <option value="materials">Falegnameria</option>
            <option value="components">Ferramenta</option>
            <option value="Illuminazione">Illuminazione</option>
          </Select>
          <SmartInput label="Categoria materiale" options={rawCatsStrict ? rawCatsStrict(sug, raw.scope) : rawCats(sug, raw.scope)} value={raw.category} onChange={e=>setRaw({...raw,category:e.target.value,subcategory:''})}/>
          <SmartInput label="Sottocategoria / variante" options={rawSubsStrict ? rawSubsStrict(sug, raw.scope, raw.category) : rawSubs(sug, raw.scope, raw.category)} value={raw.subcategory} onChange={e=>setRaw({...raw,subcategory:e.target.value})}/>
        </div>
      </Card>

      <Card title="Catalogo prodotti finiti" icon={Tags} sub="Categorie commerciali dei prodotti realizzati. Esempio: Orologi → Anime → One Piece." action={<button onClick={() => save('/product-links', prod, 'Collezione prodotto salvata')}><Plus /> Salva</button>}>
        <div className="form-grid">
          <SmartInput label="Categoria prodotto" options={sug.product_categories} value={prod.category} onChange={e=>setProd({...prod,category:e.target.value,subcategory:'',collection:''})}/>
          <SmartInput label="Sottocategoria prodotto" options={prodSubs(sug, prod.category)} value={prod.subcategory} onChange={e=>setProd({...prod,subcategory:e.target.value,collection:''})}/>
          <SmartInput label="Collezione / tema" options={collections(sug, prod.category, prod.subcategory)} value={prod.collection} onChange={e=>setProd({...prod,collection:e.target.value})}/>
        </div>
      </Card>
    </div>

    <div className="split-main">
      <Card title="Formati per categoria" icon={Layers3} sub="Associa i formati alla categoria corretta. Esempio: Legname → 20x20, 40x40.">
        <div className="form-grid compact-catalog-form">
          <SmartInput label="Categoria" options={allRawCategories} value={fmt.category} onChange={e=>setFmt({...fmt,category:e.target.value})}/>
          <SmartInput label="Formato / tipo" options={formats(sug, fmt.category)} value={fmt.value} onChange={e=>setFmt({...fmt,value:e.target.value})} placeholder="Es. 20x20, 40x40, Bobina, Rotolo"/>
          <button className="primary" onClick={saveFormat}><Plus /> Aggiungi formato</button>
        </div>
        <DataTable rows={formatRows} empty="Nessun formato configurato" columns={[
          {key:'category',label:'Categoria'},
          {key:'value',label:'Formato'},
          {key:'act',label:'',render:r=><button className="ghost danger" onClick={()=>removeFormat(r.category, r.value)}><Trash2 /></button>}
        ]} />
      </Card>

      <Card title="Spessori per categoria" icon={Layers3} sub="Associa gli spessori solo dove servono. Esempio: Legname → 2 mm, 4 mm, 10 mm.">
        <div className="form-grid compact-catalog-form">
          <SmartInput label="Categoria" options={allRawCategories} value={thk.category} onChange={e=>setThk({...thk,category:e.target.value})}/>
          <SmartInput label="Spessore" options={thicknesses(sug, thk.category)} value={thk.value} onChange={e=>setThk({...thk,value:e.target.value})} placeholder="Es. 2 mm, 4 mm, 10 mm"/>
          <button className="primary" onClick={saveThickness}><Plus /> Aggiungi spessore</button>
        </div>
        <DataTable rows={thicknessRows} empty="Nessuno spessore configurato" columns={[
          {key:'category',label:'Categoria'},
          {key:'value',label:'Spessore'},
          {key:'act',label:'',render:r=><button className="ghost danger" onClick={()=>removeThickness(r.category, r.value)}><Trash2 /></button>}
        ]} />
      </Card>
    </div>

    <Card title="Tipologie per sottocategoria" icon={Settings2} sub="Usale per casi come Illuminazione → Alimentatori → 12V → Da presa / Da incasso.">
      <div className="form-grid compact-catalog-form">
        <SmartInput label="Categoria" options={allRawCategories} value={typ.category} onChange={e=>setTyp({...typ,category:e.target.value,subcategory:'',value:''})}/>
        <SmartInput label="Sottocategoria" options={typSubcategories} value={typ.subcategory} onChange={e=>setTyp({...typ,subcategory:e.target.value,value:''})}/>
        <SmartInput label="Tipologia" options={typologies(sug, typ.category, typ.subcategory)} value={typ.value} onChange={e=>setTyp({...typ,value:e.target.value})} placeholder="Es. Da presa, Da incasso, Luce calda"/>
        <button className="primary" onClick={saveTypology}><Plus /> Aggiungi tipologia</button>
      </div>
      <DataTable rows={typologyRows} empty="Nessuna tipologia configurata" columns={[
        {key:'category',label:'Categoria'},
        {key:'subcategory',label:'Sottocategoria'},
        {key:'value',label:'Tipologia'},
        {key:'act',label:'',render:r=><button className="ghost danger" onClick={()=>removeTypology(r.category, r.subcategory, r.value)}><Trash2 /></button>}
      ]} />
    </Card>

    <div className="split-main">
      <Card title="Categorie materiali presenti" icon={Layers3}>
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

      <Card title="Categorie prodotti presenti" icon={Factory}>
        <DataTable rows={prodRows} empty="Nessuna categoria prodotto" columns={[
          {key:'category',label:'Categoria'},
          {key:'subcategory',label:'Sottocategoria'},
          {key:'collection',label:'Collezione'},
          {key:'act',label:'',render:r=><button className="ghost danger" onClick={()=>removeProductLink(r)}><Trash2 /></button>}
        ]} />
      </Card>
    </div>
  </>;
}'''


def patch_backend():
    s = LEGACY.read_text(encoding="utf-8")
    if "def add_catalog_format" not in s:
        s += "\n\n" + BACKEND_HELPERS.strip() + "\n"
    LEGACY.write_text(s, encoding="utf-8")

    m = MAIN_API.read_text(encoding="utf-8")
    if "def add_catalog_format_api" not in m:
        m += "\n\n" + API_ENDPOINTS.strip() + "\n"
    MAIN_API.write_text(m, encoding="utf-8")

    print("Backend catalogo avanzato applicato.")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    start = s.find("function Setup")
    end = s.find("\nfunction People", start)

    if start == -1 or end == -1:
        raise RuntimeError("Funzione Setup non trovata")

    s = s[:start] + NEW_SETUP + "\n\n" + s[end + 1:]

    css = CSS.read_text(encoding="utf-8")
    if "/* v39.7 catalog advanced */" not in css:
        css += """

/* v39.7 catalog advanced */
.compact-catalog-form {
  grid-template-columns: repeat(3, minmax(0, 1fr)) auto;
  align-items: end;
}

.compact-catalog-form button {
  min-height: 42px;
}

@media (max-width: 1000px) {
  .compact-catalog-form {
    grid-template-columns: 1fr;
  }
}
"""
        CSS.write_text(css, encoding="utf-8")

    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend catalogo avanzato applicato.")


def main():
    patch_backend()
    patch_frontend()
    print("Patch v39.7.0 catalogo avanzato completata.")


if __name__ == "__main__":
    main()
