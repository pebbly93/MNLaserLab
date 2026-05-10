from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"Blocco non trovato: {label}")
    return text.replace(old, new, 1)


def main():
    s = MAIN.read_text(encoding="utf-8")

    # ------------------------------------------------------------
    # Studio dashboard alerts
    # ------------------------------------------------------------
    if "const { data: alerts } = useApi('/workflow/alerts', {});" not in s:
        s = replace_once(
            s,
            "  const { data: r } = useApi('/report', {});",
            "  const { data: r } = useApi('/report', {});\n  const { data: alerts } = useApi('/workflow/alerts', {});",
            "Studio alerts hook"
        )

    if "Da controllare oggi" not in s:
        old = """      <Card title="Margine attività" icon={BarChart3} sub="Sintesi economica per capire se ciò che produci conviene davvero.">
        <div className="mini-stats"><Stat label="Raw" value={money(r.raw_total)} /><Stat label="Prodotti" value={money(r.product_total)} /><Stat label="Margine" value={money(r.margin_total)} sub={`${num(r.margin_pct)} %`} /></div>
      </Card>"""
        new = """      <Card title="Margine attività" icon={BarChart3} sub="Sintesi economica per capire se ciò che produci conviene davvero.">
        <div className="mini-stats"><Stat label="Raw" value={money(r.raw_total)} /><Stat label="Prodotti" value={money(r.product_total)} /><Stat label="Margine" value={money(r.margin_total)} sub={`${num(r.margin_pct)} %`} /></div>
      </Card>
      <Card title="Da controllare oggi" icon={AlertTriangle} sub="L'app evidenzia le attività che possono bloccare produzione, preventivi o margini.">
        <div className="workflow-alert-grid">
          <button onClick={() => go('materials')}><b>{alerts.materials_to_check || 0}</b><span>Materiali da verificare</span></button>
          <button onClick={() => go('materials')}><b>{alerts.low_stock_materials || 0}</b><span>Sotto scorta</span></button>
          <button onClick={() => go('quote')}><b>{alerts.open_quotes || 0}</b><span>Preventivi aperti</span></button>
          <button onClick={() => go('quote')}><b>{money(alerts.potential_quotes_value)}</b><span>Valore potenziale</span></button>
        </div>
      </Card>"""
        s = replace_once(s, old, new, "Studio alert card")

    # ------------------------------------------------------------
    # Quote advanced workflow
    # ------------------------------------------------------------
    if "const { data: business } = useApi('/settings/business', {});" not in s:
        old = """function Quote({ toast }) {
  const { data: inv } = useApi('/inventory', []);
  const { data: sug } = useApi('/suggestions', {});
  const [rows, setRows] = useState([]);
  const [item, setItem] = useState('');
  const [qty, setQty] = useState('1');
  const [res, setRes] = useState(null);
  const [materialSearch, setMaterialSearch] = useState('');
  const [filters, setFilters] = useState({ supplier: '', section: '', category: '', subcategory: '' });
  const [cost, setCost] = useState({ hours: '', rate: '', packaging: '', energy: '', wear: '', commission: '', margin: '30', discount: '' });"""
        new = """function Quote({ toast }) {
  const { data: inv } = useApi('/inventory', []);
  const { data: sug } = useApi('/suggestions', {});
  const { data: business } = useApi('/settings/business', {});
  const { data: savedQuotes, refresh: refreshQuotes } = useApi('/quotes', []);
  const [rows, setRows] = useState([]);
  const [item, setItem] = useState('');
  const [qty, setQty] = useState('1');
  const [res, setRes] = useState(null);
  const [quoteName, setQuoteName] = useState('');
  const [quoteCustomer, setQuoteCustomer] = useState('');
  const [quoteNotes, setQuoteNotes] = useState('');
  const [materialSearch, setMaterialSearch] = useState('');
  const [filters, setFilters] = useState({ supplier: '', section: '', category: '', subcategory: '' });
  const [cost, setCost] = useState({ hours: '', rate: '', packaging: '', energy: '', wear: '', commission: '', margin: '30', discount: '' });

  useEffect(() => {
    if (!business || Object.keys(business).length === 0) return;
    setCost(v => ({
      ...v,
      rate: v.rate || business.hourly_rate || '',
      packaging: v.packaging || business.default_packaging || '',
      energy: v.energy || business.default_energy || '',
      wear: v.wear || business.default_wear || '',
      commission: v.commission || business.default_commission || '',
      margin: v.margin || business.default_margin || '30',
      discount: v.discount || business.default_discount || ''
    }));
  }, [business]);"""
        s = replace_once(s, old, new, "Quote start")

    if "async function saveQuote" not in s:
        old = """  async function sale() {
    if (!res) return;
    const name = prompt('Nome vendita', 'Vendita da preventivo') || 'Vendita da preventivo';
    try {
      await postJSON('/quote/sale', { name, qty: 1, unit_price: res.discounted || res.recommended, rows, estimated_materials: [], ...cost });
      toast('Vendita da preventivo registrata');
    } catch (e) {
      toast(e.message, 'err');
    }
  }"""
        new = """  async function sale() {
    if (!res) return;
    const name = prompt('Nome vendita', quoteName || 'Vendita da preventivo') || 'Vendita da preventivo';
    try {
      await postJSON('/quote/sale', { name, customer: quoteCustomer, qty: 1, unit_price: res.discounted || res.recommended, rows, estimated_materials: [], ...cost });
      toast('Vendita da preventivo registrata');
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function saveQuote(status = 'draft') {
    try {
      const payload = {
        name: quoteName || 'Preventivo senza nome',
        customer: quoteCustomer,
        notes: quoteNotes,
        status,
        rows,
        estimates: [],
        estimated_materials: [],
        ...cost
      };
      const saved = await postJSON('/quotes', payload);
      setRes(saved.result || res);
      await refreshQuotes();
      toast(status === 'sent' ? 'Preventivo salvato come inviato' : 'Preventivo salvato');
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function quoteToProduct(q) {
    const name = prompt('Nome prodotto da creare', q.name || 'Prodotto da preventivo');
    if (!name) return;
    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/to-product`, { name });
      await refreshQuotes();
      toast('Prodotto creato dal preventivo');
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function changeQuoteStatus(q, status) {
    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/status`, { status });
      await refreshQuotes();
      toast('Stato preventivo aggiornato');
    } catch (e) {
      toast(e.message, 'err');
    }
  }"""
        s = replace_once(s, old, new, "Quote functions")

    if "Dati preventivo" not in s:
        old = """    <PageTitle title="Preventivi" desc="Costruisci il prezzo partendo dai materiali reali del magazzino, poi aggiungi lavoro, consumi, commissioni e margine." />

    <div className="quote-layout">"""
        new = """    <PageTitle title="Preventivi" desc="Costruisci il prezzo partendo dai materiali reali del magazzino, poi aggiungi lavoro, consumi, commissioni e margine." />

    <Card title="Dati preventivo" icon={FileJson} sub="Salva bozze, invia preventivi e trasformali in prodotti finiti quando diventano ripetibili.">
      <div className="form-grid">
        <Input label="Nome preventivo / prodotto" value={quoteName} onChange={e => setQuoteName(e.target.value)} placeholder="Es. Orologio One Piece 40 cm" />
        <SmartInput label="Cliente" options={sug.customers} value={quoteCustomer} onChange={e => setQuoteCustomer(e.target.value)} placeholder="Cliente o vendita diretta" />
        <Input label="Note" value={quoteNotes} onChange={e => setQuoteNotes(e.target.value)} placeholder="Dettagli lavorazione, personalizzazione, consegna..." />
      </div>
      <div className="quick-actions">
        <button onClick={() => saveQuote('draft')}><Save /> Salva bozza</button>
        <button onClick={() => saveQuote('sent')}><ArrowRight /> Segna inviato</button>
      </div>
    </Card>

    <div className="quote-layout">"""
        s = replace_once(s, old, new, "Quote header card")

    if "Salva preventivo" not in s:
        old = """        {res && <div className="quick-actions"><button onClick={sale}><ShoppingCart /> Registra vendita da preventivo</button></div>}"""
        new = """        {res && <div className="quick-actions"><button onClick={sale}><ShoppingCart /> Registra vendita da preventivo</button><button onClick={() => saveQuote('draft')}><Save /> Salva preventivo</button></div>}"""
        s = replace_once(s, old, new, "Quote result actions")

    if "Archivio preventivi" not in s:
        quote_start = s.find("function Quote")
        sales_start = s.find("\nfunction Sales", quote_start)
        if quote_start == -1 or sales_start == -1:
            raise RuntimeError("Impossibile trovare blocco Quote/Sales")

        quote_block = s[quote_start:sales_start]
        old_end = """      </Card>
    </div>
  </>;
}"""
        new_end = """      </Card>
    </div>

    <Card title="Archivio preventivi" icon={FileJson} sub="Pipeline commerciale: bozze, inviati, accettati e rifiutati.">
      <DataTable rows={list(savedQuotes)} empty="Nessun preventivo salvato" columns={[
        { key: 'date', label: 'Data' },
        { key: 'name', label: 'Preventivo' },
        { key: 'customer', label: 'Cliente', render: r => r.customer || '—' },
        { key: 'status', label: 'Stato', render: r => <span className={`quote-status ${r.status || 'draft'}`}>{r.status_label || r.status || 'bozza'}</span> },
        { key: 'value', label: 'Valore', render: r => money(r.potential_value || r.recommended || r.discounted) },
        { key: 'act', label: 'Azioni', render: r => <div className="table-actions">
          <button className="ghost" onClick={() => changeQuoteStatus(r, 'sent')}>Inviato</button>
          <button className="ghost" onClick={() => changeQuoteStatus(r, 'accepted')}>Accettato</button>
          <button className="ghost" onClick={() => changeQuoteStatus(r, 'rejected')}>Rifiutato</button>
          <button className="ghost" onClick={() => quoteToProduct(r)}>Crea prodotto</button>
        </div> }
      ]} />
    </Card>
  </>;
}"""
        if old_end not in quote_block:
            raise RuntimeError("Fine funzione Quote non trovata")
        quote_block = quote_block.replace(old_end, new_end, 1)
        s = s[:quote_start] + quote_block + s[sales_start:]

    # ------------------------------------------------------------
    # Settings business settings
    # ------------------------------------------------------------
    if "const [biz, setBiz]" not in s:
        old = """function SettingsPage({ toast }) {
  const [info, setInfo] = useState({});
  const [msg, setMsg] = useState('');
  const [importText, setImportText] = useState('');"""
        new = """function SettingsPage({ toast }) {
  const [info, setInfo] = useState({});
  const [msg, setMsg] = useState('');
  const [importText, setImportText] = useState('');
  const [biz, setBiz] = useState({});

  async function loadBusiness() {
    try {
      setBiz(await getJSON('/settings/business'));
    } catch (e) {}
  }"""
        s = replace_once(s, old, new, "Settings start")

        old = """  useEffect(() => { loadInfo(); }, []);"""
        new = """  useEffect(() => { loadInfo(); loadBusiness(); }, []);"""
        s = replace_once(s, old, new, "Settings useEffect")

        old = """  async function importDb() { try { const parsed = JSON.parse(importText); await postJSON('/maintenance/import', { data: parsed }); setImportText(''); toast('Archivio importato'); await loadInfo(); } catch(e) { toast('JSON non valido o import non riuscito: ' + (e.message || e), 'err'); } }
  return <>
    <PageTitle title="Impostazioni" desc="Gestione professionale dell’archivio: backup, export, import, pulizia e reset controllato." />"""
        new = """  async function importDb() { try { const parsed = JSON.parse(importText); await postJSON('/maintenance/import', { data: parsed }); setImportText(''); toast('Archivio importato'); await loadInfo(); } catch(e) { toast('JSON non valido o import non riuscito: ' + (e.message || e), 'err'); } }
  async function saveBusiness() { try { await postJSON('/settings/business', biz); await loadBusiness(); toast('Impostazioni economiche salvate'); } catch(e) { toast(e.message, 'err'); } }
  return <>
    <PageTitle title="Impostazioni" desc="Gestione professionale dell’archivio: backup, export, import, pulizia e reset controllato." />
    <Card title="Impostazioni economiche" icon={Settings2} sub="Valori standard usati nei preventivi: tariffa, margine, commissioni e costi ricorrenti." action={<button className="primary" onClick={saveBusiness}><Save /> Salva impostazioni</button>}>
      <div className="form-grid small-grid">
        <Input label="Tariffa oraria €/h" type="number" step="0.01" value={biz.hourly_rate ?? ''} onChange={e => setBiz({ ...biz, hourly_rate: e.target.value })} />
        <Input label="Margine standard %" type="number" step="0.01" value={biz.default_margin ?? ''} onChange={e => setBiz({ ...biz, default_margin: e.target.value })} />
        <Input label="Commissione standard %" type="number" step="0.01" value={biz.default_commission ?? ''} onChange={e => setBiz({ ...biz, default_commission: e.target.value })} />
        <Input label="Sconto standard %" type="number" step="0.01" value={biz.default_discount ?? ''} onChange={e => setBiz({ ...biz, default_discount: e.target.value })} />
        <Input label="Imballaggio €" type="number" step="0.01" value={biz.default_packaging ?? ''} onChange={e => setBiz({ ...biz, default_packaging: e.target.value })} />
        <Input label="Energia €" type="number" step="0.01" value={biz.default_energy ?? ''} onChange={e => setBiz({ ...biz, default_energy: e.target.value })} />
        <Input label="Usura laser €" type="number" step="0.01" value={biz.default_wear ?? ''} onChange={e => setBiz({ ...biz, default_wear: e.target.value })} />
        <Input label="Validità preventivo giorni" type="number" step="1" value={biz.quote_validity_days ?? ''} onChange={e => setBiz({ ...biz, quote_validity_days: e.target.value })} />
      </div>
    </Card>"""
        s = replace_once(s, old, new, "Settings business card")

    # ------------------------------------------------------------
    # Command Palette global search
    # ------------------------------------------------------------
    if "global-results" not in s:
        old = """function CommandPalette({ open, setOpen, nav, go }) { const [q, setQ] = useState(''); if (!open) return null; const rows = nav.filter(n => n.label.toLowerCase().includes(q.toLowerCase())); return <div className="cmd-back" onMouseDown={() => setOpen(false)}><div className="cmd" onMouseDown={e=>e.stopPropagation()}><div><Command /><input autoFocus placeholder="Vai a..." value={q} onChange={e=>setQ(e.target.value)} /></div>{rows.map(n => <button key={n.id} onClick={() => { go(n.id); setOpen(false); }}><n.icon />{n.label}<ChevronRight /></button>)}</div></div>; }"""
        new = """function CommandPalette({ open, setOpen, nav, go }) {
  const [q, setQ] = useState('');
  const { data: results } = useApi(q ? `/global-search?q=${encodeURIComponent(q)}` : '/global-search?q=', {});
  if (!open) return null;
  const rows = nav.filter(n => n.label.toLowerCase().includes(q.toLowerCase()));
  const resultGroups = [
    ['Materiali', results.materials, 'materials'],
    ['Prodotti', results.products, 'products'],
    ['Clienti', results.customers, 'people'],
    ['Fornitori', results.suppliers, 'people'],
    ['Preventivi', results.quotes, 'quote'],
    ['Vendite', results.sales, 'sales'],
  ];
  return <div className="cmd-back" onMouseDown={() => setOpen(false)}>
    <div className="cmd cmd-wide" onMouseDown={e=>e.stopPropagation()}>
      <div><Command /><input autoFocus placeholder="Cerca o vai a..." value={q} onChange={e=>setQ(e.target.value)} /></div>
      {rows.map(n => <button key={n.id} onClick={() => { go(n.id); setOpen(false); }}><n.icon />{n.label}<ChevronRight /></button>)}
      {q && <div className="global-results">
        {resultGroups.map(([label, values, target]) => list(values).length ? <section key={label}>
          <b>{label}</b>
          {list(values).map((r, i) => <button key={label + i} onClick={() => { go(target); setOpen(false); }}>
            <Search />
            <span>{r.name || r.id}<small>{r.subtitle || r.status || ''}</small></span>
            {r.value !== undefined && <em>{money(r.value)}</em>}
          </button>)}
        </section> : null)}
      </div>}
    </div>
  </div>;
}"""
        s = replace_once(s, old, new, "Command palette")

    MAIN.write_text(s, encoding="utf-8")

    # ------------------------------------------------------------
    # CSS
    # ------------------------------------------------------------
    css = CSS.read_text(encoding="utf-8")
    marker = "/* workflow advanced frontend patch */"
    if marker not in css:
        css += """

/* workflow advanced frontend patch */
.workflow-alert-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.workflow-alert-grid button {
  text-align: left;
  border: 1px solid rgba(148, 163, 184, .24);
  background: rgba(255,255,255,.06);
  color: inherit;
  border-radius: 18px;
  padding: 16px;
  cursor: pointer;
}

.workflow-alert-grid b {
  display: block;
  font-size: 22px;
  margin-bottom: 4px;
}

.workflow-alert-grid span {
  color: var(--muted);
  font-size: 12px;
}

.quote-status {
  display: inline-flex;
  border-radius: 999px;
  padding: 5px 9px;
  font-size: 11px;
  font-weight: 800;
  border: 1px solid rgba(148, 163, 184, .28);
  background: rgba(148, 163, 184, .12);
}

.quote-status.sent {
  background: rgba(59, 130, 246, .14);
  color: #93c5fd;
}

.quote-status.accepted {
  background: rgba(34, 197, 94, .14);
  color: #86efac;
}

.quote-status.rejected {
  background: rgba(239, 68, 68, .14);
  color: #fca5a5;
}

.quote-status.expired {
  background: rgba(249, 115, 22, .16);
  color: #fdba74;
}

.table-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.table-actions button {
  padding: 7px 9px;
  font-size: 11px;
}

.cmd-wide {
  width: min(860px, calc(100vw - 36px));
}

.global-results {
  display: grid;
  gap: 12px;
  max-height: 52vh;
  overflow: auto;
  padding: 8px 2px 2px;
}

.global-results section {
  display: grid;
  gap: 6px;
}

.global-results section > b {
  color: var(--muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: .08em;
  padding: 6px 8px 0;
}

.global-results button {
  display: grid !important;
  grid-template-columns: 22px 1fr auto;
  gap: 10px;
  align-items: center;
}

.global-results small {
  display: block;
  color: var(--muted);
  margin-top: 2px;
}

.global-results em {
  font-style: normal;
  color: var(--muted);
  font-weight: 800;
}

@media (max-width: 900px) {
  .workflow-alert-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
"""
        CSS.write_text(css, encoding="utf-8")

    print("Patch frontend workflow avanzato completata.")
    print(f"Aggiornato: {MAIN}")
    print(f"Aggiornato: {CSS}")


if __name__ == "__main__":
    main()
