from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN_API = ROOT / "backend" / "app" / "main.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


BACKEND_HELPERS = r'''

# ---------------------------------------------------------------------------
# v39.8.0 - Preventivi stampabili / PDF cliente e interno
# ---------------------------------------------------------------------------

def _html_escape(value):
    return (
        str(value if value is not None else "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _money_html(value):
    return f"€ {parse_float(value):.2f}"


def _quote_price_value(quote):
    result = quote.get("result") or {}
    return (
        quote.get("discounted")
        or result.get("discounted")
        or quote.get("recommended")
        or result.get("recommended")
        or quote.get("potential_value")
        or 0
    )


def quote_customer_html(db, quote_id):
    quote = get_quote(db, quote_id)
    result = quote.get("result") or {}

    title = quote.get("name") or "Preventivo"
    customer = quote.get("customer") or "Cliente"
    notes = quote.get("notes") or quote.get("description") or ""
    price = _quote_price_value(quote)
    date = quote.get("date") or today_str()
    validity_days = business_settings(db).get("quote_validity_days", 15)

    rows_html = ""
    public_rows = quote.get("rows", []) or []
    for row in public_rows:
        label = row.get("label") or row.get("name") or "Voce"
        qty = parse_float(row.get("qty", 1))
        unit = row.get("unit", "")
        rows_html += f"""
          <tr>
            <td>{_html_escape(label)}</td>
            <td class="right">{qty:.2f} {_html_escape(unit)}</td>
          </tr>
        """

    if not rows_html:
        rows_html = """
          <tr>
            <td>Realizzazione personalizzata MN Laser Lab</td>
            <td class="right">1</td>
          </tr>
        """

    return f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <title>Preventivo cliente - {_html_escape(title)}</title>
  <style>
    @page {{ size: A4; margin: 18mm; }}
    body {{
      font-family: Arial, Helvetica, sans-serif;
      color: #111827;
      margin: 0;
      background: #ffffff;
    }}
    .page {{
      max-width: 780px;
      margin: 0 auto;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 3px solid #058482;
      padding-bottom: 18px;
      margin-bottom: 28px;
    }}
    .brand h1 {{
      margin: 0;
      font-size: 28px;
      letter-spacing: -0.03em;
    }}
    .brand p {{
      margin: 5px 0 0;
      color: #4b5563;
      font-size: 13px;
    }}
    .doc-badge {{
      text-align: right;
      font-size: 12px;
      color: #4b5563;
    }}
    .doc-badge b {{
      display: block;
      color: #058482;
      font-size: 18px;
      margin-bottom: 4px;
    }}
    .box {{
      border: 1px solid #e5e7eb;
      border-radius: 16px;
      padding: 18px;
      margin-bottom: 18px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }}
    .label {{
      display: block;
      color: #6b7280;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: .08em;
      margin-bottom: 4px;
    }}
    .value {{
      font-weight: 700;
      font-size: 15px;
    }}
    h2 {{
      margin: 0 0 12px;
      font-size: 22px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
    }}
    th {{
      background: #f3f4f6;
      text-align: left;
      font-size: 12px;
      color: #374151;
      padding: 10px;
    }}
    td {{
      border-bottom: 1px solid #e5e7eb;
      padding: 10px;
      font-size: 13px;
    }}
    .right {{
      text-align: right;
    }}
    .price {{
      margin-top: 26px;
      border-radius: 18px;
      background: linear-gradient(135deg, #058482, #0f766e);
      color: white;
      padding: 22px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .price span {{
      font-size: 13px;
      opacity: .9;
    }}
    .price b {{
      font-size: 30px;
    }}
    .notes {{
      color: #374151;
      line-height: 1.55;
      white-space: pre-wrap;
    }}
    .footer {{
      margin-top: 30px;
      padding-top: 14px;
      border-top: 1px solid #e5e7eb;
      color: #6b7280;
      font-size: 12px;
      display: flex;
      justify-content: space-between;
      gap: 18px;
    }}
    .print-btn {{
      position: fixed;
      right: 20px;
      top: 20px;
      border: 0;
      background: #058482;
      color: white;
      border-radius: 999px;
      padding: 12px 18px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 12px 30px rgba(0,0,0,.18);
    }}
    @media print {{
      .print-btn {{ display: none; }}
      body {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
    }}
  </style>
</head>
<body>
  <button class="print-btn" onclick="window.print()">Stampa / Salva PDF</button>
  <main class="page">
    <section class="header">
      <div class="brand">
        <h1>MN Laser Lab</h1>
        <p>Creazioni artigianali in legno · Taglio e incisione laser</p>
        <p>Filippo Lolli · filippololli1@gmail.com</p>
      </div>
      <div class="doc-badge">
        <b>Preventivo</b>
        <span>{_html_escape(date)}</span><br>
        <span>ID: {_html_escape(quote.get("id", ""))}</span>
      </div>
    </section>

    <section class="box grid">
      <div>
        <span class="label">Cliente</span>
        <span class="value">{_html_escape(customer)}</span>
      </div>
      <div>
        <span class="label">Validità preventivo</span>
        <span class="value">{int(parse_float(validity_days, 15))} giorni</span>
      </div>
    </section>

    <section class="box">
      <h2>{_html_escape(title)}</h2>
      <div class="notes">{_html_escape(notes or "Realizzazione personalizzata secondo specifiche concordate.")}</div>

      <table>
        <thead>
          <tr>
            <th>Descrizione</th>
            <th class="right">Quantità</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </section>

    <section class="price">
      <span>Totale preventivo</span>
      <b>{_money_html(price)}</b>
    </section>

    <section class="footer">
      <span>Preventivo generato con MN Laser Lab Manager.</span>
      <span>Il presente documento non include dettagli interni di costo.</span>
    </section>
  </main>
</body>
</html>"""


def quote_internal_html(db, quote_id):
    quote = get_quote(db, quote_id)
    result = quote.get("result") or {}
    title = quote.get("name") or "Preventivo"
    rows = quote.get("rows", []) or []

    material_rows = ""
    for row in rows:
        label = row.get("label") or row.get("name") or "Voce"
        qty = parse_float(row.get("qty", 1))
        unit = row.get("unit", "")
        unit_cost = parse_float(row.get("unit_cost", row.get("cost_per_unit", row.get("weighted_average_cost", 0))))
        cost = parse_float(row.get("cost", qty * unit_cost))

        material_rows += f"""
          <tr>
            <td>{_html_escape(label)}</td>
            <td class="right">{qty:.2f} {_html_escape(unit)}</td>
            <td class="right">{_money_html(unit_cost)}</td>
            <td class="right">{_money_html(cost)}</td>
          </tr>
        """

    if not material_rows:
        material_rows = """
          <tr>
            <td colspan="4">Nessun materiale collegato</td>
          </tr>
        """

    real = result.get("real", result.get("real_cost", quote.get("real", 0)))
    min_price = result.get("min", result.get("min_price", quote.get("min", 0)))
    recommended = result.get("recommended", quote.get("recommended", 0))
    discounted = result.get("discounted", quote.get("discounted", 0))
    premium = result.get("premium", quote.get("premium", 0))

    return f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <title>PDF interno - {_html_escape(title)}</title>
  <style>
    @page {{ size: A4; margin: 14mm; }}
    body {{
      font-family: Arial, Helvetica, sans-serif;
      color: #111827;
      margin: 0;
      background: #ffffff;
    }}
    .page {{
      max-width: 820px;
      margin: 0 auto;
    }}
    .header {{
      border-bottom: 3px solid #111827;
      padding-bottom: 14px;
      margin-bottom: 20px;
    }}
    h1 {{
      margin: 0;
      font-size: 25px;
    }}
    .muted {{
      color: #6b7280;
      font-size: 12px;
    }}
    .box {{
      border: 1px solid #e5e7eb;
      border-radius: 14px;
      padding: 14px;
      margin-bottom: 14px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }}
    .kpi {{
      background: #f9fafb;
      border-radius: 12px;
      padding: 12px;
    }}
    .kpi span {{
      display: block;
      color: #6b7280;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: .06em;
    }}
    .kpi b {{
      display: block;
      margin-top: 5px;
      font-size: 17px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th {{
      background: #f3f4f6;
      text-align: left;
      padding: 9px;
      font-size: 12px;
    }}
    td {{
      padding: 9px;
      border-bottom: 1px solid #e5e7eb;
      font-size: 12px;
    }}
    .right {{
      text-align: right;
    }}
    .print-btn {{
      position: fixed;
      right: 20px;
      top: 20px;
      border: 0;
      background: #111827;
      color: white;
      border-radius: 999px;
      padding: 12px 18px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 12px 30px rgba(0,0,0,.18);
    }}
    @media print {{
      .print-btn {{ display: none; }}
      body {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
    }}
  </style>
</head>
<body>
  <button class="print-btn" onclick="window.print()">Stampa / Salva PDF</button>
  <main class="page">
    <section class="header">
      <h1>Analisi interna preventivo</h1>
      <div class="muted">MN Laser Lab Manager · Filippo Lolli · filippololli1@gmail.com</div>
      <div class="muted">ID: {_html_escape(quote.get("id", ""))} · Data: {_html_escape(quote.get("date", ""))}</div>
    </section>

    <section class="box">
      <h2>{_html_escape(title)}</h2>
      <p class="muted">Cliente: {_html_escape(quote.get("customer", "—"))}</p>
      <p class="muted">{_html_escape(quote.get("notes", ""))}</p>
    </section>

    <section class="box grid">
      <div class="kpi"><span>Costo reale</span><b>{_money_html(real)}</b></div>
      <div class="kpi"><span>Prezzo minimo</span><b>{_money_html(min_price)}</b></div>
      <div class="kpi"><span>Consigliato</span><b>{_money_html(recommended)}</b></div>
      <div class="kpi"><span>Premium</span><b>{_money_html(premium)}</b></div>
    </section>

    <section class="box grid">
      <div class="kpi"><span>Ore lavoro</span><b>{parse_float(quote.get("hours")):.2f}</b></div>
      <div class="kpi"><span>Tariffa/h</span><b>{_money_html(quote.get("rate"))}</b></div>
      <div class="kpi"><span>Margine</span><b>{parse_float(quote.get("margin")):.2f}%</b></div>
      <div class="kpi"><span>Sconto</span><b>{parse_float(quote.get("discount")):.2f}%</b></div>
    </section>

    <section class="box">
      <h2>Materiali</h2>
      <table>
        <thead>
          <tr>
            <th>Materiale</th>
            <th class="right">Quantità</th>
            <th class="right">Costo/u</th>
            <th class="right">Totale</th>
          </tr>
        </thead>
        <tbody>
          {material_rows}
        </tbody>
      </table>
    </section>

    <section class="box grid">
      <div class="kpi"><span>Packaging</span><b>{_money_html(quote.get("packaging"))}</b></div>
      <div class="kpi"><span>Energia</span><b>{_money_html(quote.get("energy"))}</b></div>
      <div class="kpi"><span>Usura</span><b>{_money_html(quote.get("wear"))}</b></div>
      <div class="kpi"><span>Commissioni</span><b>{parse_float(quote.get("commission")):.2f}%</b></div>
    </section>
  </main>
</body>
</html>"""
'''


