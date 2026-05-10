from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


WIZARD_CODE = r'''
function ProductWizard({ inv, sug, refresh, refreshSug, toast }) {
  const [step, setStep] = useState(1);
  const [materialSearch, setMaterialSearch] = useState('');
  const [selectedMaterial, setSelectedMaterial] = useState('');
  const [materialQty, setMaterialQty] = useState('1');

  const [draft, setDraft] = useState({
    name: '',
    section: 'Prodotti Finiti / Semilavorati',
    category: '',
    subcategory: '',
    collection: '',
    unit: 'pz',
    stock: 0,
    labor_hours: '',
    hourly_rate: '',
    extra_unit_cost: '',
    description: '',
    bom: []
  });

  const filteredMaterials = useMemo(() => {
    const q = materialSearch.toLowerCase().trim();

    return list(inv).filter(i => {
      const text = [
        i.name,
        i.section,
        i.category,
        i.subcategory,
        i.size,
        i.thickness,
        i.supplier_details
      ].join(' ').toLowerCase();

      if (Number(i.stock || 0) <= 0) return false;
      if (Number(i.cost_per_unit || i.weighted_average_cost || 0) <= 0) return false;

      return !q || q.split(/\s+/).every(part => text.includes(part));
    }).slice(0, 80);
  }, [inv, materialSearch]);

  const selected = list(inv).find(x => x.key === selectedMaterial);

  const materialCost = draft.bom.reduce((sum, row) => {
    const item = list(inv).find(x => x.key === row.name || x.name === row.name);
    return sum + Number(row.qty || 0) * Number(item?.cost_per_unit || item?.weighted_average_cost || 0);
  }, 0);

  const laborCost = Number(draft.labor_hours || 0) * Number(draft.hourly_rate || 0);
  const extraCost = Number(draft.extra_unit_cost || 0);
  const unitCost = materialCost + laborCost + extraCost;

  const canNext = () => {
    if (step === 1) return draft.name.trim().length > 0;
    if (step === 2) return draft.category.trim().length > 0;
    if (step === 3) return draft.bom.length > 0;
    if (step === 4) return true;
    return true;
  };

  function next() {
    if (!canNext()) {
      toast('Completa i campi richiesti prima di continuare', 'err');
      return;
    }
    setStep(s => Math.min(5, s + 1));
  }

  function back() {
    setStep(s => Math.max(1, s - 1));
  }

  function addBomMaterial() {
    const item = list(inv).find(x => x.key === selectedMaterial);
    const q = Number(materialQty || 0);

    if (!item || q <= 0) {
      toast('Seleziona un materiale e una quantità valida', 'err');
      return;
    }

    const existingIndex = draft.bom.findIndex(x => x.name === item.key);

    if (existingIndex >= 0) {
      const nextBom = draft.bom.map((x, i) =>
        i === existingIndex ? { ...x, qty: Number(x.qty || 0) + q } : x
      );
      setDraft(v => ({ ...v, bom: nextBom }));
    } else {
      setDraft(v => ({
        ...v,
        bom: [
          ...v.bom,
          {
            name: item.key,
            label: item.name,
            qty: q,
            unit: item.unit || '',
            category: item.category || '',
            subcategory: item.subcategory || '',
            size: item.size || '',
            thickness: item.thickness || '',
            unit_cost: Number(item.cost_per_unit || item.weighted_average_cost || 0)
          }
        ]
      }));
    }

    setSelectedMaterial('');
    setMaterialQty('1');
  }

  function removeBomMaterial(index) {
    setDraft(v => ({
      ...v,
      bom: v.bom.filter((_, i) => i !== index)
    }));
  }

  async function saveWizardProduct() {
    if (!draft.name.trim()) {
      toast('Nome prodotto richiesto', 'err');
      return;
    }

    if (!draft.bom.length) {
      toast('Aggiungi almeno un materiale alla distinta base', 'err');
      return;
    }

    try {
      await postJSON('/products', {
        ...draft,
        stock: Number(draft.stock || 0),
        labor_hours: Number(draft.labor_hours || 0),
        hourly_rate: Number(draft.hourly_rate || 0),
        extra_unit_cost: Number(draft.extra_unit_cost || 0),
        bom: draft.bom.map(row => ({
          name: row.name,
          qty: Number(row.qty || 0)
        }))
      });

      toast('Prodotto creato con wizard');
      setStep(1);
      setMaterialSearch('');
      setSelectedMaterial('');
      setMaterialQty('1');
      setDraft({
        name: '',
        section: 'Prodotti Finiti / Semilavorati',
        category: '',
        subcategory: '',
        collection: '',
        unit: 'pz',
        stock: 0,
        labor_hours: '',
        hourly_rate: '',
        extra_unit_cost: '',
        description: '',
        bom: []
      });

      await refresh();
      await refreshSug();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  const steps = [
    ['Identità', 'Nome e descrizione'],
    ['Catalogo', 'Categoria e collezione'],
    ['Materiali', 'Distinta base'],
    ['Costi', 'Lavoro ed extra'],
    ['Riepilogo', 'Controllo finale']
  ];

  return <Card title="Wizard nuovo prodotto" icon={Wand2}>
    <div className="product-wizard">
      <div className="wizard-steps">
        {steps.map(([title, desc], i) => <button
          key={title}
          className={step === i + 1 ? 'active' : step > i + 1 ? 'done' : ''}
          onClick={() => setStep(i + 1)}
        >
          <span>{i + 1}</span>
          <div>
            <b>{title}</b>
            <small>{desc}</small>
          </div>
        </button>)}
      </div>

      {step === 1 && <div className="wizard-panel">
        <div className="wizard-section-title">
          <b>Identità prodotto</b>
          <span>Dai un nome chiaro alla creazione. Sarà usato in magazzino, preventivi e vendite.</span>
        </div>

        <div className="form-grid">
          <Input label="Nome prodotto" value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })} placeholder="Es. Orologio One Piece 40 cm" />
          <SmartInput label="Unità" options={sug.units} value={draft.unit} onChange={e => setDraft({ ...draft, unit: e.target.value })} />
          <Input label="Descrizione" value={draft.description} onChange={e => setDraft({ ...draft, description: e.target.value })} placeholder="Dettagli lavorazione, finitura, colore..." />
        </div>
      </div>}

      {step === 2 && <div className="wizard-panel">
        <div className="wizard-section-title">
          <b>Categoria e collezione</b>
          <span>Collega il prodotto al catalogo commerciale.</span>
        </div>

        <div className="form-grid">
          <SmartInput label="Categoria" options={sug.product_categories} value={draft.category} onChange={e => setDraft({ ...draft, category: e.target.value, subcategory: '', collection: '' })} />
          <SmartInput label="Sottocategoria" options={prodSubs(sug, draft.category)} value={draft.subcategory} onChange={e => setDraft({ ...draft, subcategory: e.target.value, collection: '' })} />
          <SmartInput label="Collezione" options={collections(sug, draft.category, draft.subcategory)} value={draft.collection} onChange={e => setDraft({ ...draft, collection: e.target.value })} />
        </div>
      </div>}

      {step === 3 && <div className="wizard-panel">
        <div className="wizard-section-title">
          <b>Materiali e distinta base</b>
          <span>Aggiungi i materiali reali dal magazzino. Verranno usati per calcolare il costo interno.</span>
        </div>

        <div className="wizard-material-layout">
          <div className="wizard-material-search">
            <SearchBox value={materialSearch} onChange={setMaterialSearch} placeholder="Cerca materiale: betulla, acrilico, led..." />

            <div className="wizard-material-results">
              {filteredMaterials.map(m => <button
                key={m.key}
                className={selectedMaterial === m.key ? 'selected' : ''}
                onClick={() => setSelectedMaterial(m.key)}
              >
                <div>
                  <b>{m.name}</b>
                  <small>{[m.category, m.subcategory, m.size, m.thickness].filter(Boolean).join(' · ')}</small>
                </div>
                <span>{num(m.stock)} {m.unit || ''}</span>
                <strong>{money(m.cost_per_unit || m.weighted_average_cost)}</strong>
              </button>)}

              {!filteredMaterials.length && <Empty text="Nessun materiale disponibile" />}
            </div>
          </div>

          <div className="wizard-bom-box">
            <div className="selected-material-box">
              {selected ? <>
                <span>Materiale selezionato</span>
                <b>{selected.name}</b>
                <small>{[selected.category, selected.subcategory, selected.size, selected.thickness].filter(Boolean).join(' · ')}</small>
              </> : <Empty text="Seleziona materiale" />}
            </div>

            <div className="quote-add-line">
              <input type="number" step="0.01" value={materialQty} onChange={e => setMaterialQty(e.target.value)} />
              <div className="quote-mini-total">
                <span>Costo riga</span>
                <b>{money(selected ? Number(selected.cost_per_unit || selected.weighted_average_cost || 0) * Number(materialQty || 0) : 0)}</b>
              </div>
              <button className="primary" onClick={addBomMaterial}><Plus /> Aggiungi</button>
            </div>

            <div className="wizard-bom-list">
              {draft.bom.map((row, i) => <div key={i} className="wizard-bom-row">
                <div>
                  <b>{row.label || row.name}</b>
                  <small>{row.qty} {row.unit || ''} · {row.category || 'materiale'}</small>
                </div>
                <strong>{money(Number(row.qty || 0) * Number(row.unit_cost || 0))}</strong>
                <button className="ghost danger" onClick={() => removeBomMaterial(i)}>×</button>
              </div>)}

              {!draft.bom.length && <Empty text="Nessun materiale aggiunto" />}
            </div>
          </div>
        </div>
      </div>}

      {step === 4 && <div className="wizard-panel">
        <div className="wizard-section-title">
          <b>Costi lavoro ed extra</b>
          <span>Imposta tempo di lavorazione, tariffa e costi aggiuntivi per calcolare il costo interno.</span>
        </div>

        <div className="form-grid">
          <Input label="Ore lavoro" type="number" step="0.01" value={draft.labor_hours} onChange={e => setDraft({ ...draft, labor_hours: e.target.value })} />
          <Input label="Tariffa €/h" type="number" step="0.01" value={draft.hourly_rate} onChange={e => setDraft({ ...draft, hourly_rate: e.target.value })} />
          <Input label="Extra per pezzo €" type="number" step="0.01" value={draft.extra_unit_cost} onChange={e => setDraft({ ...draft, extra_unit_cost: e.target.value })} />
        </div>

        <div className="wizard-cost-grid">
          <Stat label="Materiali" value={money(materialCost)} />
          <Stat label="Lavoro" value={money(laborCost)} />
          <Stat label="Extra" value={money(extraCost)} />
          <Stat label="Costo interno/u" value={money(unitCost)} tone="mint" />
        </div>
      </div>}

      {step === 5 && <div className="wizard-panel">
        <div className="wizard-section-title">
          <b>Riepilogo prodotto</b>
          <span>Controlla i dati prima di creare la scheda prodotto.</span>
        </div>

        <div className="wizard-summary">
          <div>
            <span>Nome</span>
            <b>{draft.name || '—'}</b>
          </div>
          <div>
            <span>Categoria</span>
            <b>{[draft.category, draft.subcategory, draft.collection].filter(Boolean).join(' · ') || '—'}</b>
          </div>
          <div>
            <span>Materiali BOM</span>
            <b>{draft.bom.length}</b>
          </div>
          <div>
            <span>Costo interno/u</span>
            <b>{money(unitCost)}</b>
          </div>
        </div>

        <div className="wizard-bom-list review">
          {draft.bom.map((row, i) => <div key={i} className="wizard-bom-row">
            <div>
              <b>{row.label || row.name}</b>
              <small>{row.qty} {row.unit || ''}</small>
            </div>
            <strong>{money(Number(row.qty || 0) * Number(row.unit_cost || 0))}</strong>
          </div>)}
        </div>
      </div>}

      <div className="wizard-actions">
        <button className="ghost" onClick={back} disabled={step === 1}>Indietro</button>
        {step < 5
          ? <button className="primary" onClick={next}>Continua <ArrowRight /></button>
          : <button className="primary" onClick={saveWizardProduct}><Save /> Salva prodotto</button>}
      </div>
    </div>
  </Card>;
}
'''


