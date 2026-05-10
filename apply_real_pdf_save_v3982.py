from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN_API = ROOT / "backend" / "app" / "main.py"
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
DESKTOP_MAIN = ROOT / "desktop" / "main.js"
PRELOAD = ROOT / "desktop" / "preload.js"


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"Blocco non trovato: {label}")
    return text.replace(old, new, 1)


BACKEND_FIX = r'''

# ---------------------------------------------------------------------------
# v39.8.2 - Ricerca robusta preventivi per PDF
# ---------------------------------------------------------------------------

def get_quote_flexible(db, quote_id):
    quotes = db.get("quotes", []) or []

    for q in quotes:
        if str(q.get("id", "")) == str(quote_id):
            return q

    # fallback: alcune versioni vecchie possono avere id salvati come indice/stringa
    try:
        idx = int(str(quote_id))
        if 0 <= idx < len(quotes):
            return quotes[idx]
    except Exception:
        pass

    # fallback: se arriva un id parziale o codificato diversamente
    qid = str(quote_id or "").strip()
    for q in quotes:
        current = str(q.get("id", "")).strip()
        if current and (current.endswith(qid) or qid.endswith(current)):
            return q

    raise ValueError("Preventivo non trovato")
'''


API_FIX = r'''

@app.get("/api/quote-pdf/customer", response_class=HTMLResponse)
def quote_customer_pdf_query_api(id: str):
    try:
        db = load_db()
        quote = get_quote_flexible(db, id)
        return HTMLResponse(quote_customer_html(db, quote.get("id", id)))
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@app.get("/api/quote-pdf/internal", response_class=HTMLResponse)
def quote_internal_pdf_query_api(id: str):
    try:
        db = load_db()
        quote = get_quote_flexible(db, id)
        return HTMLResponse(quote_internal_html(db, quote.get("id", id)))
    except ValueError as exc:
        raise HTTPException(404, str(exc))
'''


def patch_backend():
    s = LEGACY.read_text(encoding="utf-8")
    if "def get_quote_flexible" not in s:
        s += "\n\n" + BACKEND_FIX.strip() + "\n"
    LEGACY.write_text(s, encoding="utf-8")

    m = MAIN_API.read_text(encoding="utf-8")
    if "quote_customer_pdf_query_api" not in m:
        # Serve HTMLResponse importato: se già presente non fa nulla.
        if "from fastapi.responses import HTMLResponse" not in m:
            m = m.replace(
                "from fastapi import FastAPI, HTTPException",
                "from fastapi import FastAPI, HTTPException\nfrom fastapi.responses import HTMLResponse"
            )
        m += "\n\n" + API_FIX.strip() + "\n"

    MAIN_API.write_text(m, encoding="utf-8")
    print("Backend PDF robusto applicato.")


def patch_preload():
    if not PRELOAD.exists():
        PRELOAD.write_text("", encoding="utf-8")

    s = PRELOAD.read_text(encoding="utf-8")

    if "saveQuotePdf" not in s:
        if "contextBridge" not in s:
            s = """const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("mnLaserLab", {
  appVersion: () => ipcRenderer.invoke("app-version"),
  checkForUpdates: () => ipcRenderer.invoke("check-for-updates"),
  saveQuotePdf: (payload) => ipcRenderer.invoke("save-quote-pdf", payload)
});
"""
        else:
            # Prova ad aggiungere la funzione dentro un oggetto già esposto.
            s = re.sub(
                r"(checkForUpdates\s*:\s*\(\)\s*=>\s*ipcRenderer\.invoke\([\"']check-for-updates[\"']\)\s*,?)",
                r"\1\n  saveQuotePdf: (payload) => ipcRenderer.invoke(\"save-quote-pdf\", payload),",
                s,
                count=1
            )

            if "saveQuotePdf" not in s:
                s += """

try {
  contextBridge.exposeInMainWorld("mnLaserLabPdf", {
    saveQuotePdf: (payload) => ipcRenderer.invoke("save-quote-pdf", payload)
  });
} catch (_) {}
"""

    PRELOAD.write_text(s, encoding="utf-8")
    print("Preload PDF applicato.")