API_ENDPOINTS = r'''

from fastapi.responses import HTMLResponse


@app.get("/api/quotes/{quote_id:path}/pdf/customer", response_class=HTMLResponse)
def quote_customer_pdf_api(quote_id: str):
    try:
        return HTMLResponse(quote_customer_html(load_db(), quote_id))
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@app.get("/api/quotes/{quote_id:path}/pdf/internal", response_class=HTMLResponse)
def quote_internal_pdf_api(quote_id: str):
    try:
        return HTMLResponse(quote_internal_html(load_db(), quote_id))
    except ValueError as exc:
        raise HTTPException(404, str(exc))
'''


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"Blocco non trovato: {label}")
    return text.replace(old, new, 1)


def patch_backend():
    s = LEGACY.read_text(encoding="utf-8")
    if "def quote_customer_html" not in s:
        s += "\n\n" + BACKEND_HELPERS.strip() + "\n"
    LEGACY.write_text(s, encoding="utf-8")

    m = MAIN_API.read_text(encoding="utf-8")
    if "def quote_customer_pdf_api" not in m:
        m += "\n\n" + API_ENDPOINTS.strip() + "\n"
    MAIN_API.write_text(m, encoding="utf-8")

    print("Backend PDF preventivi applicato.")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    if "function openQuotePdf" not in s:
        old = """  async function changeQuoteStatus(q, status) {
    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/status`, { status });
      await refreshQuotes();
      toast('Stato preventivo aggiornato');
    } catch (e) {
      toast(e.message, 'err');
    }
  }"""

        new = """  async function changeQuoteStatus(q, status) {
    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/status`, { status });
      await refreshQuotes();
      toast('Stato preventivo aggiornato');
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  function openQuotePdf(q, type = 'customer') {
    if (!q?.id) {
      toast('Salva prima il preventivo', 'err');
      return;
    }
    const url = `/api/quotes/${encodeURIComponent(q.id)}/pdf/${type}`;
    window.open(url, '_blank');
  }"""
        s = replace_once(s, old, new, "openQuotePdf function")

    old_actions = """          <button className="ghost" onClick={() => changeQuoteStatus(r, 'sent')}>Inviato</button>
          <button className="ghost" onClick={() => changeQuoteStatus(r, 'accepted')}>Accettato</button>
          <button className="ghost" onClick={() => changeQuoteStatus(r, 'rejected')}>Rifiutato</button>
          <button className="ghost" onClick={() => quoteToProduct(r)}>Crea prodotto</button>"""

    new_actions = """          <button className="ghost" onClick={() => openQuotePdf(r, 'customer')}>PDF cliente</button>
          <button className="ghost" onClick={() => openQuotePdf(r, 'internal')}>PDF interno</button>
          <button className="ghost" onClick={() => changeQuoteStatus(r, 'sent')}>Inviato</button>
          <button className="ghost" onClick={() => changeQuoteStatus(r, 'accepted')}>Accettato</button>
          <button className="ghost" onClick={() => changeQuoteStatus(r, 'rejected')}>Rifiutato</button>
          <button className="ghost" onClick={() => quoteToProduct(r)}>Crea prodotto</button>"""

    if old_actions in s and "PDF cliente" not in s:
        s = s.replace(old_actions, new_actions, 1)

    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend PDF preventivi applicato.")


def main():
    patch_backend()
    patch_frontend()
    print("Patch v39.8.0 PDF preventivi completata.")


if __name__ == "__main__":
    main()
