from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


AREA_COMPONENT = r'''
function CatalogAreaInlineManager({ toast, refreshTax, refreshSug }) {
  const { data: areas, refresh: refreshAreas } = useApi('/catalog/areas', []);
  const [areaName, setAreaName] = useState('');

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

  return <div className="catalog-inline-area-manager">
    <div className="catalog-inline-title">
      <b>Gestisci aree</b>
      <small>Aggiungi ambiti come Finiture, Packaging o Vernici.</small>
    </div>

    <div className="catalog-inline-area-form">
      <input
        placeholder="Nuova area..."
        value={areaName}
        onChange={e => setAreaName(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter') saveArea(); }}
      />
      <button className="primary" onClick={saveArea}><Plus /></button>
    </div>

    <div className="area-chip-list compact">
      {list(areas).map(a => <span key={a} className="area-chip">
        {a}
        <button title="Elimina area" onClick={() => removeArea(a)}><Trash2 /></button>
      </span>)}
    </div>
  </div>;
}

'''


def replace_catalog_advanced_component(s: str) -> str:
    """
    Trasforma CatalogAdvancedSettings:
    prima conteneva Aree + Trattamenti.
    Ora deve contenere SOLO Trattamenti legno.
    """
    start = s.find("function CatalogAdvancedSettings")
    if start == -1:
        return s

    end = s.find("\nfunction Setup({ toast })", start)
    if end == -1:
        raise RuntimeError("Fine CatalogAdvancedSettings non trovata")

    old = s[start:end]

    # Ricostruisce il componente mantenendo solo logica trattamenti.
    new = r'''
function CatalogAdvancedSettings({ toast, refreshSug }) {
  const { data: treatments, refresh: refreshTreatments } = useApi('/catalog/wood-treatments', []);
  const [tr, setTr] = useState({ name: '', type: 'pacchetto', steps: 'Fondo + Colore + Trasparente', unit_cost: '', labor_hours: '', notes: '' });

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

  return <div className="catalog-treatments-section">
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
    return s[:start] + new.strip() + "\n\n" + s[end:]


def insert_area_component_definition(s: str) -> str:
    if "function CatalogAreaInlineManager" in s:
        return s

    marker = "function CatalogAdvancedSettings"
    idx = s.find(marker)
    if idx == -1:
        raise RuntimeError("CatalogAdvancedSettings non trovato per inserire CatalogAreaInlineManager")

    return s[:idx] + AREA_COMPONENT + "\n" + s[idx:]


def move_treatments_below_catalog(s: str) -> str:
    setup_start = s.find("function Setup({ toast })")
    if setup_start == -1:
        raise RuntimeError("Setup non trovata")

    setup_end = s.find("\nfunction ", setup_start + 1)
    if setup_end == -1:
        setup_end = len(s)

    block = s[setup_start:setup_end]

    widget_old = "    <CatalogAdvancedSettings toast={toast} refreshTax={refreshTax} refreshSug={refreshSug} />"
    widget_new = "    <CatalogAdvancedSettings toast={toast} refreshSug={refreshSug} />"

    # Rimuove il pannello trattamenti da sopra.
    block = block.replace("\n" + widget_old, "")
    block = block.replace("\n" + widget_new, "")
    block = block.replace(widget_old + "\n", "")
    block = block.replace(widget_new + "\n", "")

    # Inserisce trattamenti prima della chiusura del fragment, quindi sotto gestione catalogo.
    last_fragment_close = block.rfind("</>;")
    if last_fragment_close == -1:
        raise RuntimeError("Chiusura fragment Setup non trovata")

    block = block[:last_fragment_close] + "\n    <CatalogAdvancedSettings toast={toast} refreshSug={refreshSug} />\n  " + block[last_fragment_close:]

    return s[:setup_start] + block + s[setup_end:]


def insert_inline_area_manager_in_area_column(s: str) -> str:
    setup_start = s.find("function Setup({ toast })")
    if setup_start == -1:
        raise RuntimeError("Setup non trovata")

    setup_end = s.find("\nfunction ", setup_start + 1)
    if setup_end == -1:
        setup_end = len(s)

    block = s[setup_start:setup_end]

    if "<CatalogAreaInlineManager" in block:
        return s

    insert = '          <CatalogAreaInlineManager toast={toast} refreshTax={refreshTax} refreshSug={refreshSug} />'

    # Cerca il punto più probabile: subito dopo titolo "Aree" / "Ambito del materiale".
    patterns = [
        r'(<h3>\s*Aree\s*</h3>\s*<small>[^<]*Ambito del materiale[^<]*</small>)',
        r'(<b>\s*Aree\s*</b>\s*<small>[^<]*Ambito del materiale[^<]*</small>)',
        r'(Ambito del materiale</small>)',
        r'(Ambito del materiale</span>)',
    ]

    for pat in patterns:
        m = re.search(pat, block, flags=re.DOTALL)
        if m:
            pos = m.end()
            block = block[:pos] + "\n" + insert + block[pos:]
            return s[:setup_start] + block + s[setup_end:]

    # Fallback: inserisce prima del primo elenco area, cercando Falegnameria.
    idx = block.find("Falegnameria")
    if idx != -1:
        line_start = block.rfind("\n", 0, idx)
        block = block[:line_start] + "\n" + insert + block[line_start:]
        return s[:setup_start] + block + s[setup_end:]

    raise RuntimeError("Non ho trovato il punto dove inserire il gestore aree nella colonna Aree")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    s = replace_catalog_advanced_component(s)
    s = insert_area_component_definition(s)
    s = move_treatments_below_catalog(s)
    s = insert_inline_area_manager_in_area_column(s)

    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend: aree integrate nella colonna Aree, trattamenti spostati sotto.")


def patch_css():
    css = CSS.read_text(encoding="utf-8")

    if "/* v41.1.2 integrated catalog layout */" not in css:
        css += r'''

