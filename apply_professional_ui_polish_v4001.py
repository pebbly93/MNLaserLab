from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS = ROOT / "frontend" / "src" / "style.css"
MAIN = ROOT / "frontend" / "src" / "main.jsx"


def main():
    css = CSS.read_text(encoding="utf-8")

    if "/* v40.0.1 professional alignment polish */" not in css:
        css += r'''

/* v40.0.1 professional alignment polish */

/* ---------- Global rhythm ---------- */
.card {
  align-self: start;
}

.card header {
  align-items: flex-start;
  gap: 18px;
}

.card header h2 {
  line-height: 1.15;
}

.card header p {
  max-width: 860px;
}

.form-grid,
.buy-grid,
.small-grid,
.stock-form,
.catalog-editor-grid {
  align-items: end;
}

.field {
  min-width: 0;
}

.field label,
label {
  min-height: 18px;
}

input,
select,
textarea,
button {
  box-sizing: border-box;
}

button svg {
  flex-shrink: 0;
}

.table-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 7px;
  flex-wrap: wrap;
  min-width: max-content;
}

.table-actions button {
  min-height: 34px;
  padding: 8px 11px;
  white-space: nowrap;
}

.table-wrap table {
  table-layout: auto;
}

.table-wrap th,
.table-wrap td {
  vertical-align: middle;
}

.table-wrap td:last-child,
.table-wrap th:last-child {
  text-align: right;
}

/* ---------- Suggestions compact and aligned ---------- */
.compact-suggestions {
  min-height: 0;
  align-items: flex-start;
}

.compact-suggestions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  max-width: 165px;
}

.compact-suggestions small {
  min-height: 28px;
  line-height: 28px;
}

/* ---------- Production panel ---------- */
.production-panel {
  display: grid;
  gap: 16px;
}

.production-panel > .inline {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) 140px auto auto;
  gap: 10px;
  align-items: center;
}

.production-panel > .inline select,
.production-panel > .inline input,
.production-panel > .inline button {
  min-height: 44px;
}

.production-panel > .inline button {
  justify-content: center;
}

.production-check-list {
  display: grid;
  gap: 14px;
}

.production-row {
  border-radius: 22px;
  padding: 16px;
  background:
    linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.035));
}

.production-row-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  align-items: start;
}

.production-row-head > div {
  min-width: 0;
}

.production-row-head b {
  font-size: 15px;
  line-height: 1.25;
  word-break: break-word;
}

.production-row-head small {
  line-height: 1.45;
}

.production-row .quote-status {
  align-self: start;
  white-space: nowrap;
}

/* ---------- Alternative cards ---------- */
.variant-panel {
  display: grid;
  gap: 12px;
}

.variant-panel h4 {
  font-size: 13px;
  letter-spacing: .02em;
  color: var(--text);
}

.variant-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
  align-items: stretch;
}

.variant-card {
  min-height: 168px;
  grid-template-rows: auto auto 1fr auto;
  align-content: start;
  gap: 10px;
  padding: 14px;
  border-radius: 18px;
  transition: transform .14s ease, border-color .14s ease, background .14s ease;
}

.variant-card:hover {
  transform: translateY(-1px);
}

.variant-card > div {
  min-width: 0;
}

.variant-card b {
  font-size: 14px;
  line-height: 1.25;
  word-break: break-word;
}

.variant-card small {
  line-height: 1.35;
  min-height: 30px;
}

.variant-card span {
  display: inline-flex;
  width: fit-content;
  align-items: center;
  border-radius: 999px;
  padding: 5px 9px;
  background: rgba(255,255,255,.07);
  border: 1px solid rgba(148, 163, 184, .18);
  font-size: 12px;
}

.variant-card em {
  line-height: 1.45;
  min-height: 34px;
}

.variant-card strong {
  display: inline-flex;
  width: fit-content;
  align-items: center;
  min-height: 26px;
  border-radius: 999px;
  padding: 5px 9px;
  background: rgba(34,197,94,.10);
  border: 1px solid rgba(34,197,94,.22);
  color: #86efac;
  font-size: 11px;
  font-weight: 900;
}

.selected-variant {
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px 14px;
  align-items: center;
}

.selected-variant b {
  min-width: 0;
  word-break: break-word;
}

/* ---------- Notice boxes ---------- */
.notice {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  line-height: 1.45;
}

.notice svg {
  margin-top: 1px;
  flex-shrink: 0;
}

/* ---------- Detail modal polish ---------- */
.detail-modal-head {
  min-height: 82px;
}

.detail-modal-title {
  min-width: 0;
}

.detail-modal-title h2 {
  line-height: 1.15;
}

.detail-modal-title p {
  line-height: 1.4;
}

.detail-hero {
  align-items: center;
}

.detail-hero > div {
  min-width: 0;
}

.detail-hero strong {
  word-break: break-word;
}

.detail-grid .stat {
  min-height: 116px;
  justify-content: space-between;
}

.detail-columns {
  align-items: start;
}

.detail-columns .table-card {
  height: 100%;
}

/* ---------- Catalog polish ---------- */
.catalog-workbench {
  align-items: stretch;
}

.catalog-column {
  height: 100%;
}

.catalog-list button {
  min-height: 64px;
}

.catalog-list button b {
  line-height: 1.25;
}

.catalog-list button small {
  line-height: 1.35;
}

.catalog-create-box .field,
.catalog-inline-add .field {
  margin: 0;
}

.catalog-inline-add {
  align-items: end;
}

.catalog-inline-add button {
  min-width: 42px;
}

.pill-list > span {
  min-height: 30px;
  line-height: 1;
}

.pill-list > span button {
  display: inline-grid;
  place-items: center;
  line-height: 1;
}

/* ---------- Stats alignment ---------- */
.stats,
.mini-stats,
.inventory-quality,
.compact-stats {
  align-items: stretch;
}

.stat {
  min-width: 0;
}

.stat strong {
  line-height: 1.12;
  word-break: break-word;
}

.stat small {
  line-height: 1.35;
}

/* ---------- Quote and material browser polish ---------- */
.material-browser {
  align-items: stretch;
}

.material-pick {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 12px;
  align-items: center;
  min-height: 74px;
}

.material-pick span {
  min-width: 0;
}

.material-pick b,
.material-pick small {
  display: block;
}

.material-pick b {
  line-height: 1.25;
  word-break: break-word;
}

.material-pick small {
  line-height: 1.35;
}

.material-pick em,
.material-pick strong {
  white-space: nowrap;
}

/* ---------- Responsive ---------- */
@media (max-width: 1050px) {
  .production-panel > .inline {
    grid-template-columns: 1fr 120px;
  }

  .production-panel > .inline button {
    width: 100%;
  }

  .production-row-head {
    grid-template-columns: 1fr;
  }

  .production-row .quote-status {
    justify-self: start;
  }

  .material-pick {
    grid-template-columns: 1fr;
    align-items: start;
  }

  .table-actions {
    justify-content: flex-start;
  }

  .table-wrap td:last-child,
  .table-wrap th:last-child {
    text-align: left;
  }
}

@media (max-width: 720px) {
  .production-panel > .inline {
    grid-template-columns: 1fr;
  }

  .variant-grid {
    grid-template-columns: 1fr;
  }

  .detail-hero {
    align-items: flex-start;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")
        print("CSS professional polish aggiunto.")
    else:
        print("CSS professional polish già presente.")

    # Piccolo miglioramento testo nella produzione, se presente
    s = MAIN.read_text(encoding="utf-8")

    old = """<h4>Alternative consigliate</h4>"""
    new = """<h4>Alternative consigliate in base a categoria, formato, spessore e stock</h4>"""
    if old in s and new not in s:
        s = s.replace(old, new, 1)

    # Rende più chiaro il dettaglio stock nelle alternative
    old = """<span>{num(v.stock)} {v.unit || ''}</span>
                  <em>{v.notes}</em>
                  <strong>{v.can_cover ? 'Copre produzione' : 'Stock parziale'}</strong>"""
    new = """<span>Stock: {num(v.stock)} {v.unit || ''}</span>
                  <em>{v.notes}</em>
                  <strong>{v.can_cover ? 'Copre produzione' : 'Stock parziale'}</strong>"""
    if old in s:
        s = s.replace(old, new, 1)

    MAIN.write_text(s, encoding="utf-8")
    print("Frontend microcopy produzione aggiornato.")

    print("Patch v40.0.1 professional UI polish completata.")


if __name__ == "__main__":
    main()
