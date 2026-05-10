from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"


def patch_customer_pdf(s: str) -> str:
    start = s.find("def quote_customer_html")
    end = s.find("\ndef ", start + 1)

    if start == -1:
        raise RuntimeError("quote_customer_html non trovata")

    block = s[start:end]

    if "_pdf_brand_css(db)" not in block:
        block = block.replace(
            "<head>",
            "<head>\\n{_pdf_brand_css(db)}",
            1
        )

    # Inserisce brand block dopo body, se possibile.
    if "_pdf_brand_block(db)" not in block:
        block = block.replace(
            "<body>",
            "<body>\\n{_pdf_brand_block(db)}\\n<div class='pdf-intro'>{get_pdf_settings(db).get('intro_text','')}</div>",
            1
        )

    # Inserisce termini e footer prima della chiusura body.
    if "pdf-terms" not in block:
        block = block.replace(
            "</body>",
            "<div class='pdf-terms'>{get_pdf_settings(db).get('terms','')}</div>\\n<div class='pdf-footer'>{get_pdf_settings(db).get('footer','')}</div>\\n</body>",
            1
        )

    return s[:start] + block + s[end:]


def patch_internal_pdf(s: str) -> str:
    start = s.find("def quote_internal_html")
    end = s.find("\ndef ", start + 1)

    if start == -1:
        raise RuntimeError("quote_internal_html non trovata")

    block = s[start:end]

    if "_pdf_brand_css(db)" not in block:
        block = block.replace(
            "<head>",
            "<head>\\n{_pdf_brand_css(db)}",
            1
        )

    if "_pdf_brand_block(db)" not in block:
        block = block.replace(
            "<body>",
            "<body>\\n{_pdf_brand_block(db)}",
            1
        )

    if "pdf-footer" not in block:
        block = block.replace(
            "</body>",
            "<div class='pdf-footer'>{get_pdf_settings(db).get('footer','')}</div>\\n</body>",
            1
        )

    return s[:start] + block + s[end:]


def main():
    s = LEGACY.read_text(encoding="utf-8")

    s = patch_customer_pdf(s)
    s = patch_internal_pdf(s)

    LEGACY.write_text(s, encoding="utf-8")
    print("Patch v40.7.1 applicata: modello PDF integrato in PDF cliente/interno.")


if __name__ == "__main__":
    main()
