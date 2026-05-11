from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"

def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    # Rimuove completamente il componente SystemPage inserito dalla patch precedente.
    s = re.sub(
        r"\nfunction SystemPage\(\{ toast \}\)\s*\{.*?\n\}\n\nfunction ",
        "\nfunction ",
        s,
        flags=re.DOTALL
    )

    # Rimuove eventuale voce menu inserita in modo automatico.
    s = re.sub(
        r"\n\s*\{\s*id:\s*'system'\s*,\s*label:\s*'Sistema'\s*,\s*icon:\s*Activity\s*\},",
        "",
        s
    )

    s = re.sub(
        r"\n\s*\{\s*id:\s*\"system\"\s*,\s*label:\s*\"Sistema\"\s*,\s*icon:\s*Activity\s*\},",
        "",
        s
    )

    # Rimuove eventuale render pagina inserito prima di settings.
    s = re.sub(
        r"\n\s*\{\s*page\s*===\s*'system'\s*&&\s*<SystemPage\s+toast=\{toast\}\s*/>\s*\}",
        "",
        s
    )
    s = re.sub(
        r"\n\s*\{\s*active\s*===\s*'system'\s*&&\s*<SystemPage\s+toast=\{toast\}\s*/>\s*\}",
        "",
        s
    )
    s = re.sub(
        r"\n\s*\{\s*view\s*===\s*'system'\s*&&\s*<SystemPage\s+toast=\{toast\}\s*/>\s*\}",
        "",
        s
    )

    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend ripristinato: SystemPage rimossa temporaneamente.")

def patch_css():
    css = CSS.read_text(encoding="utf-8")

    css = re.sub(
        r"\n/\* v42\.2\.0 system page / mobile QR \*/.*?(?=\n/\*|\Z)",
        "\n",
        css,
        flags=re.DOTALL
    )

    CSS.write_text(css, encoding="utf-8")
    print("CSS SystemPage rimosso temporaneamente.")

def main():
    patch_frontend()
    patch_css()
    print("Patch v42.2.0b completata: app sbloccata.")

if __name__ == "__main__":
    main()
