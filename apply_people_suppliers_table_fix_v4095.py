from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS = ROOT / "frontend" / "src" / "style.css"

def main():
    css = CSS.read_text(encoding="utf-8")

    if "/* v40.9.5 people suppliers table fix */" not in css:
        css += r'''

/* v40.9.5 people suppliers table fix */

/* Pagina Clienti e fornitori: evita testo verticale nella tabella fornitori */
.people-grid,
.people-page,
.people-section {
  min-width: 0;
}

/* Le tabelle nella pagina contatti devono potersi allargare e scrollare */
.table-wrap {
  max-width: 100%;
}

/* Fix generale anti-testo-lettera-per-lettera */
td,
th {
  word-break: normal !important;
  overflow-wrap: normal !important;
  white-space: normal;
}

/* Colonna azioni esclusa: può restare compatta */
td:last-child,
th:last-child {
  white-space: nowrap;
}

/* Tabella fornitori: larghezze minime leggibili */
.suppliers-table,
.people-suppliers-table {
  min-width: 760px;
  table-layout: fixed;
}

.suppliers-table th:nth-child(1),
.suppliers-table td:nth-child(1),
.people-suppliers-table th:nth-child(1),
.people-suppliers-table td:nth-child(1) {
  width: 180px;
  min-width: 180px;
  white-space: nowrap !important;
}

.suppliers-table th:nth-child(2),
.suppliers-table td:nth-child(2),
.people-suppliers-table th:nth-child(2),
.people-suppliers-table td:nth-child(2) {
  width: 180px;
  min-width: 180px;
  white-space: nowrap !important;
}

.suppliers-table th:nth-child(3),
.suppliers-table td:nth-child(3),
.people-suppliers-table th:nth-child(3),
.people-suppliers-table td:nth-child(3) {
  width: auto;
  min-width: 320px;
}

/* Fallback se la tabella non ha classi dedicate: prima tabella della pagina clienti/fornitori */
.card:has([data-people-suppliers]) table,
.card:has(.supplier-links-cell) table {
  min-width: 760px;
  table-layout: fixed;
}

/* Celle link categorie fornitori */
.supplier-links-cell,
.supplier-sections-cell,
.muted-cell {
  word-break: normal !important;
  overflow-wrap: anywhere;
  line-height: 1.45;
}

/* Nome e aree fornitore non devono mai andare verticali */
.supplier-name-cell,
.supplier-area-cell {
  white-space: nowrap !important;
  word-break: keep-all !important;
  overflow-wrap: normal !important;
}

/* Se la card è stretta, meglio scroll orizzontale invece di distruggere il testo */
.card .table-wrap {
  overflow-x: auto !important;
}

/* Migliore leggibilità righe fornitori/clienti */
.card .table-wrap td {
  min-height: 54px;
  vertical-align: middle !important;
}

/* Evita che la tabella fornitori venga schiacciata dalle due colonne della pagina */
@media (max-width: 1400px) {
  .split-main:has(.people-suppliers-table),
  .split-main:has(.suppliers-table) {
    grid-template-columns: 1fr !important;
  }
}

@media (max-width: 900px) {
  .suppliers-table,
  .people-suppliers-table {
    min-width: 680px;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")
        print("CSS fix tabella fornitori applicato.")
    else:
        print("Fix già presente.")

if __name__ == "__main__":
    main()
