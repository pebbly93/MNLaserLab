from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN_API = ROOT / "backend" / "app" / "main.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


BACKEND_CODE = r'''

# ---------------------------------------------------------------------------
# v40.4.0 - Import CSV acquisti
# ---------------------------------------------------------------------------

def import_purchase_rows(db, rows):
    if not isinstance(rows, list):
        raise ValueError("Formato import non valido")

    backup = backup_database("prima_import_csv_acquisti")
    imported = 0
    errors = []

    aliases = {
        "area": ["area", "section", "sezione"],
        "category": ["categoria", "category"],
        "subcategory": ["sottocategoria", "subcategory", "variante"],
        "size": ["formato", "tipo", "size"],
        "thickness": ["spessore", "thickness"],
        "unit": ["unita", "unità", "unit"],
        "supplier": ["fornitore", "supplier"],
        "quantity": ["quantita", "quantità", "qty", "quantity"],
        "total_cost": ["costo_totale", "costo totale", "total_cost", "totale"],
    }

    def pick(row, key, default=""):
        for name in aliases.get(key, [key]):
            if name in row:
                return row.get(name, default)
        return default

    for idx, row in enumerate(rows, start=1):
        try:
            if not isinstance(row, dict):
                raise ValueError("Riga non valida")

            payload = {
                "section": pick(row, "area") or section_label(db, "materials"),
                "category": pick(row, "category"),
                "subcategory": pick(row, "subcategory"),
                "size": pick(row, "size"),
                "thickness": pick(row, "thickness"),
                "unit": pick(row, "unit") or "pz",
                "supplier": pick(row, "supplier") or "Senza fornitore",
                "quantity": pick(row, "quantity"),
                "total_cost": pick(row, "total_cost"),
            }

            add_purchase(db, payload)
            imported += 1

        except Exception as exc:
            errors.append({
                "row": idx,
                "error": str(exc),
                "data": row,
            })

    return {
        "ok": not errors,
        "imported": imported,
        "errors": errors,
        "backup": backup,
    }
'''


API_CODE = r'''

@app.post("/api/maintenance/import-purchases")
def import_purchases_api(payload: Payload):
    try:
        rows = payload.data.get("rows", [])
        return mutate(import_purchase_rows, rows)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
'''


def append_once(path: Path, marker: str, code: str):
    s = path.read_text(encoding="utf-8")
    if marker not in s:
        s += "\n\n" + code.strip() + "\n"
        path.write_text(s, encoding="utf-8")


