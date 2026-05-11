from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"

def patch_main():
    s = MAIN.read_text(encoding="utf-8")

    # Rimuove la card separata "Trattamenti e finiture preventivo"
    s = re.sub(
        r'''
\s*<Card\s+title="Trattamenti e finiture preventivo"[\s\S]*?
\s*</Card>\s*
(?=\s*<Card\s+title="Costi e margini")
''',
        "\n      ",
        s,
        flags=re.VERBOSE
    )

    # Inserisce il pannello trattamenti dentro "Costi e margini", subito prima della form-grid dei costi.
    marker = '''<Card title="Costi e margini" icon={Calculator} action={<button className="primary" onClick={calc}><Calculator /> Calcola preventivo</button>}>
        <div className="form-grid">'''

    replacement = '''<Card title="Costi e margini" icon={Calculator} action={<button className="primary" onClick={calc}><Calculator /> Calcola preventivo</button>}>
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

        <div className="form-grid">'''

    if marker not in s:
        raise RuntimeError("Card Costi e margini non trovata nel formato atteso")

    if "quote-cost-inner-section" not in s:
        s = s.replace(marker, replacement, 1)

    MAIN.write_text(s, encoding="utf-8")
    print("Quote: trattamenti integrati dentro Costi e margini.")

def patch_css():
    css = CSS.read_text(encoding="utf-8")

    if "v42.3.0c quote treatments inside costs" not in css:
        css += r'''

/* v42.3.0c quote treatments inside costs */
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
    CSS.write_text(css, encoding="utf-8")
    print("CSS quote trattamenti aggiornato.")

def main():
    patch_main()
    patch_css()
    print("Patch v42.3.0c completata.")

if __name__ == "__main__":
    main()
