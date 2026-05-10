from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS = ROOT / "frontend" / "src" / "style.css"

def main():
    css = CSS.read_text(encoding="utf-8")

    if "/* v40.7.4 material detail modal layout */" not in css:
        css += r'''

/* v40.7.4 material detail modal layout */

/* Modal dettaglio materiale: reset layout professionale */
.detail-modal,
.detail-modal * {
  box-sizing: border-box;
}

.detail-modal {
  max-width: 1180px;
  width: min(1180px, calc(100vw - 64px));
  max-height: calc(100vh - 80px);
  overflow: hidden;
}

.detail-modal-body {
  overflow-y: auto;
  overflow-x: hidden;
  padding: 22px 24px 26px;
}

/* Hero articolo */
.detail-hero {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  align-items: center;
  width: 100%;
  margin-bottom: 18px;
}

.detail-hero > div {
  min-width: 0;
}

.detail-hero b,
.detail-hero strong,
.detail-hero small,
.detail-hero span {
  max-width: 100%;
}

/* Statistiche dettaglio materiale */
.detail-stats,
.material-detail-stats {
  display: grid !important;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 22px;
}

.detail-stats .stat,
.material-detail-stats .stat {
  min-width: 0;
  min-height: 116px;
}

/* Sezione sotto: storico acquisti + usato nei prodotti */
.detail-split,
.material-detail-grid,
.material-detail-sections {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 18px;
  align-items: start;
  width: 100%;
  min-width: 0;
}

/* Se non esiste una classe dedicata, intercetta le due card/tabelle nel modal */
.detail-modal-body > .split-main,
.detail-modal-body .split-main {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
  gap: 18px !important;
  align-items: start !important;
  width: 100% !important;
  min-width: 0 !important;
}

/* Card interne nel modal */
.detail-modal .card,
.detail-modal section,
.detail-modal .table-card {
  min-width: 0 !important;
  max-width: 100% !important;
}

/* Tabelle nel dettaglio: niente colonne schiacciate strane */
.detail-modal .table-card {
  width: 100%;
  overflow: hidden !important;
}

.detail-modal .table-meta {
  display: flex !important;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  margin-bottom: 10px;
}

.detail-modal .table-wrap {
  width: 100%;
  max-width: 100%;
  overflow-x: auto !important;
  overflow-y: hidden;
  border-radius: 16px;
}

.detail-modal .table-wrap table {
  width: 100% !important;
  min-width: 520px !important;
  table-layout: fixed;
}

.detail-modal .table-wrap th,
.detail-modal .table-wrap td {
  padding: 13px 14px !important;
  vertical-align: middle;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Prima colonna più leggibile */
.detail-modal .table-wrap th:first-child,
.detail-modal .table-wrap td:first-child {
  width: 34%;
}

/* Evita il badge “1 righe” enorme/verticale */
.detail-modal .table-meta b,
.detail-modal .table-card > .table-meta b {
  display: inline-flex !important;
  width: auto !important;
  min-width: auto !important;
  height: auto !important;
  min-height: 28px !important;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 6px 10px !important;
  white-space: nowrap !important;
}

/* Empty state dentro tabelle */
.detail-modal .empty {
  min-height: 160px;
  padding: 24px;
}

/* Pulsanti bottom/detail, evita overflow */
.detail-modal button {
  white-space: nowrap;
}

/* Responsive */
@media (max-width: 1100px) {
  .detail-modal {
    width: min(980px, calc(100vw - 36px));
  }

  .detail-stats,
  .material-detail-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .detail-modal-body > .split-main,
  .detail-modal-body .split-main,
  .detail-split,
  .material-detail-grid,
  .material-detail-sections {
    grid-template-columns: 1fr !important;
  }
}

@media (max-width: 720px) {
  .detail-modal {
    width: calc(100vw - 20px);
    max-height: calc(100vh - 32px);
  }

  .detail-modal-body {
    padding: 16px;
  }

  .detail-hero {
    grid-template-columns: 1fr !important;
  }

  .detail-stats,
  .material-detail-stats {
    grid-template-columns: 1fr;
  }

  .detail-modal .table-wrap table {
    min-width: 560px !important;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")
        print("Patch v40.7.4 applicata: layout dettaglio materiale sistemato.")
    else:
        print("Patch v40.7.4 già presente.")

if __name__ == "__main__":
    main()
