from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN_API = ROOT / "backend" / "app" / "main.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


BACKEND_CODE = r'''

# ---------------------------------------------------------------------------
# v40.6.0 - Workflow preventivi avanzato
# ---------------------------------------------------------------------------

QUOTE_STATUSES = [
    "bozza",
    "inviato",
    "da_modificare",
    "accettato",
    "in_produzione",
    "consegnato",
    "rifiutato",
    "scaduto",
]


def normalize_quote_status(status):
    status = str(status or "bozza").strip().lower().replace(" ", "_")
    aliases = {
        "draft": "bozza",
        "sent": "inviato",
        "accepted": "accettato",
        "rejected": "rifiutato",
        "production": "in_produzione",
        "delivered": "consegnato",
    }
    status = aliases.get(status, status)
    return status if status in QUOTE_STATUSES else "bozza"


def quote_workflow_summary(db):
    quotes = db.get("quotes", []) or []
    counts = {s: 0 for s in QUOTE_STATUSES}

    rows = []
    for q in quotes:
        if not isinstance(q, dict):
            continue

        status = normalize_quote_status(q.get("status"))
        q["status"] = status
        counts[status] = counts.get(status, 0) + 1

        rows.append({
            "id": q.get("id", ""),
            "name": q.get("name", ""),
            "customer": q.get("customer", ""),
            "status": status,
            "date": q.get("date", ""),
            "total": q.get("discounted") or q.get("recommended") or q.get("total") or q.get("unit_price") or 0,
            "margin": q.get("margin_total", 0),
        })

    return {
        "statuses": QUOTE_STATUSES,
        "counts": counts,
        "quotes": rows,
    }


def update_quote_status(db, quote_id, status):
    status = normalize_quote_status(status)
    quote = get_quote_flexible(db, quote_id)

    quote["status"] = status
    quote["status_updated_at"] = now_str()

    quote.setdefault("history", []).append({
        "date": now_str(),
        "event": "Cambio stato",
        "status": status,
    })

    return {
        "ok": True,
        "id": quote.get("id", quote_id),
        "status": status,
    }


def duplicate_quote(db, quote_id, name=""):
    quote = get_quote_flexible(db, quote_id)
    quotes = db.setdefault("quotes", [])

    new_quote = copy.deepcopy(quote)
    new_id = f"Q{datetime.now().strftime('%Y%m%d%H%M%S')}"
    new_quote["id"] = new_id
    new_quote["name"] = (name or f"{quote.get('name', 'Preventivo')} - copia").strip()
    new_quote["status"] = "bozza"
    new_quote["date"] = today_str()
    new_quote["created_at"] = now_str()
    new_quote["status_updated_at"] = now_str()
    new_quote["history"] = [{
        "date": now_str(),
        "event": "Duplicato da preventivo",
        "source_id": quote.get("id", quote_id),
        "status": "bozza",
    }]

    quotes.append(new_quote)

    return {
        "ok": True,
        "quote": new_quote,
    }
'''


API_CODE = r'''

@app.get("/api/quotes/workflow")
def quote_workflow_api():
    return quote_workflow_summary(load_db())


@app.post("/api/quotes/{quote_id:path}/status")
def quote_status_api(quote_id: str, payload: Payload):
    def fn(db):
        return update_quote_status(db, quote_id, payload.data.get("status"))
    return mutate(fn)


@app.post("/api/quotes/{quote_id:path}/duplicate")
def quote_duplicate_api(quote_id: str, payload: Payload):
    def fn(db):
        return duplicate_quote(db, quote_id, payload.data.get("name", ""))
    return mutate(fn)
'''


def append_once(path: Path, marker: str, code: str):
    s = path.read_text(encoding="utf-8")
    if marker not in s:
        s += "\n\n" + code.strip() + "\n"
        path.write_text(s, encoding="utf-8")


