from pathlib import Path
import re

MAIN = Path("frontend/src/main.jsx")
CSS = Path("frontend/src/style.css")

NEW_COST_CARD = r'''<Card title="Costi e margini" icon={Calculator} action={<button className="primary" onClick={calc}><Calculator /> Calcola preventivo</button>}>
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

        <div className="form-grid">
          {Object.keys(cost).map(k => <Input key={k} label={costLabels[k] || k} type="number" step="0.01" value={cost[k]} onChange={e => setCost({ ...cost, [k]: e.target.value })} />)}
        </div>
      </Card>

      '''

CSS_BLOCK = r'''
/* v42.3.0o quote treatments final card rebuild */
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

def main():
    s = MAIN.read_text(encoding="utf-8")

    quote_start = s.find("function Quote(")
    sales_start = s.find("function Sales(", quote_start)

    if quote_start == -1 or sales_start == -1:
        raise RuntimeError("Non trovo function Quote / function Sales")

    quote = s[quote_start:sales_start]

    # Assicura hooks corretti dentro Quote.
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

    # Rimuove eventuale card separata trattamenti.
    quote = re.sub(
        r'\s*<Card\s+title="Trattamenti e finiture preventivo"[\s\S]*?</Card>\s*',
        '\n',
        quote,
        flags=re.DOTALL
    )

    # Trova blocco Costi e margini e lo sostituisce fino al Riepilogo rapido.
    cost_start = quote.find('<Card title="Costi e margini"')
    summary_start = quote.find('<Card title="Riepilogo rapido"', cost_start)

    if cost_start == -1:
        raise RuntimeError('Dentro Quote non trovo <Card title="Costi e margini"')

    if summary_start == -1:
        raise RuntimeError('Dentro Quote non trovo <Card title="Riepilogo rapido" dopo Costi e margini')

    quote = quote[:cost_start] + NEW_COST_CARD + quote[summary_start:]

    s = s[:quote_start] + quote + s[sales_start:]

    # Pulizia: se per caso rimangono riferimenti fuori Quote, falliamo con messaggio chiaro.
    new_quote_start = s.find("function Quote(")
    new_sales_start = s.find("function Sales(", new_quote_start)
    outside = s[new_sales_start:]

    if "woodTreatmentsQuote" in outside or "quoteTreatments" in outside or "quote-treatment-inline" in outside:
        raise RuntimeError("Rimangono riferimenti trattamenti fuori Quote. Serve pulizia manuale.")

    MAIN.write_text(s, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")

    css = re.sub(
        r'\n/\* v42\.3\.0[c-z][^*]*quote treatments[\s\S]*?(?=\n/\*|\Z)',
        '\n',
        css,
        flags=re.DOTALL
    )

    if "v42.3.0o quote treatments final card rebuild" not in css:
        css += "\n\n" + CSS_BLOCK.strip() + "\n"

    CSS.write_text(css, encoding="utf-8")

    print("Patch v42.3.0o applicata: card Costi e margini ricostruita da zero.")

if __name__ == "__main__":
    main()
