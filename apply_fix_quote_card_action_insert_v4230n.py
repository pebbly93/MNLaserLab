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

def remove_all_quote_panels(s):
    # Rimuove tutti i wrapper quote-treatment-inline, anche se finiti in mezzo al button.
    pattern = r'\s*<div className="form-grid-full quote-treatment-inline">[\s\S]*?</TreatmentCostPanel>\s*</div>\s*'
    s = re.sub(pattern, '\n', s, flags=re.DOTALL)

    # Rimuove eventuale card separata vecchia.
    pattern2 = r'\s*<Card\s+title="Trattamenti e finiture preventivo"[\s\S]*?</Card>\s*'
    s = re.sub(pattern2, '\n', s, flags=re.DOTALL)

    return s

def main():
    s = MAIN.read_text(encoding="utf-8")

    s = remove_all_quote_panels(s)

    quote_start = s.find("function Quote(")
    sales_start = s.find("function Sales(", quote_start)

    if quote_start == -1 or sales_start == -1:
        raise RuntimeError("Non trovo function Quote / function Sales")

    quote = s[quote_start:sales_start]

    # Assicura dichiarazioni dentro Quote.
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

    card_pos = quote.find('<Card title="Costi e margini"')
    if card_pos == -1:
        raise RuntimeError('Dentro Quote non trovo <Card title="Costi e margini"')

    # Qui è il punto corretto: fine action button + fine tag Card opening.
    action_end = quote.find('</button>}>', card_pos)
    if action_end == -1:
        raise RuntimeError('Non trovo chiusura action </button>}> della Card Costi e margini')

    insert_at = action_end + len('</button>}>')

    quote = quote[:insert_at] + "\n" + PANEL + quote[insert_at:]

    s = s[:quote_start] + quote + s[sales_start:]

    MAIN.write_text(s, encoding="utf-8")

    print("Fix v42.3.0n applicato: pannello trattamenti inserito dopo action button della Card.")

if __name__ == "__main__":
    main()
