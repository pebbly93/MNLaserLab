from pathlib import Path
import re

MAIN = Path("frontend/src/main.jsx")
CSS = Path("frontend/src/style.css")

NEW_DATATABLE = r'''
function DataTable({ columns, rows, empty = 'Nessun risultato', meta = 'Dati aggiornati dal database', rowClassName }) {
  const [mobileActions, setMobileActions] = useState(null);

  const actionCol = columns.find(c => {
    const key = String(c.key || '').toLowerCase();
    const label = String(c.label || '').toLowerCase();
    return key === 'actions' || key === 'azioni' || label.includes('azioni');
  });

  function isMobileTable() {
    return typeof window !== 'undefined'
      && window.matchMedia
      && window.matchMedia('(max-width: 720px)').matches;
  }

  function openMobileActions(row, index, e) {
    if (!actionCol || !isMobileTable()) return;

    const target = e?.target;
    if (target?.closest && target.closest('button,a,input,select,textarea,label')) return;

    setMobileActions({ row, index });
  }

  function rowTitle(row) {
    return row.name
      || row.product
      || row.preventivo
      || row.quote
      || row.customer
      || row.cliente
      || row.date
      || row.data
      || 'Dettaglio riga';
  }

  const summaryCols = columns.filter(c => c !== actionCol);

  const mobileModal = mobileActions && actionCol && typeof document !== 'undefined'
    ? createPortal(
      <div className="mobile-row-action-backdrop">
        <div className="mobile-row-action-sheet">
          <div className="mobile-row-action-head">
            <div>
              <span>Dettaglio riga</span>
              <b>{rowTitle(mobileActions.row)}</b>
            </div>
            <button type="button" className="ghost" onClick={() => setMobileActions(null)} aria-label="Chiudi dettaglio">×</button>
          </div>

          <div className="mobile-row-action-summary">
            {summaryCols.map(c => <div key={c.key}>
              <span>{c.label}</span>
              <b>{c.render ? c.render(mobileActions.row, mobileActions.index) : mobileActions.row[c.key]}</b>
            </div>)}
          </div>

          <div className="mobile-row-action-buttons">
            {actionCol.render
              ? actionCol.render(mobileActions.row, mobileActions.index)
              : mobileActions.row[actionCol.key]}
          </div>
        </div>
      </div>,
      document.body
    )
    : null;

  return <>
    <div className="table-card">
      <div className="table-meta">
        <b>{rows.length} righe</b>
        <span>{meta}</span>
        {actionCol && <small className="mobile-table-hint">Tocca una riga per aprire dettaglio e azioni.</small>}
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {columns.map(c => <th key={c.key} className={c === actionCol ? 'table-actions-head' : ''}>{c.label}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.length ? rows.map((r, i) => <tr
              className={`${rowClassName ? rowClassName(r, i) : ''} ${actionCol ? 'has-mobile-actions' : ''}`}
              key={r._key || r.key || r.name || i}
              onClick={e => openMobileActions(r, i, e)}
            >
              {columns.map(c => <td
                key={c.key}
                data-label={c.label}
                className={c === actionCol ? 'table-actions-cell' : ''}
              >
                {c.render ? c.render(r, i) : r[c.key]}
              </td>)}
            </tr>) : <tr><td colSpan={columns.length}><Empty text={empty}/></td></tr>}
          </tbody>
        </table>
      </div>
    </div>

    {mobileModal}
  </>;
}
'''