def replace_products_additions(s: str) -> str:
    # Inserisce ProductWizard prima di ProductionBox.
    if "function ProductWizard" not in s:
        marker = "function ProductionBox"
        if marker not in s:
            raise RuntimeError("Punto inserimento ProductWizard non trovato")
        s = s.replace(marker, WIZARD_CODE + "\n\n" + marker, 1)

    # Aggiunge tab Wizard prodotto.
    if "Wizard prodotto" not in s:
        old = """      <button className={area === 'warehouse' ? 'active' : ''} onClick={() => setArea('warehouse')}>Magazzino prodotti</button>
      <button className={area === 'sheet' ? 'active' : ''} onClick={() => setArea('sheet')}>Scheda prodotto e BOM</button>
      <button className={area === 'produce' ? 'active' : ''} onClick={() => setArea('produce')}>Produci</button>
      <button className={area === 'movements' ? 'active' : ''} onClick={() => setArea('movements')}>Movimenti</button>"""

        new = """      <button className={area === 'warehouse' ? 'active' : ''} onClick={() => setArea('warehouse')}>Magazzino prodotti</button>
      <button className={area === 'wizard' ? 'active' : ''} onClick={() => setArea('wizard')}>Wizard prodotto</button>
      <button className={area === 'sheet' ? 'active' : ''} onClick={() => setArea('sheet')}>Scheda prodotto e BOM</button>
      <button className={area === 'produce' ? 'active' : ''} onClick={() => setArea('produce')}>Produci</button>
      <button className={area === 'movements' ? 'active' : ''} onClick={() => setArea('movements')}>Movimenti</button>"""

        if old not in s:
            raise RuntimeError("Blocco tab Produzione non trovato")
        s = s.replace(old, new, 1)

    # Aggiunge render wizard.
    if "area === 'wizard'" not in s:
        old = """    {area === 'warehouse' && <ProductWarehouse products={products} refresh={() => { refresh(); refreshMovements(); }} toast={toast} onEdit={editProduct} onDelete={remove} onDuplicate={openDuplicateProduct} />}"""
        new = """    {area === 'warehouse' && <ProductWarehouse products={products} refresh={() => { refresh(); refreshMovements(); }} toast={toast} onEdit={editProduct} onDelete={remove} onDuplicate={openDuplicateProduct} />}
    {area === 'wizard' && <ProductWizard inv={inv} sug={sug} refresh={refresh} refreshSug={refreshSug} toast={toast} />}"""

        if old not in s:
            # fallback per versioni senza onDuplicate
            old = """    {area === 'warehouse' && <ProductWarehouse products={products} refresh={() => { refresh(); refreshMovements(); }} toast={toast} onEdit={editProduct} onDelete={remove} />}"""
            new = """    {area === 'warehouse' && <ProductWarehouse products={products} refresh={() => { refresh(); refreshMovements(); }} toast={toast} onEdit={editProduct} onDelete={remove} />}
    {area === 'wizard' && <ProductWizard inv={inv} sug={sug} refresh={refresh} refreshSug={refreshSug} toast={toast} />}"""

        if old not in s:
            raise RuntimeError("Blocco ProductWarehouse render non trovato")
        s = s.replace(old, new, 1)

    return s


