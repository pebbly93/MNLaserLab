from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


def main():
    s = MAIN.read_text(encoding="utf-8")

    # 1. Rimuove testi descrittivi troppo lunghi dalle card principali.
    replacements = {
        'sub="Compila da sinistra a destra: i suggerimenti cambiano in base a sezione e categoria."': '',
        'sub="Gestisci materie prime e componenti acquistati: fornitore, categoria, sottocategoria, formato, costo e stock."': 'desc="Gestisci materie prime e componenti acquistati."',
        'hint="Se scegli un fornitore già collegato, categorie e sottocategorie vengono filtrate su quel fornitore"': '',
        "hint={f.section ? `Categorie disponibili per ${f.section}` : 'Scegli prima l’area'}": '',
        "hint={f.category ? `Sottocategorie di ${f.category}` : 'Scegli prima una categoria'}": '',
        "hint=\"Esempio: Legname, Acrilico, LED, Vernici\"": '',
        "hint=\"Esempio: Betulla, Pioppo, Strisce LED\"": '',
    }

    for old, new in replacements.items():
        s = s.replace(old, new)

    # 2. Rimuove frasi ridondanti nel preview nome articolo.
    s = s.replace(
        "<small>{f.supplier ? `collegato a ${f.supplier}` : 'aggiungi fornitore per tracciabilità'}</small>",
        "<small>{f.supplier || '—'}</small>"
    )

    # 3. Accorcia placeholder troppo lunghi.
    s = s.replace(
        'placeholder="Legname, Acrilico, LED..."',
        'placeholder="Legname, Acrilico..."'
    )
    s = s.replace(
        'placeholder="Betulla, Pioppo, Strisce LED..."',
        'placeholder="Betulla, Pioppo..."'
    )

    MAIN.write_text(s, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")

    if "/* v40.1.3 compact forms polish */" not in css:
        css += r'''

/* v40.1.3 compact forms polish */

/* Titoli card più puliti: meno testo inutile */
.card header p:empty {
  display: none;
}

.card header {
  padding-bottom: 10px;
}

.card header h2 {
  margin-bottom: 0;
}

/* Card acquisto più compatta e allineata */
.buy-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px 12px;
  align-items: start;
}

.buy-grid .field {
  margin: 0;
}

.buy-grid label,
.field label {
  display: block;
  margin-bottom: 6px;
  font-size: 11px;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: rgba(226, 232, 240, .9);
}

.buy-grid input,
.buy-grid select {
  min-height: 42px;
}

/* I testi hint sotto gli input devono sparire/quasi sparire */
.field > small:not(.keep-hint),
.field .hint {
  display: none !important;
}

/* Suggerimenti: massimo compatti, non devono rompere la griglia */
.compact-suggestions,
.suggestions {
  margin-top: 6px !important;
  gap: 5px !important;
  max-height: 34px;
  overflow: hidden;
}

.compact-suggestions button,
.suggestions button {
  min-height: 24px !important;
  max-height: 24px;
  padding: 5px 8px !important;
  font-size: 10px !important;
  max-width: 110px !important;
  border-radius: 999px !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.compact-suggestions small,
.suggestions small {
  display: none !important;
}

/* Nome articolo più elegante e allineato agli input */
.name-preview {
  min-height: 92px;
  align-self: end;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 14px;
  border-radius: 18px;
}

.name-preview span {
  font-size: 10px;
  letter-spacing: .09em;
  text-transform: uppercase;
  color: var(--muted);
}

.name-preview b {
  margin-top: 4px;
  font-size: 16px;
  line-height: 1.15;
}

.name-preview small {
  margin-top: 6px;
  color: var(--muted);
  font-size: 11px;
}

/* Ordine visivo più naturale su desktop */
.buy-grid > .field:nth-child(1) { grid-column: 1; grid-row: 1; } /* Area */
.buy-grid > .field:nth-child(2) { grid-column: 2; grid-row: 1; } /* Fornitore */
.buy-grid > .field:nth-child(3) { grid-column: 3; grid-row: 1; } /* Categoria */
.buy-grid > .field:nth-child(4) { grid-column: 4; grid-row: 1; } /* Sottocategoria */

.buy-grid > .field:nth-child(5) { grid-column: 1; grid-row: 2; } /* Formato */
.buy-grid > .field:nth-child(6) { grid-column: 2; grid-row: 2; } /* Spessore */
.buy-grid > .field:nth-child(7) { grid-column: 3; grid-row: 2; } /* Unità */
.buy-grid > .field:nth-child(8) { grid-column: 4; grid-row: 2; } /* Quantità */

.buy-grid > .field:nth-child(9) { grid-column: 1; grid-row: 3; } /* Costo */
.buy-grid > .name-preview { grid-column: 2 / 5; grid-row: 3; }

/* Stat sotto acquisto coerenti */
.inventory-quality {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.inventory-quality .stat {
  min-height: 116px;
}

/* Miglioramento generale input in tutta app */
.form-grid {
  gap: 13px;
}

.form-grid input,
.form-grid select,
.form-grid textarea {
  width: 100%;
}

/* Page title più essenziale */
.page-title span {
  max-width: 780px;
  line-height: 1.45;
}

/* Responsive */
@media (max-width: 1250px) {
  .buy-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .buy-grid > .field,
  .buy-grid > .name-preview {
    grid-column: auto !important;
    grid-row: auto !important;
  }

  .buy-grid > .name-preview {
    grid-column: 1 / -1 !important;
  }

  .inventory-quality {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .buy-grid,
  .inventory-quality {
    grid-template-columns: 1fr;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")

    print("Patch v40.1.3 compact forms polish completata.")


if __name__ == "__main__":
    main()
