from pathlib import Path
import re

MAIN = Path("frontend/src/main.jsx")
CSS = Path("frontend/src/style.css")

PANEL = '''
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

CSS_BLOCK = '''
/* v42.3.0h quote treatments scoped fix */
.quote-treatment-inline {
  grid-column: 1 / -1;
  margin: 0 0 12px;
}

.quote-treatment-inline .treatment-cost-panel {
  background: rgba(255,255,255,.045);
  border: 1px solid rgba(148, 163, 184, .16);
  border-radius: 22px;
  padding: 16px;
  box-shadow: none;
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

def get_quote_block(s):
    start = s.find("function Quote(")
    if start == -1:
        raise RuntimeError("function Quote non trovata")

    # la funzione dopo Quote nel file è Sales
    end = s.find("function Sales(", start)
    if end == -1:
        raise RuntimeError("function Sales non trovata dopo Quote")

    return start, end, s[start:end]

def clean_quote_block(block):
    # Rimuove la card separata preventivo se esiste
    block = re.sub(
        r'\s*<Card\s+title="Trattamenti e finiture preventivo"[\s\S]*?</Card>\s*',
        '\n      ',
        block,
        flags=re.DOTALL
    )

    # Rimuove vecchi inserimenti dentro Costi e margini
    block = re.sub(
        r'\s*<div className="quote-cost-inner-section">[\s\S]*?<div className="quote-cost-separator"></div>\s*',
        '\n',
        block,
        flags=re.DOTALL
    )

    block = re.sub(
        r'\s*<div className="form-grid-full quote-treatment-inline">[\s\S]*?</TreatmentCostPanel>\s*</div>\s*',
        '\n',
        block,
        flags=re.DOTALL
    )

    return block

def insert_panel(block):
    card_pos = block.find('<Card title="Costi e margini"')
    if card_pos == -1:
        raise RuntimeError('Dentro Quote non trovo <Card title="Costi e margini"')

    # Trova la chiusura del tag di apertura della Card, anche se multilinea
    open_end = block.find('>', card_pos)
    if open_end == -1:
        raise RuntimeError("Tag Card Costi e margini non chiuso")

    # Inserisce subito dopo apertura Card, prima della form-grid dei costi
    return block[:open_end + 1] + "\n" + PANEL + block[open_end + 1:]

def patch_main():
    s = MAIN.read_text(encoding="utf-8")
    start, end, block = get_quote_block(s)

    block = clean_quote_block(block)
    block = insert_panel(block)

    s = s[:start] + block + s[end:]
    MAIN.write_text(s, encoding="utf-8")

    print("Quote ripulita: trattamenti inseriti dentro Costi e margini.")

def patch_css():
    css = CSS.read_text(encoding="utf-8")

    # Rimuove vecchi blocchi quote trattamenti
    css = re.sub(
        r'\n/\* v42\.3\.0[cdefg][^*]*quote treatments[\s\S]*?(?=\n/\*|\Z)',
        '\n',
        css,
        flags=re.DOTALL
    )

    if "v42.3.0h quote treatments scoped fix" not in css:
        css += "\n\n" + CSS_BLOCK.strip() + "\n"

    CSS.write_text(css, encoding="utf-8")
    print("CSS quote trattamenti ripulito.")

def main():
    patch_main()
    patch_css()
    print("Patch v42.3.0h completata.")

if __name__ == "__main__":
    main()
