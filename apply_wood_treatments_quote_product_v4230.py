from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


BACKEND_PATCH = r'''
# ---------------------------------------------------------------------------
# v42.3.0 - Wood treatments as dedicated cost section
# ---------------------------------------------------------------------------

def normalize_treatment_rows(rows):
    normalized = []
    if not isinstance(rows, list):
        return normalized

    for row in rows:
        if not isinstance(row, dict):
            continue

        name = str(row.get("name") or row.get("label") or "").strip()
        if not name:
            continue

        qty = parse_float(row.get("qty", row.get("quantity", 1)), 1)
        unit_cost = parse_float(row.get("unit_cost", row.get("cost_per_unit", 0)), 0)
        labor_hours = parse_float(row.get("labor_hours", 0), 0)
        steps = str(row.get("steps") or "").strip()
        type_ = str(row.get("type") or "trattamento").strip()
        notes = str(row.get("notes") or "").strip()

        normalized.append({
            "kind": "wood_treatment",
            "name": name,
            "label": name,
            "qty": qty,
            "unit": row.get("unit") or "app.",
            "unit_cost": unit_cost,
            "cost_per_unit": unit_cost,
            "weighted_average_cost": unit_cost,
            "labor_hours": labor_hours,
            "steps": steps,
            "type": type_,
            "notes": notes,
            "cost": round(qty * unit_cost, 2),
        })

    return normalized


def treatment_rows_cost(rows):
    return round(sum(parse_float(r.get("cost"), parse_float(r.get("qty", 1)) * parse_float(r.get("unit_cost", 0))) for r in normalize_treatment_rows(rows)), 2)


def treatment_rows_labor_hours(rows):
    return round(sum(parse_float(r.get("qty", 1)) * parse_float(r.get("labor_hours", 0)) for r in normalize_treatment_rows(rows)), 3)


try:
    _mnll_original_product_unit_cost_v4230 = product_unit_cost
except Exception:
    _mnll_original_product_unit_cost_v4230 = None

try:
    _mnll_original_product_detail_v4230 = product_detail
except Exception:
    _mnll_original_product_detail_v4230 = None

try:
    _mnll_original_save_product_v4230 = save_product
except Exception:
    _mnll_original_save_product_v4230 = None

try:
    _mnll_original_save_quote_v4230 = save_quote
except Exception:
    _mnll_original_save_quote_v4230 = None


def product_treatment_unit_cost(db, name):
    p = db.get("products", {}).get(name) or {}
    return treatment_rows_cost(p.get("treatments") or p.get("treatment_rows") or [])


def product_unit_cost(db, name):
    base = _mnll_original_product_unit_cost_v4230(db, name) if _mnll_original_product_unit_cost_v4230 else 0
    return round(parse_float(base) + product_treatment_unit_cost(db, name), 2)


def save_product(db, payload):
    result = _mnll_original_save_product_v4230(db, payload) if _mnll_original_save_product_v4230 else {"ok": True}

    name = payload.get("name") or payload.get("old_name")
    if name and name in db.get("products", {}):
        treatments = normalize_treatment_rows(payload.get("treatments") or payload.get("treatment_rows") or [])
        db["products"][name]["treatments"] = treatments
        db["products"][name]["treatment_unit_cost"] = treatment_rows_cost(treatments)
        db["products"][name]["treatment_labor_hours"] = treatment_rows_labor_hours(treatments)

    return result


def product_detail(db, name):
    detail = _mnll_original_product_detail_v4230(db, name) if _mnll_original_product_detail_v4230 else {}
    p = db.get("products", {}).get(name) or {}
    treatments = normalize_treatment_rows(p.get("treatments") or p.get("treatment_rows") or [])

    if isinstance(detail, dict):
        detail["treatments"] = treatments
        detail["treatment_cost"] = treatment_rows_cost(treatments)
        detail["treatment_labor_hours"] = treatment_rows_labor_hours(treatments)
        detail["unit_cost"] = product_unit_cost(db, name)

    return detail


def save_quote(db, payload):
    treatments = normalize_treatment_rows(payload.get("treatments") or payload.get("treatment_rows") or [])

    # Per compatibilità col calcolo attuale, i trattamenti entrano anche nelle rows,
    # ma vengono marcati come kind=wood_treatment per distinguerli dai materiali.
    rows = payload.get("rows") or []
    rows = list(rows) if isinstance(rows, list) else []

    existing_treatment_names = {
        str(r.get("name") or r.get("label") or "").strip()
        for r in rows
        if isinstance(r, dict) and r.get("kind") == "wood_treatment"
    }

    for tr in treatments:
        if tr["name"] not in existing_treatment_names:
            rows.append(tr)

    payload = {**payload, "rows": rows, "treatments": treatments, "treatment_rows": treatments}

    result = _mnll_original_save_quote_v4230(db, payload) if _mnll_original_save_quote_v4230 else {"ok": True}

    quote_id = None
    if isinstance(result, dict):
        quote_id = result.get("id") or (result.get("quote") or {}).get("id")

    if quote_id:
        for q in db.get("quotes", []) or []:
            if q.get("id") == quote_id:
                q["treatments"] = treatments
                q["treatment_rows"] = treatments
                q["treatment_cost"] = treatment_rows_cost(treatments)
                q["treatment_labor_hours"] = treatment_rows_labor_hours(treatments)
                break

    return result
'''


