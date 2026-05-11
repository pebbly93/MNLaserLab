from pathlib import Path

CSS = Path("frontend/src/style.css")

PATCH = r'''

/* v42.3.4 - Smartphone refinement for quote page only via media queries */
@media (max-width: 720px) {
  /* Preventivi: il bottone azione della card Costi e margini va sotto al contenuto */
  .card:has(.quote-treatment-inline) {
    display: flex;
    flex-direction: column;
  }

  .card:has(.quote-treatment-inline) > .card-head {
    display: grid;
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .card:has(.quote-treatment-inline) > .card-head .card-action,
  .card:has(.quote-treatment-inline) > .card-head button.primary {
    width: 100%;
    order: 99;
  }

  .card:has(.quote-treatment-inline) > .card-head button.primary {
    justify-content: center;
    min-height: 46px;
    margin-top: 6px;
  }

  /* Sposta visivamente il bottone in fondo alla card */
  .card:has(.quote-treatment-inline) > .card-head {
    display: contents;
  }

  .card:has(.quote-treatment-inline) > .card-head .card-title,
  .card:has(.quote-treatment-inline) > .card-head > div:first-child {
    order: 0;
  }

  .card:has(.quote-treatment-inline) > .quote-treatment-inline {
    order: 1;
  }

  .card:has(.quote-treatment-inline) > .form-grid {
    order: 2;
  }

  .card:has(.quote-treatment-inline) > .card-head .card-action {
    order: 3;
    margin-top: 14px;
  }

  /* Trattamenti dentro costi e margini: più comodi su smartphone */
  .quote-treatment-inline {
    margin-bottom: 14px;
  }

  .quote-treatment-inline .treatment-cost-panel {
    padding: 14px;
    border-radius: 18px;
  }

  .quote-treatment-inline .treatment-cost-head {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 8px;
  }

  .quote-treatment-inline .treatment-picker-grid {
    grid-template-columns: 1fr;
  }

  .quote-treatment-inline .treatment-add-btn {
    width: 100%;
  }

  /* Archivio preventivi: tabella trasformata in cards */
  .table-card .table-meta {
    align-items: flex-start;
    gap: 6px;
  }

  .table-card .table-wrap {
    overflow: visible;
  }

  .table-card table {
    min-width: 0;
    width: 100%;
  }

  .table-card thead {
    display: none;
  }

  .table-card tbody {
    display: grid;
    gap: 12px;
  }

  .table-card tr {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
    border: 1px solid rgba(148, 163, 184, .16);
    background: rgba(255,255,255,.045);
    border-radius: 18px;
    padding: 12px;
  }

  .table-card td {
    display: grid;
    grid-template-columns: minmax(92px, .42fr) minmax(0, 1fr);
    gap: 10px;
    align-items: start;
    border: 0 !important;
    padding: 0 !important;
    min-width: 0;
    overflow-wrap: anywhere;
  }

  .table-card td::before {
    content: attr(data-label);
    color: var(--muted);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .08em;
    font-weight: 900;
  }

  .table-card td:empty {
    display: none;
  }

  .table-card td:last-child {
    grid-template-columns: 1fr;
  }

  .table-card td:last-child::before {
    margin-bottom: 4px;
  }

  .table-card td:last-child .quick-actions,
  .table-card td:last-child div {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .table-card td:last-child button {
    flex: 1 1 auto;
    min-height: 34px;
    font-size: 12px;
    padding-inline: 10px;
  }
}

@media (max-width: 480px) {
  .table-card td {
    grid-template-columns: 1fr;
    gap: 3px;
  }

  .table-card tr {
    padding: 11px;
    border-radius: 16px;
  }

  .table-card td:last-child button {
    width: 100%;
    flex-basis: 100%;
  }
}
'''

def main():
    css = CSS.read_text(encoding="utf-8")

    if "v42.3.4 - Smartphone refinement for quote page" not in css:
        css += "\n\n" + PATCH.strip() + "\n"

    CSS.write_text(css, encoding="utf-8")
    print("Patch v42.3.4 applicata: media query smartphone preventivi.")

if __name__ == "__main__":
    main()
