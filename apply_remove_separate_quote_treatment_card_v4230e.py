from pathlib import Path

MAIN = Path("frontend/src/main.jsx")

def main():
    s = MAIN.read_text(encoding="utf-8")

    start = s.find('<Card title="Trattamenti e finiture preventivo"')
    if start == -1:
        print("Card separata Trattamenti e finiture preventivo non trovata: nulla da rimuovere.")
        return

    end = s.find('<Card title="Costi e margini"', start)
    if end == -1:
        raise RuntimeError('Card "Costi e margini" non trovata dopo la card trattamenti')

    s = s[:start] + s[end:]

    MAIN.write_text(s, encoding="utf-8")
    print("Rimossa la card separata dei trattamenti preventivo. Il pannello resta dentro Costi e margini.")

if __name__ == "__main__":
    main()