def patch_backend():
    append_once(LEGACY, "def quote_workflow_summary", BACKEND_CODE)
    append_once(MAIN_API, "def quote_workflow_api", API_CODE)
    print("Backend workflow preventivi avanzato applicato.")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    if "const quoteStatusLabels" not in s:
        marker = "const money = n =>"
        helper = r'''const quoteStatusLabels = {
  bozza: 'Bozza',
  inviato: 'Inviato',
  da_modificare: 'Da modificare',
  accettato: 'Accettato',
  in_produzione: 'In produzione',
  consegnato: 'Consegnato',
  rifiutato: 'Rifiutato',
  scaduto: 'Scaduto',
};

const quoteStatusFlow = ['bozza', 'inviato', 'da_modificare', 'accettato', 'in_produzione', 'consegnato', 'rifiutato', 'scaduto'];

'''
        if marker not in s:
            raise RuntimeError("Punto inserimento helper quote status non trovato")
        s = s.replace(marker, helper + marker, 1)

    start = s.find("function Quote(")
    end = s.find("\nfunction Sales", start)

    if start == -1 or end == -1:
        raise RuntimeError("Funzione Quote non trovata")

    quote_block = s[start:end]

    if "workflowRefresh" not in quote_block:
        quote_block = quote_block.replace(
            "const { data: sug } = useApi('/suggestions', {});",
            "const { data: sug } = useApi('/suggestions', {});\n  const { data: workflow, refresh: workflowRefresh } = useApi('/quotes/workflow', { statuses: quoteStatusFlow, counts: {}, quotes: [] });"
        )

    if "async function changeQuoteStatus" not in quote_block:
        insert = r'''
  async function changeQuoteStatus(id, status) {
    try {
      await postJSON(`/quotes/${encodeURIComponent(id)}/status`, { status });
      toast(`Stato aggiornato: ${quoteStatusLabels[status] || status}`);
      workflowRefresh();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function duplicateQuote(id, currentName) {
    const name = prompt('Nome nuovo preventivo', `${currentName || 'Preventivo'} - copia`);
    if (!name) return;

    try {
      await postJSON(`/quotes/${encodeURIComponent(id)}/duplicate`, { name });
      toast('Preventivo duplicato');
      workflowRefresh();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

'''
        point = quote_block.find("  async function calc()")
        if point == -1:
            raise RuntimeError("Punto inserimento funzioni workflow preventivo non trovato")
        quote_block = quote_block[:point] + insert + quote_block[point:]

    if "Archivio preventivi" not in quote_block:
        marker = """    <div className="split-main">"""
        workflow_ui = r'''
    <Card title="Archivio preventivi" icon={FileJson}>
      <div className="quote-workflow-stats">
        {quoteStatusFlow.map(st => <button key={st} className={`quote-status-filter ${st}`}>
          <span>{quoteStatusLabels[st]}</span>
          <b>{workflow.counts?.[st] || 0}</b>
        </button>)}
      </div>

      <div className="quote-workflow-list">
        {list(workflow.quotes).length ? list(workflow.quotes).slice(0, 20).map(q => <div key={q.id} className="quote-workflow-row">
          <div>
            <b>{q.name || q.id}</b>
            <small>{[q.customer, q.date].filter(Boolean).join(' · ') || 'Preventivo'}</small>
          </div>

          <span className={`quote-status-pill ${q.status}`}>{quoteStatusLabels[q.status] || q.status}</span>

          <strong>{money(q.total)}</strong>

          <div className="quote-workflow-actions">
            <select value={q.status || 'bozza'} onChange={e => changeQuoteStatus(q.id, e.target.value)}>
              {quoteStatusFlow.map(st => <option key={st} value={st}>{quoteStatusLabels[st]}</option>)}
            </select>
            <button className="ghost" onClick={() => duplicateQuote(q.id, q.name)}>Duplica</button>
            <button className="ghost" onClick={() => openQuotePdf(q, 'customer')}>PDF cliente</button>
            <button className="ghost" onClick={() => openQuotePdf(q, 'internal')}>PDF interno</button>
          </div>
        </div>) : <Empty text="Nessun preventivo archiviato" />}
      </div>
    </Card>

'''
        if marker not in quote_block:
            raise RuntimeError("Punto inserimento archivio preventivi non trovato")
        quote_block = quote_block.replace(marker, workflow_ui + marker, 1)

    s = s[:start] + quote_block + s[end:]
    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend workflow preventivi applicato.")


def patch_css():
    css = CSS.read_text(encoding="utf-8")

    if "/* v40.6 quote workflow */" not in css:
        css += r'''

/* v40.6 quote workflow */
.quote-workflow-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.quote-status-filter {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  color: var(--text);
  border-radius: 16px;
  padding: 11px 12px;
  display: grid;
  gap: 5px;
  text-align: left;
}

.quote-status-filter span {
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .06em;
}

.quote-status-filter b {
  font-size: 22px;
  line-height: 1;
}

.quote-workflow-list {
  display: grid;
  gap: 10px;
  max-height: 520px;
  overflow-y: auto;
  padding-right: 4px;
}

.quote-workflow-row {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  border-radius: 18px;
  padding: 12px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto minmax(320px, auto);
  gap: 12px;
  align-items: center;
}

.quote-workflow-row b,
.quote-workflow-row small {
  display: block;
  min-width: 0;
}

.quote-workflow-row b {
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quote-workflow-row small {
  color: var(--muted);
  margin-top: 3px;
}

.quote-status-pill {
  border-radius: 999px;
  padding: 7px 10px;
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
  background: rgba(148, 163, 184, .12);
  color: var(--muted);
}

.quote-status-pill.bozza { background: rgba(148, 163, 184, .14); color: #cbd5e1; }
.quote-status-pill.inviato { background: rgba(59, 130, 246, .16); color: #bfdbfe; }
.quote-status-pill.da_modificare { background: rgba(245, 158, 11, .16); color: #fde68a; }
.quote-status-pill.accettato { background: rgba(34, 197, 94, .16); color: #bbf7d0; }
.quote-status-pill.in_produzione { background: rgba(34, 211, 238, .16); color: #a5f3fc; }
.quote-status-pill.consegnato { background: rgba(16, 185, 129, .18); color: #a7f3d0; }
.quote-status-pill.rifiutato { background: rgba(239, 68, 68, .16); color: #fecaca; }
.quote-status-pill.scaduto { background: rgba(100, 116, 139, .22); color: #cbd5e1; }

.quote-workflow-actions {
  display: flex;
  gap: 7px;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.quote-workflow-actions select {
  width: 145px;
  min-height: 36px !important;
  height: 36px !important;
}

.quote-workflow-actions button {
  min-height: 36px;
  padding: 7px 10px;
}

@media (max-width: 1200px) {
  .quote-workflow-row {
    grid-template-columns: 1fr;
    align-items: start;
  }

  .quote-workflow-actions {
    justify-content: flex-start;
  }

  .quote-workflow-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .quote-workflow-stats {
    grid-template-columns: 1fr;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")


def main():
    patch_backend()
    patch_frontend()
    patch_css()
    print("Patch v40.6.0 workflow preventivi completata.")


if __name__ == "__main__":
    main()
