from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


COMPONENT = r'''
function CatalogAdvancedSettings({ toast, refreshTax, refreshSug }) {
  const { data: areas, refresh: refreshAreas } = useApi('/catalog/areas', []);
  const { data: treatments, refresh: refreshTreatments } = useApi('/catalog/wood-treatments', []);
  const [areaName, setAreaName] = useState('');
  const [tr, setTr] = useState({ name: '', type: 'pacchetto', steps: 'Fondo + Colore + Trasparente', unit_cost: '', labor_hours: '', notes: '' });

  async function saveArea() {
    if (!areaName.trim()) { toast('Inserisci il nome area', 'err'); return; }

    try {
      await postJSON('/catalog/areas', { name: areaName.trim() });
      setAreaName('');
      toast('Area catalogo salvata');
      refreshAreas();
      refreshTax?.();
      refreshSug?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function removeArea(name) {
    if (!confirm(`Eliminare l'area "${name}"? Puoi eliminarla solo se non è usata.`)) return;

    try {
      await del('/catalog/areas/' + encodeURIComponent(name));
      toast('Area eliminata');
      refreshAreas();
      refreshTax?.();
      refreshSug?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function saveTreatment() {
    if (!tr.name.trim()) { toast('Inserisci il nome trattamento', 'err'); return; }

    const payload = {
      ...tr,
      steps: String(tr.steps || '').split('+').map(x => x.trim()).filter(Boolean),
      unit_cost: Number(tr.unit_cost || 0),
      labor_hours: Number(tr.labor_hours || 0),
    };

    try {
      await postJSON('/catalog/wood-treatments', payload);
      toast('Trattamento legno salvato');
      setTr({ name: '', type: 'pacchetto', steps: 'Fondo + Colore + Trasparente', unit_cost: '', labor_hours: '', notes: '' });
      refreshTreatments();
      refreshSug?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function removeTreatment(name) {
    if (!confirm(`Eliminare il trattamento "${name}"?`)) return;

    try {
      await del('/catalog/wood-treatments/' + encodeURIComponent(name));
      toast('Trattamento eliminato');
      refreshTreatments();
      refreshSug?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  return <div className="catalog-advanced-panel">
    <Card title="Aree catalogo" icon={Layers3} sub="Crea aree personalizzate oltre Falegnameria, Ferramenta e Illuminazione.">
      <div className="inline catalog-area-form">
        <input placeholder="Nuova area, es. Finiture, Packaging, Vernici..." value={areaName} onChange={e => setAreaName(e.target.value)} />
        <button className="primary" onClick={saveArea}><Plus /> Aggiungi area</button>
      </div>

      <div className="area-chip-list">
        {list(areas).map(a => <span key={a} className="area-chip">
          {a}
          <button title="Elimina area" onClick={() => removeArea(a)}><Trash2 /></button>
        </span>)}
      </div>
    </Card>

    <Card title="Trattamenti legno" icon={Sparkles} sub="Configura cicli di finitura semplici o pacchetti: mordente, smalto, fondo, trasparente, flatting.">
      <div className="form-grid treatment-form">
        <Input label="Nome trattamento" value={tr.name} onChange={e => setTr({ ...tr, name: e.target.value })} placeholder="Pacchetto smalto completo" />
        <Select label="Tipo" value={tr.type} onChange={e => setTr({ ...tr, type: e.target.value })}>
          <option value="semplice">Semplice</option>
          <option value="pacchetto">Pacchetto</option>
        </Select>
        <Input label="Fasi" value={tr.steps} onChange={e => setTr({ ...tr, steps: e.target.value })} placeholder="Fondo + Colore + Trasparente" />
        <Input label="Costo stimato €" type="number" step="0.01" value={tr.unit_cost} onChange={e => setTr({ ...tr, unit_cost: e.target.value })} />
        <Input label="Ore lavoro" type="number" step="0.01" value={tr.labor_hours} onChange={e => setTr({ ...tr, labor_hours: e.target.value })} />
        <Input label="Note" value={tr.notes} onChange={e => setTr({ ...tr, notes: e.target.value })} />
      </div>

      <div className="quick-actions">
        <button className="primary" onClick={saveTreatment}><Save /> Salva trattamento</button>
      </div>

      <div className="treatment-list">
        {list(treatments).map(t => <div key={t.name} className="treatment-row">
          <div>
            <b>{t.name}</b>
            <small>{[t.type, list(t.steps).join(' + ')].filter(Boolean).join(' · ') || '—'}</small>
            {t.notes && <em>{t.notes}</em>}
          </div>
          <div className="treatment-meta">
            <span>€ {Number(t.unit_cost || 0).toFixed(2)}</span>
            <span>{Number(t.labor_hours || 0).toFixed(2)} h</span>
            <button className="ghost danger" onClick={() => removeTreatment(t.name)}><Trash2 /></button>
          </div>
        </div>)}
      </div>
    </Card>
  </div>;
}

'''