CSS_PATCH = r'''

/* v42.4.1 - Mobile row modal rendered through portal */
@media (max-width: 720px) {
  body:has(.mobile-row-action-backdrop) {
    overflow: hidden !important;
  }

  .mobile-row-action-backdrop {
    position: fixed !important;
    inset: 0 !important;
    z-index: 2147483647 !important;
    display: block !important;
    width: 100vw !important;
    height: 100vh !important;
    background: #07111f !important;
    overflow: hidden !important;
    padding: 0 !important;
    margin: 0 !important;
  }

  .mobile-row-action-sheet {
    position: fixed !important;
    inset: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    max-width: none !important;
    max-height: none !important;
    margin: 0 !important;
    border: 0 !important;
    border-radius: 0 !important;
    background:
      radial-gradient(circle at 85% 8%, rgba(5,132,130,.18), transparent 30%),
      linear-gradient(180deg, #091525 0%, #06101d 100%) !important;
    box-shadow: none !important;
    padding: max(14px, env(safe-area-inset-top)) 14px max(18px, env(safe-area-inset-bottom)) !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    -webkit-overflow-scrolling: touch !important;
    overscroll-behavior: contain !important;
  }

  .mobile-row-action-head {
    position: relative !important;
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) 42px !important;
    gap: 12px !important;
    align-items: center !important;
    padding: 4px 0 14px !important;
    margin: 0 0 12px !important;
    border-bottom: 1px solid rgba(148, 163, 184, .16) !important;
    background: transparent !important;
  }

  .mobile-row-action-head span {
    display: block;
    color: #19ddd6;
    font-size: 9px !important;
    text-transform: uppercase;
    letter-spacing: .14em;
    font-weight: 900;
    margin: 0 0 5px;
  }

  .mobile-row-action-head b {
    display: block;
    color: #eef6ff;
    font-size: 18px !important;
    line-height: 1.12 !important;
    overflow-wrap: anywhere;
  }

  .mobile-row-action-head button {
    width: 42px !important;
    height: 42px !important;
    min-width: 42px !important;
    min-height: 42px !important;
    border-radius: 14px !important;
    font-size: 22px !important;
    padding: 0 !important;
    display: grid !important;
    place-items: center !important;
    background: rgba(255,255,255,.08) !important;
    border: 1px solid rgba(148,163,184,.16) !important;
  }

  .mobile-row-action-summary {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 8px !important;
    margin: 0 0 14px !important;
    padding: 0 !important;
  }

  .mobile-row-action-summary div {
    border: 1px solid rgba(148, 163, 184, .13) !important;
    background: rgba(255,255,255,.04) !important;
    border-radius: 15px !important;
    padding: 9px 11px !important;
    min-width: 0 !important;
  }

  .mobile-row-action-summary span {
    display: block;
    color: rgba(188, 204, 224, .78);
    font-size: 8.5px !important;
    text-transform: uppercase;
    letter-spacing: .1em;
    font-weight: 900;
    margin-bottom: 4px;
  }

  .mobile-row-action-summary b {
    display: block;
    color: #eef6ff;
    font-size: 12.5px !important;
    line-height: 1.18 !important;
    overflow-wrap: anywhere;
    word-break: normal;
  }

  .mobile-row-action-buttons {
    position: relative !important;
    margin: 0 0 24px !important;
    padding: 12px 0 0 !important;
    border-top: 1px solid rgba(148, 163, 184, .14) !important;
    background: transparent !important;
    display: block !important;
  }

  .mobile-row-action-buttons > div {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 7px !important;
    width: 100% !important;
  }

  .mobile-row-action-buttons button,
  .mobile-row-action-buttons a {
    width: 100% !important;
    min-height: 34px !important;
    height: 34px !important;
    padding: 6px 8px !important;
    border-radius: 11px !important;
    justify-content: center !important;
    font-size: 10.5px !important;
    line-height: 1 !important;
    white-space: nowrap !important;
  }
}
'''

def patch_import(s):
    if "createPortal" in s:
        return s

    # Caso classico: import React/hooks da react
    s = re.sub(
        r"(import\s+[^;]*from\s+['\"]react['\"];\n)",
        r"\1import { createPortal } from 'react-dom';\n",
        s,
        count=1
    )

    if "createPortal" not in s:
        s = "import { createPortal } from 'react-dom';\n" + s

    return s

def replace_datatable(s):
    start = s.find("function DataTable(")
    if start == -1:
        raise RuntimeError("function DataTable non trovata")

    next_func = s.find("\nfunction ", start + 1)
    if next_func == -1:
        raise RuntimeError("Funzione successiva dopo DataTable non trovata")

    return s[:start] + NEW_DATATABLE.strip() + "\n\n" + s[next_func + 1:]

def patch_main():
    s = MAIN.read_text(encoding="utf-8")
    s = patch_import(s)
    s = replace_datatable(s)
    MAIN.write_text(s, encoding="utf-8")
    print("DataTable aggiornato: modal mobile renderizzato in document.body con createPortal.")

def patch_css():
    css = CSS.read_text(encoding="utf-8")

    # Rimuove layer precedenti del popup mobile.
    for tag in [
        "v42.3.8 - Mobile row details full screen",
        "v42.3.9 - Refined mobile fullscreen row detail",
        "v42.4.0 - Stable mobile full screen table detail, no flicker",
        "v42.4.1 - Mobile row modal rendered through portal",
    ]:
        css = re.sub(
            r'\n/\* ' + re.escape(tag) + r' \*/[\s\S]*?(?=\n/\*|\Z)',
            '\n',
            css,
            flags=re.DOTALL
        )

    css += "\n\n" + CSS_PATCH.strip() + "\n"
    CSS.write_text(css, encoding="utf-8")
    print("CSS portal modal mobile aggiornato.")

def main():
    patch_main()
    patch_css()
    print("Patch v42.4.1 completata.")

if __name__ == "__main__":
    main()
