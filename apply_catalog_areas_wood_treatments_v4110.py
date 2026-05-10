from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN = ROOT / "backend" / "app" / "main.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


BACKEND_CODE = r'''

# ---------------------------------------------------------------------------
# v41.1.0 - Aree catalogo personalizzabili + trattamenti legno
# ---------------------------------------------------------------------------

def default_catalog_areas():
    return ["Falegnameria", "Ferramenta", "Illuminazione", "Finiture"]


def get_catalog_areas(db):
    areas = db.setdefault("catalog_areas", [])

    # Migrazione morbida: integra le aree standard e quelle già ricavate dai dati.
    merged = []
    for x in default_catalog_areas() + list(areas) + list(raw_section_choices(db)):
        x = str(x or "").strip()
        if x and x not in merged:
            merged.append(x)

    db["catalog_areas"] = merged
    return merged


def add_catalog_area(db, payload):
    name = str((payload or {}).get("name", "")).strip()
    if not name:
        raise ValueError("Nome area obbligatorio")

    areas = get_catalog_areas(db)
    if name not in areas:
        areas.append(name)

    db["catalog_areas"] = areas
    return {"ok": True, "areas": areas}


def delete_catalog_area(db, name):
    name = str(name or "").strip()
    if not name:
        raise ValueError("Area non valida")

    # Non eliminare se usata in materiali/componenti/fornitori/categorie.
    used = False

    for section_key in ["materials", "components"]:
        for item in (db.get(section_key, {}) or {}).values():
            if isinstance(item, dict) and str(item.get("section", "")).strip() == name:
                used = True

    for supplier in (db.get("suppliers", {}) or {}).values():
        if isinstance(supplier, dict):
            if name in list(supplier.get("sections", []) or []):
                used = True
            for link in list(supplier.get("links", []) or []):
                if isinstance(link, dict) and str(link.get("section", "")).strip() == name:
                    used = True

    categories = db.get("categories", {}) or {}
    if name in categories:
        used = True

    if used:
        raise ValueError("Area già usata: non può essere eliminata")

    areas = [x for x in get_catalog_areas(db) if x != name]
    db["catalog_areas"] = areas

    # Se esiste come chiave vuota in categories, rimuovila.
    db.setdefault("categories", {}).pop(name, None)

    return {"ok": True, "areas": areas}


def get_wood_treatments(db):
    treatments = db.setdefault("wood_treatments", [])

    if not treatments:
        treatments.extend([
            {
                "name": "Nessuno",
                "type": "semplice",
                "steps": [],
                "unit_cost": 0,
                "labor_hours": 0,
                "notes": "Nessun trattamento applicato",
            },
            {
                "name": "Mordente + flatting ceroso",
                "type": "pacchetto",
                "steps": ["Mordente", "Flatting ceroso"],
                "unit_cost": 5,
                "labor_hours": 0.25,
                "notes": "Finitura effetto legno caldo/protetto",
            },
            {
                "name": "Fondo + colore + trasparente",
                "type": "pacchetto",
                "steps": ["Fondo", "Colore", "Trasparente"],
                "unit_cost": 8,
                "labor_hours": 0.4,
                "notes": "Pacchetto smalto completo",
            },
        ])

    return treatments


def save_wood_treatment(db, payload):
    payload = payload or {}

    name = str(payload.get("name", "")).strip()
    if not name:
        raise ValueError("Nome trattamento obbligatorio")

    treatment = {
        "name": name,
        "type": str(payload.get("type", "semplice") or "semplice").strip(),
        "steps": [str(x).strip() for x in payload.get("steps", []) if str(x).strip()] if isinstance(payload.get("steps"), list) else [x.strip() for x in str(payload.get("steps", "")).split("+") if x.strip()],
        "unit_cost": parse_float(payload.get("unit_cost")),
        "labor_hours": parse_float(payload.get("labor_hours")),
        "notes": str(payload.get("notes", "") or "").strip(),
    }

    treatments = get_wood_treatments(db)

    for i, existing in enumerate(treatments):
        if str(existing.get("name", "")).strip().lower() == name.lower():
            treatments[i] = {**existing, **treatment}
            db["wood_treatments"] = treatments
            return {"ok": True, "treatment": treatments[i], "updated": True}

    treatments.append(treatment)
    db["wood_treatments"] = treatments
    return {"ok": True, "treatment": treatment, "created": True}


def delete_wood_treatment(db, name):
    name = str(name or "").strip()
    if not name:
        raise ValueError("Trattamento non valido")

    if name.lower() == "nessuno":
        raise ValueError("Il trattamento 'Nessuno' non può essere eliminato")

    treatments = get_wood_treatments(db)
    treatments = [t for t in treatments if str(t.get("name", "")).strip() != name]
    db["wood_treatments"] = treatments

    return {"ok": True, "treatments": treatments}
'''


