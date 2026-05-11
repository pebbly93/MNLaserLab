from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"

PANEL = r'''
        <div className="quote-cost-inner-section">
          <TreatmentCostPanel
            title="Trattamenti e finiture"
            treatments={woodTreatmentsQuote}
            selectedRows={quoteTreatments}
            setSelectedRows={setQuoteTreatments}
            toast={toast}
            compact
          />
        </div>

        <div className="quote-cost-separator"></div>
'''

CSS_BLOCK = r'''
/* v42.3.0d quote treatments inside costs */
.quote-cost-inner-section {
  margin-bottom: 14px;
}

.quote-cost-inner-section .treatment-cost-panel {
  background: rgba(15, 23, 42, .24);
  border-color: rgba(5, 132, 130, .20);
  border-radius: 18px;
}

.quote-cost-inner-section .treatment-cost-head {
  padding-bottom: 10px;
}

.quote-cost-inner-section .treatment-cost-head b {
  font-size: 15px;
}

.quote-cost-inner-section .treatment-cost-head span {
  font-size: 12px;
}

.quote-cost-inner-section .treatment-picker-grid {
  grid-template-columns: minmax(170px, 1.2fr) minmax(90px, .45fr) minmax(120px, .55fr) auto;
}

.quote-cost-separator {
  height: 1px;
  background: rgba(148, 163, 184, .14);
  margin: 2px 0 14px;
}

@media (max-width: 980px) {
  .quote-cost-inner-section .treatment-picker-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 620px) {
  .quote-cost-inner-section .treatment-picker-grid {
    grid-template-columns: 1fr;
  }
}
'''

def remove_separate_quote_treatment_card(s: str) -> str:
    # Rimuove solo la card separata dei preventivi.
    pattern = r'''
\s*<Card\s+title="Trattamenti e finiture preventivo"[\s\S]*?
\s*</Card>\s*
(?=\s*<Card\s+title="Costi e margini")
'''
    s2 = re.sub(pattern, "\n      ", s, flags=re.VERBOSE)

    # Fallback se la card non è immediatamente prima di Costi e margini.
    pattern2 = r'''
\s*<Card\s+title="Trattamenti e finiture preventivo"[\s\S]*?
\s*</Card>\s*
'''
    s2 = re.sub(pattern2, "\n      ", s2, flags=re.VERBOSE)

    return s2

def insert_panel_inside_costs(s: str) -> str:
    if "quote-cost-inner-section" in s:
        return s

    # Trova apertura card Costi e margini, anche se spezzata su più righe.
    m = re.search(r'(<Card\s+title="Costi e margini"[\s\S]*?>)', s)
    if not m:
        raise RuntimeError('Card "Costi e margini" non trovata. Esegui: grep -n "Costi e margini" frontend/src/main.jsx')

    insert_at = m.end()
    return s[:insert_at] + "\n" + PANEL + s[insert_at:]

def patch_main():
    s = MAIN.read_text(encoding="utf-8")
    s = remove_separate_quote_treatment_card(s)
    s = insert_panel_inside_costs(s)
    MAIN.write_text(s, encoding="utf-8")
    print("Quote: trattamenti spostati dentro Costi e margini.")

def patch_css():
    css = CSS.read_text(encoding="utf-8")

    css = re.sub(
        r"\n/\* v42\.3\.0c quote treatments inside costs \*/.*?(?=\n/\*|\Z)",
        "\n",
        css,
        flags=re.DOTALL
    )

    if "v42.3.0d quote treatments inside costs" not in css:
        css += "\n\n" + CSS_BLOCK.strip() + "\n"

    CSS.write_text(css, encoding="utf-8")
    print("CSS aggiornato.")

def main():
    patch_main()
    patch_css()
    print("Patch v42.3.0d completata.")

if __name__ == "__main__":
    main()
