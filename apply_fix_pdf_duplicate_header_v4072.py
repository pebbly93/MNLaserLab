from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"


def clean_injected_blocks(s: str) -> str:
    # Rimuove l'iniezione aggressiva fatta nella v40.7.1.
    replacements = [
        "\\n{_pdf_brand_css(db)}",
        "{_pdf_brand_css(db)}",
        "\\n{_pdf_brand_block(db)}\\n<div class='pdf-intro'>{get_pdf_settings(db).get('intro_text','')}</div>",
        "\\n{_pdf_brand_block(db)}",
        "{_pdf_brand_block(db)}",
        "<div class='pdf-terms'>{get_pdf_settings(db).get('terms','')}</div>\\n<div class='pdf-footer'>{get_pdf_settings(db).get('footer','')}</div>\\n",
        "<div class='pdf-footer'>{get_pdf_settings(db).get('footer','')}</div>\\n",
    ]

    for old in replacements:
        s = s.replace(old, "")

    return s


def add_safe_pdf_template_helpers(s: str) -> str:
    if "def apply_pdf_brand_to_html" in s:
        return s

    helper = r'''

# ---------------------------------------------------------------------------
# v40.7.2 - Applicazione sicura modello PDF senza doppia intestazione
# ---------------------------------------------------------------------------

def apply_pdf_brand_to_html(db, html, kind="customer"):
    """Applica dati PDF/brand al documento già esistente senza duplicare header."""
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

    # Sostituzioni leggere sui testi storici.
    html = html.replace("MN Laser Lab", company)
    html = html.replace("Filippo Lolli - filippololli1@gmail.com", f"{author} - {email}".strip(" -"))
    html = html.replace("#058482", color)

    # Se il documento aveva il testo standard, lo sostituiamo con quello configurato.
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
        html = html.replace(
            "Preventivo generato con MN Laser Lab Manager.",
            footer
        )

    # Inietta dettagli aziendali solo dentro la testata già esistente, non come nuovo header.
    contact_bits = [x for x in [author, email, phone, address, website, vat] if x]
    contact_line = " · ".join(contact_bits)

    if contact_line:
        # Se troviamo una riga contatto vecchia, la rendiamo più completa.
        html = html.replace(
            f"{author} - {email}".strip(" -"),
            contact_line
        )

    # Logo: lo inseriamo solo se non esiste già un logo e se troviamo il titolo azienda.
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
        max-width: 72px;
        max-height: 54px;
        object-fit: contain;
        display: block;
      }}
      @media print {{
        .print-button, .print-actions, button {{
          display: none !important;
        }}
      }}
    </style>
    """

    if "</head>" in html and "pdf-brand-title-row" not in html.split("</head>")[0]:
        html = html.replace("</head>", extra_css + "\n</head>", 1)
    elif "</head>" in html:
        html = html.replace("</head>", extra_css + "\n</head>", 1)

    return html
'''
    return s + "\n\n" + helper.strip() + "\n"


def wrap_pdf_function(s: str, fn_name: str, kind: str) -> str:
    start = s.find(f"def {fn_name}")
    if start == -1:
        raise RuntimeError(f"{fn_name} non trovata")

    end = s.find("\ndef ", start + 1)
    if end == -1:
        end = len(s)

    block = s[start:end]

    if "apply_pdf_brand_to_html" in block:
        return s

    # Caso più comune: return html
    if "return html" in block:
        block = block.replace("return html", f"return apply_pdf_brand_to_html(db, html, '{kind}')", 1)
    else:
        # Fallback: intercetta l'ultimo return f'''...''' non è sicuro, quindi segnala.
        raise RuntimeError(f"Non trovo 'return html' in {fn_name}. Serve patch adattata alla funzione reale.")

    return s[:start] + block + s[end:]


def main():
    s = LEGACY.read_text(encoding="utf-8")

    s = clean_injected_blocks(s)
    s = add_safe_pdf_template_helpers(s)

    s = wrap_pdf_function(s, "quote_customer_html", "customer")
    s = wrap_pdf_function(s, "quote_internal_html", "internal")

    LEGACY.write_text(s, encoding="utf-8")
    print("Patch v40.7.2 applicata: rimossa doppia intestazione PDF e applicato modello in modo sicuro.")


if __name__ == "__main__":
    main()
