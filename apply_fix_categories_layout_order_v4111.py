from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"

def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    setup_start = s.find("function Setup({ toast })")
    if setup_start == -1:
        raise RuntimeError("function Setup({ toast }) non trovata")

    setup_end = s.find("\nfunction ", setup_start + 1)
    if setup_end == -1:
        setup_end = len(s)

    block = s[setup_start:setup_end]

    widget = "    <CatalogAdvancedSettings toast={toast} refreshTax={refreshTax} refreshSug={refreshSug} />"

    # Rimuove il widget dalla posizione attuale, ovunque sia dentro Setup.
    block = block.replace("\n" + widget, "")
    block = block.replace(widget + "\n", "")

    # Lo inserisce dopo il PageTitle, cercando la riga completa.
    page_title_idx = block.find("<PageTitle")
    if page_title_idx == -1:
        raise RuntimeError("PageTitle dentro Setup non trovato")

    # trova la fine del tag PageTitle, che può essere su una sola riga JSX
    page_title_end = block.find("/>", page_title_idx)
    if page_title_end == -1:
        raise RuntimeError("Fine PageTitle non trovata")

    page_title_end += 2

    block = block[:page_title_end] + "\n" + widget + block[page_title_end:]

    s = s[:setup_start] + block + s[setup_end:]
    FRONTEND.write_text(s, encoding="utf-8")
    print("Pannello aree/trattamenti spostato sotto il titolo Catalogo.")

def patch_css():
    css = CSS.read_text(encoding="utf-8")

    if "/* v41.1.1 categories layout order */" not in css:
        css += r'''

/* v41.1.1 categories layout order */
.catalog-advanced-panel {
  margin-top: 18px;
  margin-bottom: 22px;
}

/* Evita che le nuove card sembrino parte dell'header pagina */
.catalog-advanced-panel > .card {
  min-height: auto;
}

/* La pagina Catalogo deve avere un flusso verticale chiaro:
   1 titolo, 2 strumenti avanzati, 3 gestione catalogo */
.catalog-advanced-panel + .split-main,
.catalog-advanced-panel + .catalog-board,
.catalog-advanced-panel + .catalog-grid,
.catalog-advanced-panel + .setup-catalog-grid {
  margin-top: 4px;
}

/* Su mobile le card avanzate devono stare compatte sotto il titolo */
@media (max-width: 820px) {
  .catalog-advanced-panel {
    margin-top: 14px;
    margin-bottom: 16px;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")
        print("CSS ordine pagina categorie applicato.")
    else:
        print("CSS v41.1.1 già presente.")

def main():
    patch_frontend()
    patch_css()
    print("Patch v41.1.1 completata.")

if __name__ == "__main__":
    main()
