from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"

NEW_CUSTOMER = r'''
def quote_customer_html(db, quote_id):
    quote = get_quote(db, quote_id)
    result = quote.get("result") or {}

    title = quote.get("name") or "Preventivo"
    customer = quote.get("customer") or "Cliente"
    notes = quote.get("notes") or quote.get("description") or ""
    price = _quote_price_value(quote)
    date = quote.get("date") or today_str()
    validity_days = business_settings(db).get("quote_validity_days", 15)
    quote_id_value = quote.get("id", quote_id)

    rows_html = ""
    public_rows = quote.get("rows", []) or []

    for row in public_rows:
        label = row.get("label") or row.get("name") or "Voce"
        qty = parse_float(row.get("qty", 1))
        unit = row.get("unit", "")

        rows_html += f"""
          <tr>
            <td>
              <b>{_html_escape(label)}</b>
              <small>Voce inclusa nella realizzazione</small>
            </td>
            <td class="right">{qty:.2f} {_html_escape(unit)}</td>
          </tr>
        """

    if not rows_html:
        rows_html = """
          <tr>
            <td>
              <b>Realizzazione personalizzata MN Laser Lab</b>
              <small>Lavorazione secondo specifiche concordate</small>
            </td>
            <td class="right">1</td>
          </tr>
        """

    project_fee = parse_float(quote.get("project_fee"))
    project_fee_row = ""
    if project_fee > 0:
        project_fee_row = f"""
          <tr class="project-row">
            <td>
              <b>Spese di progetto</b>
              <small>Studio, progettazione, preparazione file e impostazione lavorazione</small>
            </td>
            <td class="right">{_money_html(project_fee)}</td>
          </tr>
        """

    html = f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <title>Preventivo cliente - {_html_escape(title)}</title>
  <style>
    @page {{ size: A4; margin: 16mm; }}

    body {{
      font-family: Arial, Helvetica, sans-serif;
      color: #0f172a;
      margin: 0;
      background: #eef2f7;
    }}

    .page {{
      max-width: 860px;
      margin: 0 auto;
      background: #ffffff;
      border-radius: 24px;
      padding: 34px 38px;
      box-shadow: 0 28px 80px rgba(15, 23, 42, .14);
    }}

    .header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 28px;
      align-items: start;
      border-bottom: 3px solid #058482;
      padding-bottom: 22px;
      margin-bottom: 26px;
    }}

    .brand h1 {{
      margin: 0;
      font-size: 30px;
      line-height: 1.05;
      letter-spacing: -0.045em;
      color: #0f172a;
    }}

    .brand p {{
      margin: 6px 0 0;
      color: #64748b;
      font-size: 13px;
      line-height: 1.4;
    }}

    .doc-badge {{
      min-width: 190px;
      text-align: right;
      font-size: 12px;
      color: #64748b;
    }}

    .doc-badge b {{
      display: block;
      color: #058482;
      font-size: 22px;
      margin-bottom: 6px;
      letter-spacing: -0.035em;
    }}

    .doc-badge span {{
      display: block;
      line-height: 1.5;
    }}

    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1.3fr) minmax(240px, .7fr);
      gap: 18px;
      margin-bottom: 18px;
    }}

    .box {{
      border: 1px solid #e2e8f0;
      background: #ffffff;
      border-radius: 18px;
      padding: 18px;
    }}

    .soft-box {{
      background: #f8fafc;
    }}

    .label {{
      display: block;
      color: #64748b;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: .08em;
      margin-bottom: 5px;
      font-weight: 800;
    }}

    .value {{
      display: block;
      font-weight: 800;
      font-size: 16px;
      color: #0f172a;
      line-height: 1.3;
    }}

    h2 {{
      margin: 0 0 10px;
      font-size: 24px;
      letter-spacing: -0.035em;
      color: #0f172a;
    }}

    .notes {{
      color: #334155;
      line-height: 1.6;
      white-space: pre-wrap;
      font-size: 13.5px;
    }}

    .section-title {{
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 18px;
      margin: 24px 0 10px;
    }}

    .section-title h3 {{
      margin: 0;
      font-size: 17px;
      letter-spacing: -0.025em;
    }}

    .section-title span {{
      color: #64748b;
      font-size: 12px;
    }}

    table {{
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      table-layout: fixed;
      overflow: hidden;
      border-radius: 16px;
      border: 1px solid #e2e8f0;
      background: #ffffff;
    }}

    th {{
      background: #f1f5f9;
      text-align: left;
      font-size: 11px;
      color: #475569;
      text-transform: uppercase;
      letter-spacing: .075em;
      padding: 12px 14px;
      border-bottom: 1px solid #e2e8f0;
    }}

    td {{
      border-bottom: 1px solid #e5e7eb;
      padding: 14px;
      font-size: 13px;
      color: #1e293b;
      vertical-align: middle;
      line-height: 1.35;
    }}

    tr:last-child td {{
      border-bottom: 0;
    }}

    td b {{
      display: block;
      font-size: 13.5px;
      color: #0f172a;
      margin-bottom: 3px;
    }}

    td small {{
      display: block;
      color: #64748b;
      font-size: 11.5px;
      line-height: 1.35;
    }}

    .right {{
      text-align: right;
      white-space: nowrap;
    }}

    .project-row td {{
      background: rgba(5, 132, 130, .055);
    }}

    .project-row b {{
      color: #058482;
    }}

    .total-card {{
      margin-top: 22px;
      border-radius: 22px;
      background: linear-gradient(135deg, #058482, #0f766e);
      color: white;
      padding: 24px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 18px;
      align-items: center;
      box-shadow: 0 18px 42px rgba(5, 132, 130, .20);
    }}

    .total-card span {{
      display: block;
      font-size: 12px;
      opacity: .88;
      text-transform: uppercase;
      letter-spacing: .08em;
      margin-bottom: 4px;
      font-weight: 800;
    }}

    .total-card small {{
      display: block;
      opacity: .82;
      font-size: 12px;
      line-height: 1.4;
    }}

    .total-card b {{
      font-size: 34px;
      letter-spacing: -0.045em;
      white-space: nowrap;
    }}

    .terms {{
      margin-top: 20px;
      border-radius: 16px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      padding: 15px 16px;
      color: #475569;
      font-size: 12px;
      line-height: 1.55;
    }}

    .footer {{
      margin-top: 26px;
      padding-top: 14px;
      border-top: 1px solid #e5e7eb;
      color: #64748b;
      font-size: 11.5px;
      display: flex;
      justify-content: space-between;
      gap: 18px;
      line-height: 1.45;
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
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 12px 30px rgba(0,0,0,.18);
      z-index: 100;
    }}

    @media print {{
      body {{
        background: white;
        print-color-adjust: exact;
        -webkit-print-color-adjust: exact;
      }}

      .page {{
        max-width: none;
        margin: 0;
        padding: 0;
        box-shadow: none;
        border-radius: 0;
      }}

      .print-btn {{
        display: none;
      }}
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
        <span>{_html_escape(date)}</span>
        <span>ID: {_html_escape(quote_id_value)}</span>
      </div>
    </section>

    <section class="hero">
      <div class="box">
        <span class="label">Oggetto preventivo</span>
        <h2>{_html_escape(title)}</h2>
        <div class="notes">{_html_escape(notes or "Realizzazione personalizzata secondo specifiche concordate.")}</div>
      </div>

      <div class="box soft-box">
        <span class="label">Cliente</span>
        <span class="value">{_html_escape(customer)}</span>
        <br>
        <span class="label">Validità</span>
        <span class="value">{int(parse_float(validity_days, 15))} giorni</span>
      </div>
    </section>

    <div class="section-title">
      <h3>Riepilogo lavorazione</h3>
      <span>Documento cliente</span>
    </div>

    <table>
      <thead>
        <tr>
          <th>Descrizione</th>
          <th class="right">Quantità / Importo</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
        {project_fee_row}
      </tbody>
    </table>

    <section class="total-card">
      <div>
        <span>Totale preventivo</span>
        <small>Importo finale riservato al cliente. Il documento non mostra costi interni o marginalità.</small>
      </div>
      <b>{_money_html(price)}</b>
    </section>

    <section class="terms">
      Il preventivo è valido salvo disponibilità materiali e conferma finale della lavorazione.
    </section>

    <section class="footer">
      <span>Preventivo generato con MN Laser Lab Manager.</span>
      <span>Il presente documento non include dettagli interni di costo.</span>
    </section>
  </main>
</body>
</html>"""

    return apply_pdf_brand_to_html(db, html, 'customer', quote)
'''

def replace_function(source: str, name: str, new_code: str) -> str:
    start = source.find(f"def {name}(")
    if start == -1:
        raise RuntimeError(f"Funzione non trovata: {name}")

    end = source.find("\ndef ", start + 1)
    if end == -1:
        end = len(source)

    return source[:start] + new_code.strip() + "\n\n" + source[end + 1:]


def main():
    s = LEGACY.read_text(encoding="utf-8")
    s = replace_function(s, "quote_customer_html", NEW_CUSTOMER)
    LEGACY.write_text(s, encoding="utf-8")
    print("Patch v40.9.1 applicata: PDF cliente reso simile al PDF interno, ma senza dati riservati.")


if __name__ == "__main__":
    main()
