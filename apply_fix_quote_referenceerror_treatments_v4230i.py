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
/* v42.3.0i quote treatments stable inline */
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

.quote-treatment-inline .treatment-cost-head {
  padding-bottom: 12px;
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

def find_function_block(s, name, next_name):
    start = s.find(f"function {name}(")
    if start == -1:
        raise RuntimeError(f"function {name} non trovata")

    end = s.find(f"function {next_name}(", start)
    if end == -1:
        raise RuntimeError(f"function {next_name} non trovata dopo {name}")

    return start, end, s[start:end]

def clean_quote_block(block):
    # Rimuove card separata preventivo.
    block = re.sub(
        r'\s*<Card\s+title="Trattamenti e finiture preventivo"[\s\S]*?</Card>\s*',
        '\n',
        block,
        flags=re.DOTALL
    )

    # Rimuove vecchi wrapper.
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

def ensure_quote_hooks(block):
    # Subito dopo function Quote({ toast }) {
    if "const { data: woodTreatmentsQuote } = useApi('/catalog/wood-treatments', []);" not in block:
        block = block.replace(
            "function Quote({ toast }) {",
            "function Quote({ toast }) {\n  const { data: woodTreatmentsQuote } = useApi('/catalog/wood-treatments', []);",
            1
        )

    # Dopo const [rows, setRows]
    if "const [quoteTreatments, setQuoteTreatments] = useState([]);" not in block:
        block = block.replace(
            "const [rows, setRows] = useState([]);",
            "const [rows, setRows] = useState([]);\n  const [quoteTreatments, setQuoteTreatments] = useState([]);",
            1
        )

    return block

def ensure_calc_uses_treatments(block):
    # Se calc non usa quoteRowsForCalc, patcha in modo conservativo.
    if "const quoteRowsForCalc = [...rows, ...quoteTreatments];" not in block:
        block = block.replace(
            "async function calc() {",
            "async function calc() {\n    const quoteRowsForCalc = [...rows, ...quoteTreatments];",
            1
        )

    block = block.replace(
        "postJSON('/quote/calculate', { rows, estimated_materials: [], ...cost })",
        "postJSON('/quote/calculate', { rows: quoteRowsForCalc, treatments: quoteTreatments, treatment_rows: quoteTreatments, estimated_materials: [], ...cost })"
    )

    return block

def insert_panel_inside_cost_card(block):
    card_pos = block.find('<Card title="Costi e margini"')
    if card_pos == -1:
        raise RuntimeError('Dentro Quote non trovo <Card title="Costi e margini"')

    open_end = block.find('>', card_pos)
    if open_end == -1:
        raise RuntimeError("Tag apertura Costi e margini non chiuso")

    return block[:open_end + 1] + "\n" + PANEL + block[open_end + 1:]

def patch_main():
    s = MAIN.read_text(encoding="utf-8")

    start, end, block = find_function_block(s, "Quote", "Sales")

    block = clean_quote_block(block)
    block = ensure_quote_hooks(block)
    block = ensure_calc_uses_treatments(block)
    block = insert_panel_inside_cost_card(block)

    s = s[:start] + block + s[end:]
    MAIN.write_text(s, encoding="utf-8")

    print("Quote riparata: hook trattamenti definiti e pannello reinserito dentro Costi e margini.")

def patch_css():
    css = CSS.read_text(encoding="utf-8")

    # Rimuove vecchi stili quote trattamenti c/d/f/g/h, lasciando intatti gli stili base TreatmentCostPanel.
    css = re.sub(
        r'\n/\* v42\.3\.0[cdefghi][^*]*quote treatments[\s\S]*?(?=\n/\*|\Z)',
        '\n',
        css,
        flags=re.DOTALL
    )

    if "v42.3.0i quote treatments stable inline" not in css:
        css += "\n\n" + CSS_BLOCK.strip() + "\n"

    CSS.write_text(css, encoding="utf-8")
    print("CSS quote trattamenti stabilizzato.")

def main():
    patch_main()
    patch_css()
    print("Patch v42.3.0i completata.")

if __name__ == "__main__":
    main()
