from pathlib import Path
import re

CSS = Path("frontend/src/style.css")

def main():
    css = CSS.read_text(encoding="utf-8")

    css = re.sub(
        r'\n/\* v42\.3\.4 - Smartphone refinement for quote page only via media queries \*/[\s\S]*?(?=\n/\*|\Z)',
        '\n',
        css,
        flags=re.DOTALL
    )

    CSS.write_text(css, encoding="utf-8")
    print("Rollback v42.3.4 applicato: media query mobile preventivi rimosse.")

if __name__ == "__main__":
    main()
