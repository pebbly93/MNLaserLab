from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"

LOGO_COMPONENT = r'''
function MNLogoMark() {
  return (
    <div className="mn-logo-mark" aria-label="MN Laser Lab">
      <svg viewBox="0 0 120 120" role="img">
        <rect x="8" y="8" width="104" height="104" rx="26" fill="rgba(255,255,255,.96)" />
        <circle cx="60" cy="60" r="43" fill="none" stroke="#0f172a" strokeWidth="4" opacity=".16" />
        <path d="M25 68 L25 45 L36 45 L47 59 L58 45 L69 45 L69 75 L58 75 L58 61 L49 72 L45 72 L36 61 L36 75 L25 75 Z" fill="#0f172a"/>
        <path d="M73 45 L94 45 L94 55 L84 55 L84 75 L73 75 Z" fill="#058482"/>
        <path d="M30 84 C43 91 76 91 91 82" fill="none" stroke="#058482" strokeWidth="5" strokeLinecap="round"/>
      </svg>
    </div>
  );
}

'''

def insert_logo_component(s: str) -> str:
    if "function MNLogoMark" in s:
        return s

    # Inserisce prima del primo componente noto.
    markers = ["function Sidebar", "function App", "function Layout", "function PageTitle"]
    for marker in markers:
        idx = s.find(marker)
        if idx != -1:
            return s[:idx] + LOGO_COMPONENT + "\n\n" + s[idx:]

    return LOGO_COMPONENT + "\n\n" + s


def replace_logo_img(s: str) -> str:
    # Sostituisce img che puntano al logo con componente inline.
    patterns = [
        r'<img\s+[^>]*src=\{?["\']?/mn_laser_lab_logo\.png["\']?\}?[^>]*>',
        r'<img\s+[^>]*src=\{?["\']?mn_laser_lab_logo\.png["\']?\}?[^>]*>',
        r'<img\s+[^>]*src=\{?["\']?/logo\.png["\']?\}?[^>]*>',
        r'<img\s+[^>]*src=\{?["\']?logo\.png["\']?\}?[^>]*>',
    ]

    for pat in patterns:
        s = re.sub(pat, "<MNLogoMark />", s)

    # Caso molto comune: <img className="..." src={logo} ...>
    # Non lo tocchiamo genericamente per non rompere altre immagini.

    return s


def add_css(css: str) -> str:
    if "/* v42.0.6 embedded logo fallback */" in css:
        return css

    css += r'''

/* v42.0.6 embedded logo fallback */
.mn-logo-mark {
  width: 52px;
  height: 52px;
  min-width: 52px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  overflow: hidden;
  background: rgba(255,255,255,.92);
  border: 1px solid rgba(15,23,42,.08);
  box-shadow: 0 12px 30px rgba(0,0,0,.16);
}

.mn-logo-mark svg {
  width: 100%;
  height: 100%;
  display: block;
}

.sidebar .mn-logo-mark,
.side .mn-logo-mark,
nav .mn-logo-mark {
  flex: 0 0 auto;
}

@media (max-width: 640px) {
  .mn-logo-mark {
    width: 46px;
    height: 46px;
    min-width: 46px;
    border-radius: 14px;
  }
}
'''
    return css


def main():
    s = FRONTEND.read_text(encoding="utf-8")
    s = insert_logo_component(s)
    s = replace_logo_img(s)
    FRONTEND.write_text(s, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = add_css(css)
    CSS.write_text(css, encoding="utf-8")

    print("Patch v42.0.6 applicata: logo embedded fallback inserito.")

if __name__ == "__main__":
    main()
