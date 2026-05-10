from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"

GOOD_FUNC = r'''
def inject_pdf_back_button(html):
    back_button = """  <button class="back-btn" onclick="window.location.href='/'">← Torna al gestionale</button>"""

    if "back-btn" not in html:
        html = html.replace("<body>", "<body>\n" + back_button, 1)

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
        html = html.replace("</style>", css + "\n  </style>", 1)

    return html
'''

def replace_function(source: str, name: str, new_code: str) -> str:
    start = source.find(f"def {name}(")
    if start == -1:
        source += "\n\n" + new_code.strip() + "\n"
        return source

    end = source.find("\ndef ", start + 1)
    if end == -1:
        end = len(source)

    return source[:start] + new_code.strip() + "\n\n" + source[end + 1:]

def main():
    s = LEGACY.read_text(encoding="utf-8")
    s = replace_function(s, "inject_pdf_back_button", GOOD_FUNC)
    LEGACY.write_text(s, encoding="utf-8")
    print("Fix syntax inject_pdf_back_button applicato.")

if __name__ == "__main__":
    main()