FRONTEND_HELPERS = r'''
function TreatmentCostPanel({ treatments = [], selectedRows = [], setSelectedRows, toast, title = "Trattamenti e finiture", compact = false }) {
  const [selected, setSelected] = useState('');
  const [qty, setQty] = useState(1);
  const [overrideCost, setOverrideCost] = useState('');

  const current = list(treatments).find(t => t.name === selected);
  const total = list(selectedRows).reduce((sum, r) => sum + Number(r.cost || 0), 0);

  function addTreatment() {
    if (!current) {
      toast && toast('Seleziona un trattamento', 'err');
      return;
    }

    const q = Number(qty || 1);
    const unitCost = overrideCost !== '' ? Number(overrideCost || 0) : Number(current.unit_cost || 0);

    const row = {
      kind: 'wood_treatment',
      name: current.name,
      label: current.name,
      type: current.type || 'trattamento',
      steps: current.steps || '',
      notes: current.notes || '',
      qty: q,
      unit: 'app.',
      unit_cost: unitCost,
      cost_per_unit: unitCost,
      weighted_average_cost: unitCost,
      labor_hours: Number(current.labor_hours || 0),
      cost: q * unitCost,
    };

    setSelectedRows(v => [...list(v), row]);
    setSelected('');
    setQty(1);
    setOverrideCost('');
  }

  function removeTreatment(i) {
    setSelectedRows(v => list(v).filter((_, idx) => idx !== i));
  }

  return <div className={compact ? "treatment-cost-panel compact" : "treatment-cost-panel"}>
    <div className="treatment-cost-head">
      <div>
        <b>{title}</b>
        <span>Finiture applicate al pezzo, separate dai materiali.</span>
      </div>
      <strong>{money(total)}</strong>
    </div>

    <div className="treatment-picker-grid">
      <Select label="Tipo trattamento" value={selected} onChange={e => {
        setSelected(e.target.value);
        setOverrideCost('');
      }}>
        <option value="">Scegli trattamento</option>
        {list(treatments).map(t => <option key={t.name} value={t.name}>{t.name}</option>)}
      </Select>

      <Input label="Applicazioni" type="number" step="0.01" value={qty} onChange={e => setQty(e.target.value)} />
      <Input label="Costo override €" type="number" step="0.01" value={overrideCost} onChange={e => setOverrideCost(e.target.value)} />
      <button type="button" className="primary treatment-add-btn" onClick={addTreatment}>+ Aggiungi</button>
    </div>

    {current && <div className="selected-treatment-preview">
      <b>{current.name}</b>
      <span>{current.type || 'trattamento'} · {current.steps || 'Fasi non indicate'}</span>
      <em>{money(overrideCost !== '' ? Number(overrideCost || 0) : Number(current.unit_cost || 0))} · {num(current.labor_hours || 0)} h</em>
    </div>}

    <div className="selected-treatment-list">
      {list(selectedRows).length ? list(selectedRows).map((r, i) => <div key={`${r.name}-${i}`} className="selected-treatment-row">
        <div>
          <b>{r.name}</b>
          <span>{r.type || 'trattamento'} · {r.steps || 'Fasi non indicate'}</span>
          {r.notes && <small>{r.notes}</small>}
        </div>
        <div className="selected-treatment-values">
          <span>{num(r.qty)} app.</span>
          <strong>{money(r.cost)}</strong>
          <button type="button" className="ghost danger" onClick={() => removeTreatment(i)}>×</button>
        </div>
      </div>) : <div className="empty-treatment">Nessun trattamento applicato.</div>}
    </div>
  </div>;
}
'''


