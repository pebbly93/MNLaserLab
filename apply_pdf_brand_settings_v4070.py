from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN_API = ROOT / "backend" / "app" / "main.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


BACKEND_CODE = r'''

# ---------------------------------------------------------------------------
# v40.7.0 - Impostazioni modello PDF / brand
# ---------------------------------------------------------------------------

def default_pdf_settings():
    return {
        "company_name": "MN Laser Lab",
        "author": "Filippo Lolli",
        "email": "filippololli1@gmail.com",
        "phone": "",
        "address": "",
        "website": "",
        "vat": "",
        "logo_data_url": "",
        "primary_color": "#058482",
        "customer_title": "Preventivo cliente",
        "internal_title": "Scheda interna preventivo",
        "intro_text": "Grazie per averci contattato. Di seguito trovi il riepilogo del preventivo richiesto.",
        "terms": "Il preventivo è valido salvo disponibilità materiali e conferma finale della lavorazione.",
        "footer": "MN Laser Lab - Creazioni artigianali in legno e taglio laser",
    }


def get_pdf_settings(db):
    settings = db.setdefault("pdf_settings", {})
    base = default_pdf_settings()
    for k, v in base.items():
        settings.setdefault(k, v)
    return settings


def update_pdf_settings(db, payload):
    settings = get_pdf_settings(db)
    allowed = set(default_pdf_settings().keys())

    for key, value in (payload or {}).items():
        if key in allowed:
            settings[key] = str(value or "")

    db["pdf_settings"] = settings
    return settings


def export_pdf_settings(db):
    return {
        "filename": f"mn_laser_lab_pdf_template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "data": get_pdf_settings(db),
    }


def import_pdf_settings(db, payload):
    if not isinstance(payload, dict):
        raise ValueError("Modello PDF non valido")
    return update_pdf_settings(db, payload)
'''


API_CODE = r'''

@app.get("/api/settings/pdf")
def get_pdf_settings_api():
    return get_pdf_settings(load_db())


@app.post("/api/settings/pdf")
def update_pdf_settings_api(payload: Payload):
    def fn(db):
        return update_pdf_settings(db, payload.data)
    return mutate(fn)


@app.get("/api/settings/pdf/export")
def export_pdf_settings_api():
    return export_pdf_settings(load_db())


@app.post("/api/settings/pdf/import")
def import_pdf_settings_api(payload: Payload):
    def fn(db):
        return import_pdf_settings(db, payload.data)
    return mutate(fn)
'''


PDF_INJECTION = r'''
def _pdf_brand_block(db):
    s = get_pdf_settings(db)
    logo = s.get("logo_data_url", "")
    logo_html = f'<img class="brand-logo" src="{logo}" alt="Logo" />' if logo else ""
    return f"""
    <div class="brand-head">
      <div>
        {logo_html}
      </div>
      <div class="brand-company">
        <h1>{s.get('company_name','MN Laser Lab')}</h1>
        <p>{s.get('author','')}</p>
        <p>{s.get('email','')} {s.get('phone','')}</p>
        <p>{s.get('address','')}</p>
        <p>{s.get('website','')} {s.get('vat','')}</p>
      </div>
    </div>
    """


def _pdf_brand_css(db):
    s = get_pdf_settings(db)
    color = s.get("primary_color", "#058482") or "#058482"
    return f"""
    <style>
      :root {{ --brand: {color}; }}
      .brand-head {{
        display: flex;
        justify-content: space-between;
        gap: 24px;
        align-items: flex-start;
        border-bottom: 3px solid var(--brand);
        padding-bottom: 18px;
        margin-bottom: 24px;
      }}
      .brand-logo {{
        max-width: 150px;
        max-height: 80px;
        object-fit: contain;
      }}
      .brand-company {{
        text-align: right;
        font-size: 12px;
        color: #475569;
      }}
      .brand-company h1 {{
        margin: 0 0 6px;
        color: #0f172a;
        font-size: 24px;
      }}
      .brand-company p {{
        margin: 2px 0;
      }}
      .pdf-intro {{
        border-left: 4px solid var(--brand);
        padding: 10px 14px;
        background: #f8fafc;
        margin: 18px 0;
        color: #334155;
      }}
      .pdf-terms {{
        margin-top: 28px;
        padding: 14px;
        background: #f8fafc;
        border-radius: 10px;
        color: #475569;
        font-size: 12px;
      }}
      .pdf-footer {{
        margin-top: 28px;
        border-top: 1px solid #e2e8f0;
        padding-top: 12px;
        font-size: 11px;
        color: #64748b;
        text-align: center;
      }}
    </style>
    """
'''