def main():
    s = MAIN.read_text(encoding="utf-8")
    s = replace_products_additions(s)
    MAIN.write_text(s, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    if "/* v40.2 product wizard */" not in css:
        css += r'''

/* v40.2 product wizard */
.product-wizard {
  display: grid;
  gap: 18px;
}

.wizard-steps {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.wizard-steps button {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  color: var(--text);
  border-radius: 18px;
  padding: 12px;
  display: flex;
  gap: 10px;
  align-items: center;
  text-align: left;
  cursor: pointer;
}

.wizard-steps button span {
  width: 30px;
  height: 30px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(255,255,255,.08);
  font-weight: 900;
  flex: 0 0 auto;
}

.wizard-steps button b,
.wizard-steps button small {
  display: block;
}

.wizard-steps button small {
  color: var(--muted);
  margin-top: 2px;
  line-height: 1.25;
}

.wizard-steps button.active {
  border-color: rgba(34, 211, 238, .5);
  background: rgba(34, 211, 238, .12);
}

.wizard-steps button.done span {
  background: rgba(34, 197, 94, .16);
  color: #86efac;
}

.wizard-panel {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  border-radius: 24px;
  padding: 18px;
  display: grid;
  gap: 18px;
}

.wizard-section-title b,
.wizard-section-title span {
  display: block;
}

.wizard-section-title b {
  font-size: 18px;
}

.wizard-section-title span {
  color: var(--muted);
  margin-top: 4px;
}

.wizard-material-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(360px, .85fr);
  gap: 16px;
  align-items: start;
}

.wizard-material-search,
.wizard-bom-box {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.wizard-material-results {
  display: grid;
  gap: 8px;
  max-height: 460px;
  overflow-y: auto;
  padding-right: 5px;
}

.wizard-material-results button {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  color: var(--text);
  border-radius: 16px;
  padding: 12px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 12px;
  align-items: center;
  text-align: left;
  cursor: pointer;
}

.wizard-material-results button.selected {
  border-color: rgba(34, 211, 238, .55);
  background: rgba(34, 211, 238, .12);
}

.wizard-material-results b,
.wizard-material-results small {
  display: block;
  min-width: 0;
}

.wizard-material-results small {
  color: var(--muted);
  margin-top: 3px;
}

.wizard-material-results span,
.wizard-material-results strong {
  white-space: nowrap;
}

.wizard-bom-list {
  display: grid;
  gap: 8px;
  max-height: 360px;
  overflow-y: auto;
  padding-right: 4px;
}

.wizard-bom-list.review {
  max-height: none;
}

.wizard-bom-row {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  border-radius: 16px;
  padding: 10px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto 36px;
  gap: 10px;
  align-items: center;
}

.wizard-bom-list.review .wizard-bom-row {
  grid-template-columns: minmax(0, 1fr) auto;
}

.wizard-bom-row b,
.wizard-bom-row small {
  display: block;
}

.wizard-bom-row small {
  color: var(--muted);
  margin-top: 3px;
}

.wizard-bom-row button {
  width: 36px;
  height: 36px;
  min-height: 36px;
  padding: 0;
}

.wizard-cost-grid,
.wizard-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.wizard-summary > div {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  border-radius: 18px;
  padding: 14px;
}

.wizard-summary span,
.wizard-summary b {
  display: block;
}

.wizard-summary span {
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .06em;
  margin-bottom: 6px;
}

.wizard-summary b {
  line-height: 1.25;
}

.wizard-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 1200px) {
  .wizard-steps,
  .wizard-material-layout,
  .wizard-cost-grid,
  .wizard-summary {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 760px) {
  .wizard-steps,
  .wizard-material-layout,
  .wizard-cost-grid,
  .wizard-summary {
    grid-template-columns: 1fr;
  }

  .wizard-material-results button,
  .wizard-bom-row {
    grid-template-columns: 1fr;
  }

  .wizard-actions {
    flex-direction: column;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")

    print("Patch v40.2.0 wizard nuovo prodotto completata.")


if __name__ == "__main__":
    main()
