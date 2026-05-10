from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"


NEW_HELPER = r'''
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

    # Logo fallback MN se non è stato caricato un logo nelle impostazioni.
    if not logo:
        logo = (
            "data:image/svg+xml;utf8,"
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 160 160'>"
            "<rect width='160' height='160' rx='34' fill='%23f8fafc'/>"
            "<circle cx='80' cy='80' r='62' fill='white' stroke='%23058482' stroke-width='6'/>"
            "<text x='80' y='76' text-anchor='middle' font-family='Arial, Helvetica, sans-serif' font-size='34' font-weight='900' fill='%230f172a'>MN</text>"
            "<text x='80' y='103' text-anchor='middle' font-family='Arial, Helvetica, sans-serif' font-size='13' font-weight='700' fill='%23058482'>LASER LAB</text>"
            "</svg>"
        )

    contact_bits = [x for x in [author, email, phone, address, website, vat] if str(x or "").strip()]
    contact_line = " · ".join(contact_bits)

    # Pulizia residui patch precedenti.
    html = html.replace("{_pdf_brand_css(db)}", "")
    html = html.replace("{_pdf_brand_block(db)}", "")

    # Sostituzioni dinamiche.
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

    business_subtitle = footer or "Creazioni artigianali in legno e taglio laser"
    for old in old_subtitles:
        html = html.replace(old, business_subtitle)

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

    # Rimuove eventuale testata duplicata nata dalle patch precedenti.
    html = re.sub(
        r"<div class=['\"]brand-head['\"].*?</div>\s*</div>",
        "",
        html,
        flags=re.DOTALL
    )

    # Inserisce il logo nella testata esistente.
    if "pdf-brand-logo-inline" not in html:
        logo_html = f"<img class='pdf-brand-logo-inline' src='{logo}' alt='Logo MN Laser Lab' />"
        html = html.replace(
            f"<h1>{company}</h1>",
            f"<div class='pdf-brand-title-row'>{logo_html}<div><h1>{company}</h1><p class='pdf-dynamic-contact'>{contact_line}</p></div></div>",
            1
        )

    # Se il contatto non è entrato, lo aggiunge sotto il titolo.
    if contact_line and contact_line not in html:
        html = html.replace(
            f"<h1>{company}</h1>",
            f"<h1>{company}</h1><p class='pdf-dynamic-contact'>{contact_line}</p>",
            1
        )

    # Spese di progetto: voce separata nel PDF solo se > 0.
    if project_fee > 0 and "pdf-project-fee" not in html:
        project_fee_html = f"""
        <div class="pdf-project-fee">
          <span>Spese di progetto</span>
          <strong>€ {project_fee:.2f}</strong>
        </div>
        """

        if "Totale preventivo" in html:
            html = html.replace("Totale preventivo", project_fee_html + "\nTotale preventivo", 1)
        else:
            html = html.replace("</body>", project_fee_html + "\n</body>", 1)

    # CSS professionale PDF.
    extra_css = f"""
    <style>
      :root {{
        --brand: {color};
        --ink: #0f172a;
        --muted: #64748b;
        --line: #e2e8f0;
        --soft: #f8fafc;
      }}

      body {{
        background: #f1f5f9 !important;
        color: var(--ink) !important;
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif !important;
        margin: 0 !important;
        padding: 34px 0 44px !important;
      }}

      .page, main, .document, .quote-page {{
        width: min(920px, calc(100vw - 64px)) !important;
        margin: 0 auto !important;
        background: #ffffff !important;
      }}

      .pdf-brand-title-row {{
        display: flex !important;
        align-items: center !important;
        gap: 16px !important;
      }}

      .pdf-brand-logo-inline {{
        width: 74px !important;
        height: 74px !important;
        object-fit: contain !important;
        display: block !important;
        flex: 0 0 auto !important;
      }}

      .pdf-dynamic-contact {{
        margin: 5px 0 0 !important;
        color: var(--muted) !important;
        font-size: 13px !important;
        line-height: 1.35 !important;
        font-weight: 600 !important;
      }}

      h1 {{
        margin: 0 !important;
        font-size: 28px !important;
        line-height: 1.05 !important;
        letter-spacing: -0.04em !important;
      }}

      h2, h3 {{
        letter-spacing: -0.025em !important;
      }}

      table {{
        width: 100% !important;
        border-collapse: collapse !important;
        table-layout: fixed !important;
      }}

      th {{
        background: #f1f5f9 !important;
        color: #475569 !important;
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: .06em !important;
        padding: 12px 13px !important;
      }}

      td {{
        padding: 13px !important;
        border-bottom: 1px solid #e5e7eb !important;
        color: #1e293b !important;
        font-size: 13px !important;
        line-height: 1.35 !important;
      }}

      td:last-child,
      th:last-child,
      .right {{
        text-align: right !important;
      }}

      .pdf-project-fee {{
        margin: 18px 0 10px !important;
        border: 1px solid rgba(5, 132, 130, .22) !important;
        background: linear-gradient(135deg, rgba(5,132,130,.08), rgba(5,132,130,.03)) !important;
        border-radius: 16px !important;
        padding: 15px 18px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 18px !important;
        color: var(--ink) !important;
      }}

      .pdf-project-fee span {{
        font-size: 13px !important;
        font-weight: 800 !important;
        color: #334155 !important;
      }}

      .pdf-project-fee strong {{
        font-size: 22px !important;
        color: var(--brand) !important;
      }}

      .print-button,
      .print-actions,
      button {{
        position: fixed;
        top: 24px;
        right: 24px;
      }}

      @media print {{
        body {{
          background: white !important;
          padding: 0 !important;
        }}

        .page, main, .document, .quote-page {{
          width: 100% !important;
          margin: 0 !important;
          box-shadow: none !important;
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

    # Sostituisce helper PDF con versione professionale.
    s = replace_function(s, "apply_pdf_brand_to_html", NEW_HELPER)

    # Le funzioni PDF devono passare quote all'helper, altrimenti non può leggere project_fee.
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

    # Normalizza eventuali doppioni accidentali.
    s = s.replace("quote, quote)", "quote)")
    s = s.replace("quote, quote", "quote")

    # Assicura che save_quote salvi sempre project_fee.
    start = s.find("def save_quote")
    if start != -1:
        end = s.find("\ndef ", start + 1)
        if end == -1:
            end = len(s)
        block = s[start:end]

        if 'quote["project_fee"]' not in block:
            anchors = [
                'quote["status"]',
                "quote['status']",
                "quotes = db.setdefault",
            ]

            inserted = False
            for a in anchors:
                pos = block.find(a)
                if pos != -1:
                    line_start = block.rfind("\n", 0, pos) + 1
                    block = block[:line_start] + '    quote["project_fee"] = parse_float(payload.get("project_fee"))\n' + block[line_start:]
                    inserted = True
                    break

            if not inserted:
                block = block.replace("return quote", 'quote["project_fee"] = parse_float(payload.get("project_fee"))\n    return quote', 1)

            s = s[:start] + block + s[end:]

    # Assicura che calculate_quote legga e sommi project_fee.
    start = s.find("def calculate_quote")
    if start != -1:
        end = s.find("\ndef ", start + 1)
        if end == -1:
            end = len(s)
        block = s[start:end]

        if "project_fee = parse_float" not in block:
            # inserisci dopo la prima riga della funzione
            first_nl = block.find("\n")
            block = block[:first_nl+1] + '    project_fee = parse_float(payload.get("project_fee"))\n' + block[first_nl+1:]

        # aggiunge project_fee alla prima assegnazione real_cost se non presente
        lines = block.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith("real_cost =") and "project_fee" not in line:
                lines[i] = line.rstrip() + " + project_fee"
                break
        block = "\n".join(lines)

        if '"project_fee"' not in block and "'project_fee'" not in block:
            if '"real_cost":' in block:
                block = block.replace('"real_cost":', '"project_fee": round(project_fee, 2),\n        "real_cost":', 1)
            elif "'real_cost':" in block:
                block = block.replace("'real_cost':", "'project_fee': round(project_fee, 2),\n        'real_cost':", 1)

        s = s[:start] + block + s[end:]

    LEGACY.write_text(s, encoding="utf-8")
    print("Backend PDF professionale + project_fee applicato.")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    start = s.find("function Quote(")
    end = s.find("\nfunction Sales", start)
    if start == -1 or end == -1:
        raise RuntimeError("Funzione Quote non trovata")

    block = s[start:end]

    # Aggiunge project_fee allo stato cost se manca.
    m = re.search(r"const \[cost, setCost\] = useState\(\{([^}]+)\}\);", block, re.DOTALL)
    if m and "project_fee" not in m.group(1):
        old_obj = m.group(1)
        new_obj = old_obj.replace("commission: ''", "commission: '', project_fee: ''")
        if new_obj == old_obj:
            new_obj = old_obj + ", project_fee: ''"
        block = block[:m.start(1)] + new_obj + block[m.end(1):]

    # Aggiunge label se manca.
    m = re.search(r"const costLabels = \{([^}]+)\};", block, re.DOTALL)
    if m and "project_fee" not in m.group(1):
        old_obj = m.group(1)
        new_obj = old_obj.replace("commission: 'Commissioni %'", "commission: 'Commissioni %', project_fee: 'Spese di progetto €'")
        if new_obj == old_obj:
            new_obj = old_obj + ", project_fee: 'Spese di progetto €'"
        block = block[:m.start(1)] + new_obj + block[m.end(1):]

    s = s[:start] + block + s[end:]
    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend project_fee verificato.")


def main():
    patch_backend()
    patch_frontend()
    print("Patch v40.8.4 completata.")


if __name__ == "__main__":
    main()
