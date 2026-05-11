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

  const summaryCols = columns.filter(c => c !== actionCol).slice(0, 6);

  return <div className="table-card">
    <div className="table-meta">
      <b>{rows.length} righe</b>
      <span>{meta}</span>
      {actionCol && <small className="mobile-table-hint">Su smartphone tocca una riga per aprire le azioni.</small>}
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

    {mobileActions && actionCol && <div className="mobile-row-action-backdrop" onClick={() => setMobileActions(null)}>
      <div className="mobile-row-action-sheet" onClick={e => e.stopPropagation()}>
        <div className="mobile-row-action-head">
          <div>
            <span>Azioni riga</span>
            <b>{rowTitle(mobileActions.row)}</b>
          </div>
          <button className="ghost" onClick={() => setMobileActions(null)}>×</button>
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
    </div>}
  </div>;
}
'''

CSS_PATCH = r'''

/* v42.3.7 - Mobile table compact mode with action popup */
.mobile-table-hint {
  display: none;
}

.mobile-row-action-backdrop {
  display: none;
}

@media (max-width: 720px) {
  .mobile-table-hint {
    display: block;
    color: var(--muted);
    font-size: 10.5px;
    line-height: 1.25;
    margin-top: 2px;
  }

  .table-card {
    padding: 9px !important;
    border-radius: 18px !important;
  }

  .table-wrap {
    overflow-x: hidden !important;
    width: 100%;
    max-width: 100%;
  }

  .table-wrap table {
    width: 100% !important;
    min-width: 0 !important;
    table-layout: fixed !important;
  }

  .table-wrap th,
  .table-wrap td {
    padding: 7px 5px !important;
    font-size: 9.4px !important;
    line-height: 1.12 !important;
    max-width: none !important;
    min-width: 0 !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    word-break: normal !important;
  }

  .table-wrap th {
    font-size: 8.2px !important;
    letter-spacing: .04em !important;
  }

  .table-wrap td b,
  .table-wrap td strong {
    font-size: 9.6px !important;
    line-height: 1.1 !important;
  }

  .table-wrap tr {
    min-height: unset !important;
    height: auto !important;
  }

  .table-wrap .table-actions-head,
  .table-wrap .table-actions-cell {
    display: none !important;
  }

  .table-wrap tr.has-mobile-actions {
    cursor: pointer;
  }

  .table-wrap tr.has-mobile-actions:active {
    background: rgba(5, 132, 130, .12);
  }

  .mobile-row-action-backdrop {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: grid;
    align-items: end;
    background: rgba(2, 6, 23, .58);
    backdrop-filter: blur(8px);
    padding: 12px;
  }

  .mobile-row-action-sheet {
    width: 100%;
    max-height: 82vh;
    overflow: auto;
    border-radius: 24px;
    border: 1px solid rgba(148, 163, 184, .22);
    background: rgba(15, 23, 42, .96);
    box-shadow: 0 -20px 60px rgba(0,0,0,.42);
    padding: 14px;
  }

  .mobile-row-action-head {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 10px;
    align-items: start;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(148, 163, 184, .16);
    margin-bottom: 12px;
  }

  .mobile-row-action-head span {
    display: block;
    color: var(--muted);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .08em;
    font-weight: 900;
    margin-bottom: 4px;
  }

  .mobile-row-action-head b {
    display: block;
    color: var(--text);
    font-size: 15px;
    line-height: 1.2;
    overflow-wrap: anywhere;
  }

  .mobile-row-action-head button {
    min-width: 42px;
    min-height: 38px;
    font-size: 20px !important;
    padding: 0 !important;
  }

  .mobile-row-action-summary {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 14px;
  }

  .mobile-row-action-summary div {
    border: 1px solid rgba(148, 163, 184, .14);
    background: rgba(255,255,255,.045);
    border-radius: 14px;
    padding: 9px;
    min-width: 0;
  }

  .mobile-row-action-summary span {
    display: block;
    color: var(--muted);
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: .07em;
    font-weight: 900;
    margin-bottom: 4px;
  }

  .mobile-row-action-summary b {
    display: block;
    color: var(--text);
    font-size: 12px;
    line-height: 1.15;
    overflow-wrap: anywhere;
  }

  .mobile-row-action-buttons {
    display: grid !important;
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .mobile-row-action-buttons > *,
  .mobile-row-action-buttons button,
  .mobile-row-action-buttons a {
    width: 100% !important;
    min-height: 42px !important;
    justify-content: center !important;
    font-size: 12.5px !important;
    border-radius: 14px !important;
  }

  .mobile-row-action-buttons div {
    display: grid !important;
    grid-template-columns: 1fr;
    gap: 8px;
  }
}

@media (max-width: 430px) {
  .table-wrap th,
  .table-wrap td {
    padding: 6px 4px !important;
    font-size: 8.8px !important;
  }

  .table-wrap th {
    font-size: 7.8px !important;
  }

  .mobile-row-action-summary {
    grid-template-columns: 1fr;
  }
}
'''

def replace_datatable(s: str) -> str:
    start = s.find("function DataTable(")
    if start == -1:
        raise RuntimeError("function DataTable non trovata")

    next_func = s.find("\nfunction ", start + 1)
    if next_func == -1:
        raise RuntimeError("Funzione successiva dopo DataTable non trovata")

    return s[:start] + NEW_DATATABLE.strip() + "\n\n" + s[next_func + 1:]

def main():
    s = MAIN.read_text(encoding="utf-8")
    s = replace_datatable(s)
    MAIN.write_text(s, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")

    css = re.sub(
        r'\n/\* v42\.3\.7 - Mobile table compact mode with action popup \*/[\s\S]*?(?=\n/\*|\Z)',
        '\n',
        css,
        flags=re.DOTALL
    )

    css += "\n\n" + CSS_PATCH.strip() + "\n"
    CSS.write_text(css, encoding="utf-8")

    print("Patch v42.3.7 applicata: tabelle mobile compatte + azioni in popup.")

if __name__ == "__main__":
    main()
