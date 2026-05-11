from pathlib import Path
import re

MAIN = Path("frontend/src/main.jsx")
CSS = Path("frontend/src/style.css")

CSS_PATCH = r'''

/* v42.4.0 - Stable mobile full screen table detail, no flicker */
@media (max-width: 720px) {
  body:has(.mobile-row-action-backdrop) {
    overflow: hidden !important;
    touch-action: none;
  }

  .mobile-row-action-backdrop {
    position: fixed !important;
    inset: 0 !important;
    z-index: 999999 !important;
    display: block !important;
    background: #07111f !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
    transform: translateZ(0);
    -webkit-transform: translateZ(0);
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
  }

  .mobile-row-action-sheet {
    position: fixed !important;
    inset: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    max-width: none !important;
    max-height: none !important;
    margin: 0 !important;
    border: 0 !important;
    border-radius: 0 !important;
    background:
      radial-gradient(circle at 85% 8%, rgba(5,132,130,.18), transparent 30%),
      linear-gradient(180deg, #091525 0%, #06101d 100%) !important;
    box-shadow: none !important;
    padding: max(14px, env(safe-area-inset-top)) 14px max(16px, env(safe-area-inset-bottom)) !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    -webkit-overflow-scrolling: touch !important;
    overscroll-behavior: contain !important;
    display: block !important;
  }

  .mobile-row-action-head {
    position: relative !important;
    top: auto !important;
    z-index: 1 !important;
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) 42px !important;
    gap: 12px !important;
    align-items: center !important;
    padding: 4px 0 14px !important;
    margin: 0 0 12px !important;
    border-bottom: 1px solid rgba(148, 163, 184, .16) !important;
    background: transparent !important;
    backdrop-filter: none !important;
  }

  .mobile-row-action-head span {
    display: block;
    color: #19ddd6;
    font-size: 9px !important;
    text-transform: uppercase;
    letter-spacing: .14em;
    font-weight: 900;
    margin: 0 0 5px;
  }

  .mobile-row-action-head b {
    display: block;
    color: #eef6ff;
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
    background: rgba(255,255,255,.08) !important;
    border: 1px solid rgba(148,163,184,.16) !important;
  }

  .mobile-row-action-summary {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 8px !important;
    margin: 0 0 14px !important;
    padding: 0 !important;
  }

  .mobile-row-action-summary div {
    border: 1px solid rgba(148, 163, 184, .13) !important;
    background: rgba(255,255,255,.04) !important;
    border-radius: 15px !important;
    padding: 9px 11px !important;
    min-width: 0 !important;
  }

  .mobile-row-action-summary span {
    display: block;
    color: rgba(188, 204, 224, .78);
    font-size: 8.5px !important;
    text-transform: uppercase;
    letter-spacing: .1em;
    font-weight: 900;
    margin-bottom: 4px;
  }

  .mobile-row-action-summary b {
    display: block;
    color: #eef6ff;
    font-size: 12.5px !important;
    line-height: 1.18 !important;
    overflow-wrap: anywhere;
    word-break: normal;
  }

  .mobile-row-action-buttons {
    position: relative !important;
    bottom: auto !important;
    z-index: 1 !important;
    margin: 0 0 18px !important;
    padding: 12px 0 0 !important;
    border-top: 1px solid rgba(148, 163, 184, .14) !important;
    background: transparent !important;
    backdrop-filter: none !important;
    display: block !important;
  }

  .mobile-row-action-buttons > div {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 7px !important;
    width: 100% !important;
  }

  .mobile-row-action-buttons button,
  .mobile-row-action-buttons a {
    width: 100% !important;
    min-height: 34px !important;
    height: 34px !important;
    padding: 6px 8px !important;
    border-radius: 11px !important;
    justify-content: center !important;
    font-size: 10.5px !important;
    line-height: 1 !important;
    white-space: nowrap !important;
  }

  .mobile-row-action-buttons button svg,
  .mobile-row-action-buttons a svg {
    width: 13px !important;
    height: 13px !important;
  }
}

@media (max-width: 390px) {
  .mobile-row-action-sheet {
    padding-left: 12px !important;
    padding-right: 12px !important;
  }

  .mobile-row-action-buttons > div {
    grid-template-columns: 1fr 1fr !important;
    gap: 6px !important;
  }

  .mobile-row-action-buttons button,
  .mobile-row-action-buttons a {
    height: 32px !important;
    min-height: 32px !important;
    font-size: 10px !important;
    padding: 5px 6px !important;
  }

  .mobile-row-action-summary div {
    padding: 8px 10px !important;
  }
}
'''

def patch_main():
    s = MAIN.read_text(encoding="utf-8")

    # Chiudi solo con X. Niente chiusura su backdrop, evita flicker/tap strani.
    s = s.replace(
        '<div className="mobile-row-action-backdrop" onClick={() => setMobileActions(null)}>',
        '<div className="mobile-row-action-backdrop">'
    )

    s = s.replace(
        '<div className="mobile-row-action-sheet" onClick={e => e.stopPropagation()}>',
        '<div className="mobile-row-action-sheet">'
    )

    s = s.replace(
        '<button className="ghost" onClick={() => setMobileActions(null)}>×</button>',
        '<button type="button" className="ghost" onClick={() => setMobileActions(null)} aria-label="Chiudi dettaglio">×</button>'
    )

    MAIN.write_text(s, encoding="utf-8")
    print("JS popup mobile stabilizzato.")

def patch_css():
    css = CSS.read_text(encoding="utf-8")

    # Rimuove versioni precedenti del popup fullscreen mobile.
    for tag in [
        "v42.3.8 - Mobile row details full screen",
        "v42.3.9 - Refined mobile fullscreen row detail",
        "v42.4.0 - Stable mobile full screen table detail, no flicker",
    ]:
        css = re.sub(
            r'\n/\* ' + re.escape(tag) + r' \*/[\s\S]*?(?=\n/\*|\Z)',
            '\n',
            css,
            flags=re.DOTALL
        )

    css += "\n\n" + CSS_PATCH.strip() + "\n"
    CSS.write_text(css, encoding="utf-8")
    print("CSS popup mobile stabile applicato.")

def main():
    patch_main()
    patch_css()
    print("Patch v42.4.0 completata.")

if __name__ == "__main__":
    main()
