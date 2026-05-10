from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    start = s.find("function Quote(")
    end = s.find("\nfunction Sales", start)

    if start == -1 or end == -1:
        raise RuntimeError("Funzione Quote non trovata")

    block = s[start:end]

    # Sostituisce classi dei pulsanti workflow se già presenti.
    block = block.replace('className="workflow-action production"', 'className="quote-action quote-action-production"')
    block = block.replace('className="workflow-action product"', 'className="quote-action quote-action-product"')
    block = block.replace('className="workflow-action sale"', 'className="quote-action quote-action-sale"')
    block = block.replace('className="workflow-action delivered"', 'className="quote-action quote-action-delivered"')

    # Colora meglio PDF e stati se i pulsanti sono ancora ghost.
    block = block.replace(
        '<button className="ghost" onClick={() => openQuotePdf(r, \'customer\')}>PDF cliente</button>',
        '<button className="quote-action quote-action-pdf" onClick={() => openQuotePdf(r, \'customer\')}>PDF cliente</button>'
    )
    block = block.replace(
        '<button className="ghost" onClick={() => openQuotePdf(r, \'internal\')}>PDF interno</button>',
        '<button className="quote-action quote-action-pdf-internal" onClick={() => openQuotePdf(r, \'internal\')}>PDF interno</button>'
    )

    block = block.replace(
        '<button onClick={()=>changeQuoteStatus(r.id, \'sent\')}>Inviato</button>',
        '<button className="quote-action quote-action-sent" onClick={()=>changeQuoteStatus(r.id, \'sent\')}>Inviato</button>'
    )
    block = block.replace(
        '<button onClick={()=>changeQuoteStatus(r.id, \'accepted\')}>Accettato</button>',
        '<button className="quote-action quote-action-accepted" onClick={()=>changeQuoteStatus(r.id, \'accepted\')}>Accettato</button>'
    )
    block = block.replace(
        '<button onClick={()=>changeQuoteStatus(r.id, \'rejected\')}>Rifiutato</button>',
        '<button className="quote-action quote-action-rejected" onClick={()=>changeQuoteStatus(r.id, \'rejected\')}>Rifiutato</button>'
    )

    # Supporta anche stati nuovi in italiano se presenti.
    block = block.replace(
        '<button className="ghost" onClick={() => changeQuoteStatus(q.id, \'inviato\')}>Inviato</button>',
        '<button className="quote-action quote-action-sent" onClick={() => changeQuoteStatus(q.id, \'inviato\')}>Inviato</button>'
    )
    block = block.replace(
        '<button className="ghost" onClick={() => changeQuoteStatus(q.id, \'accettato\')}>Accettato</button>',
        '<button className="quote-action quote-action-accepted" onClick={() => changeQuoteStatus(q.id, \'accettato\')}>Accettato</button>'
    )
    block = block.replace(
        '<button className="ghost" onClick={() => changeQuoteStatus(q.id, \'rifiutato\')}>Rifiutato</button>',
        '<button className="quote-action quote-action-rejected" onClick={() => changeQuoteStatus(q.id, \'rifiutato\')}>Rifiutato</button>'
    )

    # Se la lista usa ancora r invece di q per stati nuovi.
    block = block.replace(
        '<button className="ghost" onClick={() => changeQuoteStatus(r.id, \'inviato\')}>Inviato</button>',
        '<button className="quote-action quote-action-sent" onClick={() => changeQuoteStatus(r.id, \'inviato\')}>Inviato</button>'
    )
    block = block.replace(
        '<button className="ghost" onClick={() => changeQuoteStatus(r.id, \'accettato\')}>Accettato</button>',
        '<button className="quote-action quote-action-accepted" onClick={() => changeQuoteStatus(r.id, \'accettato\')}>Accettato</button>'
    )
    block = block.replace(
        '<button className="ghost" onClick={() => changeQuoteStatus(r.id, \'rifiutato\')}>Rifiutato</button>',
        '<button className="quote-action quote-action-rejected" onClick={() => changeQuoteStatus(r.id, \'rifiutato\')}>Rifiutato</button>'
    )

    # Se esiste un bottone crea prodotto vecchio.
    block = block.replace(
        '<button onClick={()=>createProductFromQuote(r)}>Crea prodotto</button>',
        '<button className="quote-action quote-action-product" onClick={()=>createProductFromQuote(r)}>Crea prodotto</button>'
    )

    s = s[:start] + block + s[end:]
    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend archivio preventivi ripulito.")