def patch_backend():
    append_once(LEGACY, "def import_purchase_rows", BACKEND_CODE)
    append_once(MAIN_API, "def import_purchases_api", API_CODE)
    print("Backend import CSV acquisti applicato.")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    if "function parseCsvPurchases" not in s:
        marker = "function downloadJson(filename, data)"
        helper = r'''
function parseCsvPurchases(text) {
  const raw = String(text || '').trim();
  if (!raw) return [];

  const lines = raw.split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) return [];

  function splitCsvLine(line) {
    const out = [];
    let cur = '';
    let quote = false;

    for (let i = 0; i < line.length; i++) {
      const ch = line[i];

      if (ch === '"') {
        if (quote && line[i + 1] === '"') {
          cur += '"';
          i++;
        } else {
          quote = !quote;
        }
      } else if ((ch === ',' || ch === ';') && !quote) {
        out.push(cur.trim());
        cur = '';
      } else {
        cur += ch;
      }
    }

    out.push(cur.trim());
    return out;
  }

  const headers = splitCsvLine(lines[0]).map(h => h.trim().toLowerCase());
  return lines.slice(1).map((line, index) => {
    const values = splitCsvLine(line);
    const row = { _row: index + 2 };

    headers.forEach((h, i) => {
      row[h] = values[i] ?? '';
    });

    return row;
  });
}

'''
        if marker not in s:
            raise RuntimeError("Punto inserimento helper CSV non trovato")
        s = s.replace(marker, helper + marker, 1)

    start = s.find("function SettingsPage")
    end = s.find("\nfunction CommandPalette", start)

    if start == -1 or end == -1:
        raise RuntimeError("SettingsPage non trovata")

    old_settings = s[start:end]

    if "csvText" not in old_settings:
        old_settings = old_settings.replace(
            "const [backups, setBackups] = useState([]);",
            "const [backups, setBackups] = useState([]);\n  const [csvText, setCsvText] = useState('');\n  const [csvPreview, setCsvPreview] = useState([]);"
        )

        insert_after_import = r'''
  function previewCsv() {
    const rows = parseCsvPurchases(csvText);
    setCsvPreview(rows);
    if (!rows.length) {
      toast('Nessuna riga valida nel CSV', 'err');
    } else {
      toast(`${rows.length} righe pronte per import`);
    }
  }

  async function importPurchasesCsv() {
    const rows = csvPreview.length ? csvPreview : parseCsvPurchases(csvText);

    if (!rows.length) {
      toast('Nessuna riga da importare', 'err');
      return;
    }

    if (!confirm(`Importare ${rows.length} righe acquisto? Verrà creato un backup automatico prima dell’import.`)) return;

    try {
      const r = await postJSON('/maintenance/import-purchases', { rows });
      setMsg(`Importate: ${r.imported}\nErrori: ${list(r.errors).length}\nBackup: ${r.backup}`);

      if (list(r.errors).length) {
        toast(`Import completato con ${list(r.errors).length} errori`, 'err');
      } else {
        toast('Import acquisti completato');
        setCsvText('');
        setCsvPreview([]);
      }

      await loadInfo();
      await loadBackups();
    } catch(e) {
      toast(e.message, 'err');
    }
  }

'''
        point = old_settings.find("  function backupSize(bytes)")
        if point == -1:
            raise RuntimeError("Punto inserimento funzioni CSV non trovato")
        old_settings = old_settings[:point] + insert_after_import + old_settings[point:]

        import_card = r'''
    <Card title="Import CSV acquisti" icon={Upload}>
      <div className="csv-import-grid">
        <div>
          <textarea
            className="import-box"
            value={csvText}
            onChange={e => setCsvText(e.target.value)}
            placeholder={'area,categoria,sottocategoria,formato,spessore,unita,fornitore,quantita,costo_totale\nFalegnameria,Legname,Betulla,20x20,2 mm,pz,Fornitore,10,25'}
          />
          <div className="quick-actions">
            <button className="ghost" onClick={previewCsv}><Search /> Anteprima</button>
            <button className="primary" onClick={importPurchasesCsv}><Upload /> Importa acquisti</button>
            <button className="ghost" onClick={() => { setCsvText(''); setCsvPreview([]); }}>Svuota</button>
          </div>
        </div>

        <div className="csv-preview">
          <b>Anteprima</b>
          {csvPreview.length ? csvPreview.slice(0, 8).map((r, i) => <div key={i} className="csv-preview-row">
            <span>{r.area || r.sezione || 'Area'}</span>
            <strong>{r.categoria || r.category || 'Categoria'}</strong>
            <small>{[r.sottocategoria, r.formato, r.spessore, r.quantita || r.quantità, r.costo_totale].filter(Boolean).join(' · ')}</small>
          </div>) : <Empty text="Nessuna anteprima" />}
        </div>
      </div>
    </Card>

'''
        target = """    <Card title="Import archivio JSON" icon={Upload}>"""
        if target not in old_settings:
            raise RuntimeError("Card import JSON non trovata")
        old_settings = old_settings.replace(target, import_card + target, 1)

    s = s[:start] + old_settings + s[end:]
    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend import CSV acquisti applicato.")


def patch_css():
    css = CSS.read_text(encoding="utf-8")
    if "/* v40.4 csv purchase import */" not in css:
        css += r'''

/* v40.4 csv purchase import */
.csv-import-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(320px, .85fr);
  gap: 16px;
  align-items: start;
}

.csv-preview {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  border-radius: 18px;
  padding: 14px;
  display: grid;
  gap: 9px;
  max-height: 420px;
  overflow-y: auto;
}

.csv-preview > b {
  display: block;
  margin-bottom: 4px;
}

.csv-preview-row {
  border: 1px solid rgba(148, 163, 184, .14);
  background: rgba(2, 6, 23, .14);
  border-radius: 14px;
  padding: 10px;
  display: grid;
  gap: 3px;
}

.csv-preview-row span {
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .06em;
}

.csv-preview-row strong {
  line-height: 1.2;
}

.csv-preview-row small {
  color: var(--muted);
  line-height: 1.35;
}

@media (max-width: 900px) {
  .csv-import-grid {
    grid-template-columns: 1fr;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")


def main():
    patch_backend()
    patch_frontend()
    patch_css()
    print("Patch v40.4.0 import CSV acquisti completata.")


if __name__ == "__main__":
    main()