def patch_desktop_main():
    s = DESKTOP_MAIN.read_text(encoding="utf-8")

    # Aggiunge BrowserWindow già importato? main.js ha già BrowserWindow.
    if "ipcMain.handle(\"save-quote-pdf\"" not in s:
        insert = r'''
ipcMain.handle("save-quote-pdf", async (_event, payload) => {
  const url = payload && payload.url;
  const defaultName = payload && payload.defaultName ? payload.defaultName : "preventivo.pdf";

  if (!url) {
    return { ok: false, error: "URL PDF mancante" };
  }

  try {
    const targetWindow = mainWindow || BrowserWindow.getFocusedWindow();

    const result = await dialog.showSaveDialog(targetWindow, {
      title: "Salva preventivo PDF",
      defaultPath: defaultName,
      filters: [
        { name: "PDF", extensions: ["pdf"] }
      ]
    });

    if (result.canceled || !result.filePath) {
      return { ok: false, canceled: true };
    }

    const pdfWindow = new BrowserWindow({
      show: false,
      width: 1240,
      height: 1754,
      webPreferences: {
        sandbox: false,
        nodeIntegration: false,
        contextIsolation: true
      }
    });

    await pdfWindow.loadURL(url);

    const pdfData = await pdfWindow.webContents.printToPDF({
      printBackground: true,
      landscape: false,
      marginsType: 0,
      pageSize: "A4"
    });

    fs.writeFileSync(result.filePath, pdfData);
    pdfWindow.close();

    return { ok: true, path: result.filePath };
  } catch (err) {
    return { ok: false, error: err && err.message ? err.message : String(err) };
  }
});
'''

        marker = 'ipcMain.handle("check-for-updates", async () => {'
        idx = s.find(marker)
        if idx == -1:
            # fallback: prima di app.whenReady
            idx = s.find("app.whenReady")
            if idx == -1:
                raise RuntimeError("Punto inserimento IPC PDF non trovato in desktop/main.js")
            s = s[:idx] + insert + "\n\n" + s[idx:]
        else:
            s = s[:idx] + insert + "\n\n" + s[idx:]

    DESKTOP_MAIN.write_text(s, encoding="utf-8")
    print("Desktop main PDF applicato.")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    # Sostituisce funzione openQuotePdf con versione Electron save dialog + fallback browser.
    pattern = re.compile(
        r"  function openQuotePdf\(q, type = 'customer'\) \{[\s\S]*?\n  \}",
        re.MULTILINE
    )

    new_func = r'''  async function openQuotePdf(q, type = 'customer') {
    if (!q?.id) {
      toast('Salva prima il preventivo', 'err');
      return;
    }

    const backendBase =
      window.location.protocol === 'file:'
        ? 'http://127.0.0.1:8000'
        : window.location.origin.includes('5173')
          ? 'http://127.0.0.1:8000'
          : window.location.origin;

    const url = `${backendBase}/api/quote-pdf/${type}?id=${encodeURIComponent(q.id)}`;
    const cleanName = String(q.name || 'preventivo')
      .replace(/[^\w\d\-_\s]/g, '')
      .trim()
      .replace(/\s+/g, '_');

    const defaultName = `${type === 'customer' ? 'Preventivo_cliente' : 'Preventivo_interno'}_${cleanName || q.id}.pdf`;

    const api = window.mnLaserLab || window.mnLaserLabPdf;

    if (api?.saveQuotePdf) {
      const result = await api.saveQuotePdf({ url, defaultName });

      if (result?.ok) {
        toast(`PDF salvato: ${result.path}`);
        return;
      }

      if (result?.canceled) {
        toast('Salvataggio annullato');
        return;
      }

      toast(result?.error || 'Salvataggio PDF non riuscito', 'err');
      return;
    }

    const popup = window.open(url, '_blank');

    if (!popup) {
      window.location.href = url;
    }
  }'''

    if "api.saveQuotePdf" not in s:
        match = pattern.search(s)
        if not match:
            raise RuntimeError("Funzione openQuotePdf non trovata nel frontend")
        s = s[:match.start()] + new_func + s[match.end():]

    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend PDF save applicato.")


def main():
    patch_backend()
    patch_preload()
    patch_desktop_main()
    patch_frontend()
    print("Patch v39.8.2 salvataggio PDF reale completata.")


if __name__ == "__main__":
    main()
