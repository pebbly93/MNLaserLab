from pathlib import Path
import re

MAIN = Path("frontend/src/main.jsx")
CSS = Path("frontend/src/style.css")

def patch_main():
    s = MAIN.read_text(encoding="utf-8")

    # Mostra tutti i dettagli, non solo le prime 6 colonne.
    s = s.replace(
        "const summaryCols = columns.filter(c => c !== actionCol).slice(0, 6);",
        "const summaryCols = columns.filter(c => c !== actionCol);"
    )

    # Testo più coerente.
    s = s.replace(
        "{actionCol && <small className=\"mobile-table-hint\">Su smartphone tocca una riga per aprire le azioni.</small>}",
        "{actionCol && <small className=\"mobile-table-hint\">Tocca una riga per aprire dettaglio e azioni.</small>}"
    )

    s = s.replace(
        "<span>Azioni riga</span>",
        "<span>Dettaglio riga</span>"
    )

    MAIN.write_text(s, encoding="utf-8")
    print("DataTable mobile aggiornato: dettagli completi nel popup.")

def patch_css():
    css = CSS.read_text(encoding="utf-8")

    patch = r'''

/* v42.3.8 - Mobile row details full screen */
@media (max-width: 720px) {
  .mobile-row-action-backdrop {
    position: fixed !important;
    inset: 0 !important;
    z-index: 99999 !important;
    display: block !important;
    background:
      radial-gradient(circle at top right, rgba(5,132,130,.24), transparent 34%),
      rgba(2, 6, 23, .94) !important;
    backdrop-filter: blur(12px);
    padding: 0 !important;
    overflow: hidden !important;
  }

  .mobile-row-action-sheet {
    width: 100vw !important;
    height: 100dvh !important;
    max-height: 100dvh !important;
    border-radius: 0 !important;
    border: 0 !important;
    background: rgba(8, 15, 28, .98) !important;
    box-shadow: none !important;
    padding: 16px !important;
    overflow-y: auto !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 14px !important;
  }

  .mobile-row-action-head {
    position: sticky;
    top: 0;
    z-index: 2;
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) auto !important;
    gap: 12px !important;
    align-items: center !important;
    padding: 4px 0 14px !important;
    margin: 0 !important;
    border-bottom: 1px solid rgba(148, 163, 184, .18) !important;
    background: linear-gradient(180deg, rgba(8,15,28,.98), rgba(8,15,28,.92)) !important;
    backdrop-filter: blur(8px);
  }

  .mobile-row-action-head span {
    display: block;
    color: var(--accent);
    font-size: 10px !important;
    text-transform: uppercase;
    letter-spacing: .1em;
    font-weight: 900;
    margin-bottom: 5px;
  }

  .mobile-row-action-head b {
    display: block;
    color: var(--text);
    font-size: 20px !important;
    line-height: 1.12 !important;
    overflow-wrap: anywhere;
  }

  .mobile-row-action-head button {
    width: 46px !important;
    height: 46px !important;
    min-width: 46px !important;
    min-height: 46px !important;
    border-radius: 16px !important;
    font-size: 26px !important;
    padding: 0 !important;
    display: grid !important;
    place-items: center !important;
  }

  .mobile-row-action-summary {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 10px !important;
    margin: 0 !important;
  }

  .mobile-row-action-summary div {
    border: 1px solid rgba(148, 163, 184, .14) !important;
    background: rgba(255,255,255,.045) !important;
    border-radius: 18px !important;
    padding: 12px !important;
    min-width: 0 !important;
  }

  .mobile-row-action-summary span {
    display: block;
    color: var(--muted);
    font-size: 10px !important;
    text-transform: uppercase;
    letter-spacing: .08em;
    font-weight: 900;
    margin-bottom: 6px;
  }

  .mobile-row-action-summary b {
    display: block;
    color: var(--text);
    font-size: 14px !important;
    line-height: 1.22 !important;
    overflow-wrap: anywhere;
    word-break: normal;
  }

  .mobile-row-action-buttons {
    position: sticky;
    bottom: 0;
    z-index: 2;
    margin-top: auto !important;
    padding: 14px 0 0 !important;
    border-top: 1px solid rgba(148, 163, 184, .18) !important;
    background: linear-gradient(0deg, rgba(8,15,28,.98), rgba(8,15,28,.92)) !important;
    backdrop-filter: blur(8px);
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 9px !important;
  }

  .mobile-row-action-buttons > *,
  .mobile-row-action-buttons div {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 9px !important;
    width: 100% !important;
  }

  .mobile-row-action-buttons button,
  .mobile-row-action-buttons a {
    width: 100% !important;
    min-height: 46px !important;
    border-radius: 16px !important;
    justify-content: center !important;
    font-size: 13px !important;
  }
}
'''

    css = re.sub(
        r'\n/\* v42\.3\.8 - Mobile row details full screen \*/[\s\S]*?(?=\n/\*|\Z)',
        '\n',
        css,
        flags=re.DOTALL
    )

    css += "\n\n" + patch.strip() + "\n"
    CSS.write_text(css, encoding="utf-8")
    print("CSS mobile full screen row details applicato.")

def main():
    patch_main()
    patch_css()
    print("Patch v42.3.8 completata.")

if __name__ == "__main__":
    main()
