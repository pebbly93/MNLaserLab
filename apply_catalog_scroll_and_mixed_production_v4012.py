from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


NEW_PRODUCE_PRODUCT = r'''
def produce_product(db, product_name, qty, substitutions=None):
    substitutions = substitutions or {}
    check = production_check(db, product_name, qty)
    deductions = []

    for row in check["rows"]:
        if row["ok"]:
            deductions.append((row["table"], row["key"], row["needed"]))
            continue

        sub = substitutions.get(str(row["index"])) or substitutions.get(row["index"])

        if not sub:
            raise ValueError(f"Materiale mancante non risolto: {row['name']}")

        # v40.1.2: supporto produzione mista.
        # Accetta:
        # substitutions[index] = {"table": "...", "key": "..."}             vecchio modo
        # substitutions[index] = {"mix": [{"table": "...", "key": "...", "qty": 1}, ...]}
        if isinstance(sub, dict) and isinstance(sub.get("mix"), list):
            total_mix = 0.0
            for part in sub.get("mix", []):
                part_qty = parse_float(part.get("qty"))
                if part_qty <= 0:
                    continue
                deductions.append((part.get("table"), part.get("key"), part_qty))
                total_mix += part_qty

            if total_mix + 0.000001 < parse_float(row["needed"]):
                raise ValueError(
                    f"Sostituzione parziale insufficiente per {row['name']}: "
                    f"richiesto {row['needed']:.2f}, coperto {total_mix:.2f}"
                )
        else:
            deductions.append((sub["table"], sub["key"], row["needed"]))

    for table, key, need in deductions:
        if table not in db or key not in db.get(table, {}):
            raise ValueError(f"Materiale non trovato: {key}")
        if parse_float(db[table][key].get("stock")) + 0.000001 < need:
            raise ValueError(
                f"Stock insufficiente per {display_name_from_key(key, db[table][key])}: "
                f"disponibile {parse_float(db[table][key].get('stock')):.2f}, richiesto {need:.2f}"
            )

    for table, key, need in deductions:
        db[table][key]["stock"] = parse_float(db[table][key].get("stock")) - need

    db["products"][product_name]["stock"] = parse_float(db["products"][product_name].get("stock")) + qty

    return {
        "ok": True,
        "deductions": deductions,
        "new_stock": db["products"][product_name]["stock"]
    }
'''


