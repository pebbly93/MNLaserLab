from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN_API = ROOT / "backend" / "app" / "main.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


BACKEND_HELPERS = r'''

# ---------------------------------------------------------------------------
# v40.3.0 - Backup avanzato e ripristino
# ---------------------------------------------------------------------------

def list_backups():
    root = user_data_dir()
    rows = []

    for p in sorted(root.glob("mn_laser_lab_*_*.db"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            stat = p.stat()
            rows.append({
                "filename": p.name,
                "path": str(p),
                "size": stat.st_size,
                "updated_at": datetime.fromtimestamp(stat.st_mtime).strftime("%d-%m-%Y %H:%M:%S"),
            })
        except Exception:
            pass

    return rows


def backup_database_named(name="manuale"):
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in str(name or "manuale").strip())
    safe = safe or "manuale"
    return backup_database(safe)


def restore_database_from_backup(filename):
    filename = str(filename or "").strip()
    if not filename:
        raise ValueError("Nome backup mancante")

    root = user_data_dir()
    source = root / filename

    if not source.exists() or source.suffix.lower() != ".db":
        raise ValueError("Backup non trovato")

    # Backup di sicurezza prima del ripristino.
    safety = backup_database("prima_ripristino")

    target = db_path()

    # Chiude eventuali connessioni indirette creando una copia atomica semplice.
    shutil.copy2(source, target)

    return {
        "ok": True,
        "restored": str(source),
        "safety_backup": safety,
        "db_path": str(target),
    }
'''


API_ENDPOINTS = r'''

@app.get("/api/maintenance/backups")
def maintenance_backups():
    return {"backups": list_backups()}


@app.post("/api/maintenance/backup-named")
def backup_named(payload: Payload):
    name = payload.data.get("name") or "manuale"
    return {"backup": backup_database_named(name), "backups": list_backups()}


@app.post("/api/maintenance/restore")
def restore_backup(payload: Payload):
    try:
        filename = payload.data.get("filename") or ""
        return restore_database_from_backup(filename)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
'''


def append_once(path: Path, marker: str, code: str):
    s = path.read_text(encoding="utf-8")
    if marker not in s:
        s += "\n\n" + code.strip() + "\n"
        path.write_text(s, encoding="utf-8")


