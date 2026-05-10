from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
CSS = ROOT / "frontend" / "src" / "style.css"


PDF_HELPER = r'''
def apply_pdf_brand_to_html(db, html, kind="customer", quote=None):
    settings = get_pdf_settings(db)
    quote = quote or {}

    company = settings.get("company_name", "MN Laser Lab") or "MN Laser Lab"
    author = settings.get("author", "Filippo Lolli") or "Filippo Lolli"
    email = settings.get("email", "filippololli1@gmail.com") or "filippololli1@gmail.com"
    phone = settings.get("phone", "") or ""
    address = settings.get("address", "") or ""
    website = settings.get("website", "") or ""
    vat = settings.get("vat", "") or ""
    color = settings.get("primary_color", "#058482") or "#058482"
    footer = settings.get("footer", "MN Laser Lab - Creazioni artigianali in legno e taglio laser") or ""
    terms = settings.get("terms", "") or ""
    intro = settings.get("intro_text", "") or ""
    logo = settings.get("logo_data_url", "") or ""

    project_fee = parse_float(quote.get("project_fee"))

    if not logo:
        logo = (
            "data:image/svg+xml;utf8,"
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 180 180'>"
            "<rect width='180' height='180' rx='38' fill='%23ffffff'/>"
            "<circle cx='90' cy='90' r='68' fill='%23f8fafc' stroke='%23058482' stroke-width='7'/>"
            "<text x='90' y='86' text-anchor='middle' font-family='Arial, Helvetica, sans-serif' font-size='39' font-weight='900' fill='%230f172a'>MN</text>"
            "<text x='90' y='116' text-anchor='middle' font-family='Arial, Helvetica, sans-serif' font-size='14' font-weight='800' fill='%23058482'>LASER LAB</text>"
            "</svg>"
        )

    contact_bits = [x for x in [author, email, phone, address, website, vat] if str(x or "").strip()]
    contact_line = " · ".join(contact_bits)

    html = html.replace("{_pdf_brand_css(db)}", "")
    html = html.replace("{_pdf_brand_block(db)}", "")
    html = html.replace("#058482", color)
    html = html.replace("MN Laser Lab", company)

    old_contacts = [
        "Filippo Lolli - filippololli1@gmail.com",
        "Filippo Lolli · filippololli1@gmail.com",
        "Filippo Lolli - filippololli@gmail.com",
        "Filippo Lolli · filippololli@gmail.com",
        "Mauro Nocco · mnlaserlab@gmail.com",
        "Mauro Nocco - mnlaserlab@gmail.com",
        "mnlaserlab@gmail.com",
        "filippololli@gmail.com",
        "filippololli1@gmail.com",
    ]

    for old in old_contacts:
        html = html.replace(old, contact_line or old)

    old_subtitles = [
        "Creazioni artigianali in legno · Taglio e incisione laser",
        "Creazioni artigianali in legno - Taglio e incisione laser",
        "Creazioni artigianali in legno e taglio laser",
        "MN Laser Lab - Creazioni artigianali in legno e taglio laser",
    ]

    for old in old_subtitles:
        html = html.replace(old, footer or "Creazioni artigianali in legno e taglio laser")

    if intro:
        html = html.replace(
            "Grazie per averci contattato. Di seguito trovi il riepilogo del preventivo richiesto.",
            intro
        )

    if terms:
        html = html.replace(
            "Il preventivo è valido salvo disponibilità materiali e conferma finale della lavorazione.",
            terms
        )

    if footer:
        html = html.replace("Preventivo generato con MN Laser Lab Manager.", footer)

    try:
        html = re.sub(
            r"<div class=['\"]brand-head['\"].*?</div>\s*</div>",
            "",
            html,
            flags=re.DOTALL
        )
    except Exception:
        pass

    if "pdf-brand-logo-inline" not in html:
        logo_html = f"<img class='pdf-brand-logo-inline' src='{logo}' alt='Logo MN Laser Lab' />"
        html = html.replace(
            f"<h1>{company}</h1>",
            f"<div class='pdf-brand-title-row'>{logo_html}<div class='pdf-brand-text'><h1>{company}</h1><p class='pdf-dynamic-contact'>{contact_line}</p></div></div>",
            1
        )

    if contact_line and contact_line not in html:
        html = html.replace(
            f"<h1>{company}</h1>",
            f"<h1>{company}</h1><p class='pdf-dynamic-contact'>{contact_line}</p>",
            1
        )

    if project_fee > 0 and "pdf-project-fee" not in html:
        project_fee_html = f"""
        <div class="pdf-project-fee">
          <div>
            <span>Voce aggiuntiva</span>
            <b>Spese di progetto</b>
          </div>
          <strong>€ {project_fee:.2f}</strong>
        </div>
        """

        if "Totale preventivo" in html:
            html = html.replace("Totale preventivo", project_fee_html + "\nTotale preventivo", 1)
        else:
            html = html.replace("</body>", project_fee_html + "\n</body>", 1)

    extra_css = f"""
    <style>
      :root {{
        --brand: {color};
        --brand-dark: #046b69;
        --ink: #0f172a;
        --muted: #64748b;
        --line: #e2e8f0;
        --soft: #f8fafc;
        --paper: #ffffff;
      }}

      * {{
        box-sizing: border-box;
      }}

      body {{
        background: #e5e7eb !important;
        color: var(--ink) !important;
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif !important;
        margin: 0 !important;
        padding: 38px 0 48px !important;
        -webkit-font-smoothing: antialiased;
      }}

      body > *:not(.print-button):not(.print-actions):not(button) {{
        max-width: 920px !important;
        margin-left: auto !important;
        margin-right: auto !important;
      }}

      .page, main, .document, .quote-page, .container {{
        width: min(920px, calc(100vw - 64px)) !important;
        margin: 0 auto !important;
        background: #ffffff !important;
        border-radius: 22px !important;
        box-shadow: 0 28px 80px rgba(15, 23, 42, .14) !important;
        padding: 34px 38px !important;
      }}

      .pdf-brand-title-row {{
        display: flex !important;
        align-items: center !important;
        gap: 18px !important;
      }}

      .pdf-brand-logo-inline {{
        width: 78px !important;
        height: 78px !important;
        object-fit: contain !important;
        display: block !important;
        flex: 0 0 auto !important;
        border-radius: 18px !important;
      }}

      .pdf-brand-text {{
        min-width: 0 !important;
      }}

      .pdf-dynamic-contact {{
        margin: 7px 0 0 !important;
        color: var(--muted) !important;
        font-size: 12.5px !important;
        line-height: 1.45 !important;
        font-weight: 600 !important;
        max-width: 560px !important;
      }}

      h1 {{
        margin: 0 !important;
        font-size: 29px !important;
        line-height: 1.05 !important;
        letter-spacing: -0.045em !important;
        color: var(--ink) !important;
      }}

      h2, h3 {{
        color: var(--ink) !important;
        letter-spacing: -0.03em !important;
      }}

      p {{
        color: #334155 !important;
        line-height: 1.55 !important;
      }}

      table {{
        width: 100% !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
        table-layout: fixed !important;
        overflow: hidden !important;
        border-radius: 14px !important;
        border: 1px solid var(--line) !important;
      }}

      th {{
        background: #f1f5f9 !important;
        color: #475569 !important;
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: .07em !important;
        padding: 12px 14px !important;
        border-bottom: 1px solid var(--line) !important;
      }}

      td {{
        padding: 14px !important;
        border-bottom: 1px solid #e5e7eb !important;
        color: #1e293b !important;
        font-size: 13px !important;
        line-height: 1.38 !important;
        vertical-align: middle !important;
      }}

      tr:last-child td {{
        border-bottom: 0 !important;
      }}

      td:last-child,
      th:last-child,
      .right {{
        text-align: right !important;
      }}

      .pdf-project-fee {{
        margin: 18px 0 10px !important;
        border: 1px solid rgba(5, 132, 130, .22) !important;
        background: linear-gradient(135deg, rgba(5,132,130,.09), rgba(5,132,130,.025)) !important;
        border-radius: 18px !important;
        padding: 16px 20px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 20px !important;
        color: var(--ink) !important;
      }}

      .pdf-project-fee span {{
        display: block !important;
        font-size: 10.5px !important;
        font-weight: 900 !important;
        color: var(--brand) !important;
        letter-spacing: .08em !important;
        text-transform: uppercase !important;
        margin-bottom: 3px !important;
      }}

      .pdf-project-fee b {{
        display: block !important;
        font-size: 15px !important;
        color: #1e293b !important;
      }}

      .pdf-project-fee strong {{
        font-size: 23px !important;
        color: var(--brand) !important;
        white-space: nowrap !important;
      }}

      .print-button,
      .print-actions,
      button {{
        position: fixed;
        top: 24px;
        right: 24px;
        z-index: 99;
      }}

      @media print {{
        @page {{
          size: A4;
          margin: 14mm;
        }}

        body {{
          background: white !important;
          padding: 0 !important;
        }}

        .page, main, .document, .quote-page, .container, body > * {{
          width: 100% !important;
          max-width: 100% !important;
          margin: 0 !important;
          box-shadow: none !important;
          border-radius: 0 !important;
          padding: 0 !important;
        }}

        .print-button, .print-actions, button {{
          display: none !important;
        }}
      }}
    </style>
    """

    if "</head>" in html:
        html = html.replace("</head>", extra_css + "\n</head>", 1)

    return html
'''


