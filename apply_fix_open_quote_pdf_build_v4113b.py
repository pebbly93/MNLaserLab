from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"

NEW_FUNC = r'''
  async function openQuotePdf(q, type = 'customer') {
    const id = q?.id || q?.quote_id || q;
    if (!id) {
      toast('Preventivo non valido', 'err');
      return;
    }

    const host = window.location.hostname || '127.0.0.1';
    const protocol = window.location.protocol?.startsWith('http') ? window.location.protocol : 'http:';
    const apiRoot = `${protocol}//${host}:8000`;
    const url = `${apiRoot}/api/quote-pdf/${type}?id=${encodeURIComponent(id)}`;

    const isElectronRuntime = /Electron/i.test(navigator.userAgent || '');

    // In Electron evitiamo window.open perché spesso viene bloccato o non apre la finestra.
    // Apriamo il PDF/HTML nella stessa finestra.
    if (isElectronRuntime) {
      window.location.href = url;
      return;
    }

    // Browser normale: nuova scheda, con fallback sulla stessa finestra.
    const opened = window.open(url, '_blank', 'noopener,noreferrer');
    if (!opened) {
      window.location.href = url;
    }
  }

'''

def find_function_bounds(s: str, name: str):
    start = s.find(f"async function {name}")
    if start == -1:
        raise RuntimeError(f"Funzione {name} non trovata")

    brace = s.find("{", start)
    if brace == -1:
        raise RuntimeError(f"Graffa apertura funzione {name} non trovata")

    depth = 0
    i = brace

    while i < len(s):
        ch = s[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1

    raise RuntimeError(f"Graffa chiusura funzione {name} non trovata")

def main():
    s = FRONTEND.read_text(encoding="utf-8")
    start, end = find_function_bounds(s, "openQuotePdf")
    s = s[:start] + NEW_FUNC + s[end:]
    FRONTEND.write_text(s, encoding="utf-8")
    print("openQuotePdf riparata: build JSX valida e PDF Electron in stessa finestra.")

if __name__ == "__main__":
    main()
