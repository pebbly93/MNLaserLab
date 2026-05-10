from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN_API = ROOT / "backend" / "app" / "main.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"Blocco non trovato: {label}")
    return text.replace(old, new, 1)


BACKEND_HELPERS = r'''

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
'''


API_ENDPOINTS = r'''

@app.get("/api/products/{name:path}/detail")
def product_detail_api(name: str):
    try:
        return product_detail(load_db(), name)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
'''


def patch_backend():
    s = LEGACY.read_text(encoding="utf-8")
    if "def product_detail(db, name):" not in s:
        s += "\n\n" + BACKEND_HELPERS.strip() + "\n"
    LEGACY.write_text(s, encoding="utf-8")

    m = MAIN_API.read_text(encoding="utf-8")
    if "def product_detail_api" not in m:
        m += "\n\n" + API_ENDPOINTS.strip() + "\n"
    MAIN_API.write_text(m, encoding="utf-8")

    print("Backend dettaglio applicato.")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    # Stato dettaglio materiali in Materials
    old = """function Materials({ toast }) {
  const { data: items, loading, error, refresh } = useApi('/inventory', []);"""
    new = """function Materials({ toast }) {
  const { data: items, loading, error, refresh } = useApi('/inventory', []);"""
    # blocco lasciato invariato, sotto aggiungiamo stato se non c'è
    if "const [materialDetail, setMaterialDetail]" not in s:
        old2 = """  const [statusFilter, setStatusFilter] = useState('all');"""
        new2 = """  const [statusFilter, setStatusFilter] = useState('all');
  const [materialDetail, setMaterialDetail] = useState(null);"""
        s = replace_once(s, old2, new2, "material detail state")

    if "async function openMaterialDetail" not in s:
        old2 = """  async function remove(r) { if (!confirm('Eliminare questo articolo?')) return; try { await del('/raw/' + encodeURIComponent(r.table) + '/' + encodeURIComponent(r.key)); toast('Articolo eliminato'); refresh(); } catch (e) { toast(e.message, 'err'); } }"""
        new2 = """  async function remove(r) { if (!confirm('Eliminare questo articolo?')) return; try { await del('/raw/' + encodeURIComponent(r.table) + '/' + encodeURIComponent(r.key)); toast('Articolo eliminato'); refresh(); } catch (e) { toast(e.message, 'err'); } }
  async function openMaterialDetail(r) {
    try {
      setMaterialDetail(await getJSON('/raw-detail/' + encodeURIComponent(r.table) + '/' + encodeURIComponent(r.key)));
    } catch (e) {
      toast(e.message, 'err');
    }
  }"""
        s = replace_once(s, old2, new2, "open material detail")

    old2 = """        { key: 'act', label: '', render: r => <button className="ghost danger" onClick={() => remove(r)}><Trash2 /></button> }"""
    new2 = """        { key: 'act', label: 'Azioni', render: r => <div className="table-actions">
          <button className="ghost" onClick={() => openMaterialDetail(r)}>Dettaglio</button>
          <button className="ghost danger" onClick={() => remove(r)}><Trash2 /></button>
        </div> }"""
    if old2 in s:
        s = s.replace(old2, new2, 1)

    # Inserisci pannello materiale dopo card Stock materiali
    if "Dettaglio materiale" not in s:
        marker = """    </Card>
  </>;
}

function ProductionBox"""
        panel = """    </Card>
    {materialDetail && <Card title="Dettaglio materiale" icon={Archive} sub="Storico acquisti, utilizzo nei prodotti e stato economico dell’articolo." action={<button className="ghost" onClick={() => setMaterialDetail(null)}>Chiudi</button>}>
      <div className="detail-grid">
        <Stat label="Articolo" value={materialDetail.name || '—'} />
        <Stat label="Stock" value={`${num(materialDetail.item?.stock)} ${materialDetail.item?.unit || ''}`} />
        <Stat label="Costo medio" value={money(materialDetail.item?.weighted_average_cost ?? materialDetail.item?.cost_per_unit)} />
        <Stat label="Valore stock" value={money(materialDetail.stock_value)} />
      </div>
      <div className="detail-columns">
        <div>
          <h3>Storico acquisti</h3>
          <DataTable rows={list(materialDetail.purchase_history).slice(0, 12)} empty="Nessuno storico acquisti" columns={[
            { key: 'date', label: 'Data' },
            { key: 'supplier', label: 'Fornitore' },
            { key: 'qty', label: 'Q.tà', render: r => num(r.qty) },
            { key: 'unit_cost', label: 'Costo/u', render: r => money(r.unit_cost) },
            { key: 'total_cost', label: 'Totale', render: r => money(r.total_cost) }
          ]} />
        </div>
        <div>
          <h3>Usato nei prodotti</h3>
          <DataTable rows={list(materialDetail.used_in_products)} empty="Non risulta usato in prodotti" columns={[
            { key: 'product', label: 'Prodotto' },
            { key: 'qty', label: 'Q.tà BOM', render: r => `${num(r.qty)} ${r.unit || ''}` }
          ]} />
        </div>
      </div>
    </Card>}
  </>;
}

function ProductionBox"""
        s = replace_once(s, marker, panel, "material detail panel")

    # ProductWarehouse: stato dettaglio
    if "const [productDetail, setProductDetail]" not in s:
        old2 = """  const [movement, setMovement] = useState({ product: '', qty: '', reason: 'Rettifica inventario', note: '' });"""
        new2 = """  const [movement, setMovement] = useState({ product: '', qty: '', reason: 'Rettifica inventario', note: '' });
  const [productDetail, setProductDetail] = useState(null);"""
        s = replace_once(s, old2, new2, "product detail state")

    if "async function openProductDetail" not in s:
        old2 = """  async function adjust(sign = 1) {"""
        new2 = """  async function openProductDetail(name) {
    try {
      setProductDetail(await getJSON(`/products/${encodeURIComponent(name)}/detail`));
    } catch (e) {
      toast(e.message, 'err');
    }
  }
  async function adjust(sign = 1) {"""
        s = replace_once(s, old2, new2, "open product detail")

    old2 = """          <button className="ghost" onClick={() => onEdit(r)}>Modifica</button>
          <button className="ghost danger" onClick={() => onDelete(r.name)}>Elimina</button>"""
    new2 = """          <button className="ghost" onClick={() => openProductDetail(r.name)}>Dettaglio</button>
          <button className="ghost" onClick={() => onEdit(r)}>Modifica</button>
          <button className="ghost danger" onClick={() => onDelete(r.name)}>Elimina</button>"""
    if old2 in s:
        s = s.replace(old2, new2, 1)

    # Inserisci pannello prodotto dopo card Magazzino prodotti finiti
    if "Dettaglio prodotto finito" not in s:
        marker = """    </Card>
  </>;
}

function Products"""
        panel = """    </Card>
    {productDetail && <Card title="Dettaglio prodotto finito" icon={PackageCheck} sub="Distinta base, costi interni, movimenti e vendite collegate." action={<button className="ghost" onClick={() => setProductDetail(null)}>Chiudi</button>}>
      <div className="detail-grid">
        <Stat label="Prodotto" value={productDetail.name || '—'} />
        <Stat label="Stock" value={`${num(productDetail.stock)} ${productDetail.product?.unit || 'pz'}`} />
        <Stat label="Costo interno/u" value={money(productDetail.unit_cost)} />
        <Stat label="Valore stock" value={money(productDetail.value)} />
      </div>
      <div className="detail-grid compact-detail">
        <Stat label="Materiali/u" value={money(productDetail.material_cost)} />
        <Stat label="Lavoro/u" value={money(productDetail.labor_cost)} />
        <Stat label="Extra/u" value={money(productDetail.extra_cost)} />
      </div>
      <div className="detail-columns">
        <div>
          <h3>Distinta base</h3>
          <DataTable rows={list(productDetail.bom)} empty="Nessuna distinta base" columns={[
            { key: 'label', label: 'Materiale' },
            { key: 'qty', label: 'Q.tà', render: r => `${num(r.qty)} ${r.unit || ''}` },
            { key: 'unit_cost', label: 'Costo/u', render: r => money(r.unit_cost) },
            { key: 'cost', label: 'Costo', render: r => money(r.cost) },
            { key: 'ok', label: 'Stock', render: r => r.ok ? 'OK' : 'Da verificare' }
          ]} />
        </div>
        <div>
          <h3>Movimenti</h3>
          <DataTable rows={list(productDetail.movements).slice(0, 12)} empty="Nessun movimento" columns={[
            { key: 'date', label: 'Data' },
            { key: 'qty', label: 'Q.tà', render: r => num(r.qty) },
            { key: 'reason', label: 'Causale' },
            { key: 'note', label: 'Note' }
          ]} />
        </div>
      </div>
    </Card>}
  </>;
}

function Products"""
        # Questo marker potrebbe colpire ProductWarehouse, che è esattamente quello voluto
        start = s.find("function ProductWarehouse")
        end = s.find("function Products", start)
        block = s[start:end]
        if marker.replace("\nfunction Products", "") not in block:
            # fallback più semplice: prima di function Products
            insert_at = s.find("\nfunction Products", start)
            if insert_at == -1:
                raise RuntimeError("Punto inserimento dettaglio prodotto non trovato")
            s = s[:insert_at] + """
    {productDetail && <Card title="Dettaglio prodotto finito" icon={PackageCheck} sub="Distinta base, costi interni, movimenti e vendite collegate." action={<button className="ghost" onClick={() => setProductDetail(null)}>Chiudi</button>}>
      <div className="detail-grid">
        <Stat label="Prodotto" value={productDetail.name || '—'} />
        <Stat label="Stock" value={`${num(productDetail.stock)} ${productDetail.product?.unit || 'pz'}`} />
        <Stat label="Costo interno/u" value={money(productDetail.unit_cost)} />
        <Stat label="Valore stock" value={money(productDetail.value)} />
      </div>
      <div className="detail-columns">
        <div>
          <h3>Distinta base</h3>
          <DataTable rows={list(productDetail.bom)} empty="Nessuna distinta base" columns={[
            { key: 'label', label: 'Materiale' },
            { key: 'qty', label: 'Q.tà', render: r => `${num(r.qty)} ${r.unit || ''}` },
            { key: 'unit_cost', label: 'Costo/u', render: r => money(r.unit_cost) },
            { key: 'cost', label: 'Costo', render: r => money(r.cost) },
            { key: 'ok', label: 'Stock', render: r => r.ok ? 'OK' : 'Da verificare' }
          ]} />
        </div>
        <div>
          <h3>Movimenti</h3>
          <DataTable rows={list(productDetail.movements).slice(0, 12)} empty="Nessun movimento" columns={[
            { key: 'date', label: 'Data' },
            { key: 'qty', label: 'Q.tà', render: r => num(r.qty) },
            { key: 'reason', label: 'Causale' },
            { key: 'note', label: 'Note' }
          ]} />
        </div>
      </div>
    </Card>}
""" + s[insert_at:]
        else:
            s = replace_once(s, marker, panel, "product detail panel")

    FRONTEND.write_text(s, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    if "/* v39.6 detail panels */" not in css:
        css += """

/* v39.6 detail panels */
.detail-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 12px 0 18px;
}

.detail-grid.compact-detail {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.detail-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.detail-columns h3 {
  margin: 8px 0 10px;
  font-size: 15px;
}

@media (max-width: 1000px) {
  .detail-grid,
  .detail-grid.compact-detail,
  .detail-columns {
    grid-template-columns: 1fr;
  }
}
"""
        CSS.write_text(css, encoding="utf-8")

    print("Frontend dettaglio applicato.")


def main():
    patch_backend()
    patch_frontend()
    print("Patch v39.6.0 dettaglio completata.")


if __name__ == "__main__":
    main()