CSS_PATCH = r'''
/* v42.3.0 treatments and finishes */
.treatment-cost-panel {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  border-radius: 22px;
  padding: 16px;
  display: grid;
  gap: 14px;
}

.treatment-cost-panel.compact {
  padding: 14px;
}

.treatment-cost-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
  border-bottom: 1px solid rgba(148, 163, 184, .14);
  padding-bottom: 12px;
}

.treatment-cost-head b {
  display: block;
  color: var(--text);
  font-size: 16px;
}

.treatment-cost-head span {
  display: block;
  color: var(--muted);
  margin-top: 4px;
  line-height: 1.35;
}

.treatment-cost-head strong {
  white-space: nowrap;
  color: var(--accent);
  font-size: 18px;
}

.treatment-picker-grid {
  display: grid;
  grid-template-columns: minmax(220px, 1.5fr) minmax(100px, .5fr) minmax(130px, .65fr) auto;
  gap: 10px;
  align-items: end;
}

.treatment-add-btn {
  height: 44px;
  align-self: end;
}

.selected-treatment-preview {
  border: 1px dashed rgba(5,132,130,.35);
  background: rgba(5,132,130,.08);
  border-radius: 16px;
  padding: 12px;
  display: grid;
  gap: 4px;
}

.selected-treatment-preview b {
  color: var(--text);
}

.selected-treatment-preview span,
.selected-treatment-preview em {
  color: var(--muted);
  font-style: normal;
  line-height: 1.35;
}

.selected-treatment-list {
  display: grid;
  gap: 10px;
}

.selected-treatment-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  border: 1px solid rgba(148, 163, 184, .14);
  background: rgba(15, 23, 42, .25);
  border-radius: 16px;
  padding: 12px;
}

.selected-treatment-row b {
  display: block;
  color: var(--text);
}

.selected-treatment-row span,
.selected-treatment-row small {
  display: block;
  color: var(--muted);
  line-height: 1.35;
  margin-top: 2px;
}

.selected-treatment-values {
  display: flex;
  align-items: center;
  gap: 10px;
}

.selected-treatment-values strong {
  color: var(--accent);
  min-width: 72px;
  text-align: right;
}

.empty-treatment {
  color: var(--muted);
  border: 1px dashed rgba(148, 163, 184, .18);
  border-radius: 16px;
  padding: 12px;
  text-align: center;
}

@media (max-width: 960px) {
  .treatment-picker-grid {
    grid-template-columns: 1fr 1fr;
  }

  .treatment-add-btn {
    width: 100%;
  }
}

@media (max-width: 620px) {
  .treatment-picker-grid,
  .selected-treatment-row {
    grid-template-columns: 1fr;
  }

  .selected-treatment-values {
    justify-content: space-between;
  }
}
'''


