from pathlib import Path
import re

MAIN = Path("frontend/src/main.jsx")

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

def remove_all_quote_treatment_inline(s):
    pattern = r'\s*<div className="form-grid-full quote-treatment-inline">[\s\S]*?</TreatmentCostPanel>\s*</div>\s*'
    return re.sub(pattern, '\n', s, flags=re.DOTALL)

def main():
    s = MAIN.read_text(encoding="utf-8")

    # 1. Rimuove TUTTI i blocchi quote-treatment-inline, compreso quello finito fuori Quote.
    s = remove_all_quote_treatment_inline(s)

    quote_start = s.find("function Quote(")
    sales_start = s.find("function Sales(", quote_start)

    if quote_start == -1 or sales_start == -1:
        raise RuntimeError("Non trovo function Quote / function Sales")

    quote_block = s[quote_start:sales_start]

    # 2. Assicura hook dentro Quote.
    if "const { data: woodTreatmentsQuote } = useApi('/catalog/wood-treatments', []);" not in quote_block:
        quote_block = quote_block.replace(
            "function Quote({ toast }) {",
            "function Quote({ toast }) {\n  const { data: woodTreatmentsQuote } = useApi('/catalog/wood-treatments', []);",
            1
        )

    if "const [quoteTreatments, setQuoteTreatments] = useState([]);" not in quote_block:
        quote_block = quote_block.replace(
            "const [rows, setRows] = useState([]);",
            "const [rows, setRows] = useState([]);\n  const [quoteTreatments, setQuoteTreatments] = useState([]);",
            1
        )

    # 3. Inserisce il pannello dentro Costi e margini, subito dopo apertura Card.
    card_pos = quote_block.find('<Card title="Costi e margini"')
    if card_pos == -1:
        raise RuntimeError('Dentro Quote non trovo <Card title="Costi e margini"')

    open_end = quote_block.find('>', card_pos)
    if open_end == -1:
        raise RuntimeError("Apertura Card Costi e margini non chiusa")

    quote_block = quote_block[:open_end + 1] + "\n" + PANEL + quote_block[open_end + 1:]

    s = s[:quote_start] + quote_block + s[sales_start:]

    MAIN.write_text(s, encoding="utf-8")
    print("Fix v42.3.0k applicato: quote-treatment-inline ora esiste solo dentro Quote.")

if __name__ == "__main__":
    main()
