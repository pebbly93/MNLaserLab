from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


AREA_SECTION = r'''
function CatalogAreasSection({ toast, refreshTax, refreshSug }) {
  const { data: areas, refresh: refreshAreas } = useApi('/catalog/areas', []);
  const [areaName, setAreaName] = useState('');

  async function saveArea() {
    const name = areaName.trim();
    if (!name) {
      toast('Inserisci il nome area', 'err');
      return;
    }

    try {
      await postJSON('/catalog/areas', { name });
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
    if (!confirm(`Eliminare l'area "${name}"? Puoi eliminarla solo se non è usata da materiali, categorie o fornitori.`)) return;

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

  return <Card title="Gestione aree catalogo" icon={Layers3} sub="Crea e organizza gli ambiti principali del catalogo: materiali, componenti, finiture, packaging, vernici e lavorazioni.">
    <div className="area-manager-layout">
      <div className="area-create-box">
        <label>Nuova area</label>
        <div className="area-create-row">
          <input
            placeholder="Es. Finiture, Packaging, Vernici..."
            value={areaName}
            onChange={e => setAreaName(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') saveArea(); }}
          />
          <button className="primary" onClick={saveArea}><Plus /> Aggiungi</button>
        </div>
        <small>Le aree compariranno negli acquisti, nei fornitori e nella gestione categorie.</small>
      </div>

      <div className="area-table-box">
        <div className="area-table-head">
          <b>Aree disponibili</b>
          <span>{list(areas).length} aree</span>
        </div>

        <div className="area-table">
          {list(areas).map(a => <div className="area-table-row" key={a}>
            <div>
              <b>{a}</b>
              <small>Ambito catalogo</small>
            </div>
            <button className="ghost danger" onClick={() => removeArea(a)}><Trash2 /> Elimina</button>
          </div>)}
        </div>
      </div>
    </div>
  </Card>;
}

'''


def replace_or_insert_area_section_component(s: str) -> str:
    # Rimuove il vecchio CatalogAreaInlineManager se presente.
    start = s.find("function CatalogAreaInlineManager")
    if start != -1:
      end = s.find("\nfunction ", start + 1)
      if end == -1:
          end = len(s)
      s = s[:start] + s[end:]

    if "function CatalogAreasSection" not in s:
        marker = "function CatalogAdvancedSettings"
        idx = s.find(marker)
        if idx == -1:
            marker = "function Setup({ toast })"
            idx = s.find(marker)
        if idx == -1:
            raise RuntimeError("Non trovo punto inserimento CatalogAreasSection")
        s = s[:idx] + AREA_SECTION + "\n" + s[idx:]

    return s


def cleanup_area_inline_usage(s: str) -> str:
    s = re.sub(r"\n\s*<CatalogAreaInlineManager[^>]*\/>", "", s)
    return s


def insert_area_section_after_pagetitle(s: str) -> str:
    setup_start = s.find("function Setup({ toast })")
    if setup_start == -1:
        raise RuntimeError("Setup non trovata")

    setup_end = s.find("\nfunction ", setup_start + 1)
    if setup_end == -1:
        setup_end = len(s)

    block = s[setup_start:setup_end]

    # Rimuove eventuali duplicati.
    block = re.sub(r"\n\s*<CatalogAreasSection[^>]*\/>", "", block)

    page_title_idx = block.find("<PageTitle")
    if page_title_idx == -1:
        raise RuntimeError("PageTitle dentro Setup non trovato")

    page_title_end = block.find("/>", page_title_idx)
    if page_title_end == -1:
        raise RuntimeError("Fine PageTitle non trovata")

    page_title_end += 2

    insert = "\n    <CatalogAreasSection toast={toast} refreshTax={refreshTax} refreshSug={refreshSug} />"

    block = block[:page_title_end] + insert + block[page_title_end:]

    return s[:setup_start] + block + s[setup_end:]