def append_backend():
    s = LEGACY.read_text(encoding="utf-8")
    if "v42.3.0 - Wood treatments as dedicated cost section" not in s:
        s += "\n\n" + BACKEND_PATCH.strip() + "\n"
    LEGACY.write_text(s, encoding="utf-8")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    if "function TreatmentCostPanel" not in s:
        idx = s.find("function ProductWizard")
        if idx == -1:
            raise RuntimeError("function ProductWizard non trovata")
        s = s[:idx] + FRONTEND_HELPERS + "\n\n" + s[idx:]

    # ProductWizard: aggiunge useApi trattamenti e stato treatments nel draft se manca.
    if "const { data: woodTreatments } = useApi('/catalog/wood-treatments'" not in s:
        s = s.replace(
            "function ProductWizard({ inv, sug, refresh, refreshSug, toast }) {",
            "function ProductWizard({ inv, sug, refresh, refreshSug, toast }) {\n  const { data: woodTreatments } = useApi('/catalog/wood-treatments', []);",
            1
        )

    # Aggiunge treatments al draft iniziale del wizard.
    s = s.replace(
        "bom: [],",
        "bom: [], treatments: [],",
        1
    )

    # Costo trattamento nel wizard.
    if "const treatmentCost = list(draft.treatments)" not in s:
        s = s.replace(
            "const extraCost = Number(draft.extra_unit_cost || 0);",
            "const extraCost = Number(draft.extra_unit_cost || 0);\n  const treatmentCost = list(draft.treatments).reduce((sum, r) => sum + Number(r.cost || 0), 0);",
            1
        )

    # totalCost include treatmentCost.
    s = s.replace(
        "const totalCost = materialCost + laborCost + extraCost;",
        "const totalCost = materialCost + treatmentCost + laborCost + extraCost;",
        1
    )

    # Payload ProductWizard include treatments.
    if "treatments: list(draft.treatments)" not in s:
        s = s.replace(
            "bom: list(draft.bom),",
            "bom: list(draft.bom),\n          treatments: list(draft.treatments),",
            1
        )

    # Reset draft include treatments.
    s = s.replace(
        "bom: []",
        "bom: [], treatments: []",
        1
    )

    # Inserisce panel trattamenti nel ProductWizard prima del blocco costi/lavoro.
    if "title=\"Trattamenti e finiture prodotto\"" not in s:
        marker = '<span>Imposta tempo di lavorazione, tariffa e costi aggiuntivi per calcolare il costo interno.</span>'
        insert = '''</div>
      </Card>

      <Card title="Trattamenti e finiture prodotto" icon={Settings2} sub="Finiture applicate al pezzo, gestite separatamente dalla distinta materiali.">
        <TreatmentCostPanel
          treatments={woodTreatments}
          selectedRows={draft.treatments}
          setSelectedRows={(fn) => setDraft(v => ({ ...v, treatments: typeof fn === 'function' ? fn(v.treatments || []) : fn }))}
          toast={toast}
          compact
        />
      </Card>

      <Card title="Lavoro, extra e costo interno" icon={Calculator}>
        <div className="muted-hint">
          <span>Imposta tempo di lavorazione, tariffa e costi aggiuntivi per calcolare il costo interno.</span>'''
        s = s.replace(marker, insert, 1)

    # Aggiunge voce trattamento al grid costi wizard se trova extra.
    if "<span>Trattamenti</span><b>{money(treatmentCost)}</b>" not in s:
        s = s.replace(
            "<span>Extra</span><b>{money(extraCost)}</b>",
            "<span>Trattamenti</span><b>{money(treatmentCost)}</b>\n          <span>Extra</span><b>{money(extraCost)}</b>",
            1
        )

    # Products manual form: stato iniziale include treatments.
    s = s.replace(
        "extra_unit_cost: '', bom: []",
        "extra_unit_cost: '', bom: [], treatments: []",
        1
    )

    # Products component: carica trattamenti.
    if "const { data: woodTreatmentsProducts } = useApi('/catalog/wood-treatments'" not in s:
        s = s.replace(
            "function Products({ toast }) {",
            "function Products({ toast }) {\n  const { data: woodTreatmentsProducts } = useApi('/catalog/wood-treatments', []);",
            1
        )

    # Save manual product payload mantiene treatments.
    if "treatments: list(p.treatments)" not in s:
        s = s.replace(
            "await postJSON('/products', payload);",
            "payload.treatments = list(p.treatments);\n      await postJSON('/products', payload);",
            1
        )

    # Inserisce card trattamenti nel form Products prima di Extra/u se possibile.
    if "Trattamenti e finiture scheda prodotto" not in s:
        marker = '<Input label="Extra/u €" type="number" step="0.01" value={p.extra_unit_cost} onChange={e => setP({ ...p, extra_unit_cost: e.target.value })} />'
        replacement = '''<div className="form-grid-full">
            <TreatmentCostPanel
              title="Trattamenti e finiture scheda prodotto"
              treatments={woodTreatmentsProducts}
              selectedRows={p.treatments}
              setSelectedRows={(fn) => setP(v => ({ ...v, treatments: typeof fn === 'function' ? fn(v.treatments || []) : fn }))}
              toast={toast}
              compact
            />
          </div>
          <Input label="Extra/u €" type="number" step="0.01" value={p.extra_unit_cost} onChange={e => setP({ ...p, extra_unit_cost: e.target.value })} />'''
        s = s.replace(marker, replacement, 1)

    # Quote: carica trattamenti e stato.
    if "const { data: woodTreatmentsQuote } = useApi('/catalog/wood-treatments'" not in s:
        s = s.replace(
            "function Quote({ toast }) {",
            "function Quote({ toast }) {\n  const { data: woodTreatmentsQuote } = useApi('/catalog/wood-treatments', []);",
            1
        )

    if "const [quoteTreatments, setQuoteTreatments]" not in s:
        s = s.replace(
            "const [rows, setRows] = useState([]);",
            "const [rows, setRows] = useState([]);\n  const [quoteTreatments, setQuoteTreatments] = useState([]);",
            1
        )

    # Quote calc/save/sale: include treatment rows in payload.
    if "const quoteRowsForCalc = [...rows, ...quoteTreatments]" not in s:
        s = s.replace(
            "async function calc() {",
            "async function calc() {\n    const quoteRowsForCalc = [...rows, ...quoteTreatments];",
            1
        )
        s = s.replace(
            "postJSON('/quote/calculate', { rows, estimated_materials: [], ...cost })",
            "postJSON('/quote/calculate', { rows: quoteRowsForCalc, treatments: quoteTreatments, treatment_rows: quoteTreatments, estimated_materials: [], ...cost })",
            1
        )

    s = s.replace(
        "await postJSON('/quote/sale', { name, customer: quoteCustomer, qty: 1, unit_price: res.discounted || res.recommended, rows, estimated_materials: [], ...cost });",
        "await postJSON('/quote/sale', { name, customer: quoteCustomer, qty: 1, unit_price: res.discounted || res.recommended, rows: [...rows, ...quoteTreatments], treatments: quoteTreatments, treatment_rows: quoteTreatments, estimated_materials: [], ...cost });",
        1
    )

    if "treatments: quoteTreatments" not in s:
        s = s.replace(
            "rows,",
            "rows: [...rows, ...quoteTreatments],\n        treatments: quoteTreatments,\n        treatment_rows: quoteTreatments,",
            1
        )

    # Inserisce panel trattamenti nel Quote prima della card Costi e margini.
    if "Trattamenti e finiture preventivo" not in s:
        marker = '<Card title="Costi e margini" icon={Calculator} action={<button className="primary" onClick={calc}><Calculator /> Calcola preventivo</button>}>'
        insert = '''<Card title="Trattamenti e finiture preventivo" icon={Settings2} sub="Seleziona finiture e pacchetti configurati nel catalogo. Entrano nel costo reale senza essere trattati come materie prime.">
        <TreatmentCostPanel
          treatments={woodTreatmentsQuote}
          selectedRows={quoteTreatments}
          setSelectedRows={setQuoteTreatments}
          toast={toast}
        />
      </Card>

      <Card title="Costi e margini" icon={Calculator} action={<button className="primary" onClick={calc}><Calculator /> Calcola preventivo</button>}>'''
        s = s.replace(marker, insert, 1)

    FRONTEND.write_text(s, encoding="utf-8")


def append_css():
    css = CSS.read_text(encoding="utf-8")
    if "v42.3.0 treatments and finishes" not in css:
        css += "\n\n" + CSS_PATCH.strip() + "\n"

    if ".form-grid-full" not in css:
        css += "\n\n.form-grid-full { grid-column: 1 / -1; }\n"

    CSS.write_text(css, encoding="utf-8")


def main():
    append_backend()
    patch_frontend()
    append_css()
    print("Patch v42.3.0 applicata: trattamenti/finiture in preventivi e schede prodotto.")

if __name__ == "__main__":
    main()
