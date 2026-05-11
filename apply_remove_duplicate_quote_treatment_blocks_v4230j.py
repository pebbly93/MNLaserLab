from pathlib import Path
import re

MAIN = Path("frontend/src/main.jsx")

def find_block_bounds(s, marker_pos):
    """
    Trova il div wrapper <div className="form-grid-full quote-treatment-inline"> ... </div>
    usando un conteggio semplice dei div.
    """
    start = s.rfind('<div className="form-grid-full quote-treatment-inline">', 0, marker_pos + 1)
    if start == -1:
        return None

    pos = start
    depth = 0

    tag_re = re.compile(r'</?div\b[^>]*>', re.I)
    for m in tag_re.finditer(s, start):
        tag = m.group(0)

        if tag.startswith('</'):
            depth -= 1
            if depth == 0:
                return start, m.end()
        else:
            depth += 1

    return None

def main():
    s = MAIN.read_text(encoding="utf-8")

    quote_start = s.find("function Quote(")
    sales_start = s.find("function Sales(", quote_start)

    if quote_start == -1 or sales_start == -1:
        raise RuntimeError("Non trovo function Quote / function Sales")

    marker = '<div className="form-grid-full quote-treatment-inline">'
    positions = [m.start() for m in re.finditer(re.escape(marker), s)]

    print("Blocchi quote-treatment-inline trovati:", len(positions), positions)

    keep_done = False
    remove_ranges = []

    for pos in positions:
        inside_quote = quote_start <= pos < sales_start

        if inside_quote and not keep_done:
            keep_done = True
            continue

        bounds = find_block_bounds(s, pos)
        if bounds:
            remove_ranges.append(bounds)

    # Rimuove dal fondo verso l'inizio.
    for start, end in sorted(remove_ranges, reverse=True):
        s = s[:start] + "\n" + s[end:]

    MAIN.write_text(s, encoding="utf-8")

    print(f"Rimossi {len(remove_ranges)} blocchi duplicati/fuori Quote. Lasciato solo il primo dentro Quote.")

if __name__ == "__main__":
    main()
