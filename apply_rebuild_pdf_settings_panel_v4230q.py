from pathlib import Path

MAIN = Path("frontend/src/main.jsx")

NEW_PANEL = r'''
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

  async function exportPdfSettings() {
    try {
      const r = await getJSON('/settings/pdf/export');
      downloadJson('mn_laser_lab_pdf_settings.json', r);
      toast('Modello PDF esportato');
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function importPdfSettings() {
    try {
      const parsed = JSON.parse(importModelText || '{}');
      await postJSON('/settings/pdf/import', parsed);
      toast('Modello PDF importato');
      setImportModelText('');
      await refreshPdfSettings();
    } catch (e) {
      toast(e.message || 'JSON non valido', 'err');
    }
  }

  return <Card title="Modello PDF e dati azienda" icon={FileJson} action={<button className="primary" onClick={savePdfSettings}><Save /> Salva modello PDF</button>}>
    <div className="pdf-settings-layout">
      <div className="pdf-settings-form">
        <div className="form-grid">
          <Input label="Nome azienda / brand" value={pdfForm.company_name || ''} onChange={e => setPdf('company_name', e.target.value)} />
          <Input label="Sottotitolo" value={pdfForm.company_subtitle || ''} onChange={e => setPdf('company_subtitle', e.target.value)} />
          <Input label="Referente" value={pdfForm.contact_name || ''} onChange={e => setPdf('contact_name', e.target.value)} />
          <Input label="Email" value={pdfForm.email || ''} onChange={e => setPdf('email', e.target.value)} />
          <Input label="Telefono" value={pdfForm.phone || ''} onChange={e => setPdf('phone', e.target.value)} />
          <Input label="Sito web" value={pdfForm.website || ''} onChange={e => setPdf('website', e.target.value)} />
          <Input label="Indirizzo" value={pdfForm.address || ''} onChange={e => setPdf('address', e.target.value)} />
          <Input label="Colore principale" value={pdfForm.primary_color || '#058482'} onChange={e => setPdf('primary_color', e.target.value)} />
          <Input label="Validità preventivo giorni" type="number" step="1" value={pdfForm.quote_validity_days || ''} onChange={e => setPdf('quote_validity_days', e.target.value)} />
        </div>

        <label className="field form-grid-full">
          <span>Note footer PDF</span>
          <textarea value={pdfForm.footer_note || ''} onChange={e => setPdf('footer_note', e.target.value)} placeholder="Testo da mostrare a fondo pagina nei preventivi..." />
        </label>

        <div className="quick-actions">
          <button className="ghost" onClick={exportPdfSettings}>Esporta modello</button>
        </div>

        <div className="import-box">
          <label className="field">
            <span>Importa modello JSON</span>
            <textarea value={importModelText} onChange={e => setImportModelText(e.target.value)} placeholder='Incolla qui il JSON esportato...' />
          </label>
          <button className="ghost" onClick={importPdfSettings}>Importa modello</button>
        </div>
      </div>

      <div className="pdf-settings-preview">
        <div className="pdf-preview-sheet">
          <div className="pdf-preview-header">
            <img src="/mn_laser_lab_logo.png" alt="Logo MN Laser Lab" />
            <div>
              <b>{pdfForm.company_name || 'MN Laser Lab'}</b>
              <span>{pdfForm.company_subtitle || 'Creazioni artigianali in legno e taglio laser'}</span>
            </div>
          </div>

          <div className="pdf-preview-title">Preventivo</div>

          <div className="pdf-preview-lines">
            <span></span>
            <span></span>
            <span></span>
          </div>

          <div className="pdf-preview-total">
            <span>Totale preventivo</span>
            <b>€ 120,00</b>
          </div>

          <small>{pdfForm.footer_note || 'Preventivo generato con MN Laser Lab Manager.'}</small>
        </div>
      </div>
    </div>
  </Card>;
}
'''

def main():
    s = MAIN.read_text(encoding="utf-8")

    start = s.find("function PdfSettingsPanel(")
    end = s.find("function SettingsPage(", start)

    if start == -1:
      raise RuntimeError("function PdfSettingsPanel non trovata")
    if end == -1:
      raise RuntimeError("function SettingsPage non trovata dopo PdfSettingsPanel")

    s = s[:start] + NEW_PANEL.strip() + "\n\n" + s[end:]

    MAIN.write_text(s, encoding="utf-8")
    print("Patch v42.3.0q applicata: PdfSettingsPanel ricostruito pulito.")

if __name__ == "__main__":
    main()
