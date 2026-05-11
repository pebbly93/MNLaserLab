from pathlib import Path
import re

MAIN = Path("frontend/src/main.jsx")
CSS = Path("frontend/src/style.css")

CSS_PATCH = r'''

/* v42.3.9 - Refined mobile fullscreen row detail */
@media (max-width: 720px) {
  .mobile-row-action-backdrop {
    position: fixed !important;
    inset: 0 !important;
    z-index: 99999 !important;
    display: block !important;
    background:
      radial-gradient(circle at 85% 5%, rgba(5,132,130,.22), transparent 34%),
      linear-gradient(180deg, rgba(8,15,28,.98), rgba(2,6,23,.98)) !important;
    backdrop-filter: none !important;
    padding: env(safe-area-inset-top) 12px env(safe-area-inset-bottom) !important;
    overflow: hidden !important;
  }

  .mobile-row-action-sheet {
    width: 100% !important;
    height: 100dvh !important;
    max-height: 100dvh !important;
    max-width: 540px !important;
    margin: 0 auto !important;
    border-radius: 0 !important;
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    padding: 14px 0 18px !important;
    overflow-y: auto !important;
    overscroll-behavior: contain !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 12px !important;
  }

  .mobile-row-action-head {
    position: sticky !important;
    top: 0 !important;
    z-index: 3 !important;
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) auto !important;
    gap: 12px !important;
    align-items: center !important;
    padding: 8px 0 12px !important;
    margin: 0 !important;
    border-bottom: 1px solid rgba(148, 163, 184, .16) !important;
    background: rgba(8,15,28,.96) !important;
  }

  .mobile-row-action-head span {
    display: block;
    color: var(--accent);
    font-size: 9.5px !important;
    text-transform: uppercase;
    letter-spacing: .12em;
    font-weight: 900;
    margin-bottom: 4px;
  }

  .mobile-row-action-head b {
    display: block;
    color: var(--text);
    font-size: 18px !important;
    line-height: 1.12 !important;
    overflow-wrap: anywhere;
  }

  .mobile-row-action-head button {
    width: 42px !important;
    height: 42px !important;
    min-width: 42px !important;
    min-height: 42px !important;
    border-radius: 14px !important;
    font-size: 22px !important;
    padding: 0 !important;
    display: grid !important;
    place-items: center !important;
    background: rgba(255,255,255,.075) !important;
  }

  .mobile-row-action-summary {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 8px !important;
    margin: 0 !important;
    padding-bottom: 4px !important;
  }

  .mobile-row-action-summary div {
    border: 1px solid rgba(148, 163, 184, .12) !important;
    background: rgba(255,255,255,.04) !important;
    border-radius: 16px !important;
    padding: 10px 12px !important;
    min-width: 0 !important;
  }

  .mobile-row-action-summary span {
    display: block;
    color: var(--muted);
    font-size: 9px !important;
    text-transform: uppercase;
    letter-spacing: .09em;
    font-weight: 900;
    margin-bottom: 5px;
  }

  .mobile-row-action-summary b {
    display: block;
    color: var(--text);
    font-size: 13px !important;
    line-height: 1.2 !important;
    overflow-wrap: anywhere;
    word-break: normal;
  }

  .mobile-row-action-buttons {
    position: sticky !important;
    bottom: 0 !important;
    z-index: 3 !important;
    margin-top: auto !important;
    padding: 12px 0 4px !important;
    border-top: 1px solid rgba(148, 163, 184, .14) !important;
    background: rgba(8,15,28,.96) !important;
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 8px !important;
  }

  .mobile-row-action-buttons > div {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 8px !important;
    width: 100% !important;
  }

  .mobile-row-action-buttons button,
  .mobile-row-action-buttons a {
    width: 100% !important;
    min-height: 36px !important;
    height: 36px !important;
    padding: 7px 10px !important;
    border-radius: 12px !important;
    justify-content: center !important;
    font-size: 11px !important;
    line-height: 1 !important;
    white-space: nowrap !important;
  }

  .mobile-row-action-buttons button svg,
  .mobile-row-action-buttons a svg {
    width: 14px !important;
    height: 14px !important;
  }
}

@media (max-width: 390px) {
  .mobile-row-action-buttons > div {
    grid-template-columns: 1fr !important;
  }

  .mobile-row-action-buttons button,
  .mobile-row-action-buttons a {
    height: 34px !important;
    min-height: 34px !important;
    font-size: 10.5px !important;
  }

  .mobile-row-action-summary div {
    padding: 9px 10px !important;
  }
}
'''

def patch_main():
    s = MAIN.read_text(encoding="utf-8")

    # Evita che il tap sul contenuto/backdrop produca comportamenti strani.
    s = s.replace(
        '<div className="mobile-row-action-backdrop" onClick={() => setMobileActions(null)}>',
        '<div className="mobile-row-action-backdrop">',
    )

    s = s.replace(
        '<button className="ghost" onClick={() => setMobileActions(null)}>×</button>',
        '<button type="button" className="ghost" onClick={() => setMobileActions(null)} aria-label="Chiudi dettaglio">×</button>',
    )

    MAIN.write_text(s, encoding="utf-8")
    print("DataTable mobile popup: click backdrop disattivato, chiusura solo da X.")

def patch_css():
    css = CSS.read_text(encoding="utf-8")

    css = re.sub(
        r'\n/\* v42\.3\.9 - Refined mobile fullscreen row detail \*/[\s\S]*?(?=\n/\*|\Z)',
        '\n',
        css,
        flags=re.DOTALL
    )

    css += "\n\n" + CSS_PATCH.strip() + "\n"
    CSS.write_text(css, encoding="utf-8")
    print("CSS popup fullscreen mobile raffinato.")

def main():
    patch_main()
    patch_css()
    print("Patch v42.3.9 completata.")

if __name__ == "__main__":
    main()