/* v41.1.2 integrated catalog layout */

/* Il pannello avanzato non deve stare sopra al titolo pagina */
.catalog-advanced-panel {
  display: none !important;
}

/* Trattamenti sotto la gestione catalogo */
.catalog-treatments-section {
  margin-top: 22px;
}

/* Gestore aree integrato nella colonna 1 */
.catalog-inline-area-manager {
  margin: 12px 0 14px;
  padding: 12px;
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  border-radius: 18px;
}

.catalog-inline-title {
  margin-bottom: 10px;
}

.catalog-inline-title b,
.catalog-inline-title small {
  display: block;
}

.catalog-inline-title b {
  font-size: 12px;
  letter-spacing: .04em;
  text-transform: uppercase;
  color: var(--text);
}

.catalog-inline-title small {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.35;
  margin-top: 2px;
}

.catalog-inline-area-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 42px;
  gap: 8px;
  align-items: center;
}

.catalog-inline-area-form input {
  min-height: 40px;
}

.catalog-inline-area-form button {
  width: 42px;
  height: 40px;
  min-height: 40px;
  padding: 0;
  display: grid;
  place-items: center;
  border-radius: 14px;
}

.catalog-inline-area-form svg {
  width: 17px;
  height: 17px;
}

.area-chip-list.compact {
  margin-top: 10px;
  gap: 6px;
  max-height: 96px;
  overflow-y: auto;
  padding-right: 3px;
}

.area-chip-list.compact .area-chip {
  font-size: 11px;
  padding: 6px 7px 6px 9px;
}

.area-chip-list.compact .area-chip button {
  width: 21px;
  height: 21px;
  min-height: 21px;
}

/* Gestione catalogo più allineata */
.catalog-board,
.catalog-grid,
.setup-catalog-grid,
.category-manager-grid {
  align-items: stretch !important;
}

.catalog-board > *,
.catalog-grid > *,
.setup-catalog-grid > *,
.category-manager-grid > * {
  min-height: 0;
}

/* Colonna 4: scroll interno vero */
.catalog-board > *:nth-child(4),
.catalog-grid > *:nth-child(4),
.setup-catalog-grid > *:nth-child(4),
.category-manager-grid > *:nth-child(4) {
  max-height: 640px !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
}

/* Colonne più ordinate */
.catalog-board .card,
.catalog-grid .card,
.setup-catalog-grid .card,
.category-manager-grid .card {
  height: 100%;
}

/* Trattamenti più larghi e sotto */
.catalog-treatments-section .card {
  overflow: hidden;
}

.catalog-treatments-section .treatment-list {
  max-height: 300px;
}

/* Mobile */
@media (max-width: 900px) {
  .catalog-inline-area-form {
    grid-template-columns: 1fr;
  }

  .catalog-inline-area-form button {
    width: 100%;
  }

  .area-chip-list.compact {
    max-height: none;
  }

  .catalog-board > *:nth-child(4),
  .catalog-grid > *:nth-child(4),
  .setup-catalog-grid > *:nth-child(4),
  .category-manager-grid > *:nth-child(4) {
    max-height: none !important;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")
        print("CSS: layout categorie integrato applicato.")


def main():
    patch_frontend()
    patch_css()
    print("Patch v41.1.2 completata.")


if __name__ == "__main__":
    main()
