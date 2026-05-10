from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS = ROOT / "frontend" / "src" / "style.css"

def main():
    css = CSS.read_text(encoding="utf-8")

    if "/* v40.1.1 catalog layout polish */" not in css:
        css += r'''

/* v40.1.1 catalog layout polish */

/* Evita overflow orizzontali brutti nella pagina Catalogo */
.content-main,
main,
.card,
.catalog-workbench,
.catalog-column,
.catalog-config-card,
.catalog-create-box,
.catalog-selected-box {
  min-width: 0;
}

/* La workbench non deve uscire dalla finestra */
.catalog-workbench {
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  grid-template-columns:
    minmax(170px, 0.72fr)
    minmax(230px, 1fr)
    minmax(230px, 1fr)
    minmax(300px, 1.18fr);
  gap: 12px;
}

/* Colonne più compatte e professionali */
.catalog-column {
  min-height: 0;
  max-height: calc(100vh - 270px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 12px;
}

/* Header fisso, contenuto scrollabile */
.catalog-column-head {
  flex: 0 0 auto;
  margin-bottom: 10px;
}

.catalog-list {
  flex: 1 1 auto;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 4px;
  align-content: start;
}

/* Scrollbar meno invasiva */
.catalog-list::-webkit-scrollbar,
.detail-modal-body::-webkit-scrollbar {
  width: 8px;
}

.catalog-list::-webkit-scrollbar-thumb,
.detail-modal-body::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, .28);
  border-radius: 999px;
}

.catalog-list::-webkit-scrollbar-track,
.detail-modal-body::-webkit-scrollbar-track {
  background: transparent;
}

/* Card interne più ordinate */
.catalog-list button {
  width: 100%;
  min-height: 58px;
  padding: 10px 11px;
  overflow: hidden;
}

.catalog-list button b,
.catalog-list button small {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.catalog-list button b {
  white-space: nowrap;
}

.catalog-list button small {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* Box creazione categoria più compatto */
.catalog-create-box {
  flex: 0 0 auto;
  padding: 10px;
  gap: 8px;
}

.catalog-create-box .field {
  margin: 0;
}

.catalog-create-box input,
.catalog-create-box select,
.catalog-create-box button {
  min-height: 38px;
}

/* Box categoria selezionata */
.catalog-selected-box {
  flex: 0 0 auto;
  padding: 10px;
}

.catalog-selected-box b {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Configurazioni a destra: non devono allargare la colonna */
.catalog-linked {
  gap: 10px;
}

.catalog-config-card {
  flex: 0 0 auto;
  padding: 11px;
  overflow: hidden;
}

.catalog-config-head {
  min-width: 0;
}

.catalog-config-head b,
.catalog-config-head small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Input + bottone nei formati/spessori/tipologie */
.catalog-inline-add {
  grid-template-columns: minmax(0, 1fr) 38px;
  gap: 7px;
}

.catalog-inline-add .field {
  min-width: 0;
}

.catalog-inline-add input {
  min-width: 0;
  height: 38px;
}

.catalog-inline-add button {
  width: 38px;
  height: 38px;
  min-width: 38px;
  min-height: 38px;
  padding: 0;
}

/* Pill ordinate, massimo controllo spazio */
.pill-list {
  max-height: 116px;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 3px;
}

.pill-list > span {
  max-width: 100%;
  min-width: 0;
  min-height: 28px;
  padding: 6px 8px;
}

.pill-list > span {
  overflow: hidden;
}

.pill-list > span button {
  flex-shrink: 0;
}

.pill-list > span::first-letter {
  text-transform: uppercase;
}

/* Topbar catalogo allineata */
.catalog-topbar {
  grid-template-columns: minmax(0, auto) minmax(260px, 1fr);
  align-items: center;
}

.catalog-mode-tabs {
  min-width: 0;
}

.catalog-mode-tabs button {
  min-height: 38px;
  padding: 9px 13px;
}

/* Sezione prodotti finiti più ordinata */
.catalog-editor-grid {
  width: 100%;
  max-width: 100%;
  grid-template-columns: repeat(3, minmax(0, 1fr)) auto;
}

.catalog-editor-grid .field {
  min-width: 0;
}

/* Tabelle più compatte dentro catalogo */
.catalog-workbench + .split-main .table-card,
.card .table-card {
  min-width: 0;
}

.table-card {
  max-width: 100%;
}

.table-wrap {
  max-width: 100%;
}

/* Titoli lunghi nelle tabelle */
.table-wrap td,
.table-wrap th {
  overflow-wrap: anywhere;
}

/* Responsive migliore: evita 4 colonne quando lo spazio non basta */
@media (max-width: 1500px) {
  .catalog-workbench {
    grid-template-columns:
      minmax(160px, .75fr)
      minmax(220px, 1fr)
      minmax(220px, 1fr)
      minmax(280px, 1.1fr);
  }

  .catalog-column {
    max-height: calc(100vh - 285px);
  }
}

@media (max-width: 1280px) {
  .catalog-workbench {
    grid-template-columns: 1fr 1fr;
    overflow: visible;
  }

  .catalog-column {
    max-height: 520px;
  }

  .catalog-linked {
    grid-column: 1 / -1;
  }

  .catalog-linked .catalog-config-card {
    max-width: 100%;
  }
}

@media (max-width: 900px) {
  .catalog-topbar {
    grid-template-columns: 1fr;
  }

  .catalog-mode-tabs {
    width: 100%;
  }

  .catalog-mode-tabs button {
    flex: 1 1 auto;
  }

  .catalog-workbench {
    grid-template-columns: 1fr;
  }

  .catalog-column {
    max-height: none;
    overflow: visible;
  }

  .catalog-list {
    max-height: 360px;
  }

  .catalog-editor-grid {
    grid-template-columns: 1fr;
  }
}

/* Distinzione visiva tra aree materiali/componenti/prodotti */
.catalog-areas .catalog-list button:nth-child(1).selected {
  border-color: rgba(34, 211, 238, .58);
}

.catalog-areas .catalog-list button:nth-child(2).selected {
  border-color: rgba(184, 137, 75, .68);
}

.catalog-areas .catalog-list button:nth-child(3).selected {
  border-color: rgba(250, 204, 21, .62);
}
'''
        CSS.write_text(css, encoding="utf-8")
        print("Patch v40.1.1 catalog layout polish applicata.")
    else:
        print("Patch v40.1.1 già presente.")

if __name__ == "__main__":
    main()