def replace_function(source: str, name: str, new_code: str) -> str:
    start = source.find(f"def {name}(")
    if start == -1:
        return source + "\n\n" + new_code.strip() + "\n"

    end = source.find("\ndef ", start + 1)
    if end == -1:
        end = len(source)

    return source[:start] + new_code.strip() + "\n\n" + source[end + 1:]


def patch_backend():
    s = LEGACY.read_text(encoding="utf-8")

    if "import re" not in s.split("\n")[:50]:
        lines = s.splitlines()
        pos = 0
        for i, line in enumerate(lines[:50]):
            if line.startswith("import ") or line.startswith("from "):
                pos = i + 1
        lines.insert(pos, "import re")
        s = "\n".join(lines) + "\n"

    s = replace_function(s, "apply_pdf_brand_to_html", PDF_HELPER)

    s = s.replace(
        "apply_pdf_brand_to_html(db, html, 'customer')",
        "apply_pdf_brand_to_html(db, html, 'customer', quote)"
    )
    s = s.replace(
        'apply_pdf_brand_to_html(db, html, "customer")',
        'apply_pdf_brand_to_html(db, html, "customer", quote)'
    )
    s = s.replace(
        "apply_pdf_brand_to_html(db, html, 'internal')",
        "apply_pdf_brand_to_html(db, html, 'internal', quote)"
    )
    s = s.replace(
        'apply_pdf_brand_to_html(db, html, "internal")',
        'apply_pdf_brand_to_html(db, html, "internal", quote)'
    )

    s = s.replace("quote, quote)", "quote)")
    s = s.replace("quote, quote", "quote")

    LEGACY.write_text(s, encoding="utf-8")
    print("PDF professionale definitivo applicato.")


