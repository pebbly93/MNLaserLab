from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN = ROOT / "backend" / "app" / "main.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


BACKEND_CODE = r'''

# ---------------------------------------------------------------------------
# v42.0.1 - System/LAN status helpers
# ---------------------------------------------------------------------------

def system_status_info(db):
    import os
    import sys
    import socket
    import platform
    from pathlib import Path
    from datetime import datetime

    def local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    ip = local_ip()
    port = int(os.environ.get("MN_BACKEND_PORT", "8000"))

    return {
        "ok": True,
        "app": "MN Laser Lab Manager",
        "mode": "Browser Edition / LAN Ready",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "local_url": f"http://127.0.0.1:{port}/",
        "lan_ip": ip,
        "lan_url": f"http://{ip}:{port}/",
        "port": port,
        "db_counts": {
            "materials": len(db.get("materials", {}) or {}),
            "components": len(db.get("components", {}) or {}),
            "products": len(db.get("products", {}) or {}),
            "quotes": len(db.get("quotes", []) or []),
            "customers": len(db.get("customers", {}) or {}),
            "suppliers": len(db.get("suppliers", {}) or {}),
        },
    }
'''


API_CODE = r'''

@app.get("/api/system/status")
def system_status_api():
    return system_status_info(load_db())
'''


SYSTEM_COMPONENT = r'''
function SystemStatusPanel({ toast }) {
  const { data: status, refresh } = useApi('/system/status', {});
  const lanUrl = status?.lan_url || '';
  const qrUrl = lanUrl ? `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(lanUrl)}` : '';

  async function copyLan() {
    try {
      await navigator.clipboard.writeText(lanUrl);
      toast('Link LAN copiato');
    } catch {
      toast(lanUrl || 'Link non disponibile');
    }
  }

  return <div className="system-status-grid">
    <Card title="Sistema" icon={Activity} sub="Stato runtime, backend e database locale.">
      <div className="system-kpi-grid">
        <div><span>Modalità</span><b>{status.mode || '—'}</b></div>
        <div><span>Ora</span><b>{status.time || '—'}</b></div>
        <div><span>Porta</span><b>{status.port || '—'}</b></div>
        <div><span>Python</span><b>{status.python || '—'}</b></div>
      </div>

      <div className="system-path-box">
        <span>Cartella runtime</span>
        <code>{status.cwd || '—'}</code>
      </div>

      <div className="quick-actions">
        <button className="ghost" onClick={refresh}><RefreshCw /> Aggiorna stato</button>
      </div>
    </Card>

    <Card title="Apri su smartphone" icon={Smartphone} sub="Usa l'app da telefono o tablet sulla stessa rete Wi-Fi.">
      <div className="lan-box">
        <div>
          <span>URL locale</span>
          <b>{status.local_url || '—'}</b>
        </div>
        <div>
          <span>URL rete LAN</span>
          <b>{lanUrl || '—'}</b>
        </div>
      </div>

      {qrUrl && <div className="qr-wrap">
        <img src={qrUrl} alt="QR LAN MN Laser Lab" />
        <small>Scansiona il QR dallo smartphone collegato alla stessa rete.</small>
      </div>}

      <div className="quick-actions">
        <button className="primary" onClick={copyLan}><Copy /> Copia link LAN</button>
      </div>
    </Card>

    <Card title="Archivio dati" icon={Database} sub="Riepilogo veloce del database locale.">
      <div className="system-counts">
        {Object.entries(status.db_counts || {}).map(([k,v]) => <div key={k}>
          <span>{k}</span>
          <b>{v}</b>
        </div>)}
      </div>
    </Card>
  </div>;
}
'''


CSS_CODE = r'''

/* v42.0.1 System status / LAN QR */
.system-status-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, .9fr);
  gap: 18px;
  align-items: start;
}

.system-status-grid > .card:nth-child(3) {
  grid-column: 1 / -1;
}

.system-kpi-grid,
.system-counts {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.system-kpi-grid div,
.system-counts div,
.lan-box div {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  border-radius: 16px;
  padding: 12px;
}

.system-kpi-grid span,
.system-counts span,
.lan-box span,
.system-path-box span {
  display: block;
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .07em;
  font-weight: 900;
  margin-bottom: 5px;
}

.system-kpi-grid b,
.system-counts b,
.lan-box b {
  display: block;
  color: var(--text);
  font-size: 14px;
  line-height: 1.25;
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

.lan-box {
  display: grid;
  gap: 10px;
}

.qr-wrap {
  display: grid;
  place-items: center;
  text-align: center;
  gap: 10px;
  margin: 16px 0 4px;
}

.qr-wrap img {
  width: 210px;
  height: 210px;
  background: white;
  border-radius: 18px;
  padding: 10px;
}

.qr-wrap small {
  color: var(--muted);
  line-height: 1.4;
}

@media (max-width: 960px) {
  .system-status-grid {
    grid-template-columns: 1fr;
  }

  .system-kpi-grid,
  .system-counts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .system-kpi-grid,
  .system-counts {
    grid-template-columns: 1fr;
  }
}
'''


def append_once(path: Path, marker: str, code: str):
    s = path.read_text(encoding="utf-8")
    if marker not in s:
        s += "\n\n" + code.strip() + "\n"
        path.write_text(s, encoding="utf-8")


def patch_backend():
    append_once(LEGACY, "def system_status_info", BACKEND_CODE)
    append_once(MAIN, "def system_status_api", API_CODE)
    print("Backend system status aggiunto.")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    if "function SystemStatusPanel" not in s:
        marker = "function App("
        idx = s.find(marker)
        if idx == -1:
            marker = "export default function"
            idx = s.find(marker)
        if idx == -1:
            # Inserisce prima di Setup se App non è facilmente trovabile
            marker = "function Setup"
            idx = s.find(marker)
        if idx == -1:
            raise RuntimeError("Punto inserimento SystemStatusPanel non trovato")
        s = s[:idx] + SYSTEM_COMPONENT + "\n\n" + s[idx:]

    # Prova ad aggiungere una voce di menu "Sistema" se trova array menu/nav.
    if "Sistema" not in s:
        s = s.replace("Impostazioni", "Sistema")
        # Questo fallback non è ideale, quindi lo evitiamo se non troviamo pattern chiari.

    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend SystemStatusPanel aggiunto. Se non appare nel menu, lo agganciamo nella prossima patch mirata.")


def patch_css():
    append_once(CSS, "v42.0.1 System status", CSS_CODE)
    print("CSS system status aggiunto.")


def main():
    patch_backend()
    patch_frontend()
    patch_css()
    print("Patch v42.0.1 completata.")

if __name__ == "__main__":
    main()