def append_once(path: Path, marker: str, code: str):
    s = path.read_text(encoding="utf-8")
    if marker not in s:
        s += "\n\n" + code.strip() + "\n"
        path.write_text(s, encoding="utf-8")


def patch_backend():
    append_once(LEGACY, "def default_pdf_settings", BACKEND_CODE)
    append_once(LEGACY, "def _pdf_brand_block", PDF_INJECTION)
    append_once(MAIN_API, "def get_pdf_settings_api", API_CODE)
    print("Backend impostazioni PDF applicato.")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    if "function PdfSettingsPanel" not in s:
        marker = "function SettingsPage"
        panel = r'''
function PdfSettingsPanel({ toast }) {
  const { data: pdfSettings, refresh: refreshPdfSettings } = useApi('/settings/pdf', {});
  const [pdfForm, setPdfForm] = useState({});
  const [importModelText, setImportModelText] = useState('');

  useEffect(() => {
    setPdfForm(pdfSettings || {});
  }, [JSON.stringify(pdfSettings || {})]);

  function setPdf(key, value) {
    setPdfForm(v => ({ ...v, [key]: value }));
  }

  async function savePdfSettings() {
    try {
      await postJSON('/settings/pdf', pdfForm);
      toast('Modello PDF salvato');
      await refreshPdfSettings();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function exportPdfModel() {
    try {
      const r = await getJSON('/settings/pdf/export');
      downloadJson(r.filename || 'mn_laser_lab_pdf_template.json', r.data || {});
      toast('Modello PDF esportato');
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function importPdfModel() {
    try {
      const parsed = JSON.parse(importModelText);
      await postJSON('/settings/pdf/import', parsed);
      setImportModelText('');
      toast('Modello PDF importato');
      await refreshPdfSettings();
    } catch (e) {
      toast('Modello non valido: ' + (e.message || e), 'err');
    }
  }

  return <Card title="Modello PDF e dati azienda" icon={FileJson} action={<button className="primary" onClick={savePdfSettings}><Save /> Salva modello PDF</button>}>
    <div className="pdf-settings-layout">
      <div className="pdf-settings-form">
        <div className="form-grid">
          <Input label="Nome attività" value={pdfForm.company_name || ''} onChange={e => setPdf('company_name', e.target.value)} />
          <Input label="Autore / titolare" value={pdfForm.author || ''} onChange={e => setPdf('author', e.target.value)} />
          <Input label="Email" value={pdfForm.email || ''} onChange={e => setPdf('email', e.target.value)} />
          <Input label="Telefono" value={pdfForm.phone || ''} onChange={e => setPdf('phone', e.target.value)} />
          <Input label="Indirizzo" value={pdfForm.address || ''} onChange={e => setPdf('address', e.target.value)} />
          <Input label="Sito web" value={pdfForm.website || ''} onChange={e => setPdf('website', e.target.value)} />
          <Input label="P.IVA / CF" value={pdfForm.vat || ''} onChange={e => setPdf('vat', e.target.value)} />
          <Input label="Colore principale" value={pdfForm.primary_color || '#058482'} onChange={e => setPdf('primary_color', e.target.value)} />
        </div>

        <div className="form-grid">
          <Input label="Titolo PDF cliente" value={pdfForm.customer_title || ''} onChange={e => setPdf('customer_title', e.target.value)} />
          <Input label="Titolo PDF interno" value={pdfForm.internal_title || ''} onChange={e => setPdf('internal_title', e.target.value)} />
        </div>

        <Field label="Testo introduttivo">
          <textarea value={pdfForm.intro_text || ''} onChange={e => setPdf('intro_text', e.target.value)} />
        </Field>

        <Field label="Condizioni commerciali">
          <textarea value={pdfForm.terms || ''} onChange={e => setPdf('terms', e.target.value)} />
        </Field>

        <Field label="Footer PDF">
          <textarea value={pdfForm.footer || ''} onChange={e => setPdf('footer', e.target.value)} />
        </Field>

        <Field label="Logo Base64 / Data URL">
          <textarea value={pdfForm.logo_data_url || ''} onChange={e => setPdf('logo_data_url', e.target.value)} placeholder="data:image/png;base64,..." />
        </Field>
      </div>

      <div className="pdf-settings-preview">
        <div className="pdf-preview-page">
          <div className="pdf-preview-head" style={{ borderColor: pdfForm.primary_color || '#058482' }}>
            <div className="pdf-preview-logo">
              {pdfForm.logo_data_url ? <img src={pdfForm.logo_data_url} alt="Logo" /> : <span>Logo</span>}
            </div>
            <div>
              <h3>{pdfForm.company_name || 'MN Laser Lab'}</h3>
              <p>{pdfForm.author || 'Filippo Lolli'}</p>
              <p>{pdfForm.email || 'filippololli1@gmail.com'}</p>
            </div>
          </div>
          <h4>{pdfForm.customer_title || 'Preventivo cliente'}</h4>
          <p className="pdf-preview-intro">{pdfForm.intro_text || 'Testo introduttivo del preventivo.'}</p>
          <div className="pdf-preview-table">
            <span>Descrizione</span><span>Totale</span>
            <b>Creazione personalizzata</b><b>€ 120.00</b>
          </div>
          <p className="pdf-preview-terms">{pdfForm.terms || 'Condizioni commerciali.'}</p>
          <small>{pdfForm.footer || 'Footer PDF'}</small>
        </div>

        <div className="quick-actions">
          <button className="ghost" onClick={exportPdfModel}><Download /> Esporta modello</button>
        </div>

        <textarea className="import-box small" value={importModelText} onChange={e => setImportModelText(e.target.value)} placeholder="Incolla qui il JSON del modello PDF..." />
        <div className="quick-actions">
          <button className="primary" onClick={importPdfModel}><Upload /> Importa modello</button>
          <button className="ghost" onClick={() => setImportModelText('')}>Svuota</button>
        </div>
      </div>
    </div>
  </Card>;
}

'''
        if marker not in s:
            raise RuntimeError("Punto inserimento PdfSettingsPanel non trovato")
        s = s.replace(marker, panel + marker, 1)

    if "<PdfSettingsPanel toast={toast} />" not in s:
        target = """    <Card title="Import archivio JSON" icon={Upload}>"""
        if target in s:
            s = s.replace(target, "    <PdfSettingsPanel toast={toast} />\n\n" + target, 1)
        else:
            raise RuntimeError("Punto inserimento pannello PDF in Settings non trovato")

    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend impostazioni PDF applicato.")


