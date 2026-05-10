from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS = ROOT / "frontend" / "src" / "style.css"

def main():
    css = CSS.read_text(encoding="utf-8")

    if "/* v40.1.6 restore professional forms */" not in css:
        css += r'''

/* v40.1.6 restore professional forms */

/* =========================================================
   RESET FORM PROFESSIONALE
   Le patch precedenti avevano compresso troppo label, input e suggerimenti.
   Qui ripristiniamo una griglia pulita, leggibile e stabile.
   ========================================================= */

/* Font e ritmo generale: torna più morbido e leggibile */
body,
input,
select,
textarea,
button {
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}

.card header h2,
.page-title h1,
.stat strong,
.brand b,
nav button,
.quick-actions button,
button {
  letter-spacing: normal;
}

/* Card: più respiro, meno compressione */
.card {
  overflow: hidden !important;
}

.card header {
  display: flex !important;
  align-items: flex-start !important;
  justify-content: space-between !important;
  gap: 18px !important;
  padding-bottom: 16px !important;
}

.card header h2 {
  font-size: 18px !important;
  line-height: 1.2 !important;
  font-weight: 800 !important;
}

.card header p {
  display: block !important;
  margin-top: 6px !important;
  line-height: 1.45 !important;
  font-size: 14px !important;
  color: var(--muted) !important;
  max-width: 760px !important;
}

/* Label: non devono più accavallarsi */
.field label,
.form-grid label,
.buy-grid label,
.stock-form label,
.quote-filters label,
.catalog-editor-grid label {
  height: auto !important;
  min-height: 18px !important;
  display: block !important;
  margin: 0 0 7px 0 !important;
  font-size: 11px !important;
  line-height: 1.2 !important;
  letter-spacing: .075em !important;
  text-transform: uppercase !important;
  white-space: normal !important;
  overflow: visible !important;
}

/* Input: dimensione uniforme, non schiacciata */
input,
select,
textarea {
  min-height: 44px !important;
  height: auto !important;
  width: 100% !important;
  min-width: 0 !important;
  font-size: 14px !important;
  line-height: 1.3 !important;
}

select {
  height: 44px !important;
}

/* Campi: ogni campo vive nel suo box */
.field {
  display: block !important;
  min-width: 0 !important;
  width: 100% !important;
  margin: 0 !important;
  position: relative !important;
}

/* Suggerimenti: tornano sotto l'input, ordinati, non tra i campi */
.suggestions,
.compact-suggestions {
  position: static !important;
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 6px !important;
  margin-top: 8px !important;
  max-height: 32px !important;
  overflow: hidden !important;
  width: 100% !important;
  z-index: auto !important;
}

.suggestions button,
.compact-suggestions button {
  height: 26px !important;
  min-height: 26px !important;
  max-height: 26px !important;
  padding: 5px 9px !important;
  font-size: 11px !important;
  line-height: 1 !important;
  max-width: 125px !important;
  border-radius: 999px !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

/* Nasconde solo gli hint lunghi, non i suggerimenti */
.field > small:not(.keep-hint),
.field .hint {
  display: none !important;
}

/* =========================================================
   ACQUISTI - layout corretto
   ========================================================= */

.buy-grid {
  display: grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap: 18px 20px !important;
  align-items: start !important;
}

/* Elimina definitivamente vecchi posizionamenti manuali */
.buy-grid > .field,
.buy-grid > .name-preview {
  grid-column: auto !important;
  grid-row: auto !important;
}

/* Nome articolo prende una riga pulita */
.buy-grid .name-preview {
  grid-column: 1 / -1 !important;
  min-height: 96px !important;
  padding: 18px !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  border-radius: 20px !important;
}

.name-preview span {
  font-size: 11px !important;
  letter-spacing: .075em !important;
  line-height: 1.2 !important;
}

.name-preview b {
  font-size: 18px !important;
  line-height: 1.2 !important;
  margin-top: 6px !important;
}

.name-preview small {
  font-size: 12px !important;
  line-height: 1.25 !important;
  margin-top: 6px !important;
}

/* La card acquisto non deve mostrare contenuto fuori posto */
.card:has(.buy-grid) {
  overflow: hidden !important;
}

/* =========================================================
   CLIENTI / FORNITORI
   ========================================================= */

#supplier-form.form-grid,
#customer-form.form-grid {
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  gap: 18px 20px !important;
  align-items: start !important;
}

#supplier-form .suggestions,
#customer-form .suggestions {
  max-height: 32px !important;
}

/* =========================================================
   VENDITE / MOVIMENTI
   ========================================================= */

.stock-form,
.form-grid.stock-form {
  display: grid !important;
  grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
  gap: 18px 20px !important;
  align-items: start !important;
}

/* =========================================================
   PREVENTIVI
   ========================================================= */

.quote-filters {
  display: grid !important;
  grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
  gap: 16px !important;
  align-items: start !important;
}

.quote-search-head {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) auto !important;
  gap: 12px !important;
  align-items: center !important;
}

.material-browser {
  max-height: 440px !important;
  overflow-y: auto !important;
  padding-right: 6px !important;
}

.material-pick {
  min-height: 78px !important;
  padding: 13px 14px !important;
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) auto auto !important;
  gap: 14px !important;
  align-items: center !important;
}

/* =========================================================
   PRODUZIONE
   ========================================================= */

.production-panel > .inline {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) 130px auto auto !important;
  gap: 12px !important;
  align-items: center !important;
}

.production-panel > .inline select,
.production-panel > .inline input,
.production-panel > .inline button {
  height: 44px !important;
  min-height: 44px !important;
}

.variant-card {
  min-height: 176px !important;
  padding: 16px !important;
}

.variant-card em {
  -webkit-line-clamp: 3 !important;
  min-height: 44px !important;
}

/* =========================================================
   CATALOGO
   ========================================================= */

.catalog-topbar {
  display: grid !important;
  grid-template-columns: auto minmax(0, 1fr) !important;
  gap: 16px !important;
  align-items: center !important;
}

.catalog-workbench {
  display: grid !important;
  grid-template-columns:
    minmax(180px, .7fr)
    minmax(260px, 1fr)
    minmax(260px, 1fr)
    minmax(380px, 1.35fr) !important;
  gap: 14px !important;
  align-items: stretch !important;
}

.catalog-column {
  min-width: 0 !important;
  max-height: calc(100vh - 250px) !important;
  overflow: hidden !important;
  display: flex !important;
  flex-direction: column !important;
}

.catalog-list {
  overflow-y: auto !important;
  overflow-x: hidden !important;
}

.catalog-create-box {
  display: grid !important;
  gap: 13px !important;
  padding: 14px !important;
}

.catalog-create-box button {
  min-height: 42px !important;
}

.catalog-inline-add {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) 42px !important;
  gap: 9px !important;
  align-items: start !important;
}

.catalog-inline-add button {
  width: 42px !important;
  height: 44px !important;
  min-height: 44px !important;
}

.pill-list {
  max-height: 150px !important;
  overflow-y: auto !important;
}

/* =========================================================
   TABELLE
   ========================================================= */

.table-card,
.table-wrap {
  max-width: 100% !important;
  overflow: hidden !important;
}

.table-wrap {
  overflow-x: auto !important;
}

.table-wrap table {
  min-width: 780px !important;
}

.table-wrap th,
.table-wrap td {
  vertical-align: middle !important;
  line-height: 1.35 !important;
}

/* =========================================================
   SIDEBAR
   ========================================================= */

.side-note {
  line-height: 1.4 !important;
  font-size: 12px !important;
}

.side-note br {
  display: initial !important;
}

/* =========================================================
   RESPONSIVE
   ========================================================= */

@media (max-width: 1350px) {
  .buy-grid,
  #supplier-form.form-grid,
  #customer-form.form-grid,
  .stock-form,
  .quote-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }

  .catalog-workbench {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }

  .catalog-linked {
    grid-column: 1 / -1 !important;
  }
}

@media (max-width: 900px) {
  .buy-grid,
  #supplier-form.form-grid,
  #customer-form.form-grid,
  .stock-form,
  .quote-filters,
  .quote-search-head,
  .production-panel > .inline,
  .catalog-topbar,
  .catalog-workbench {
    grid-template-columns: 1fr !important;
  }

  .catalog-column {
    max-height: none !important;
  }

  .material-pick {
    grid-template-columns: 1fr !important;
  }

  .card header {
    display: grid !important;
    grid-template-columns: 1fr !important;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")
        print("Patch v40.1.6 restore professional forms applicata.")
    else:
        print("Patch v40.1.6 già presente.")

if __name__ == "__main__":
    main()
