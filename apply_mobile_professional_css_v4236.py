from pathlib import Path
import re

CSS = Path("frontend/src/style.css")

PATCH = r'''

/* v42.3.6 - Mobile Professional UX Layer
   Obiettivo: rendere tutta l'app usabile da smartphone senza alterare il desktop.
*/
@media (max-width: 820px) {
  html,
  body,
  #root {
    width: 100%;
    max-width: 100%;
    overflow-x: hidden;
  }

  body {
    font-size: 14px;
  }

  * {
    box-sizing: border-box;
  }

  .app,
  .shell,
  .layout,
  .main,
  main,
  .content,
  .page,
  .page-content {
    width: 100%;
    max-width: 100%;
    min-width: 0;
    overflow-x: hidden;
  }

  /* Spaziature generali */
  .main,
  main,
  .content,
  .page-content {
    padding-left: 12px !important;
    padding-right: 12px !important;
  }

  /* Header pagina */
  .page-title,
  .page-head,
  .page-header {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 10px !important;
    align-items: start !important;
    margin-bottom: 14px !important;
  }

  .page-title h1,
  .page-head h1,
  .page-header h1 {
    font-size: clamp(22px, 7vw, 30px) !important;
    line-height: 1.05 !important;
    letter-spacing: -0.04em !important;
    overflow-wrap: anywhere;
  }

  .page-title p,
  .page-head p,
  .page-header p,
  .subtitle,
  .page-subtitle {
    font-size: 13px !important;
    line-height: 1.4 !important;
    max-width: 100% !important;
  }

  /* Cards */
  .card {
    width: 100%;
    max-width: 100%;
    min-width: 0;
    border-radius: 20px !important;
    padding: 14px !important;
    overflow: hidden;
  }

  .card + .card {
    margin-top: 14px;
  }

  .card-head,
  .card-header {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 10px !important;
    align-items: start !important;
    margin-bottom: 12px !important;
  }

  .card-head h2,
  .card-head h3,
  .card-header h2,
  .card-header h3,
  .card-title {
    font-size: 17px !important;
    line-height: 1.18 !important;
    overflow-wrap: anywhere;
  }

  .card-head p,
  .card-header p,
  .card-sub,
  .card small {
    font-size: 12px !important;
    line-height: 1.35 !important;
  }

  .card-action,
  .card-head > button,
  .card-head .primary,
  .card-header > button,
  .card-header .primary {
    width: 100%;
    justify-content: center;
  }

  /* Grid globali */
  .grid,
  .split,
  .split-main,
  .dashboard-grid,
  .settings-grid,
  .pdf-settings-layout,
  .system-page-grid,
  .quote-layout,
  .products-layout,
  .people-layout,
  .report-grid,
  .form-grid {
    grid-template-columns: 1fr !important;
    gap: 12px !important;
    width: 100% !important;
    min-width: 0 !important;
  }

  .form-grid-full {
    grid-column: 1 / -1;
  }

  /* Form */
  label,
  .field,
  .input-wrap,
  .select-wrap {
    min-width: 0 !important;
    width: 100% !important;
  }

  input,
  select,
  textarea {
    width: 100% !important;
    max-width: 100% !important;
    min-height: 44px;
    font-size: 14px !important;
    border-radius: 14px !important;
  }

  textarea {
    min-height: 96px;
    line-height: 1.35;
  }

  .field span,
  label span {
    font-size: 11px !important;
    line-height: 1.2 !important;
  }

  /* Bottoni */
  button,
  .button,
  .primary,
  .ghost {
    min-height: 40px;
    border-radius: 14px !important;
    font-size: 13px !important;
    line-height: 1.15 !important;
  }

  .quick-actions,
  .actions,
  .button-row,
  .toolbar {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
    width: 100%;
  }

  .quick-actions button,
  .actions button,
  .button-row button,
  .toolbar button {
    flex: 1 1 auto;
    min-width: min(150px, 100%);
  }

  /* KPI / statistiche */
  .stats,
  .stat-grid,
  .kpi-grid,
  .wizard-cost-grid,
  .system-kpi-grid,
  .system-counts,
  .update-status-box {
    grid-template-columns: 1fr 1fr !important;
    gap: 10px !important;
  }

  .stat,
  .kpi,
  .metric {
    min-width: 0 !important;
    padding: 12px !important;
    border-radius: 16px !important;
  }

  .stat b,
  .kpi b,
  .metric b {
    font-size: 18px !important;
    overflow-wrap: anywhere;
  }

  .stat span,
  .kpi span,
  .metric span {
    font-size: 11px !important;
    line-height: 1.25 !important;
  }

  /* Tabelle: compatte, non trasformate in card */
  .table-card {
    width: 100%;
    max-width: 100%;
    min-width: 0;
    overflow: hidden;
    border-radius: 18px !important;
    padding: 10px !important;
  }

  .table-meta {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 3px !important;
    align-items: start !important;
    margin-bottom: 8px !important;
  }

  .table-meta b {
    font-size: 12px !important;
  }

  .table-meta span {
    font-size: 11px !important;
    line-height: 1.3 !important;
  }

  .table-wrap {
    width: 100%;
    max-width: 100%;
    overflow-x: auto !important;
    overflow-y: hidden;
    -webkit-overflow-scrolling: touch;
    border-radius: 14px;
  }

  .table-wrap table {
    width: 100%;
    min-width: 560px;
    table-layout: auto;
    border-collapse: collapse;
  }

  .table-wrap th,
  .table-wrap td {
    padding: 8px 7px !important;
    max-width: 140px;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    word-break: normal;
    font-size: 10.8px !important;
    line-height: 1.22 !important;
    vertical-align: middle;
  }

  .table-wrap th {
    font-size: 9.3px !important;
    letter-spacing: .05em;
  }

  .table-wrap td b,
  .table-wrap td strong {
    font-size: 11.2px !important;
    line-height: 1.18 !important;
  }

  .table-wrap td:last-child {
    max-width: 210px;
  }

  .table-wrap td:last-child > div,
  .table-wrap .quick-actions {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 5px !important;
  }

  .table-wrap button {
    min-height: 28px !important;
    padding: 5px 7px !important;
    font-size: 10.5px !important;
    border-radius: 10px !important;
    white-space: nowrap;
  }

  /* Wizard / prodotti */
  .wizard,
  .wizard-panel,
  .wizard-body,
  .wizard-steps {
    width: 100%;
    min-width: 0;
  }

  .wizard-steps {
    display: flex !important;
    overflow-x: auto;
    gap: 8px;
    padding-bottom: 4px;
    -webkit-overflow-scrolling: touch;
  }

  .wizard-steps button {
    flex: 0 0 auto;
    min-width: 120px;
    font-size: 11px !important;
    padding: 8px 10px !important;
  }

  .bom-row,
  .material-row,
  .selected-treatment-row,
  .treatment-row {
    grid-template-columns: 1fr !important;
    gap: 10px !important;
  }

  .selected-treatment-values {
    width: 100%;
    justify-content: space-between;
    flex-wrap: wrap;
  }

  .treatment-picker-grid {
    grid-template-columns: 1fr !important;
  }

  .treatment-add-btn {
    width: 100%;
  }

  /* Preventivi: bottone calcolo leggibile e in basso se la card usa i trattamenti */
  .quote-treatment-inline {
    margin-bottom: 12px !important;
  }

  .quote-treatment-inline .treatment-cost-panel {
    padding: 13px !important;
    border-radius: 18px !important;
  }

  .card:has(.quote-treatment-inline) {
    display: flex;
    flex-direction: column;
  }

  .card:has(.quote-treatment-inline) .form-grid {
    order: 2;
  }

  .card:has(.quote-treatment-inline) .quote-treatment-inline {
    order: 1;
  }

  .card:has(.quote-treatment-inline) .card-head,
  .card:has(.quote-treatment-inline) .card-header {
    order: 0;
  }

  .card:has(.quote-treatment-inline) .card-action,
  .card:has(.quote-treatment-inline) .card-head button.primary,
  .card:has(.quote-treatment-inline) .card-header button.primary {
    order: 9;
    margin-top: 10px;
    width: 100%;
  }

  /* Modali */
  .modal,
  .modal-card,
  .detail-modal,
  .dialog {
    width: calc(100vw - 20px) !important;
    max-width: calc(100vw - 20px) !important;
    max-height: calc(100vh - 24px) !important;
    overflow: auto !important;
    border-radius: 20px !important;
  }

  .modal-body,
  .detail-modal-body {
    overflow-x: hidden;
  }

  /* Barre operative */
  .ux-bar,
  .focus-strip {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 10px !important;
    padding: 10px !important;
    border-radius: 18px !important;
  }

  .ux-flow-mini {
    display: flex !important;
    gap: 8px !important;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 3px;
  }

  .ux-flow-mini button {
    flex: 0 0 auto;
    min-width: 118px;
  }

  .focus-strip button {
    width: 100%;
    justify-content: center;
  }

  /* Immagini e preview */
  img,
  svg,
  canvas {
    max-width: 100%;
  }

  .pdf-settings-preview,
  .pdf-preview-sheet {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
  }
}

@media (max-width: 480px) {
  .main,
  main,
  .content,
  .page-content {
    padding-left: 10px !important;
    padding-right: 10px !important;
  }

  .card {
    padding: 12px !important;
    border-radius: 18px !important;
  }

  .stats,
  .stat-grid,
  .kpi-grid,
  .wizard-cost-grid,
  .system-kpi-grid,
  .system-counts,
  .update-status-box {
    grid-template-columns: 1fr !important;
  }

  .table-wrap table {
    min-width: 520px;
  }

  .table-wrap th,
  .table-wrap td {
    max-width: 118px;
    padding: 7px 6px !important;
    font-size: 10.3px !important;
  }

  .table-wrap th {
    font-size: 8.8px !important;
  }

  .quick-actions button,
  .actions button,
  .button-row button,
  .toolbar button {
    flex-basis: 100%;
  }

  .page-title h1,
  .page-head h1,
  .page-header h1 {
    font-size: 24px !important;
  }
}
'''

def main():
    css = CSS.read_text(encoding="utf-8")

    # Rimuove vecchi tentativi mobile responsive.
    css = re.sub(
        r'\n/\* v42\.3\.4 - Smartphone refinement for quote page only via media queries \*/[\s\S]*?(?=\n/\*|\Z)',
        '\n',
        css,
        flags=re.DOTALL
    )

    css = re.sub(
        r'\n/\* v42\.3\.5 - Tabelle compatte e adattate alla larghezza card \*/[\s\S]*?(?=\n/\*|\Z)',
        '\n',
        css,
        flags=re.DOTALL
    )

    css = re.sub(
        r'\n/\* v42\.3\.6 - Mobile Professional UX Layer[\s\S]*?(?=\n/\*|\Z)',
        '\n',
        css,
        flags=re.DOTALL
    )

    css += "\n\n" + PATCH.strip() + "\n"

    CSS.write_text(css, encoding="utf-8")
    print("Patch v42.3.6 applicata: layer mobile professionale globale.")

if __name__ == "__main__":
    main()
