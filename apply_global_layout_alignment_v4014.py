from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


def main():
    s = MAIN.read_text(encoding="utf-8")

    # Rimuove sottotesti ridondanti dalle card più affollate.
    remove_subs = [
        'sub="Compila da sinistra a destra: i suggerimenti cambiano in base a sezione e categoria."',
        'sub="Controlla disponibilità materiali, produci e carica automaticamente il magazzino prodotti finiti."',
        'sub="Usalo per rettifiche manuali, campioni, pezzi danneggiati o carichi non generati da produzione."',
        'sub="Cerca nel magazzino per nome, categoria, fornitore, formato o spessore. Aggiungi i materiali al preventivo con un click."',
        'sub="Seleziona un materiale dalla ricerca, imposta la quantità e aggiungilo al calcolo."',
        'sub="Collega il fornitore a un’area e, quando possibile, alla categoria/sottocategoria che vende. Così negli acquisti non vedrai più suggerimenti generici."',
        'sub="Usa i clienti per preventivi, vendite e storico lavori personalizzati."',
        'sub="Struttura più ordinata per evitare valori fuori contesto, come 12V dentro Falegnameria/Legname."',
    ]

    for x in remove_subs:
        s = s.replace(x, "")

    # Accorcia alcuni testi pagina lunghi.
    s = s.replace(
        'desc="Gestisci schede prodotto, distinta base, produzione e magazzino dei prodotti finiti MN Laser Lab."',
        'desc="Gestisci prodotti, distinta base, produzione e magazzino."'
    )
    s = s.replace(
        'desc="Costruisci il prezzo partendo dai materiali reali del magazzino, poi aggiungi lavoro, consumi, commissioni e margine."',
        'desc="Calcola prezzi e margini partendo dai materiali reali."'
    )
    s = s.replace(
        'desc="Sezione dedicata ai contatti: fornitori per acquistare materiali, clienti per preventivi e vendite."',
        'desc="Gestisci fornitori, clienti e collegamenti al catalogo."'
    )
    s = s.replace(
        'desc="Gestione guidata: scegli l’area, poi categoria e sottocategoria. Formati, spessori e tipologie restano collegati al contesto corretto."',
        'desc="Gestisci aree, categorie, sottocategorie e configurazioni collegate."'
    )

    # Accorcia microcopy laterale.
    s = s.replace(
        'Acquisti → Produzione → Preventivi → Vendite. Backup, import ed export sono in Impostazioni.',
        'Acquisti → Produzione → Preventivi → Vendite.'
    )

    MAIN.write_text(s, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")

    if "/* v40.1.4 global layout alignment */" not in css:
        css += r'''

/* v40.1.4 global layout alignment */

/* --------- Base alignment system --------- */
:root {
  --ui-field-h: 42px;
  --ui-radius: 18px;
  --ui-gap: 12px;
}

.content-main {
  max-width: 1480px;
  margin: 0 auto;
}

.page-title {
  min-height: 132px;
  align-items: center;
}

.page-title h1 {
  line-height: .95;
  letter-spacing: -0.055em;
}

.page-title span {
  line-height: 1.42;
  max-width: 760px;
}

.card {
  overflow: hidden;
}

.card header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  padding-bottom: 12px;
}

.card header > div:first-child {
  min-width: 0;
}

.card header h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 28px;
  margin: 0;
}

.card header h2 svg {
  width: 19px;
  height: 19px;
  flex: 0 0 auto;
}

.card header p {
  margin-top: 4px;
  max-width: 680px;
  line-height: 1.35;
}

.card header p:empty {
  display: none;
}

.card-actions {
  align-self: center;
}

.card-actions button,
.quick-actions button,
button.primary,
button.ghost,
button.danger {
  min-height: var(--ui-field-h);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  white-space: nowrap;
}

/* --------- Inputs and labels --------- */
.form-grid,
.buy-grid,
.small-grid,
.stock-form,
.catalog-editor-grid,
.quote-filters {
  align-items: start;
  gap: var(--ui-gap);
}

.field {
  min-width: 0;
  margin: 0;
}

.field label,
.form-grid label,
.buy-grid label {
  height: 18px;
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  font-size: 11px;
  letter-spacing: .075em;
  text-transform: uppercase;
  color: rgba(226, 232, 240, .88);
}

input,
select,
textarea {
  width: 100%;
  min-height: var(--ui-field-h);
}

textarea {
  resize: vertical;
}

/* --------- Suggestions compact --------- */
.suggestions,
.compact-suggestions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 5px !important;
  margin-top: 6px !important;
  max-height: 30px;
  overflow: hidden;
}

.suggestions button,
.compact-suggestions button {
  height: 24px !important;
  min-height: 24px !important;
  max-height: 24px !important;
  padding: 4px 8px !important;
  max-width: 105px !important;
  font-size: 10px !important;
  line-height: 1 !important;
  border-radius: 999px !important;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.field > small,
.field .hint,
.compact-suggestions small,
.suggestions small {
  display: none !important;
}

/* --------- Acquisti --------- */
.buy-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: start;
}

.buy-grid .name-preview {
  min-height: 88px;
  align-self: end;
  justify-content: center;
}

.name-preview {
  overflow: hidden;
}

.name-preview b,
.name-preview small {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.name-preview b {
  line-height: 1.16;
}

.inventory-quality {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.inventory-quality .stat,
.compact-stats .stat,
.stats .stat {
  min-height: 118px;
}

/* --------- Vendite / clienti / fornitori forms --------- */
.split-main {
  align-items: start;
}

.split-main > .card {
  min-width: 0;
}

.stock-form {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

#supplier-form.form-grid,
#customer-form.form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

#supplier-form .field,
#customer-form .field {
  min-width: 0;
}

/* --------- Produzione --------- */
.section-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.production-panel > .inline {
  grid-template-columns: minmax(0, 1fr) 120px auto auto;
  align-items: end;
}

.production-panel > .inline select,
.production-panel > .inline input,
.production-panel > .inline button {
  height: var(--ui-field-h);
}

.production-row {
  overflow: hidden;
}

.variant-grid {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.variant-card {
  min-width: 0;
  overflow: hidden;
}

.variant-card b,
.variant-card small,
.variant-card em {
  max-width: 100%;
}

.variant-card em {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  min-height: 32px;
  overflow: hidden;
}

.mixed-production-box {
  overflow: hidden;
}

.mix-line {
  min-width: 0;
}

/* --------- Preventivi --------- */
.quote-layout {
  align-items: start;
}

.quote-search-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}

.quote-filters {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.material-browser {
  max-height: 360px;
  overflow-y: auto;
  padding-right: 4px;
}

.material-pick {
  min-height: 70px;
}

.selected-material-box {
  min-height: 140px;
}

.quote-add-line {
  display: grid;
  grid-template-columns: 100px minmax(130px, 1fr) auto;
  gap: 10px;
  align-items: center;
}

.quote-mini-total {
  min-height: var(--ui-field-h);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* --------- Catalogo categorie --------- */
.catalog-topbar {
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
}

.catalog-workbench {
  grid-template-columns:
    minmax(165px, .62fr)
    minmax(245px, .95fr)
    minmax(245px, .95fr)
    minmax(390px, 1.55fr);
  gap: 12px;
  align-items: stretch;
}

.catalog-column {
  min-width: 0;
  max-height: calc(100vh - 250px);
}

.catalog-column-head {
  min-height: 42px;
}

.catalog-column-head b,
.catalog-column-head small {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.catalog-list button {
  min-height: 56px;
  display: grid;
  align-content: center;
}

.catalog-create-box {
  gap: 9px;
}

.catalog-create-box button {
  width: 100%;
}

.catalog-linked {
  overflow-y: auto;
  padding-right: 8px;
}

.catalog-config-card {
  min-width: 0;
}

.catalog-inline-add {
  grid-template-columns: minmax(0, 1fr) 40px;
}

.catalog-inline-add button {
  width: 40px;
  height: 40px;
  min-height: 40px;
}

.pill-list {
  max-height: 126px;
  overflow-y: auto;
}

/* --------- Tables --------- */
.table-card {
  overflow: hidden;
}

.table-wrap {
  overflow-x: auto;
}

.table-wrap table {
  min-width: 760px;
}

.table-wrap th,
.table-wrap td {
  vertical-align: middle;
}

.table-actions {
  justify-content: flex-end;
}

/* --------- Sidebar cleanup --------- */
.side-note {
  line-height: 1.35;
}

.side-note br {
  display: none;
}

/* --------- Responsive --------- */
@media (max-width: 1350px) {
  .buy-grid,
  .quote-filters,
  .stock-form {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .catalog-workbench {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .catalog-linked {
    grid-column: 1 / -1;
  }

  .catalog-column {
    max-height: 540px;
  }
}

@media (max-width: 900px) {
  .page-title {
    min-height: auto;
  }

  .card header {
    grid-template-columns: 1fr;
  }

  .buy-grid,
  .quote-filters,
  .stock-form,
  #supplier-form.form-grid,
  #customer-form.form-grid,
  .catalog-workbench,
  .catalog-topbar,
  .quote-search-head,
  .quote-add-line,
  .production-panel > .inline {
    grid-template-columns: 1fr;
  }

  .inventory-quality {
    grid-template-columns: 1fr 1fr;
  }

  .material-browser {
    max-height: none;
  }

  .catalog-column {
    max-height: none;
  }
}

@media (max-width: 620px) {
  .inventory-quality {
    grid-template-columns: 1fr;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")

    print("Patch v40.1.4 global layout alignment completata.")


if __name__ == "__main__":
    main()
