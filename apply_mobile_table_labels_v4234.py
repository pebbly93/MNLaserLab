from pathlib import Path

MAIN = Path("frontend/src/main.jsx")

OLD = """<td key={c.key}>{c.render ? c.render(r, i) : r[c.key]}</td>"""
NEW = """<td key={c.key} data-label={c.label}>{c.render ? c.render(r, i) : r[c.key]}</td>"""

def main():
    s = MAIN.read_text(encoding="utf-8")

    if OLD not in s:
        print("Pattern DataTable già aggiornato o non trovato.")
        return

    s = s.replace(OLD, NEW, 1)
    MAIN.write_text(s, encoding="utf-8")
    print("DataTable aggiornato con data-label per vista mobile.")

if __name__ == "__main__":
    main()