def patch_css():
    css = CSS.read_text(encoding="utf-8")

    if "/* v40.9 global ui polish */" not in css:
        css += r'''

/* v40.9 global ui polish */

/* Respiro generale */
.card,
.panel,
.table-card {
  border-radius: 24px;
}

.card-head,
.panel-head {
  gap: 12px;
}

.card-head h3,
.panel-head h3 {
  letter-spacing: -0.025em;
}

/* Form più ordinati */
.form-grid {
  align-items: end;
  gap: 14px 16px;
}

label,
.field label {
  letter-spacing: .065em;
}

input,
select,
textarea {
  min-height: 44px;
}

textarea {
  line-height: 1.45;
}

/* Suggerimenti meno invasivi */
.smart-suggestions,
.suggest-row,
.quick-suggestions {
  gap: 6px;
  max-width: 100%;
}

.smart-suggestions button,
.suggest-row button,
.quick-suggestions button {
  min-height: 24px;
  padding: 5px 8px;
  font-size: 11px;
  border-radius: 999px;
}

/* Tabelle più professionali */
.table-wrap {
  border-radius: 18px;
  overflow: auto;
}

table {
  border-collapse: separate;
  border-spacing: 0;
}

th {
  font-size: 11px;
  letter-spacing: .075em;
  line-height: 1.2;
  vertical-align: middle;
}

td {
  vertical-align: middle;
  line-height: 1.35;
}

td b,
td strong {
  line-height: 1.25;
}

/* Azioni in tabella */
td:last-child button,
.table-actions button {
  min-height: 34px;
  padding: 7px 10px;
  border-radius: 999px;
}

/* Bottoni più coerenti */
button {
  transition: transform .15s ease, filter .15s ease, border-color .15s ease, background .15s ease;
}

button:hover {
  transform: translateY(-1px);
}

/* Sezioni tab più pulite */
.section-tabs {
  gap: 8px;
  flex-wrap: wrap;
}

.section-tabs button {
  min-height: 38px;
  padding: 9px 14px;
  border-radius: 999px;
}

/* Stat card più equilibrate */
.stats {
  gap: 14px;
}

.stat {
  min-width: 0;
  overflow: hidden;
}

.stat b,
.stat strong {
  letter-spacing: -0.035em;
}

/* Modali più puliti */
.modal,
.detail-modal {
  border-radius: 28px;
}

.modal-head,
.detail-modal-head {
  padding: 22px 24px;
}

.modal-body,
.detail-modal-body {
  padding: 22px 24px 26px;
}

/* Archivio preventivi più leggibile */
.quote-workflow-actions {
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 7px !important;
  justify-content: flex-start !important;
  align-items: center !important;
}

.quote-action,
.workflow-action {
  min-height: 34px;
  height: 34px;
  border-radius: 999px;
  padding: 7px 11px;
  font-size: 12px;
  font-weight: 900;
  white-space: nowrap;
}

.quote-action-pdf {
  background: rgba(59, 130, 246, .14);
  border-color: rgba(59, 130, 246, .36);
  color: #bfdbfe;
}

.quote-action-pdf-internal {
  background: rgba(99, 102, 241, .13);
  border-color: rgba(99, 102, 241, .34);
  color: #c7d2fe;
}

.quote-action-sent {
  background: rgba(14, 165, 233, .13);
  border-color: rgba(14, 165, 233, .34);
  color: #bae6fd;
}

.quote-action-accepted {
  background: rgba(34, 197, 94, .15);
  border-color: rgba(34, 197, 94, .38);
  color: #bbf7d0;
}

.quote-action-rejected {
  background: rgba(244, 63, 94, .14);
  border-color: rgba(244, 63, 94, .36);
  color: #fecdd3;
}

.quote-action-production,
.workflow-action.production {
  background: rgba(34, 211, 238, .15);
  border-color: rgba(34, 211, 238, .40);
  color: #a5f3fc;
}

.quote-action-product,
.workflow-action.product {
  background: rgba(168, 85, 247, .15);
  border-color: rgba(168, 85, 247, .38);
  color: #e9d5ff;
}

.quote-action-sale,
.workflow-action.sale {
  background: rgba(20, 184, 166, .16);
  border-color: rgba(20, 184, 166, .38);
  color: #99f6e4;
}

.quote-action-delivered,
.workflow-action.delivered {
  background: rgba(16, 185, 129, .16);
  border-color: rgba(16, 185, 129, .38);
  color: #a7f3d0;
}

/* Responsive globale */
@media (max-width: 1200px) {
  .split-main,
  .wide-grid {
    grid-template-columns: 1fr !important;
  }

  .form-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 760px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .stats {
    grid-template-columns: 1fr !important;
  }

  .card,
  .panel,
  .table-card {
    border-radius: 20px;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")
        print("Pulizia UI globale applicata.")
    else:
        print("Pulizia UI globale già presente.")


def main():
    patch_backend()
    patch_css()
    print("Patch v40.9.0 completata: PDF definitivo + UI polish globale.")


if __name__ == "__main__":
    main()