def patch_css():
    css = CSS.read_text(encoding="utf-8")
    if "/* v40.7 pdf settings */" not in css:
        css += r'''

/* v40.7 pdf settings */
.pdf-settings-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(360px, .85fr);
  gap: 18px;
  align-items: start;
}

.pdf-settings-form {
  display: grid;
  gap: 14px;
}

.pdf-settings-form textarea {
  min-height: 82px;
}

.pdf-settings-preview {
  display: grid;
  gap: 12px;
}

.pdf-preview-page {
  background: #fff;
  color: #0f172a;
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 20px 60px rgba(0,0,0,.24);
  display: grid;
  gap: 14px;
}

.pdf-preview-head {
  display: grid;
  grid-template-columns: 90px minmax(0, 1fr);
  gap: 14px;
  align-items: center;
  border-bottom: 3px solid #058482;
  padding-bottom: 14px;
}

.pdf-preview-logo {
  width: 82px;
  height: 58px;
  border-radius: 12px;
  background: #f1f5f9;
  display: grid;
  place-items: center;
  color: #64748b;
  overflow: hidden;
  font-size: 12px;
}

.pdf-preview-logo img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.pdf-preview-head h3 {
  margin: 0;
  font-size: 20px;
}

.pdf-preview-head p {
  margin: 2px 0;
  color: #64748b;
  font-size: 12px;
}

.pdf-preview-page h4 {
  margin: 0;
  font-size: 18px;
}

.pdf-preview-intro,
.pdf-preview-terms {
  background: #f8fafc;
  border-radius: 12px;
  padding: 12px;
  color: #475569;
  font-size: 12px;
  line-height: 1.45;
}

.pdf-preview-table {
  display: grid;
  grid-template-columns: 1fr auto;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
}

.pdf-preview-table span,
.pdf-preview-table b {
  padding: 10px;
  border-bottom: 1px solid #e2e8f0;
}

.pdf-preview-table span {
  background: #f8fafc;
  color: #64748b;
  font-size: 11px;
  text-transform: uppercase;
}

.pdf-preview-page small {
  color: #64748b;
  text-align: center;
}

.import-box.small {
  min-height: 120px;
}

@media (max-width: 1050px) {
  .pdf-settings-layout {
    grid-template-columns: 1fr;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")


def main():
    patch_backend()
    patch_frontend()
    patch_css()
    print("Patch v40.7.0 impostazioni PDF/brand completata.")


if __name__ == "__main__":
    main()