CSS_BLOCK = r'''

/* v41.1 catalog areas wood treatments */
.catalog-advanced-panel {
  display: grid;
  grid-template-columns: minmax(0, .8fr) minmax(0, 1.2fr);
  gap: 18px;
  margin-bottom: 18px;
  align-items: start;
}

.catalog-area-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: end;
}

.area-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.area-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(148, 163, 184, .18);
  background: rgba(255,255,255,.055);
  border-radius: 999px;
  padding: 7px 9px 7px 12px;
  font-size: 12px;
  font-weight: 800;
  color: var(--text);
}

.area-chip button {
  width: 24px;
  height: 24px;
  min-height: 24px;
  padding: 0;
  border-radius: 999px;
  display: grid;
  place-items: center;
  color: #fecaca;
  background: rgba(239, 68, 68, .10);
  border-color: rgba(239, 68, 68, .22);
}

.area-chip svg {
  width: 13px;
  height: 13px;
}

.treatment-form {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.treatment-list {
  display: grid;
  gap: 9px;
  margin-top: 14px;
  max-height: 360px;
  overflow-y: auto;
  padding-right: 4px;
}

.treatment-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  border-radius: 16px;
  padding: 12px;
}

.treatment-row b,
.treatment-row small,
.treatment-row em {
  display: block;
  min-width: 0;
}

.treatment-row b {
  font-size: 13px;
  line-height: 1.25;
}

.treatment-row small {
  color: var(--muted);
  margin-top: 3px;
  line-height: 1.35;
}

.treatment-row em {
  color: var(--muted);
  opacity: .86;
  font-style: normal;
  font-size: 11px;
  margin-top: 4px;
}

.treatment-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.treatment-meta span {
  border-radius: 999px;
  background: rgba(5, 132, 130, .12);
  color: #99f6e4;
  border: 1px solid rgba(5, 132, 130, .25);
  padding: 6px 9px;
  font-size: 11px;
  font-weight: 900;
}

.treatment-meta button {
  width: 32px;
  height: 32px;
  min-height: 32px;
  padding: 0;
  display: grid;
  place-items: center;
}

@media (max-width: 1180px) {
  .catalog-advanced-panel {
    grid-template-columns: 1fr;
  }

  .treatment-form {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .catalog-area-form,
  .treatment-form,
  .treatment-row {
    grid-template-columns: 1fr;
  }

  .treatment-meta {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
'''


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    if "function CatalogAdvancedSettings" not in s:
      marker = "function Setup({ toast })"
      if marker not in s:
          raise RuntimeError("function Setup({ toast }) non trovata")
      s = s.replace(marker, COMPONENT + "\n" + marker, 1)

    if "<CatalogAdvancedSettings" not in s:
        setup_start = s.find("function Setup({ toast })")
        if setup_start == -1:
            raise RuntimeError("Setup non trovata")

        setup_end = s.find("\nfunction ", setup_start + 1)
        if setup_end == -1:
            setup_end = len(s)

        block = s[setup_start:setup_end]

        # Inserisce subito dopo return <>.
        if "return <>" in block:
            block = block.replace(
                "return <>",
                "return <>\n    <CatalogAdvancedSettings toast={toast} refreshTax={refreshTax} refreshSug={refreshSug} />",
                1
            )
        else:
            # fallback: prima del primo div principale dopo return
            raise RuntimeError("return <> dentro Setup non trovato")

        s = s[:setup_start] + block + s[setup_end:]

    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend v41.1.0b applicato")


def patch_css():
    css = CSS.read_text(encoding="utf-8")
    if "/* v41.1 catalog areas wood treatments */" not in css:
        css += CSS_BLOCK
        CSS.write_text(css, encoding="utf-8")
        print("CSS v41.1 applicato")
    else:
        print("CSS v41.1 già presente")


def main():
    patch_frontend()
    patch_css()
    print("Patch frontend fix v41.1.0b completata")


if __name__ == "__main__":
    main()