NEW_PRODUCTION_BOX = r'''function ProductionBox({ products, refresh, toast }) {
  const [name, setName] = useState('');
  const [qty, setQty] = useState(1);
  const [check, setCheck] = useState(null);
  const [substitutions, setSubstitutions] = useState({});
  const [mixDrafts, setMixDrafts] = useState({});

  async function checkNow() {
    if (!name) return;
    try {
      const result = await postJSON(`/products/${encodeURIComponent(name)}/check-production`, { qty });
      setCheck(result);
      setSubstitutions({});
      setMixDrafts({});
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
      setMixDrafts({});
      refresh();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  const rows = list(check?.rows);
  const missingRows = rows.filter(r => !r.ok);
  const isResolved = row => {
    const sub = substitutions[String(row.index)];
    if (!sub) return false;
    if (Array.isArray(sub.mix)) {
      const total = sub.mix.reduce((a, x) => a + Number(x.qty || 0), 0);
      return total + 0.000001 >= Number(row.needed || 0);
    }
    return true;
  };
  const allResolved = !missingRows.length || missingRows.every(isResolved);

  function originalPart(row) {
    const available = Number(row.available || 0);
    const needed = Number(row.needed || 0);
    const qtyUse = Math.max(0, Math.min(available, needed));
    if (qtyUse <= 0) return null;
    return {
      table: row.table,
      key: row.key,
      name: row.name,
      qty: qtyUse,
      original: true
    };
  }

  function chooseVariant(row, variant) {
    const needed = Number(row.needed || 0);
    const part = originalPart(row);
    const remaining = Math.max(0, needed - Number(part?.qty || 0));
    const variantQty = Math.min(Number(variant.stock || 0), remaining || needed);

    const mix = [];
    if (part) mix.push(part);
    mix.push({
      table: variant.table,
      key: variant.key,
      name: variant.name,
      qty: variantQty
    });

    setSubstitutions(v => ({
      ...v,
      [String(row.index)]: {
        mix
      }
    }));
  }

  function setMixQty(row, partIndex, value) {
    const key = String(row.index);
    const current = substitutions[key];
    if (!current?.mix) return;

    const nextMix = current.mix.map((part, i) => i === partIndex ? { ...part, qty: Number(value || 0) } : part);

    setSubstitutions(v => ({
      ...v,
      [key]: {
        mix: nextMix
      }
    }));
  }

  function addVariantToMix(row, variant) {
    const key = String(row.index);
    const current = substitutions[key]?.mix || [];
    const exists = current.some(x => x.table === variant.table && x.key === variant.key);

    if (exists) {
      toast('Alternativa già presente nel mix', 'err');
      return;
    }

    const covered = current.reduce((a, x) => a + Number(x.qty || 0), 0);
    const remaining = Math.max(0, Number(row.needed || 0) - covered);
    const qtyToUse = Math.min(Number(variant.stock || 0), remaining || 1);

    setSubstitutions(v => ({
      ...v,
      [key]: {
        mix: [
          ...current,
          {
            table: variant.table,
            key: variant.key,
            name: variant.name,
            qty: qtyToUse
          }
        ]
      }
    }));
  }

  function removeMixPart(row, partIndex) {
    const key = String(row.index);
    const current = substitutions[key]?.mix || [];
    const nextMix = current.filter((_, i) => i !== partIndex);

    setSubstitutions(v => ({
      ...v,
      [key]: nextMix.length ? { mix: nextMix } : undefined
    }));
  }

  function clearVariant(row) {
    setSubstitutions(v => {
      const next = { ...v };
      delete next[String(row.index)];
      return next;
    });
  }

  function mixTotal(row) {
    const sub = substitutions[String(row.index)];
    return list(sub?.mix).reduce((a, x) => a + Number(x.qty || 0), 0);
  }

  function mixRemaining(row) {
    return Math.max(0, Number(row.needed || 0) - mixTotal(row));
  }

  return <div className="production-panel">
    <div className="inline">
      <select value={name} onChange={e => { setName(e.target.value); setCheck(null); setSubstitutions({}); setMixDrafts({}); }}>
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
          : 'Alcuni materiali risultano insufficienti. Scegli una sostituzione logica o crea un mix.'}
    </div>}

    {rows.length > 0 && <div className="production-check-list">
      {rows.map(row => {
        const selected = substitutions[String(row.index)];
        const total = mixTotal(row);
        const remaining = mixRemaining(row);

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
                ? <span className={remaining <= 0 ? 'quote-status accepted' : 'quote-status sent'}>{remaining <= 0 ? 'Risolto' : 'Parziale'}</span>
                : <span className="quote-status rejected">Mancante</span>}
          </div>

          {!row.ok && <div className="variant-panel">
            {selected?.mix && <div className="mixed-production-box">
              <div className="mixed-production-head">
                <div>
                  <span>Mix produzione</span>
                  <b>{num(total)} / {num(row.needed)} {row.unit || ''}</b>
                  <small>{remaining > 0 ? `Mancano ancora ${num(remaining)} ${row.unit || ''}` : 'Quantità coperta'}</small>
                </div>
                <button className="ghost" onClick={() => clearVariant(row)}>Svuota mix</button>
              </div>

              <div className="mix-lines">
                {selected.mix.map((part, i) => <div className="mix-line" key={i}>
                  <div>
                    <b>{part.name}</b>
                    <small>{part.original ? 'materiale originale disponibile' : 'alternativa selezionata'}</small>
                  </div>
                  <input type="number" step="0.01" value={part.qty} onChange={e => setMixQty(row, i, e.target.value)} />
                  <button className="ghost danger" onClick={() => removeMixPart(row, i)}>×</button>
                </div>)}
              </div>
            </div>}

            <h4>Alternative consigliate in base a categoria, formato, spessore e stock</h4>
            {list(row.variants).length ? <div className="variant-grid">
              {list(row.variants).map(v => <button key={v.table + v.key} type="button" className="variant-card" onClick={() => selected?.mix ? addVariantToMix(row, v) : chooseVariant(row, v)}>
                <div>
                  <b>{v.name}</b>
                  <small>{[v.category, v.subcategory, v.size, v.thickness].filter(Boolean).join(' · ')}</small>
                </div>
                <span>Stock: {num(v.stock)} {v.unit || ''}</span>
                <em>{v.notes}</em>
                <strong>{v.can_cover ? 'Copre produzione' : 'Stock parziale'}</strong>
              </button>)}
            </div> : <Empty text="Nessuna alternativa logica trovata" />}
          </div>}
        </div>;
      })}
    </div>}
  </div>;
}'''


