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

    old_datatable = """function DataTable({ columns, rows, empty = 'Nessun risultato', meta = 'Dati aggiornati dal database' }) { return <div className="table-card"><div className="table-meta"><b>{rows.length} righe</b><span>{meta}</span></div><div className="table-wrap"><table><thead><tr>{columns.map(c => <th key={c.key}>{c.label}</th>)}</tr></thead><tbody>{rows.length ? rows.map((r, i) => <tr key={r._key || r.key || r.name || i}>{columns.map(c => <td key={c.key}>{c.render ? c.render(r, i) : r[c.key]}</td>)}</tr>) : <tr><td colSpan={columns.length}><Empty text={empty}/></td></tr>}</tbody></table></div></div>; }"""

    new_datatable = """function DataTable({ columns, rows, empty = 'Nessun risultato', meta = 'Dati aggiornati dal database', rowClassName }) { return <div className="table-card"><div className="table-meta"><b>{rows.length} righe</b><span>{meta}</span></div><div className="table-wrap"><table><thead><tr>{columns.map(c => <th key={c.key}>{c.label}</th>)}</tr></thead><tbody>{rows.length ? rows.map((r, i) => <tr className={rowClassName ? rowClassName(r, i) : ''} key={r._key || r.key || r.name || i}>{columns.map(c => <td key={c.key}>{c.render ? c.render(r, i) : r[c.key]}</td>)}</tr>) : <tr><td colSpan={columns.length}><Empty text={empty}/></td></tr>}</tbody></table></div></div>; }
function InventoryBadge({ item }) { const status = item?.inventory_status || 'da_verificare'; const label = item?.inventory_badge || 'da verificare'; return <span className={`inventory-badge ${status}`}>{label}</span>; }
function inventoryRowClass(r) { return `inventory-row ${r?.inventory_status || 'da_verificare'}`; }
const inventoryFilterLabel = {
  all: 'Tutti',
  attivo: 'Attivi',
  da_verificare: 'Da verificare',
  mai_acquistato: 'Mai acquistati',
  esaurito: 'Esauriti',
  sotto_scorta: 'Sotto scorta'
};"""

    s = replace_once(s, old_datatable, new_datatable, "DataTable")

    old_materials_start = """function Materials({ toast }) {
  const { data: items, loading, error, refresh } = useApi('/inventory', []);
  const { data: opt } = useApi('/options', {});
  const { data: sug, refresh: refreshSug } = useApi('/suggestions', {});
  const [q, setQ] = useState('');
  const [f, setF] = useState({ section: 'Falegnameria', supplier: '', category: '', subcategory: '', size: '', thickness: '', unit: 'pz', quantity: 1, total_cost: 0 });"""

    new_materials_start = """function Materials({ toast }) {
  const { data: items, loading, error, refresh } = useApi('/inventory', []);
  const { data: quality } = useApi('/inventory/quality', {});
  const { data: opt } = useApi('/options', {});
  const { data: sug, refresh: refreshSug } = useApi('/suggestions', {});
  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [f, setF] = useState({ section: 'Falegnameria', supplier: '', category: '', subcategory: '', size: '', thickness: '', unit: 'pz', quantity: 1, total_cost: 0 });"""

    s = replace_once(s, old_materials_start, new_materials_start, "Materials start")

    old_rows = """  const rows = list(items).filter(x => [x.name, x.section, x.category, x.subcategory, x.supplier_details].join(' ').toLowerCase().includes(q.toLowerCase()));"""

    new_rows = """  const rows = list(items).filter(x => {
    const matchesSearch = [x.name, x.section, x.category, x.subcategory, x.supplier_details, x.inventory_badge].join(' ').toLowerCase().includes(q.toLowerCase());
    const matchesStatus = statusFilter === 'all' || x.inventory_status === statusFilter;
    return matchesSearch && matchesStatus;
  });"""

    s = replace_once(s, old_rows, new_rows, "Materials rows filter")

    old_stock_card = """    <Card title="Stock materiali" icon={Archive} action={<SearchBox value={q} onChange={setQ} placeholder="Cerca materiale, categoria o fornitore..." />}>
      {loading ? <Skeleton /> : <DataTable rows={rows} empty="Nessun materiale caricato" columns={[
        { key: 'name', label: 'Articolo' }, { key: 'section', label: 'Area' }, { key: 'category', label: 'Categoria' }, { key: 'subcategory', label: 'Variante' },
        { key: 'qty', label: 'Stock', render: r => `${num(r.stock)} ${r.unit || ''}` }, { key: 'cost', label: 'Costo medio', render: r => money(r.cost_per_unit) },
        { key: 'sup', label: 'Fornitori', render: r => <span className="muted-cell">{r.supplier_details || '—'}</span> }, { key: 'act', label: '', render: r => <button className="ghost danger" onClick={() => remove(r)}><Trash2 /></button> }
      ]} />}
    </Card>"""

    new_stock_card = """    <div className="stats inventory-quality">
      <Stat label="Attivi" value={quality.active || 0} sub="utilizzabili nei preventivi" icon={CheckCircle2} tone="mint" />
      <Stat label="Da verificare" value={quality.to_check || 0} sub="stock presente ma costo mancante" icon={AlertTriangle} tone="wood" />
      <Stat label="Mai acquistati" value={quality.never_purchased || 0} sub="preset non operativi" icon={Archive} tone="ink" />
      <Stat label="Valore reale" value={money(quality.real_value)} sub="stock valorizzato" icon={CircleDollarSign} tone="cyan" />
    </div>
    <Card title="Stock materiali" icon={Archive} action={<SearchBox value={q} onChange={setQ} placeholder="Cerca materiale, categoria o fornitore..." />}>
      <div className="inventory-filters">
        {Object.entries(inventoryFilterLabel).map(([key, label]) => <button key={key} className={statusFilter === key ? 'active' : ''} onClick={() => setStatusFilter(key)}>{label}</button>)}
      </div>
      {loading ? <Skeleton /> : <DataTable rows={rows} empty="Nessun materiale caricato" rowClassName={inventoryRowClass} columns={[
        { key: 'status', label: 'Stato', render: r => <InventoryBadge item={r} /> },
        { key: 'name', label: 'Articolo' },
        { key: 'section', label: 'Area' },
        { key: 'category', label: 'Categoria' },
        { key: 'subcategory', label: 'Variante' },
        { key: 'qty', label: 'Stock', render: r => `${num(r.stock)} ${r.unit || ''}` },
        { key: 'cost', label: 'Costo medio', render: r => money(r.weighted_average_cost ?? r.cost_per_unit) },
        { key: 'last', label: 'Ultimo acquisto', render: r => <span className="muted-cell">{r.last_supplier ? `${r.last_supplier} · ${money(r.last_unit_cost)}` : '—'}</span> },
        { key: 'sup', label: 'Fornitori', render: r => <span className="muted-cell">{r.supplier_details || '—'}</span> },
        { key: 'act', label: '', render: r => <button className="ghost danger" onClick={() => remove(r)}><Trash2 /></button> }
      ]} />}
    </Card>"""

    s = replace_once(s, old_stock_card, new_stock_card, "Stock card")

    old_filtered_materials = """    return list(inv).filter(i => {
      const text = [i.name, i.section, i.category, i.subcategory, i.supplier_details, i.unit, i.size, i.thickness].join(' ').toLowerCase();
      if (q && !q.split(/\\s+/).every(part => text.includes(part))) return false;
      if (filters.supplier && !String(i.supplier_details || '').toLowerCase().includes(filters.supplier.toLowerCase())) return false;
      if (filters.section && i.section !== filters.section) return false;
      if (filters.category && i.category !== filters.category) return false;
      if (filters.subcategory && i.subcategory !== filters.subcategory) return false;
      return true;
    }).slice(0, 120);"""

    new_filtered_materials = """    return list(inv).filter(i => {
      if (!i.usable_in_quote) return false;
      const text = [i.name, i.section, i.category, i.subcategory, i.supplier_details, i.unit, i.size, i.thickness].join(' ').toLowerCase();
      if (q && !q.split(/\\s+/).every(part => text.includes(part))) return false;
      if (filters.supplier && !String(i.supplier_details || '').toLowerCase().includes(filters.supplier.toLowerCase())) return false;
      if (filters.section && i.section !== filters.section) return false;
      if (filters.category && i.category !== filters.category) return false;
      if (filters.subcategory && i.subcategory !== filters.subcategory) return false;
      return true;
    }).slice(0, 120);"""

    s = replace_once(s, old_filtered_materials, new_filtered_materials, "Quote filtered materials")

    old_add_material_check = """    if (!it || qn <= 0) {
      toast('Seleziona un materiale e una quantità valida', 'err');
      return;
    }"""

    new_add_material_check = """    if (!it || qn <= 0) {
      toast('Seleziona un materiale e una quantità valida', 'err');
      return;
    }
    if (!it.usable_in_quote) {
      toast('Materiale non utilizzabile: stock o costo medio non valorizzato', 'err');
      return;
    }
    if (Number(it.stock || 0) < qn) {
      toast(`Stock insufficiente: disponibile ${num(it.stock)} ${it.unit || ''}`, 'err');
      return;
    }"""

    s = replace_once(s, old_add_material_check, new_add_material_check, "Quote addMaterial check")

    old_material_pick = """          {filteredMaterials.length ? filteredMaterials.map(m => <button type="button" key={m.key} className={item === m.key ? 'material-pick active' : 'material-pick'} onClick={() => setItem(m.key)}>
            <span><b>{m.name}</b><small>{[m.section, m.category, m.subcategory, m.size, m.thickness].filter(Boolean).join(' · ')}</small></span>
            <em>{num(m.stock)} {m.unit || ''}</em>
            <strong>{money(m.cost_per_unit)}</strong>
          </button>) : <Empty text="Nessun materiale trovato" />}"""

    new_material_pick = """          {filteredMaterials.length ? filteredMaterials.map(m => <button type="button" key={m.key} className={item === m.key ? 'material-pick active' : 'material-pick'} onClick={() => setItem(m.key)}>
            <span><b>{m.name}</b><small>{[m.section, m.category, m.subcategory, m.size, m.thickness].filter(Boolean).join(' · ')}</small><InventoryBadge item={m} /></span>
            <em>{num(m.stock)} {m.unit || ''}</em>
            <strong>{money(m.weighted_average_cost ?? m.cost_per_unit)}</strong>
          </button>) : <Empty text="Nessun materiale disponibile per preventivi" />}"""

    s = replace_once(s, old_material_pick, new_material_pick, "Quote material pick")

    old_material_cost = """  const materialCost = selectedMaterial ? Number(selectedMaterial.cost_per_unit || 0) * Number(qty || 0) : 0;"""
    new_material_cost = """  const materialCost = selectedMaterial ? Number((selectedMaterial.weighted_average_cost ?? selectedMaterial.cost_per_unit) || 0) * Number(qty || 0) : 0;"""
    s = replace_once(s, old_material_cost, new_material_cost, "Quote material cost")

    old_row_cost = """      cost: qn * Number(it.cost_per_unit || 0),"""
    new_row_cost = """      cost: qn * Number((it.weighted_average_cost ?? it.cost_per_unit) || 0),"""
    s = replace_once(s, old_row_cost, new_row_cost, "Quote row cost")

    MAIN.write_text(s, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    marker = "/* inventory quality patch */"
    if marker not in css:
        css += """

/* inventory quality patch */
.inventory-quality {
  margin: 14px 0 18px;
}

.inventory-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0 0 14px;
}

.inventory-filters button {
  border: 1px solid rgba(148, 163, 184, .28);
  background: rgba(255,255,255,.06);
  color: inherit;
  border-radius: 999px;
  padding: 8px 12px;
  cursor: pointer;
  font-weight: 700;
  font-size: 12px;
}

.inventory-filters button.active {
  background: rgba(34, 211, 238, .18);
  border-color: rgba(34, 211, 238, .55);
}

.inventory-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 5px 9px;
  font-size: 11px;
  font-weight: 800;
  white-space: nowrap;
  border: 1px solid rgba(148, 163, 184, .26);
  background: rgba(148, 163, 184, .12);
}

.inventory-badge.attivo {
  background: rgba(34, 197, 94, .14);
  color: #86efac;
  border-color: rgba(34, 197, 94, .38);
}

.inventory-badge.sotto_scorta {
  background: rgba(249, 115, 22, .16);
  color: #fdba74;
  border-color: rgba(249, 115, 22, .42);
}

.inventory-badge.da_verificare {
  background: rgba(234, 179, 8, .16);
  color: #fde68a;
  border-color: rgba(234, 179, 8, .42);
}

.inventory-badge.mai_acquistato {
  background: rgba(239, 68, 68, .14);
  color: #fca5a5;
  border-color: rgba(239, 68, 68, .38);
}

.inventory-badge.esaurito {
  background: rgba(148, 163, 184, .14);
  color: #cbd5e1;
  border-color: rgba(148, 163, 184, .34);
}

.inventory-row.attivo td {
  background: linear-gradient(90deg, rgba(34,197,94,.075), transparent);
}

.inventory-row.sotto_scorta td {
  background: linear-gradient(90deg, rgba(249,115,22,.09), transparent);
}

.inventory-row.da_verificare td {
  background: linear-gradient(90deg, rgba(234,179,8,.09), transparent);
}

.inventory-row.mai_acquistato td {
  background: linear-gradient(90deg, rgba(239,68,68,.085), transparent);
}

.inventory-row.esaurito td {
  opacity: .72;
}

.material-pick .inventory-badge {
  margin-top: 7px;
  width: fit-content;
}
"""
        CSS.write_text(css, encoding="utf-8")

    print("Patch frontend completata.")
    print(f"Aggiornato: {MAIN}")
    print(f"Aggiornato: {CSS}")


if __name__ == "__main__":
    main()