def patch_backend():
    append_once(LEGACY, "def list_backups", BACKEND_HELPERS)
    append_once(MAIN_API, "def maintenance_backups", API_ENDPOINTS)
    print("Backend backup avanzato applicato.")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    start = s.find("function SettingsPage")
    end = s.find("\nfunction CommandPalette", start)

    if start == -1 or end == -1:
        raise RuntimeError("Funzione SettingsPage non trovata")

    new_settings = r'''function SettingsPage({ toast }) {
  const [info, setInfo] = useState({});
  const [msg, setMsg] = useState('');
  const [importText, setImportText] = useState('');
  const [backupName, setBackupName] = useState('backup manuale');
  const [backups, setBackups] = useState([]);

  async function loadInfo() {
    try {
      setInfo(await getJSON('/maintenance/info'));
    } catch(e) {
      setMsg(e.message || String(e));
    }
  }

  async function loadBackups() {
    try {
      const r = await getJSON('/maintenance/backups');
      setBackups(list(r.backups));
    } catch(e) {
      toast(e.message || String(e), 'err');
    }
  }

  useEffect(() => {
    loadInfo();
    loadBackups();
  }, []);

  async function backup() {
    try {
      const r = await postJSON('/maintenance/backup-named', { name: backupName || 'manuale' });
      setMsg(r.backup || 'Backup creato');
      toast('Backup creato');
      await loadInfo();
      await loadBackups();
    } catch(e) {
      toast(e.message, 'err');
    }
  }

  async function cleanup() {
    try {
      const r = await postJSON('/maintenance/cleanup', {});
      setMsg(r.backup || 'Pulizia completata');
      toast('Pulizia completata');
      await loadInfo();
      await loadBackups();
    } catch(e) {
      toast(e.message, 'err');
    }
  }

  async function resetDb() {
    if (!confirm('Vuoi davvero svuotare l’archivio? Verrà creato un backup prima del reset.')) return;

    try {
      const r = await postJSON('/maintenance/reset', {});
      setMsg(r.backup || 'Archivio resettato');
      toast('Archivio resettato');
      await loadInfo();
      await loadBackups();
    } catch(e) {
      toast(e.message, 'err');
    }
  }

  async function exportDb() {
    try {
      const r = await getJSON('/maintenance/export');
      downloadJson(r.filename || 'mn_laser_lab_export.json', r.data || {});
      toast('Export JSON scaricato');
    } catch(e) {
      toast(e.message, 'err');
    }
  }

  async function importDb() {
    try {
      const parsed = JSON.parse(importText);
      await postJSON('/maintenance/import', { data: parsed });
      setImportText('');
      toast('Archivio importato');
      await loadInfo();
      await loadBackups();
    } catch(e) {
      toast('JSON non valido o import non riuscito: ' + (e.message || e), 'err');
    }
  }

  async function restoreBackup(filename) {
    if (!confirm(`Ripristinare il backup "${filename}"? Verrà creato un backup di sicurezza prima del ripristino.`)) return;

    try {
      const r = await postJSON('/maintenance/restore', { filename });
      setMsg(`Ripristinato: ${r.restored}\nBackup sicurezza: ${r.safety_backup}`);
      toast('Backup ripristinato. Ricarica l’app per vedere i dati aggiornati.');
      await loadInfo();
      await loadBackups();
    } catch(e) {
      toast(e.message, 'err');
    }
  }

  function backupSize(bytes) {
    const n = Number(bytes || 0);
    if (n > 1024 * 1024) return `${(n / 1024 / 1024).toFixed(2)} MB`;
    if (n > 1024) return `${(n / 1024).toFixed(1)} KB`;
    return `${n} B`;
  }

  return <>
    <PageTitle title="Impostazioni" desc="Backup, ripristino, export, import e manutenzione dell’archivio." />

    <div className="settings-grid">
      <Card title="Stato archivio" icon={ShieldCheck}>
        <div className="settings-info">
          <span>Database</span><b>{info.db_path || '—'}</b>
          <span>Cartella dati</span><b>{info.data_dir || '—'}</b>
          <span>Ultimo controllo</span><b>{info.checked_at || '—'}</b>
        </div>
      </Card>

      <Card title="Backup manuale" icon={Archive}>
        <div className="backup-create-row">
          <Input label="Nome backup" value={backupName} onChange={e => setBackupName(e.target.value)} />
          <button className="primary" onClick={backup}><Archive /> Crea backup</button>
        </div>

        <div className="settings-actions compact">
          <button onClick={exportDb}><Download /> Esporta JSON</button>
          <button onClick={cleanup}><RefreshCcw /> Ripulisci archivio</button>
          <button className="danger" onClick={resetDb}><Trash2 /> Reset archivio</button>
        </div>

        {msg && <pre>{msg}</pre>}
      </Card>
    </div>

    <Card title="Backup disponibili" icon={Database} action={<button className="ghost" onClick={loadBackups}><RefreshCcw /> Aggiorna</button>}>
      <div className="backup-list">
        {backups.length ? backups.map(b => <div key={b.filename} className="backup-row">
          <div>
            <b>{b.filename}</b>
            <small>{b.updated_at} · {backupSize(b.size)}</small>
          </div>
          <button className="ghost" onClick={() => restoreBackup(b.filename)}>Ripristina</button>
        </div>) : <Empty text="Nessun backup trovato" />}
      </div>
    </Card>

    <Card title="Import archivio JSON" icon={Upload}>
      <textarea className="import-box" value={importText} onChange={e=>setImportText(e.target.value)} placeholder="Incolla qui il JSON da importare..." />
      <div className="quick-actions">
        <button className="primary" onClick={importDb}><FileJson /> Importa dati</button>
        <button className="ghost" onClick={()=>setImportText('')}>Svuota campo</button>
      </div>
    </Card>
  </>;
}'''

    s = s[:start] + new_settings + "\n\n" + s[end + 1:]
    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend impostazioni backup avanzato applicato.")


def patch_css():
    css = CSS.read_text(encoding="utf-8")

    if "/* v40.3 advanced backup */" not in css:
        css += r'''

/* v40.3 advanced backup */
.backup-create-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: end;
}

.settings-actions.compact {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.backup-list {
  display: grid;
  gap: 10px;
}

.backup-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  border-radius: 18px;
  padding: 13px 14px;
}

.backup-row b,
.backup-row small {
  display: block;
  min-width: 0;
}

.backup-row b {
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.backup-row small {
  color: var(--muted);
  margin-top: 4px;
}

@media (max-width: 720px) {
  .backup-create-row,
  .backup-row {
    grid-template-columns: 1fr;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")


def main():
    patch_backend()
    patch_frontend()
    patch_css()
    print("Patch v40.3.0 backup avanzato completata.")


if __name__ == "__main__":
    main()
