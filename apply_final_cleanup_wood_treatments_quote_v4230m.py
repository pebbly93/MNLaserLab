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
/* v42.3.0m quote treatments final stable */
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

def remove_quote_inline_wrappers(s: str) -> str:
    marker = '<div className="form-grid-full quote-treatment-inline">'
    removed = 0

    while marker in s:
        start = s.find(marker)

        # Il nostro wrapper deve contenere TreatmentCostPanel. Rimuoviamo fino al primo </div> dopo il pannello.
        panel_start = s.find('<TreatmentCostPanel', start)
        if panel_start == -1:
            end = s.find('</div>', start)
            if end == -1:
                break
            s = s[:start] + "\n" + s[end + len('</div>'):]
            removed += 1
            continue

        # Supporta sia componente self-closing /> che componente chiuso </TreatmentCostPanel>
        self_close = s.find('/>', panel_start)
        explicit_close = s.find('</TreatmentCostPanel>', panel_start)

        if explicit_close != -1 and (self_close == -1 or explicit_close < self_close):
            panel_end = explicit_close + len('</TreatmentCostPanel>')
        elif self_close != -1:
            panel_end = self_close + len('/>')
        else:
            raise RuntimeError("TreatmentCostPanel senza chiusura")

        wrapper_end = s.find('</div>', panel_end)
        if wrapper_end == -1:
            raise RuntimeError("Wrapper quote-treatment-inline senza </div>")

        s = s[:start] + "\n" + s[wrapper_end + len('</div>'):]
        removed += 1

    print(f"Wrapper quote-treatment-inline rimossi: {removed}")
    return s

def remove_orphan_treatment_panels_using_quote_vars(s: str) -> str:
    removed = 0

    while "woodTreatmentsQuote" in s:
        pos = s.find("woodTreatmentsQuote")

        # Se è la dichiarazione hook dentro Quote, non rimuoverla.
        line_start = s.rfind("\n", 0, pos) + 1
        line_end = s.find("\n", pos)
        line = s[line_start:line_end if line_end != -1 else len(s)]

        if "const { data: woodTreatmentsQuote }" in line:
            # Proteggiamo temporaneamente la dichiarazione per poter rimuovere gli altri riferimenti.
            s = s[:pos] + "WOOD_TREATMENTS_QUOTE_SAFE_TOKEN" + s[pos + len("woodTreatmentsQuote"):]
            continue

        # Rimuove l'intero componente TreatmentCostPanel che contiene woodTreatmentsQuote.
        comp_start = s.rfind('<TreatmentCostPanel', 0, pos)
        if comp_start == -1:
            # fallback: rimuove la riga orfana
            s = s[:line_start] + s[(line_end + 1 if line_end != -1 else len(s)):]
            removed += 1
            continue

        self_close = s.find('/>', pos)
        explicit_close = s.find('</TreatmentCostPanel>', pos)

        if explicit_close != -1 and (self_close == -1 or explicit_close < self_close):
            comp_end = explicit_close + len('</TreatmentCostPanel>')
        elif self_close != -1:
            comp_end = self_close + len('/>')
        else:
            # fallback fino a 10 righe dopo
            comp_end = pos
            for _ in range(10):
                nxt = s.find("\n", comp_end + 1)
                if nxt == -1:
                    comp_end = len(s)
                    break
                comp_end = nxt

        # rimuove anche spazi/newline vicini
        s = s[:comp_start] + "\n" + s[comp_end:]
        removed += 1

    s = s.replace("WOOD_TREATMENTS_QUOTE_SAFE_TOKEN", "woodTreatmentsQuote")
    print(f"TreatmentCostPanel orfani rimossi: {removed}")
    return s

def clean_duplicate_hooks_inside_quote(quote: str) -> str:
    # Tiene una sola dichiarazione useApi e uno solo useState.
    hook = "  const { data: woodTreatmentsQuote } = useApi('/catalog/wood-treatments', []);\n"
    state = "  const [quoteTreatments, setQuoteTreatments] = useState([]);\n"

    quote = quote.replace(hook, "")
    quote = quote.replace(state, "")

    quote = quote.replace(
        "function Quote({ toast }) {",
        "function Quote({ toast }) {\n" + hook.rstrip(),
        1
    )

    quote = quote.replace(
        "const [rows, setRows] = useState([]);",
        "const [rows, setRows] = useState([]);\n" + state.rstrip(),
        1
    )

    return quote

def main():
    s = MAIN.read_text(encoding="utf-8")

    # 1. Elimina card separata preventivo, se ancora presente.
    while '<Card title="Trattamenti e finiture preventivo"' in s:
        start = s.find('<Card title="Trattamenti e finiture preventivo"')
        next_card = s.find('<Card title="Costi e margini"', start)
        if next_card == -1:
            break
        s = s[:start] + s[next_card:]

    # 2. Elimina wrapper e pannelli orfani.
    s = remove_quote_inline_wrappers(s)
    s = remove_orphan_treatment_panels_using_quote_vars(s)

    # 3. Ricostruisce solo dentro Quote.
    quote_start = s.find("function Quote(")
    sales_start = s.find("function Sales(", quote_start)

    if quote_start == -1 or sales_start == -1:
        raise RuntimeError("Non trovo function Quote / function Sales")

    quote = s[quote_start:sales_start]
    quote = clean_duplicate_hooks_inside_quote(quote)

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

    if "v42.3.0m quote treatments final stable" not in css:
        css += "\n\n" + CSS_BLOCK.strip() + "\n"

    CSS.write_text(css, encoding="utf-8")

    print("Patch v42.3.0m completata: resta un solo pannello trattamenti dentro Quote.")

if __name__ == "__main__":
    main()
