from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


FUNCTIONS = r'''
  async function startQuoteProduction(q) {
    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/start-production`, {});
      toast('Preventivo avviato in produzione');
      workflowRefresh?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function markQuoteDelivered(q) {
    if (!confirm('Segnare questo preventivo come consegnato?')) return;

    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/mark-delivered`, {});
      toast('Preventivo segnato come consegnato');
      workflowRefresh?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function registerQuoteSale(q) {
    const name = prompt('Nome vendita', q.name || 'Vendita da preventivo') || q.name || 'Vendita da preventivo';

    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/register-sale`, {
        name,
        customer: q.customer || '',
        qty: 1,
        unit_price: q.total || q.recommended || q.discounted || 0
      });

      toast('Vendita registrata da preventivo');
      workflowRefresh?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function createProductFromQuote(q) {
    const name = prompt('Nome prodotto da creare', q.name || 'Prodotto da preventivo');

    if (!name) return;

    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/to-product`, {
        name,
        stock: 0
      });

      toast('Prodotto creato da preventivo');
      workflowRefresh?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

'''


ACTIONS = r'''
          {(r.status === 'accettato' || r.status === 'in_produzione' || q?.status === 'accettato' || q?.status === 'in_produzione') && <button className="workflow-action production" onClick={() => startQuoteProduction(r || q)}>Produzione</button>}
          {(r.status === 'accettato' || q?.status === 'accettato') && <button className="workflow-action product" onClick={() => createProductFromQuote(r || q)}>Crea prodotto</button>}
          {(r.status === 'accettato' || r.status === 'in_produzione' || q?.status === 'accettato' || q?.status === 'in_produzione') && <button className="workflow-action sale" onClick={() => registerQuoteSale(r || q)}>Registra vendita</button>}
          {(r.status === 'in_produzione' || q?.status === 'in_produzione') && <button className="workflow-action delivered" onClick={() => markQuoteDelivered(r || q)}>Consegnato</button>}
'''


def main():
    s = FRONTEND.read_text(encoding="utf-8")

    start = s.find("function Quote(")
    end = s.find("\nfunction Sales", start)

    if start == -1 or end == -1:
        raise RuntimeError("Funzione Quote non trovata")

    block = s[start:end]

    # 1. Inserisce funzioni dentro Quote, se non presenti.
    if "async function startQuoteProduction" not in block:
        point = block.find("  async function openQuotePdf")
        if point == -1:
            point = block.find("  async function changeQuoteStatus")
        if point == -1:
            point = block.find("  async function calc")
        if point == -1:
            raise RuntimeError("Punto inserimento funzioni non trovato dentro Quote")

        block = block[:point] + FUNCTIONS + block[point:]

    # 2. Inserisce pulsanti workflow prima del PDF cliente, adattandosi alla variabile usata: r.
    if "workflow-action production" not in block:
        marker = '<button className="ghost" onClick={() => openQuotePdf(r, \'customer\')}>PDF cliente</button>'
        if marker not in block:
            marker = '<button className="ghost" onClick={() => openQuotePdf(q, \'customer\')}>PDF cliente</button>'

        if marker not in block:
            raise RuntimeError("Pulsante PDF cliente non trovato: serve vedere il blocco archivio preventivi")

        varname = "r" if "openQuotePdf(r," in marker else "q"

        actions = f'''
          {{({varname}.status === 'accettato' || {varname}.status === 'in_produzione') && <button className="workflow-action production" onClick={{() => startQuoteProduction({varname})}}>Produzione</button>}}
          {{{varname}.status === 'accettato' && <button className="workflow-action product" onClick={{() => createProductFromQuote({varname})}}>Crea prodotto</button>}}
          {{({varname}.status === 'accettato' || {varname}.status === 'in_produzione') && <button className="workflow-action sale" onClick={{() => registerQuoteSale({varname})}}>Registra vendita</button>}}
          {{{varname}.status === 'in_produzione' && <button className="workflow-action delivered" onClick={{() => markQuoteDelivered({varname})}}>Consegnato</button>}}
'''

        block = block.replace(marker, actions + "          " + marker, 1)

    s = s[:start] + block + s[end:]
    FRONTEND.write_text(s, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    if "/* v40.8 quote operational workflow */" not in css:
        css += r'''

/* v40.8 quote operational workflow */
.workflow-action {
  border: 1px solid rgba(148, 163, 184, .16);
  border-radius: 999px;
  min-height: 36px;
  padding: 7px 11px;
  font-weight: 900;
  font-size: 12px;
  color: var(--text);
  cursor: pointer;
}

.workflow-action.production {
  background: rgba(34, 211, 238, .14);
  border-color: rgba(34, 211, 238, .34);
  color: #a5f3fc;
}

.workflow-action.product {
  background: rgba(168, 85, 247, .14);
  border-color: rgba(168, 85, 247, .34);
  color: #e9d5ff;
}

.workflow-action.sale {
  background: rgba(34, 197, 94, .14);
  border-color: rgba(34, 197, 94, .34);
  color: #bbf7d0;
}

.workflow-action.delivered {
  background: rgba(16, 185, 129, .16);
  border-color: rgba(16, 185, 129, .34);
  color: #a7f3d0;
}

.workflow-action:hover {
  filter: brightness(1.12);
}
'''
        CSS.write_text(css, encoding="utf-8")

    print("Patch frontend v40.8.0b applicata.")


if __name__ == "__main__":
    main()
