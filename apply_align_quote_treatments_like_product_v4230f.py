from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"

QUOTE_PANEL = r'''
        <div className="form-grid-full quote-treatment-inline">
          <TreatmentCostPanel
            title="Trattamenti e finiture"
            treatments={woodTreatmentsQuote}
            selectedRows={quoteTreatments}
            setSelectedRows={setQuoteTreatments}
            toast={toast}
            compact
          />
        </div>
'''

CSS_PATCH = r'''
/* v42.3.0f quote treatments aligned like product BOM */
.quote-treatment-inline {
  margin: 4px 0 10px;
}

.quote-treatment-inline .treatment-cost-panel {
  background: rgba(255,255,255,.045);
  border: 1px solid rgba(148, 163, 184, .16);
  border-radius: 22px;
  padding: 16px;
}

.quote-treatment-inline .treatment-picker-grid {
  grid-template-columns: minmax(220px, 1.5fr) minmax(100px, .5fr) minmax(130px, .65fr) auto;
}

.quote-treatment-inline .treatment-add-btn {
  height: 44px;
}

@media (max-width: 980px) {
  .quote-treatment-inline .treatment-picker-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 620px) {
  .quote-treatment-inline .treatment-picker-grid {
    grid-template-columns: 1fr;
  }
}
'''

def main():
    s = MAIN.read_text(encoding="utf-8")

    # 1. Rimuove eventuale card separata rimasta.
    start = s.find('<Card title="Trattamenti e finiture preventivo"')
    if start != -1:
        end = s.find('<Card title="Costi e margini"', start)
        if end != -1:
            s = s[:start] + s[end:]

    # 2. Rimuove il vecchio inserimento dentro Costi e margini con wrapper quote-cost-inner-section.
    s = re.sub(
        r'\n\s*<div className="quote-cost-inner-section">[\s\S]*?<div className="quote-cost-separator"></div>\s*',
        '\n',
        s,
        flags=re.DOTALL
    )

    # 3. Rimuove eventuale quote-treatment-inline precedente per evitare duplicati.
    s = re.sub(
        r'\n\s*<div className="form-grid-full quote-treatment-inline">[\s\S]*?</div>\s*(?=<div className="form-grid">)',
        '\n',
        s,
        flags=re.DOTALL
    )

    # 4. Inserisce il pannello subito prima della form-grid dei costi, dentro la card Costi e margini.
    card_pos = s.find('<Card title="Costi e margini"')
    if card_pos == -1:
        raise RuntimeError('Card "Costi e margini" non trovata')

    form_pos = s.find('<div className="form-grid">', card_pos)
    if form_pos == -1:
        raise RuntimeError('form-grid della card Costi e margini non trovata')

    s = s[:form_pos] + QUOTE_PANEL + "\n        " + s[form_pos:]

    MAIN.write_text(s, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")

    # 5. Rimuove gli stili speciali precedenti che causavano effetto “blocco verde”/allineamento brutto.
    css = re.sub(
        r'\n/\* v42\.3\.0c quote treatments inside costs \*/.*?(?=\n/\*|\Z)',
        '\n',
        css,
        flags=re.DOTALL
    )
    css = re.sub(
        r'\n/\* v42\.3\.0d quote treatments inside costs \*/.*?(?=\n/\*|\Z)',
        '\n',
        css,
        flags=re.DOTALL
    )

    if "v42.3.0f quote treatments aligned like product BOM" not in css:
        css += "\n\n" + CSS_PATCH.strip() + "\n"

    CSS.write_text(css, encoding="utf-8")

    print("Patch v42.3.0f applicata: trattamenti preventivo allineati come scheda prodotto/BOM.")

if __name__ == "__main__":
    main()
