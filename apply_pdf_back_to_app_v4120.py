from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"

BACK_BUTTON = r'''
  <button class="back-btn" onclick="window.location.href='/'">← Torna al gestionale</button>
'''

BACK_CSS = r'''
    .back-btn {
      position: fixed;
      left: 20px;
      top: 20px;
      border: 0;
      background: #0f172a;
      color: white;
      border-radius: 999px;
      padding: 12px 18px;
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 12px 30px rgba(0,0,0,.18);
      z-index: 100;
    }

    @media print {
      .back-btn {
        display: none !important;
      }
    }
'''

def inject_back_button_in_html(html: str) -> str:
    if "back-btn" not in html:
        html = html.replace("<body>", "<body>\n" + BACK_BUTTON, 1)

    if ".back-btn" not in html:
        html = html.replace("</style>", BACK_CSS + "\n  </style>", 1)

    return html

def patch_function_return(source: str, fn_name: str) -> str:
    start = source.find(f"def {fn_name}(")
    if start == -1:
        print(f"{fn_name} non trovata")
        return source

    end = source.find("\ndef ", start + 1)
    if end == -1:
        end = len(source)

    block = source[start:end]

    if "inject_pdf_back_button" in block:
        return source

    # Caso cliente: return html
    block = block.replace(
        "return html",
        "return inject_pdf_back_button(html)",
        1
    )

    # Caso PDF che passa dal brand helper
    block = block.replace(
        "return apply_pdf_brand_to_html(db, html, 'customer', quote)",
        "return inject_pdf_back_button(apply_pdf_brand_to_html(db, html, 'customer', quote))"
    )
    block = block.replace(
        'return apply_pdf_brand_to_html(db, html, "customer", quote)',
        'return inject_pdf_back_button(apply_pdf_brand_to_html(db, html, "customer", quote))'
    )
    block = block.replace(
        "return apply_pdf_brand_to_html(db, html, 'internal', quote)",
        "return inject_pdf_back_button(apply_pdf_brand_to_html(db, html, 'internal', quote))"
    )
    block = block.replace(
        'return apply_pdf_brand_to_html(db, html, "internal", quote)',
        'return inject_pdf_back_button(apply_pdf_brand_to_html(db, html, "internal", quote))'
    )

    return source[:start] + block + source[end:]

def main():
    s = LEGACY.read_text(encoding="utf-8")

    if "def inject_pdf_back_button" not in s:
        helper = r'''
def inject_pdf_back_button(html):
    if "back-btn" not in html:
        html = html.replace("<body>", "<body>\n  <button class=\\"back-btn\\" onclick=\\"window.location.href='/'\\">← Torna al gestionale</button>", 1)

    if ".back-btn" not in html:
        css = """
    .back-btn {
      position: fixed;
      left: 20px;
      top: 20px;
      border: 0;
      background: #0f172a;
      color: white;
      border-radius: 999px;
      padding: 12px 18px;
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 12px 30px rgba(0,0,0,.18);
      z-index: 100;
    }

    @media print {
      .back-btn {
        display: none !important;
      }
    }
"""
        html = html.replace("</style>", css + "\\n  </style>", 1)

    return html
'''
        s += "\n\n" + helper.strip() + "\n"

    s = patch_function_return(s, "quote_customer_html")
    s = patch_function_return(s, "quote_internal_html")

    LEGACY.write_text(s, encoding="utf-8")
    print("Patch v41.2.0 applicata: pulsante Torna al gestionale nei PDF.")

if __name__ == "__main__":
    main()