API_CODE = r'''

@app.get("/api/catalog/areas")
def catalog_areas_api():
    return get_catalog_areas(load_db())


@app.post("/api/catalog/areas")
def add_catalog_area_api(payload: Payload):
    def fn(db):
        return add_catalog_area(db, payload.data)
    return mutate(fn)


@app.delete("/api/catalog/areas/{name:path}")
def delete_catalog_area_api(name: str):
    def fn(db):
        return delete_catalog_area(db, name)
    return mutate(fn)


@app.get("/api/catalog/wood-treatments")
def wood_treatments_api():
    return get_wood_treatments(load_db())


@app.post("/api/catalog/wood-treatments")
def save_wood_treatment_api(payload: Payload):
    def fn(db):
        return save_wood_treatment(db, payload.data)
    return mutate(fn)


@app.delete("/api/catalog/wood-treatments/{name:path}")
def delete_wood_treatment_api(name: str):
    def fn(db):
        return delete_wood_treatment(db, name)
    return mutate(fn)
'''


def append_once(path: Path, marker: str, code: str):
    s = path.read_text(encoding="utf-8")
    if marker not in s:
        s += "\n\n" + code.strip() + "\n"
        path.write_text(s, encoding="utf-8")


def patch_backend():
    append_once(LEGACY, "def get_catalog_areas", BACKEND_CODE)
    append_once(MAIN, "def catalog_areas_api", API_CODE)

    s = MAIN.read_text(encoding="utf-8")

    # /options: sostituisce raw_section_choices con get_catalog_areas dove possibile.
    s = s.replace('"raw_sections": raw_section_choices(db)', '"raw_sections": get_catalog_areas(db)')
    s = s.replace("'raw_sections': raw_section_choices(db)", "'raw_sections': get_catalog_areas(db)")

    MAIN.write_text(s, encoding="utf-8")
    print("Backend aree catalogo + trattamenti legno applicato.")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    # Inserisce componente gestione aree/trattamenti prima di Setup.
    if "function CatalogAdvancedSettings" not in s:
        component = r'''
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
        s = s.replace("function Setup({ toast })", component + "\nfunction Setup({ toast })", 1)

    # Inserisce il pannello avanzato dentro Setup, subito dopo PageTitle.
    if "<CatalogAdvancedSettings" not in s:
        target = '<PageTitle title="Categorie"'
        idx = s.find(target)
        if idx == -1:
            raise RuntimeError("PageTitle Categorie non trovato")

        # inserisce dopo la riga PageTitle completa
        end_line = s.find("\n", idx)
        insert = "\n    <CatalogAdvancedSettings toast={toast} refreshTax={refreshTax} refreshSug={refreshSug} />"
        s = s[:end_line] + insert + s[end_line:]

    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend aree catalogo + trattamenti legno applicato.")


def patch_css():
    css = CSS.read_text(encoding="utf-8")

    if "/* v41.1 catalog areas wood treatments */" not in css:
        css += r'''

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
        CSS.write_text(css, encoding="utf-8")
        print("CSS aree catalogo + trattamenti legno applicato.")


def main():
    patch_backend()
    patch_frontend()
    patch_css()
    print("Patch v41.1.0 completata: aree personalizzabili + trattamenti legno.")


if __name__ == "__main__":
    main()