def replace_frontend_function(source: str, name: str, new_code: str, next_name: str) -> str:
    start = source.find(f"function {name}")
    end = source.find(f"\nfunction {next_name}", start)

    if start == -1 or end == -1:
        raise RuntimeError(f"Funzione frontend non trovata: {name}")

    return source[:start] + new_code.rstrip() + "\n\n" + source[end + 1:]


def replace_backend_function(source: str, name: str, new_code: str) -> str:
    start = source.find(f"def {name}(")
    if start == -1:
        raise RuntimeError(f"Funzione backend non trovata: {name}")

    next_def = source.find("\ndef ", start + 1)
    if next_def == -1:
        next_def = len(source)

    return source[:start] + new_code.rstrip() + "\n\n" + source[next_def + 1:]


def main():
    s = LEGACY.read_text(encoding="utf-8")
    s = replace_backend_function(s, "produce_product", NEW_PRODUCE_PRODUCT)
    LEGACY.write_text(s, encoding="utf-8")
    print("Backend produzione mista aggiornato.")

    f = FRONTEND.read_text(encoding="utf-8")
    f = replace_frontend_function(f, "ProductionBox", NEW_PRODUCTION_BOX, "ProductWarehouse")
    FRONTEND.write_text(f, encoding="utf-8")
    print("Frontend produzione mista aggiornato.")

    css = CSS.read_text(encoding="utf-8")
    if "/* v40.1.2 linked config scroll and mixed production */" not in css:
        css += """

/* v40.1.2 linked config scroll and mixed production */

/* Colonna 4 più alta e realmente scorrevole */
.catalog-linked {
  max-height: calc(100vh - 230px);
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 10px;
}

.catalog-linked .catalog-config-card {
  margin-bottom: 12px;
}

.catalog-linked .pill-list {
  max-height: 210px;
}

/* Desktop larghi: diamo più spazio alla configurazione collegata */
@media (min-width: 1281px) {
  .catalog-workbench {
    grid-template-columns:
      minmax(165px, .62fr)
      minmax(220px, .92fr)
      minmax(220px, .92fr)
      minmax(360px, 1.55fr);
  }

  .catalog-linked {
    min-height: calc(100vh - 270px);
  }
}

/* Produzione mista */
.mixed-production-box {
  display: grid;
  gap: 12px;
  border: 1px solid rgba(59, 130, 246, .26);
  background: rgba(59, 130, 246, .09);
  border-radius: 18px;
  padding: 12px;
}

.mixed-production-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
}

.mixed-production-head span {
  display: block;
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .06em;
}

.mixed-production-head b {
  display: block;
  font-size: 16px;
  margin-top: 3px;
}

.mixed-production-head small {
  display: block;
  color: var(--muted);
  margin-top: 3px;
}

.mix-lines {
  display: grid;
  gap: 8px;
}

.mix-line {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 120px 36px;
  gap: 8px;
  align-items: center;
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.055);
  border-radius: 14px;
  padding: 9px;
}

.mix-line b,
.mix-line small {
  display: block;
  min-width: 0;
}

.mix-line b {
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mix-line small {
  color: var(--muted);
  font-size: 11px;
}

.mix-line input {
  min-height: 36px;
  text-align: right;
}

.mix-line button {
  width: 36px;
  height: 36px;
  min-height: 36px;
  padding: 0;
  display: grid;
  place-items: center;
}

@media (max-width: 800px) {
  .mixed-production-head,
  .mix-line {
    grid-template-columns: 1fr;
  }

  .mix-line input {
    text-align: left;
  }
}
"""
        CSS.write_text(css, encoding="utf-8")
        print("CSS v40.1.2 aggiunto.")

    print("Patch v40.1.2 completata.")


if __name__ == "__main__":
    main()
