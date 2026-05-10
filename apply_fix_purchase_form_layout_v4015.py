from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS = ROOT / "frontend" / "src" / "style.css"

def main():
    css = CSS.read_text(encoding="utf-8")

    if "/* v40.1.5 fix purchase form layout */" not in css:
        css += r'''

/* v40.1.5 fix purchase form layout */

/* Reset definitivo: niente posizionamenti manuali che accavallano i campi */
.buy-grid > .field,
.buy-grid > .name-preview {
  grid-column: auto !important;
  grid-row: auto !important;
}

/* Layout acquisto rapido pulito e stabile */
.buy-grid {
  display: grid !important;
  grid-template-columns: repeat(4, minmax(190px, 1fr)) !important;
  gap: 18px 18px !important;
  align-items: start !important;
}

/* Ogni campo resta nel suo spazio */
.buy-grid .field {
  min-width: 0 !important;
  width: 100% !important;
  display: flex !important;
  flex-direction: column !important;
}

/* Label sopra, input sotto */
.buy-grid .field label {
  height: auto !important;
  min-height: 16px !important;
  margin-bottom: 7px !important;
  white-space: nowrap !important;
}

/* Input uniformi */
.buy-grid input,
.buy-grid select {
  width: 100% !important;
  min-width: 0 !important;
  height: 42px !important;
  min-height: 42px !important;
}

/* Suggerimenti: stanno sotto il campo e non invadono gli altri */
.buy-grid .suggestions,
.buy-grid .compact-suggestions {
  position: static !important;
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 5px !important;
  margin-top: 7px !important;
  max-height: 30px !important;
  overflow: hidden !important;
  width: 100% !important;
  z-index: 1 !important;
}

/* Suggerimenti piccoli */
.buy-grid .suggestions button,
.buy-grid .compact-suggestions button {
  height: 24px !important;
  min-height: 24px !important;
  max-height: 24px !important;
  padding: 4px 8px !important;
  font-size: 10px !important;
  max-width: 105px !important;
  border-radius: 999px !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}

/* Nome articolo largo e ordinato */
.buy-grid .name-preview {
  grid-column: span 2 !important;
  width: 100% !important;
  min-height: 88px !important;
  align-self: stretch !important;
}

/* Evita che il costo totale o il nome articolo stringano la riga */
.name-preview b,
.name-preview small {
  max-width: 100% !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

/* La card acquisto rapido deve respirare */
.card:has(.buy-grid) {
  overflow: visible !important;
}

.card:has(.buy-grid) .card-actions {
  align-self: start !important;
}

/* Su schermi medi passa a 2 colonne */
@media (max-width: 1280px) {
  .buy-grid {
    grid-template-columns: repeat(2, minmax(220px, 1fr)) !important;
  }

  .buy-grid .name-preview {
    grid-column: 1 / -1 !important;
  }
}

/* Su mobile una colonna */
@media (max-width: 760px) {
  .buy-grid {
    grid-template-columns: 1fr !important;
  }

  .buy-grid .name-preview {
    grid-column: 1 !important;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")
        print("Patch v40.1.5 fix purchase form layout applicata.")
    else:
        print("Patch già presente.")

if __name__ == "__main__":
    main()
