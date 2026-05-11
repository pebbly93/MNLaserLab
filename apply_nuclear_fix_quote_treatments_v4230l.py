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
/* v42.3.0l quote treatments stable */
.quote-treatment-inline {
  grid-column: 1 / -1;
  margin: 0 0 14px;
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

def remove_all_inline_blocks(s):
    marker = '<div className="form-grid-full quote-treatment-inline">'
    removed = 0

    while marker in s:
        start = s.find(marker)
        end_marker = '</TreatmentCostPanel>'
        end = s.find(end_marker, start)

        if end == -1:
            # fallback brutale: rimuove la riga marker
            line_end = s.find("\n", start)
            s = s[:start] + s[line_end + 1:]
            removed += 1
            continue

        end = s.find('</div>', end)
        if end == -1:
            raise RuntimeError("Trovato quote-treatment-inline ma non trovo chiusura </div>")

        end += len('</div>')
        s = s[:start] + "\n" + s[end:]
        removed += 1

    return s, removed

def main():
    s = MAIN.read_text(encoding="utf-8")

    # Rimuove card separata vecchia, se presente.
    while '<Card title="Trattamenti e finiture preventivo"' in s:
        start = s.find('<Card title="Trattamenti e finiture preventivo"')
        next_card = s.find('<Card title="Costi e margini"', start)
        if next_card == -1:
            break
        s = s[:start] + s[next_card:]

    # Rimuove TUTTI i blocchi quote-treatment-inline ovunque siano finiti.
    s, removed = remove_all_inline_blocks(s)

    quote_start = s.find("function Quote(")
    sales_start = s.find("function Sales(", quote_start)

    if quote_start == -1 or sales_start == -1:
        raise RuntimeError("Non trovo function Quote / function Sales")

    quote = s[quote_start:sales_start]

    # Hook trattamenti dentro Quote.
    if "const { data: woodTreatmentsQuote } = useApi('/catalog/wood-treatments', []);" not in quote:
        quote = quote.replace(
            "function Quote({ toast }) {",
            "function Quote({ toast }) {\n  const { data: woodTreatmentsQuote } = useApi('/catalog/wood-treatments', []);",
            1
        )

    if "const [quoteTreatments, setQuoteTreatments] = useState([]);" not in quote:
        quote = quote.replace(
            "const [rows, setRows] = useState([]);",
            "const [rows, setRows] = useState([]);\n  const [quoteTreatments, setQuoteTreatments] = useState([]);",
            1
        )

    # Inserisce pannello dentro Costi e margini.
    card_pos = quote.find('<Card title="Costi e margini"')
    if card_pos == -1:
        raise RuntimeError('Dentro Quote non trovo <Card title="Costi e margini"')

    card_open_end = quote.find('>', card_pos)
    if card_open_end == -1:
        raise RuntimeError("Tag apertura Costi e margini non chiuso")

    quote = quote[:card_open_end + 1] + "\n" + PANEL + quote[card_open_end + 1:]

    s = s[:quote_start] + quote + s[sales_start:]

    MAIN.write_text(s, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(
        r'\n/\* v42\.3\.0[c-z][^*]*quote treatments[\s\S]*?(?=\n/\*|\Z)',
        '\n',
        css,
        flags=re.DOTALL
    )

    if "v42.3.0l quote treatments stable" not in css:
        css += "\n\n" + CSS_BLOCK.strip() + "\n"

    CSS.write_text(css, encoding="utf-8")

    print(f"Patch v42.3.0l applicata. Blocchi rimossi: {removed}. Reinserito 1 blocco dentro Quote.")

if __name__ == "__main__":
    main()
