from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


NEW_FIND_MATERIAL_VARIANTS = r'''
def find_material_variants(db, item_name, needed_qty=0):
    item, table, key = get_raw_item(db, item_name)
    if not item:
        return []

    category = item.get("category", "")
    subcategory = item.get("subcategory", "")
    size = item.get("size", "")
    thickness = item.get("thickness", "")
    section = item.get("section", "")

    candidates = []

    for table_name in ("materials", "components"):
        for cand_key, info in db.get(table_name, {}).items():
            if cand_key == key:
                continue

            if not isinstance(info, dict):
                continue

            stock = parse_float(info.get("stock"))
            if stock <= 0:
                continue

            cand_category = info.get("category", "")
            cand_subcategory = info.get("subcategory", "")
            cand_size = info.get("size", "")
            cand_thickness = info.get("thickness", "")
            cand_section = info.get("section", "")

            same_section = section and cand_section == section
            same_category = category and cand_category == category
            same_sub = subcategory and cand_subcategory == subcategory
            same_size = size and cand_size == size
            same_thick = thickness and cand_thickness == thickness

            # Non mischiare aree/categorie senza logica.
            # Esempio: Legname può proporre Pioppo/MDF/Betulla, ma non LED/12V.
            if category == "Legname":
                if cand_category != "Legname":
                    continue
            else:
                # Per componenti/illuminazione serve almeno stessa categoria,
                # oppure stessa area + sottocategoria molto simile.
                if not same_category:
                    continue

            score = 0
            notes = []

            if same_section:
                score += 2
                notes.append("stessa area")

            if same_category:
                score += 8
                notes.append("stessa categoria")

            if same_sub:
                score += 8
                notes.append("stessa sottocategoria/essenza")
            elif cand_subcategory:
                score += 2
                notes.append(f"alternativa: {cand_subcategory}")

            if same_size:
                score += 6
                notes.append("stesso formato")
            elif cand_size:
                score += 1
                notes.append(f"formato diverso: {cand_size}")

            if same_thick:
                score += 6
                notes.append("stesso spessore")
            elif cand_thickness:
                score += 1
                notes.append(f"spessore diverso: {cand_thickness}")

            if stock >= needed_qty:
                score += 5
                notes.append("stock sufficiente")
            else:
                notes.append("stock parziale")

            # Priorità esempi:
            # Betulla 4 mancante → Pioppo 4 molto alto
            # Betulla 4 mancante → Betulla 6 alto
            # Betulla 4 mancante → Pioppo 6 medio
            if category == "Legname":
                if same_size and same_thick:
                    score += 8
                elif same_sub and same_size:
                    score += 5
                elif same_size or same_thick:
                    score += 3

            unit_cost = parse_float(info.get("weighted_average_cost", info.get("cost_per_unit")))

            candidates.append({
                "key": cand_key,
                "table": table_name,
                "name": display_name_from_key(cand_key, info),
                "stock": stock,
                "unit": info.get("unit", ""),
                "category": cand_category,
                "subcategory": cand_subcategory,
                "size": cand_size,
                "thickness": cand_thickness,
                "supplier": info.get("supplier", ""),
                "unit_cost": unit_cost,
                "score": score,
                "can_cover": stock >= needed_qty,
                "notes": ", ".join(notes),
            })

    return sorted(
        candidates,
        key=lambda x: (
            x.get("can_cover", False),
            x.get("score", 0),
            x.get("stock", 0)
        ),
        reverse=True
    )[:10]
'''


NEW_PRODUCTION_BOX = r'''function ProductionBox({ products, refresh, toast }) {
  const [name, setName] = useState('');
  const [qty, setQty] = useState(1);
  const [check, setCheck] = useState(null);
  const [substitutions, setSubstitutions] = useState({});

  async function checkNow() {
    if (!name) return;
    try {
      const result = await postJSON(`/products/${encodeURIComponent(name)}/check-production`, { qty });
      setCheck(result);
      setSubstitutions({});
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function produce() {
    if (!name) return;

    try {
      await postJSON(`/products/${encodeURIComponent(name)}/produce`, {
        qty,
        substitutions
      });

      toast('Produzione completata');
      setCheck(null);
      setSubstitutions({});
      refresh();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  const rows = list(check?.rows);
  const missingRows = rows.filter(r => !r.ok);
  const allResolved = !missingRows.length || missingRows.every(r => substitutions[String(r.index)]);

  function chooseVariant(row, variant) {
    setSubstitutions(v => ({
      ...v,
      [String(row.index)]: {
        table: variant.table,
        key: variant.key,
        name: variant.name
      }
    }));
  }

  function clearVariant(row) {
    setSubstitutions(v => {
      const next = { ...v };
      delete next[String(row.index)];
      return next;
    });
  }

  return <div className="production-panel">
    <div className="inline">
      <select value={name} onChange={e => { setName(e.target.value); setCheck(null); setSubstitutions({}); }}>
        <option value="">Scegli prodotto</option>
        {list(products).map(p => <option key={p.name}>{p.name}</option>)}
      </select>
      <input type="number" step="0.01" value={qty} onChange={e => setQty(e.target.value)} />
      <button onClick={checkNow}><Search /> Verifica</button>
      <button className="primary" onClick={produce} disabled={check && !allResolved}>
        <Hammer /> Produci
      </button>
    </div>

    {check && <div className={check.can_produce ? 'notice ok' : 'notice warn'}>
      {check.can_produce ? <CheckCircle2 /> : <AlertTriangle />}
      {check.can_produce
        ? 'Materiali sufficienti per produrre.'
        : allResolved
          ? 'Materiali mancanti risolti con alternative selezionate. Puoi produrre.'
          : 'Alcuni materiali risultano insufficienti. Scegli una sostituzione logica.'}
    </div>}

    {rows.length > 0 && <div className="production-check-list">
      {rows.map(row => {
        const selected = substitutions[String(row.index)];

        return <div key={row.index} className={row.ok ? 'production-row ok' : 'production-row missing'}>
          <div className="production-row-head">
            <div>
              <b>{row.name}</b>
              <small>
                Richiesto: {num(row.needed)} {row.unit || ''} · Disponibile: {num(row.available)} {row.unit || ''}
              </small>
            </div>
            {row.ok
              ? <span className="quote-status accepted">Disponibile</span>
              : selected
                ? <span className="quote-status sent">Sostituito</span>
                : <span className="quote-status rejected">Mancante</span>}
          </div>

          {!row.ok && <div className="variant-panel">
            {selected && <div className="selected-variant">
              <span>Alternativa selezionata</span>
              <b>{selected.name}</b>
              <button className="ghost" onClick={() => clearVariant(row)}>Cambia</button>
            </div>}

            {!selected && <>
              <h4>Alternative consigliate</h4>
              {list(row.variants).length ? <div className="variant-grid">
                {list(row.variants).map(v => <button key={v.table + v.key} type="button" className="variant-card" onClick={() => chooseVariant(row, v)}>
                  <div>
                    <b>{v.name}</b>
                    <small>{[v.category, v.subcategory, v.size, v.thickness].filter(Boolean).join(' · ')}</small>
                  </div>
                  <span>{num(v.stock)} {v.unit || ''}</span>
                  <em>{v.notes}</em>
                  <strong>{v.can_cover ? 'Copre produzione' : 'Stock parziale'}</strong>
                </button>)}
              </div> : <Empty text="Nessuna alternativa logica trovata" />}
            </>}
          </div>}
        </div>;
      })}
    </div>}
  </div>;
}'''


