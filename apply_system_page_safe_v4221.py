from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"

SYSTEM_PAGE = r'''
function SystemPage({ toast }) {
  const { data: status, refresh } = useApi('/system/status', {});
  const { data: version } = useApi('/system/version', {});

  const lanUrl = status?.lan_url || '';
  const localUrl = status?.local_url || '';
  const qrSvg = lanUrl
    ? `https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(lanUrl)}`
    : '';

  async function copyText(text, label) {
    try {
      await navigator.clipboard.writeText(text || '');
      toast(label || 'Copiato');
    } catch {
      toast(text || 'Dato non disponibile');
    }
  }

  return <>
    <PageTitle
      title="Sistema"
      desc="Stato dell'app, accesso da smartphone, rete locale e informazioni di servizio."
    />

    <div className="system-page-grid">
      <Card title="Stato applicazione" icon={Settings2} sub="Backend locale e ambiente runtime.">
        <div className="system-kpi-grid">
          <div><span>Edizione</span><b>{status.edition || 'Browser Edition'}</b></div>
          <div><span>Versione</span><b>{status.version || version.current_version || '—'}</b></div>
          <div><span>Porta</span><b>{status.port || '—'}</b></div>
          <div><span>Ora</span><b>{status.time || '—'}</b></div>
        </div>

        <div className="system-path-box">
          <span>Cartella runtime</span>
          <code>{status.cwd || '—'}</code>
        </div>

        <div className="quick-actions">
          <button className="ghost" onClick={refresh}>Aggiorna stato</button>
        </div>
      </Card>

      <Card title="Accesso mobile" icon={Settings2} sub="Apri il gestionale da smartphone o tablet sulla stessa rete Wi-Fi.">
        <div className="lan-access-box">
          <div>
            <span>Da questo PC</span>
            <b>{localUrl || '—'}</b>
            <button className="ghost" onClick={() => copyText(localUrl, 'Link locale copiato')}>Copia</button>
          </div>

          <div>
            <span>Da smartphone / rete LAN</span>
            <b>{lanUrl || '—'}</b>
            <button className="primary" onClick={() => copyText(lanUrl, 'Link LAN copiato')}>Copia link LAN</button>
          </div>
        </div>

        {qrSvg && <div className="mobile-qr-box">
          <img src={qrSvg} alt="QR code accesso mobile MN Laser Lab" />
          <small>Scansiona il QR con lo smartphone collegato alla stessa rete Wi-Fi del PC.</small>
        </div>}
      </Card>

      <Card title="Database locale" icon={Settings2} sub="Conteggio rapido dei dati principali salvati.">
        <div className="system-counts">
          {Object.entries(status.db_counts || {}).map(([k, v]) => (
            <div key={k}>
              <span>{k}</span>
              <b>{v}</b>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Aggiornamenti" icon={Settings2} sub="Base per il futuro update manager della Browser Edition.">
        <div className="update-status-box">
          <div>
            <span>Canale</span>
            <b>{version.channel || 'browser-edition'}</b>
          </div>
          <div>
            <span>Aggiornamenti automatici</span>
            <b>{version.automatic_updates ? 'Attivi' : 'Non ancora attivi'}</b>
          </div>
        </div>
        <p className="muted">{version.message || 'Gli aggiornamenti automatici saranno integrati in una prossima versione.'}</p>
      </Card>
    </div>
  </>;
}

'''

CSS_BLOCK = r'''
/* v42.2.1 system page / mobile QR */
.system-page-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(340px, .85fr);
  gap: 18px;
  align-items: start;
}

.system-kpi-grid,
.system-counts,
.update-status-box {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.system-kpi-grid div,
.system-counts div,
.update-status-box div,
.lan-access-box div {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  border-radius: 16px;
  padding: 12px;
  min-width: 0;
}

.system-kpi-grid span,
.system-counts span,
.update-status-box span,
.lan-access-box span,
.system-path-box span {
  display: block;
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .07em;
  font-weight: 900;
  margin-bottom: 6px;
}

.system-kpi-grid b,
.system-counts b,
.update-status-box b,
.lan-access-box b {
  display: block;
  color: var(--text);
  font-size: 14px;
  line-height: 1.28;
  overflow-wrap: anywhere;
}

.system-path-box {
  margin-top: 12px;
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(15, 23, 42, .35);
  border-radius: 16px;
  padding: 12px;
}

.system-path-box code {
  display: block;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  color: #bae6fd;
  font-size: 12px;
}

.lan-access-box {
  display: grid;
  gap: 10px;
}

.lan-access-box button {
  margin-top: 10px;
  width: 100%;
}

.mobile-qr-box {
  display: grid;
  place-items: center;
  text-align: center;
  gap: 10px;
  margin-top: 16px;
}

.mobile-qr-box img {
  width: 220px;
  height: 220px;
  background: white;
  border-radius: 20px;
  padding: 12px;
  box-shadow: 0 16px 40px rgba(0,0,0,.18);
}

.mobile-qr-box small {
  color: var(--muted);
  line-height: 1.4;
  max-width: 320px;
}

.update-status-box {
  margin-bottom: 12px;
}

@media (max-width: 1050px) {
  .system-page-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .system-kpi-grid,
  .system-counts,
  .update-status-box {
    grid-template-columns: 1fr;
  }

  .mobile-qr-box img {
    width: 200px;
    height: 200px;
  }
}
'''

def remove_existing_system_page(s: str) -> str:
    start = s.find("function SystemPage")
    if start == -1:
        return s

    # Nel nostro file la posizione sicura è prima di function App().
    app_idx = s.find("function App()", start)
    if app_idx != -1:
        return s[:start] + s[app_idx:]

    # fallback: fino alla funzione successiva
    next_fn = s.find("\nfunction ", start + 1)
    if next_fn != -1:
        return s[:start] + s[next_fn + 1:]

    return s[:start]

def main():
    s = FRONTEND.read_text(encoding="utf-8")

    # Rimuove versioni precedenti rotte.
    s = remove_existing_system_page(s)

    # Inserisce SystemPage subito prima di App.
    app_idx = s.find("function App()")
    if app_idx == -1:
        raise RuntimeError("function App() non trovata")

    s = s[:app_idx] + SYSTEM_PAGE + "\n" + s[app_idx:]

    # Aggiunge voce nav prima di Impostazioni, se manca.
    if "{ id: 'system'" not in s:
        s = s.replace(
            "{ id: 'settings', label: 'Impostazioni', icon: Settings2 },",
            "{ id: 'system', label: 'Sistema', icon: Settings2 },\n    { id: 'settings', label: 'Impostazioni', icon: Settings2 },",
            1
        )

    # Aggiunge SystemPage al router pages, se manca.
    if "system: SystemPage" not in s:
        s = s.replace(
            "settings: SettingsPage",
            "system: SystemPage, settings: SettingsPage",
            1
        )

    FRONTEND.write_text(s, encoding="utf-8")

    css = CSS.read_text(encoding="utf-8")
    css = re.sub(
        r"\n/\* v42\.2\.[01] system page.*?(?=\n/\*|\Z)",
        "\n",
        css,
        flags=re.DOTALL
    )

    if "v42.2.1 system page" not in css:
        css += "\n\n" + CSS_BLOCK.strip() + "\n"

    CSS.write_text(css, encoding="utf-8")

    print("Patch v42.2.1 applicata: Sistema agganciato a nav/pages in modo sicuro.")

if __name__ == "__main__":
    main()
