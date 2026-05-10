from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"


HELPER = r'''

# ---------------------------------------------------------------------------
# v40.7.2b - Applicazione sicura modello PDF senza doppia intestazione
# ---------------------------------------------------------------------------

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

    # Rimuove eventuali blocchi duplicati della patch precedente.
    html = html.replace("{_pdf_brand_css(db)}", "")
    html = html.replace("{_pdf_brand_block(db)}", "")

    # Colore brand.
    html = html.replace("#058482", color)

    # Testi principali.
    html = html.replace("MN Laser Lab", company)
    html = html.replace("Filippo Lolli - filippololli1@gmail.com", f"{author} - {email}".strip(" -"))

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

    contact_bits = [x for x in [author, email, phone, address, website, vat] if x]
    contact_line = " · ".join(contact_bits)

    if contact_line:
        html = html.replace(f"{author} - {email}".strip(" -"), contact_line)

    # Logo: lo inserisce nella testata esistente, non crea una seconda intestazione.
    if logo and "pdf-brand-logo-inline" not in html:
        logo_html = f"<img class='pdf-brand-logo-inline' src='{logo}' alt='Logo' />"

        # Caso frequente: <h1>MN Laser Lab</h1> dopo sostituzione.
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
      @media print {{
        .print-button, .print-actions, button {{
          display: none !important;
        }}
      }}
    </style>
    """

    if "</head>" in html and "pdf-brand-logo-inline" not in html.split("</head>")[0]:
        html = html.replace("</head>", extra_css + "\n</head>", 1)
    elif "</head>" in html:
        html = html.replace("</head>", extra_css + "\n</head>", 1)

    return html
'''


def remove_previous_bad_injections(s: str) -> str:
    bad = [
        "\\n{_pdf_brand_css(db)}",
        "{_pdf_brand_css(db)}",
        "\\n{_pdf_brand_block(db)}\\n<div class='pdf-intro'>{get_pdf_settings(db).get('intro_text','')}</div>",
        "\\n{_pdf_brand_block(db)}",
        "{_pdf_brand_block(db)}",
        "<div class='pdf-terms'>{get_pdf_settings(db).get('terms','')}</div>\\n<div class='pdf-footer'>{get_pdf_settings(db).get('footer','')}</div>\\n",
        "<div class='pdf-footer'>{get_pdf_settings(db).get('footer','')}</div>\\n",
    ]

    for x in bad:
        s = s.replace(x, "")

    return s


def remove_old_helper(s: str) -> str:
    start = s.find("def apply_pdf_brand_to_html(")
    if start == -1:
        return s

    end = s.find("\ndef ", start + 1)
    if end == -1:
        end = len(s)

    return s[:start] + s[end + 1:]


def patch_function_return(s: str, fn_name: str, kind: str) -> str:
    start = s.find(f"def {fn_name}")
    if start == -1:
        raise RuntimeError(f"{fn_name} non trovata")

    end = s.find("\ndef ", start + 1)
    if end == -1:
        end = len(s)

    block = s[start:end]

    if f"apply_pdf_brand_to_html(db," in block:
        return s

    # Caso 1: return html
    if "return html" in block:
        block = block.replace("return html", f"return apply_pdf_brand_to_html(db, html, '{kind}')", 1)
        return s[:start] + block + s[end:]

    # Caso 2: la funzione ritorna direttamente una f-string tripla:
    # return f""" ... """
    idx = block.find('return f"""')
    quote = '"""'

    if idx == -1:
        idx = block.find("return f'''")
        quote = "'''"

    if idx != -1:
        prefix = block[:idx]
        rest = block[idx:]

        # trasforma:
        # return f"""..."""
        # in:
        # html = f"""..."""
        # return apply_pdf_brand_to_html(...)
        rest = rest.replace("return f" + quote, "html = f" + quote, 1)

        # Aggiunge return dopo la chiusura della stringa.
        last = rest.rfind(quote)
        if last == -1:
            raise RuntimeError(f"Non riesco a trovare chiusura stringa in {fn_name}")

        rest = rest[:last + 3] + f"\n    return apply_pdf_brand_to_html(db, html, '{kind}')" + rest[last + 3:]

        block = prefix + rest
        return s[:start] + block + s[end:]

    raise RuntimeError(f"Non trovo un return gestibile in {fn_name}. Mandami il sed della funzione.")


def main():
    s = LEGACY.read_text(encoding="utf-8")

    s = remove_previous_bad_injections(s)
    s = remove_old_helper(s)
    s += "\n\n" + HELPER.strip() + "\n"

    s = patch_function_return(s, "quote_customer_html", "customer")
    s = patch_function_return(s, "quote_internal_html", "internal")

    LEGACY.write_text(s, encoding="utf-8")
    print("Patch v40.7.2b applicata: PDF senza doppia intestazione e modello applicato al template esistente.")


if __name__ == "__main__":
    main()
