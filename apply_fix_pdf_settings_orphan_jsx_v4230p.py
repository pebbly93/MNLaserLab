from pathlib import Path
import re

MAIN = Path("frontend/src/main.jsx")

def remove_treatment_garbage(block: str) -> str:
    # Rimuove wrapper interi quote-treatment-inline, se finiti dentro PdfSettingsPanel.
    block = re.sub(
        r'\s*<div className="form-grid-full quote-treatment-inline">[\s\S]*?</TreatmentCostPanel>\s*</div>\s*',
        '\n',
        block,
        flags=re.DOTALL
    )

    # Rimuove eventuali componenti TreatmentCostPanel orfani.
    block = re.sub(
        r'\s*<TreatmentCostPanel[\s\S]*?/>\s*',
        '\n',
        block,
        flags=re.DOTALL
    )

    # Rimuove righe orfane con variabili dei preventivi finite fuori Quote.
    block = re.sub(r'.*woodTreatmentsQuote.*\n?', '', block)
    block = re.sub(r'.*quoteTreatments.*\n?', '', block)
    block = re.sub(r'.*setQuoteTreatments.*\n?', '', block)

    return block

def main():
    s = MAIN.read_text(encoding="utf-8")

    start = s.find("function PdfSettingsPanel(")
    end = s.find("function SettingsPage(", start)

    if start == -1:
        raise RuntimeError("function PdfSettingsPanel non trovata")
    if end == -1:
        raise RuntimeError("function SettingsPage non trovata dopo PdfSettingsPanel")

    before = s[:start]
    block = s[start:end]
    after = s[end:]

    block = remove_treatment_garbage(block)

    # Corregge una chiusura Card eventualmente rimasta in forma problematica.
    block = block.replace("</Card>;", "</Card>;")

    # Se nel blocco c'è ancora quote-treatment-inline o woodTreatmentsQuote, fermiamoci.
    if "quote-treatment-inline" in block or "woodTreatmentsQuote" in block or "quoteTreatments" in block:
        raise RuntimeError("Residui trattamenti ancora presenti dentro PdfSettingsPanel")

    s = before + block + after
    MAIN.write_text(s, encoding="utf-8")

    print("Fix v42.3.0p applicato: PdfSettingsPanel ripulito da residui JSX dei trattamenti.")

if __name__ == "__main__":
    main()