def patch_css():
    css = CSS.read_text(encoding="utf-8")

    if "/* v40.8.2 quote actions polish */" not in css:
        css += r'''

/* v40.8.2 quote actions polish */

/* Archivio preventivi: più ordine e lettura immediata */
.quote-workflow-actions {
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 7px !important;
  align-items: center !important;
  justify-content: flex-start !important;
  max-width: 560px;
}

.quote-workflow-actions select {
  min-width: 136px;
  background: rgba(15, 23, 42, .82);
  border-color: rgba(148, 163, 184, .22);
}

/* Bottone base archivio preventivi */
.quote-action,
.workflow-action {
  border: 1px solid rgba(148, 163, 184, .18);
  border-radius: 999px;
  min-height: 34px;
  height: 34px;
  padding: 7px 11px;
  font-weight: 900;
  font-size: 12px;
  line-height: 1;
  color: var(--text);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.05);
}

.quote-action:hover,
.workflow-action:hover {
  filter: brightness(1.12);
  transform: translateY(-1px);
}

/* Documenti */
.quote-action-pdf {
  background: rgba(59, 130, 246, .14);
  border-color: rgba(59, 130, 246, .36);
  color: #bfdbfe;
}

.quote-action-pdf-internal {
  background: rgba(99, 102, 241, .13);
  border-color: rgba(99, 102, 241, .34);
  color: #c7d2fe;
}

/* Stati commerciali */
.quote-action-sent {
  background: rgba(14, 165, 233, .13);
  border-color: rgba(14, 165, 233, .34);
  color: #bae6fd;
}

.quote-action-accepted {
  background: rgba(34, 197, 94, .15);
  border-color: rgba(34, 197, 94, .38);
  color: #bbf7d0;
}

.quote-action-rejected {
  background: rgba(244, 63, 94, .14);
  border-color: rgba(244, 63, 94, .36);
  color: #fecdd3;
}

/* Operativi */
.quote-action-production,
.workflow-action.production {
  background: rgba(34, 211, 238, .15);
  border-color: rgba(34, 211, 238, .40);
  color: #a5f3fc;
}

.quote-action-product,
.workflow-action.product {
  background: rgba(168, 85, 247, .15);
  border-color: rgba(168, 85, 247, .38);
  color: #e9d5ff;
}

.quote-action-sale,
.workflow-action.sale {
  background: rgba(20, 184, 166, .16);
  border-color: rgba(20, 184, 166, .38);
  color: #99f6e4;
}

.quote-action-delivered,
.workflow-action.delivered {
  background: rgba(16, 185, 129, .16);
  border-color: rgba(16, 185, 129, .38);
  color: #a7f3d0;
}

/* La tabella preventivi deve respirare */
.quote-workflow-row {
  grid-template-columns: 110px minmax(130px, 1fr) minmax(70px, .7fr) 82px 86px minmax(430px, auto) !important;
  align-items: center !important;
}

.quote-workflow-row td,
.quote-workflow-row th {
  vertical-align: middle !important;
}

/* Badge stato più leggibile */
.quote-status-pill,
.quote-status {
  min-width: 62px;
  justify-content: center;
  text-align: center;
  line-height: 1.15;
}

/* Nelle tabelle standard, la colonna azioni non deve esplodere */
.table-wrap td:last-child {
  min-width: 360px;
}

@media (max-width: 1300px) {
  .quote-workflow-row {
    grid-template-columns: 1fr !important;
  }

  .quote-workflow-actions {
    max-width: none;
  }

  .table-wrap td:last-child {
    min-width: 300px;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")
        print("CSS archivio preventivi ripulito.")
    else:
        print("CSS v40.8.2 già presente.")


def main():
    patch_frontend()
    patch_css()
    print("Patch v40.8.2 completata: azioni preventivi più pulite e colorate.")


if __name__ == "__main__":
    main()
