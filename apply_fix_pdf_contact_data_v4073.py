from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"

OLD_HELPER_MARKER = "def apply_pdf_brand_to_html("

NEW_HELPER = r'''
def apply_pdf_brand_to_html(db, html, kind="customer"):
    settings = get_pdf_settings(db)

    company = settings.get("company_name", "MN Laser Lab") or "MN Laser Lab"
    author = settings.get("author", "") or ""
    email = settings.get("email", "") or ""
    phone = settings.get("phone", "") or ""
    address = settings.get("address", "") or ""
    website = settings.get("website", "") or ""
    vat = settings.get("vat", "") or ""
    color = settings.get("primary_color", "#058482") or "#058482"
    footer = settings.get("footer", "") or ""
    terms = settings.get("terms", "") or ""
    intro = settings.get("intro_text", "") or ""
    logo = settings.get("logo_data_url", "") or ""

    contact_bits = [x for x in [author, email, phone, address, website, vat] if str(x or "").strip()]
    contact_line = " · ".join(contact_bits)

    # Rimuove residui di eventuali iniezioni vecchie.
    html = html.replace("{_pdf_brand_css(db)}", "")
    html = html.replace("{_pdf_brand_block(db)}", "")

    # Colore brand.
    html = html.replace("#058482", color)

    # Nome azienda.
    html = html.replace("MN Laser Lab", company)

    # Sostituzioni robuste delle righe contatto vecchie/hardcoded.
    old_contact_variants = [
        "Filippo Lolli - filippololli1@gmail.com",
        "Filippo Lolli · filippololli1@gmail.com",
        "Filippo Lolli - filippololli@gmail.com",
        "Filippo Lolli · filippololli@gmail.com",
        "filippololli@gmail.com",
        "filippololli1@gmail.com",
    ]

    for old in old_contact_variants:
        if old in html:
            html = html.replace(old, contact_line or old)

    # Sostituisce payoff/descrizione storica, se presente.
    old_subtitle_variants = [
        "Creazioni artigianali in legno · Taglio e incisione laser",
        "Creazioni artigianali in legno - Taglio e incisione laser",
        "Creazioni artigianali in legno e taglio laser",
    ]

    business_subtitle = settings.get("business_subtitle", "") or settings.get("footer", "") or ""
    if business_subtitle:
        for old in old_subtitle_variants:
            html = html.replace(old, business_subtitle)

    # Testo introduttivo, condizioni e footer.
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

    # Se non siamo riusciti a sostituire una riga contatto, la aggiungiamo sotto il nome azienda.
    if contact_line and contact_line not in html:
        html = html.replace(
            f"<h1>{company}</h1>",
            f"<h1>{company}</h1><p class='pdf-dynamic-contact'>{contact_line}</p>",
            1
        )

    # Logo dentro la testata esistente, non come seconda intestazione.
    if logo and "pdf-brand-logo-inline" not in html:
        logo_html = f"<img class='pdf-brand-logo-inline' src='{logo}' alt='Logo' />"
        html = html.replace(
            f"<h1>{company}</h1>",
            f"<div class='pdf-brand-title-row'>{logo_html}<h1>{company}</h1></div>",
            1
        )

    extra_css = f"""
    <style>
      :root {{ --brand: {color}; }}
      .pdf-brand-title-row {{
        display: flex;
        align-items: center;
        gap: 14px;
      }}
      .pdf-brand-logo-inline {{
        max-width: 76px;
        max-height: 56px;
        object-fit: contain;
        display: block;
      }}
      .pdf-dynamic-contact {{
        margin: 4px 0;
        color: #475569;
        font-size: 13px;
      }}
      @media print {{
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


def replace_helper(source: str) -> str:
    start = source.find(OLD_HELPER_MARKER)
    if start == -1:
        return source + "\n\n" + NEW_HELPER.strip() + "\n"

    end = source.find("\ndef ", start + 1)
    if end == -1:
        end = len(source)

    return source[:start] + NEW_HELPER.strip() + "\n\n" + source[end + 1:]


def main():
    s = LEGACY.read_text(encoding="utf-8")
    s = replace_helper(s)
    LEGACY.write_text(s, encoding="utf-8")
    print("Patch v40.7.3 applicata: dati contatto PDF resi dinamici.")


if __name__ == "__main__":
    main()
