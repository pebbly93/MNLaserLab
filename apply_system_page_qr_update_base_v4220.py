from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "backend" / "app" / "main.py"
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


BACKEND_HELPERS = r'''
# ---------------------------------------------------------------------------
# v42.2.0 - System page helpers
# ---------------------------------------------------------------------------

def system_status_info(db):
    import os
    import sys
    import socket
    import platform
    from datetime import datetime

    def get_lan_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    port = int(os.environ.get("MN_BACKEND_PORT", "8000"))
    lan_ip = get_lan_ip()

    return {
        "ok": True,
        "app": "MN Laser Lab Manager",
        "edition": "Browser Edition",
        "version": "42.2.0",
        "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "port": port,
        "local_url": f"http://127.0.0.1:{port}/",
        "lan_ip": lan_ip,
        "lan_url": f"http://{lan_ip}:{port}/",
        "db_counts": {
            "materials": len(db.get("materials", {}) or {}),
            "components": len(db.get("components", {}) or {}),
            "products": len(db.get("products", {}) or {}),
            "quotes": len(db.get("quotes", []) or []),
            "customers": len(db.get("customers", {}) or {}),
            "suppliers": len(db.get("suppliers", {}) or {}),
            "sales": len(db.get("sales", []) or []),
        },
    }


def system_update_info():
    return {
        "ok": True,
        "current_version": "42.2.0",
        "channel": "browser-edition",
        "automatic_updates": False,
        "message": "Aggiornamenti automatici non ancora attivi. Usa il pacchetto Browser Edition aggiornato dalla release GitHub.",
    }
'''

MAIN_ROUTES = r'''
# ---------------------------------------------------------------------------
# v42.2.0 - System page APIs
# ---------------------------------------------------------------------------

@app.get("/api/system/status")
def system_status_api():
    return system_status_info(load_db())


@app.get("/api/system/version")
def system_version_api():
    return system_update_info()
'''

SYSTEM_PAGE = r'''
function SystemPage({ toast }) {
  const { data: status, refresh } = useApi('/system/status', {});
  const { data: version } = useApi('/system/version', {});

  const lanUrl = status?.lan_url || '';
  const localUrl = status?.local_url || '';
  const qrSvg = lanUrl
    ? `https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(lanUrl)}`
    : '';

  async function copy(text, label = 'Copiato') {
    try {
      await navigator.clipboard.writeText(text || '');
      toast(label);
    } catch {
      toast(text || 'Dato non disponibile');
    }
  }

  return <>
    <PageTitle
      title="Sistema"
      subtitle="Stato dell'app, accesso da smartphone, rete locale e informazioni di servizio."
      icon={Activity}
    />

    <div className="system-page-grid">
      <Card title="Stato applicazione" icon={Server} sub="Backend locale e ambiente runtime.">
        <div className="system-kpi-grid">
          <div><span>Edizione</span><b>{status.edition || '—'}</b></div>
          <div><span>Versione</span><b>{status.version || version.current_version || '—'}</b></div>
          <div><span>Porta</span><b>{status.port || '—'}</b></div>
          <div><span>Ora</span><b>{status.time || '—'}</b></div>
        </div>

        <div className="system-path-box">
          <span>Cartella runtime</span>
          <code>{status.cwd || '—'}</code>
        </div>

        <div className="quick-actions">
          <button className="ghost" onClick={refresh}><RefreshCw /> Aggiorna stato</button>
        </div>
      </Card>

      <Card title="Accesso mobile" icon={Smartphone} sub="Apri il gestionale da smartphone o tablet sulla stessa rete Wi-Fi.">
        <div className="lan-access-box">
          <div>
            <span>Da questo PC</span>
            <b>{localUrl || '—'}</b>
            <button className="ghost" onClick={() => copy(localUrl, 'Link locale copiato')}><Copy /> Copia</button>
          </div>

          <div>
            <span>Da smartphone / rete LAN</span>
            <b>{lanUrl || '—'}</b>
            <button className="primary" onClick={() => copy(lanUrl, 'Link LAN copiato')}><Copy /> Copia link LAN</button>
          </div>
        </div>

        {qrSvg && <div className="mobile-qr-box">
          <img src={qrSvg} alt="QR code accesso mobile MN Laser Lab" />
          <small>Scansiona il QR con lo smartphone collegato alla stessa rete Wi-Fi del PC.</small>
        </div>}
      </Card>

      <Card title="Database locale" icon={Database} sub="Conteggio rapido dei dati principali salvati.">
        <div className="system-counts">
          {Object.entries(status.db_counts || {}).map(([k, v]) => (
            <div key={k}>
              <span>{k}</span>
              <b>{v}</b>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Aggiornamenti" icon={DownloadCloud} sub="Base per il futuro update manager della Browser Edition.">
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
/* v42.2.0 system page / mobile QR */
.system-page-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(340px, .85fr);
  gap: 18px;
  align-items: start;
}

.system-page-grid > .card:nth-child(3),
.system-page-grid > .card:nth-child(4) {
  grid-column: span 1;
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


def append_once(path: Path, marker: str, code: str):
    s = path.read_text(encoding="utf-8")
    if marker not in s:
        s += "\n\n" + code.strip() + "\n"
        path.write_text(s, encoding="utf-8")


def patch_backend():
    append_once(LEGACY, "def system_status_info", BACKEND_HELPERS)
    append_once(MAIN, "def system_status_api", MAIN_ROUTES)
    print("Backend sistema/aggiornamenti base aggiunto.")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    if "function SystemPage" not in s:
        marker = "function App("
        idx = s.find(marker)
        if idx == -1:
            marker = "function Dashboard"
            idx = s.find(marker)
        if idx == -1:
            idx = 0
        s = s[:idx] + SYSTEM_PAGE + "\n\n" + s[idx:]

    # Aggancio menu/router con patch morbida: cerca una voce Impostazioni o Setup.
    if "id: 'system'" not in s and "'system'" not in s:
        replacements = [
            ("{ id: 'settings',", "{ id: 'system', label: 'Sistema', icon: Activity },\n    { id: 'settings',"),
            ("{id: 'settings',", "{id: 'system', label: 'Sistema', icon: Activity },\n    {id: 'settings',"),
            ("{ id: 'setup',", "{ id: 'system', label: 'Sistema', icon: Activity },\n    { id: 'setup',"),
            ("{id: 'setup',", "{id: 'system', label: 'Sistema', icon: Activity },\n    {id: 'setup',"),
        ]
        for old, new in replacements:
            if old in s:
                s = s.replace(old, new, 1)
                break

    # Aggancio render pagina.
    if "page === 'system'" not in s and "active === 'system'" not in s and "view === 'system'" not in s:
        render_patterns = [
            ("page === 'settings' &&", "page === 'system' && <SystemPage toast={toast} />}\n      {page === 'settings' &&"),
            ("active === 'settings' &&", "active === 'system' && <SystemPage toast={toast} />}\n      {active === 'settings' &&"),
            ("view === 'settings' &&", "view === 'system' && <SystemPage toast={toast} />}\n      {view === 'settings' &&"),
        ]
        for old, new in render_patterns:
            if old in s:
                s = s.replace(old, new, 1)
                break

    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend SystemPage inserito. Se non appare nel menu, faremo aggancio mirato sul router reale.")


def patch_css():
    append_once(CSS, "v42.2.0 system page", CSS_BLOCK)
    print("CSS sistema/QR aggiunto.")


def main():
    patch_backend()
    patch_frontend()
    patch_css()
    print("Patch v42.2.0 completata.")

if __name__ == "__main__":
    main()