def replace_function(source: str, function_name: str, new_code: str) -> str:
    pattern = rf"^def {function_name}\(.*?\):\n(?:(?:    .*\n)|(?:\n))*"
    match = re.search(pattern, source, flags=re.MULTILINE)

    if not match:
      raise RuntimeError(f"Funzione backend non trovata: {function_name}")

    return source[:match.start()] + new_code.rstrip() + "\n\n" + source[match.end():]


def replace_frontend_function(source: str, name: str, new_code: str, next_name: str) -> str:
    start = source.find(f"function {name}")
    end = source.find(f"\nfunction {next_name}", start)

    if start == -1 or end == -1:
        raise RuntimeError(f"Funzione frontend non trovata: {name}")

    return source[:start] + new_code.rstrip() + "\n\n" + source[end + 1:]


def main():
    s = LEGACY.read_text(encoding="utf-8")
    s = replace_function(s, "find_material_variants", NEW_FIND_MATERIAL_VARIANTS)
    LEGACY.write_text(s, encoding="utf-8")
    print("Backend alternative produzione aggiornato.")

    f = FRONTEND.read_text(encoding="utf-8")
    f = replace_frontend_function(f, "ProductionBox", NEW_PRODUCTION_BOX, "ProductWarehouse")
    FRONTEND.write_text(f, encoding="utf-8")
    print("Frontend alternative produzione aggiornato.")

    css = CSS.read_text(encoding="utf-8")
    if "/* v39.9 production alternatives */" not in css:
        css += """

/* v39.9 production alternatives */
.production-check-list {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.production-row {
  border: 1px solid rgba(148, 163, 184, .18);
  border-radius: 18px;
  padding: 14px;
  background: rgba(255,255,255,.045);
}

.production-row.ok {
  border-color: rgba(34,197,94,.24);
}

.production-row.missing {
  border-color: rgba(239,68,68,.28);
}

.production-row-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
}

.production-row-head b {
  display: block;
  font-size: 14px;
}

.production-row-head small {
  display: block;
  margin-top: 4px;
  color: var(--muted);
}

.variant-panel {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(148, 163, 184, .16);
}

.variant-panel h4 {
  margin: 0 0 10px;
  font-size: 13px;
}

.variant-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.variant-card {
  text-align: left;
  display: grid;
  gap: 8px;
  border: 1px solid rgba(148, 163, 184, .22);
  border-radius: 16px;
  padding: 12px;
  background: rgba(255,255,255,.055);
  color: inherit;
  cursor: pointer;
}

.variant-card:hover {
  border-color: rgba(34, 211, 238, .48);
  background: rgba(34, 211, 238, .09);
}

.variant-card b {
  display: block;
  font-size: 13px;
}

.variant-card small,
.variant-card em {
  display: block;
  color: var(--muted);
  font-size: 11px;
  font-style: normal;
}

.variant-card span {
  font-weight: 900;
}

.variant-card strong {
  color: #86efac;
  font-size: 11px;
}

.selected-variant {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: center;
  border-radius: 14px;
  background: rgba(59, 130, 246, .10);
  border: 1px solid rgba(59, 130, 246, .25);
  padding: 10px;
}

.selected-variant span {
  grid-column: 1 / -1;
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .06em;
}

@media (max-width: 900px) {
  .variant-grid {
    grid-template-columns: 1fr;
  }

  .production-row-head {
    flex-direction: column;
  }
}
"""
        CSS.write_text(css, encoding="utf-8")
        print("CSS alternative produzione aggiunto.")

    print("Patch v39.9.0 produzione con alternative completata.")


if __name__ == "__main__":
    main()
