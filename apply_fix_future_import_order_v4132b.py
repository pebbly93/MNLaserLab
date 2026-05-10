from pathlib import Path

MAIN = Path("backend/app/main.py")

def main():
    s = MAIN.read_text(encoding="utf-8")
    lines = s.splitlines()

    # Rimuove eventuali duplicati di from pathlib import Path
    lines = [line for line in lines if line.strip() != "from pathlib import Path"]

    # Trova posizione corretta: subito dopo eventuali __future__ import
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("from __future__ import"):
            insert_at = i + 1

    # Inserisce Path dopo __future__, oppure in cima se non ci sono future imports
    lines.insert(insert_at, "from pathlib import Path")

    MAIN.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Fix applicato: from pathlib import Path spostato dopo from __future__ import.")

if __name__ == "__main__":
    main()
