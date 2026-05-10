from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN_API = ROOT / "backend" / "app" / "main.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


BACKEND_CODE = r'''

# ---------------------------------------------------------------------------
# v40.8.0 - Preventivo accettato → workflow prodotto/vendita
# ---------------------------------------------------------------------------

def quote_register_sale(db, quote_id, payload=None):
    payload = payload or {}
    quote = get_quote_flexible(db, quote_id)

    name = payload.get("name") or quote.get("name") or "Vendita da preventivo"
    customer = payload.get("customer") or quote.get("customer") or ""
    qty = parse_float(payload.get("qty", 1)) or 1

    unit_price = (
        parse_float(payload.get("unit_price"))
        or parse_float(quote.get("discounted"))
        or parse_float(quote.get("recommended"))
        or parse_float(quote.get("total"))
        or parse_float(quote.get("unit_price"))
    )

    rows = quote.get("rows", []) or []
    estimated_materials = quote.get("estimated_materials", []) or []

    sale_payload = {
        "name": name,
        "customer": customer,
        "qty": qty,
        "unit_price": unit_price,
        "rows": rows,
        "estimated_materials": estimated_materials,
        "hours": quote.get("hours", 0),
        "rate": quote.get("rate", 0),
        "packaging": quote.get("packaging", 0),
        "energy": quote.get("energy", 0),
        "wear": quote.get("wear", 0),
        "commission": quote.get("commission", 0),
        "margin": quote.get("margin", 0),
        "discount": quote.get("discount", 0),
        "source": "preventivo",
        "quote_id": quote.get("id", quote_id),
    }

    result = record_quote_sale(db, sale_payload)

    quote["status"] = "consegnato"
    quote["status_updated_at"] = now_str()
    quote.setdefault("history", []).append({
        "date": now_str(),
        "event": "Vendita registrata da preventivo",
        "status": "consegnato",
    })

    return {
        "ok": True,
        "sale": result,
        "quote_status": quote["status"],
    }


def quote_start_production(db, quote_id):
    quote = get_quote_flexible(db, quote_id)

    quote["status"] = "in_produzione"
    quote["status_updated_at"] = now_str()
    quote.setdefault("history", []).append({
        "date": now_str(),
        "event": "Preventivo avviato in produzione",
        "status": "in_produzione",
    })

    return {
        "ok": True,
        "id": quote.get("id", quote_id),
        "status": "in_produzione",
    }


def quote_mark_delivered(db, quote_id):
    quote = get_quote_flexible(db, quote_id)

    quote["status"] = "consegnato"
    quote["status_updated_at"] = now_str()
    quote.setdefault("history", []).append({
        "date": now_str(),
        "event": "Preventivo segnato come consegnato",
        "status": "consegnato",
    })

    return {
        "ok": True,
        "id": quote.get("id", quote_id),
        "status": "consegnato",
    }
'''


API_CODE = r'''

@app.post("/api/quotes/{quote_id:path}/start-production")
def quote_start_production_api(quote_id: str):
    def fn(db):
        return quote_start_production(db, quote_id)
    return mutate(fn)


@app.post("/api/quotes/{quote_id:path}/register-sale")
def quote_register_sale_api(quote_id: str, payload: Payload):
    def fn(db):
        return quote_register_sale(db, quote_id, payload.data)
    return mutate(fn)


@app.post("/api/quotes/{quote_id:path}/mark-delivered")
def quote_mark_delivered_api(quote_id: str):
    def fn(db):
        return quote_mark_delivered(db, quote_id)
    return mutate(fn)
'''


def append_once(path: Path, marker: str, code: str):
    s = path.read_text(encoding="utf-8")
    if marker not in s:
        s += "\n\n" + code.strip() + "\n"
        path.write_text(s, encoding="utf-8")


def patch_backend():
    append_once(LEGACY, "def quote_register_sale", BACKEND_CODE)
    append_once(MAIN_API, "def quote_start_production_api", API_CODE)
    print("Backend workflow preventivo → produzione/vendita applicato.")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    start = s.find("function Quote(")
    end = s.find("\nfunction Sales", start)

    if start == -1 or end == -1:
        raise RuntimeError("Funzione Quote non trovata")

    block = s[start:end]

    if "async function startQuoteProduction" not in block:
        insert = r'''
  async function startQuoteProduction(q) {
    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/start-production`, {});
      toast('Preventivo avviato in produzione');
      workflowRefresh();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function markQuoteDelivered(q) {
    if (!confirm('Segnare questo preventivo come consegnato?')) return;

    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/mark-delivered`, {});
      toast('Preventivo segnato come consegnato');
      workflowRefresh();
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
        unit_price: q.total || 0
      });

      toast('Vendita registrata da preventivo');
      workflowRefresh();
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
      workflowRefresh();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

'''
        point = block.find("  async function changeQuoteStatus")
        if point == -1:
            raise RuntimeError("Punto inserimento funzioni workflow preventivo non trovato")
        block = block[:point] + insert + block[point:]

    old_actions = r'''          <div className="quote-workflow-actions">
            <select value={q.status || 'bozza'} onChange={e => changeQuoteStatus(q.id, e.target.value)}>
              {quoteStatusFlow.map(st => <option key={st} value={st}>{quoteStatusLabels[st]}</option>)}
            </select>
            <button className="ghost" onClick={() => duplicateQuote(q.id, q.name)}>Duplica</button>
            <button className="ghost" onClick={() => openQuotePdf(q, 'customer')}>PDF cliente</button>
            <button className="ghost" onClick={() => openQuotePdf(q, 'internal')}>PDF interno</button>
          </div>'''

    new_actions = r'''          <div className="quote-workflow-actions">
            <select value={q.status || 'bozza'} onChange={e => changeQuoteStatus(q.id, e.target.value)}>
              {quoteStatusFlow.map(st => <option key={st} value={st}>{quoteStatusLabels[st]}</option>)}
            </select>

            {(q.status === 'accettato' || q.status === 'in_produzione') && <button className="workflow-action production" onClick={() => startQuoteProduction(q)}>Produzione</button>}
            {q.status === 'accettato' && <button className="workflow-action product" onClick={() => createProductFromQuote(q)}>Crea prodotto</button>}
            {(q.status === 'accettato' || q.status === 'in_produzione') && <button className="workflow-action sale" onClick={() => registerQuoteSale(q)}>Registra vendita</button>}
            {q.status === 'in_produzione' && <button className="workflow-action delivered" onClick={() => markQuoteDelivered(q)}>Consegnato</button>}

            <button className="ghost" onClick={() => duplicateQuote(q.id, q.name)}>Duplica</button>
            <button className="ghost" onClick={() => openQuotePdf(q, 'customer')}>PDF cliente</button>
            <button className="ghost" onClick={() => openQuotePdf(q, 'internal')}>PDF interno</button>
          </div>'''

    if old_actions in block and "workflow-action production" not in block:
        block = block.replace(old_actions, new_actions, 1)
    elif "workflow-action production" not in block:
        raise RuntimeError("Blocco azioni archivio preventivi non trovato")

    s = s[:start] + block + s[end:]
    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend workflow preventivo → produzione/vendita applicato.")


def patch_css():
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


def main():
    patch_backend()
    patch_frontend()
    patch_css()
    print("Patch v40.8.0 completata: preventivo accettato collegato a produzione/vendita.")


if __name__ == "__main__":
    main()