def patch_open_quote_pdf(s: str) -> str:
    # Patch mirata dentro openQuotePdf: in Electron usa stessa finestra.
    idx = s.find("async function openQuotePdf")
    if idx == -1:
        print("openQuotePdf non trovata: salto patch PDF")
        return s

    end = s.find("\n  async function", idx + 1)
    if end == -1:
        end = s.find("\n  function", idx + 1)
    if end == -1:
        end = idx + 1600

    block = s[idx:end]

    if "isElectronRuntime" in block:
        return s

    # Cerca window.open nel blocco.
    if "window.open" not in block:
        print("window.open non trovato dentro openQuotePdf: salto patch PDF")
        return s

    helper = r'''
    const isElectronRuntime = /Electron/i.test(navigator.userAgent || '');
    if (isElectronRuntime) {
      window.location.href = url;
      return;
    }
'''

    # Inserisce subito prima della prima window.open(url...).
    block = block.replace("window.open", helper + "\n    window.open", 1)

    # Aggiunge fallback se popup bloccato, senza rompere l'esistente.
    block = block.replace(
        "window.open(url",
        "const opened = window.open(url",
        1
    )

    if "if (!opened)" not in block:
        # chiude in modo compatibile: se la riga diventa const opened = window.open(...)
        lines = block.splitlines()
        for i, line in enumerate(lines):
            if "const opened = window.open" in line:
                lines.insert(i + 1, "    if (!opened) window.location.href = url;")
                break
        block = "\n".join(lines)

    return s[:idx] + block + s[end:]


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    s = replace_or_insert_area_section_component(s)
    s = cleanup_area_inline_usage(s)
    s = insert_area_section_after_pagetitle(s)
    s = patch_open_quote_pdf(s)

    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend: gestione aree pulita + PDF Electron patch applicata.")


def patch_css():
    css = CSS.read_text(encoding="utf-8")

    if "/* v41.1.3 clean areas manager and electron pdf */" not in css:
        css += r'''

/* v41.1.3 clean areas manager and electron pdf */

/* Nasconde vecchi tentativi inline delle aree */
.catalog-inline-area-manager {
  display: none !important;
}

/* Card gestione aree, larga e leggibile */
.area-manager-layout {
  display: grid;
  grid-template-columns: minmax(280px, .8fr) minmax(0, 1.2fr);
  gap: 18px;
  align-items: start;
}

.area-create-box {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  border-radius: 18px;
  padding: 14px;
}

.area-create-box label {
  display: block;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: .075em;
  text-transform: uppercase;
  margin-bottom: 8px;
  color: var(--muted);
}

.area-create-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}

.area-create-row input {
  min-height: 44px;
}

.area-create-row button {
  min-height: 44px;
  white-space: nowrap;
}

.area-create-box small {
  display: block;
  margin-top: 9px;
  color: var(--muted);
  line-height: 1.4;
}

.area-table-box {
  min-width: 0;
}

.area-table-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  color: var(--muted);
}

.area-table-head b {
  color: var(--text);
}

.area-table-head span {
  border: 1px solid rgba(148, 163, 184, .18);
  background: rgba(255,255,255,.06);
  border-radius: 999px;
  padding: 5px 9px;
  font-size: 11px;
  font-weight: 900;
}

.area-table {
  display: grid;
  gap: 8px;
  max-height: 220px;
  overflow-y: auto;
  padding-right: 4px;
}

.area-table-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  border-radius: 16px;
  padding: 11px 12px;
}

.area-table-row b,
.area-table-row small {
  display: block;
}

.area-table-row b {
  font-size: 13px;
  line-height: 1.25;
}

.area-table-row small {
  margin-top: 2px;
  color: var(--muted);
  font-size: 11px;
}

.area-table-row button {
  min-height: 34px;
  padding: 7px 10px;
  border-radius: 999px;
}

/* La pagina categorie deve respirare */
.catalog-treatments-section {
  margin-top: 22px;
}

.catalog-treatments-section .card {
  overflow: hidden;
}

/* Card 4 configurazioni: scroll interno */
.catalog-board > *:nth-child(4),
.catalog-grid > *:nth-child(4),
.setup-catalog-grid > *:nth-child(4),
.category-manager-grid > *:nth-child(4) {
  max-height: 640px !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
}

@media (max-width: 900px) {
  .area-manager-layout,
  .area-create-row,
  .area-table-row {
    grid-template-columns: 1fr;
  }

  .area-create-row button,
  .area-table-row button {
    width: 100%;
  }

  .area-table {
    max-height: none;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")
        print("CSS: gestione aree pulita applicata.")


def main():
    patch_frontend()
    patch_css()
    print("Patch v41.1.3 completata.")


if __name__ == "__main__":
    main()
