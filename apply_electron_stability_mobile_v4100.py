from pathlib import Path

ROOT = Path(__file__).resolve().parent
DESKTOP_MAIN = ROOT / "desktop" / "main.js"
CSS = ROOT / "frontend" / "src" / "style.css"


def patch_desktop_main():
    p = DESKTOP_MAIN
    s = p.read_text(encoding="utf-8")

    # 1) Migliora BrowserWindow: focus/input, popup, sicurezza ragionevole.
    if "v41.0.0 electron window stability" not in s:
        s = s.replace(
            "webPreferences: {",
            """webPreferences: {
      // v41.0.0 electron window stability
      nativeWindowOpen: true,
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: true,""",
            1
        )

    # 2) Gestione window.open: PDF e link non devono bloccare Electron.
    if "setWindowOpenHandler" not in s:
        insert = r'''

// v41.0.0 - Gestione popup/PDF in Electron.
// Evita che window.open blocchi o rompa la UI principale.
function installWindowOpenHandler(win) {
  if (!win || !win.webContents) return;

  win.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const { shell } = require("electron");

      // PDF/HTML generati dal backend locale: aprili in una nuova finestra Electron.
      if (
        url.startsWith("http://127.0.0.1:") ||
        url.startsWith("http://localhost:") ||
        url.includes("/api/quote-pdf/") ||
        url.includes("/api/quotes/")
      ) {
        return {
          action: "allow",
          overrideBrowserWindowOptions: {
            width: 980,
            height: 900,
            title: "Documento MN Laser Lab",
            autoHideMenuBar: true,
            webPreferences: {
              nativeWindowOpen: true,
              contextIsolation: true,
              nodeIntegration: false,
              webSecurity: true,
            },
          },
        };
      }

      // Link esterni: browser predefinito.
      shell.openExternal(url);
      return { action: "deny" };
    } catch (e) {
      console.error("Errore apertura popup:", e);
      return { action: "allow" };
    }
  });
}
'''
        # Inserisce prima di createWindow o app.whenReady.
        marker = "function createWindow"
        if marker in s:
            s = s.replace(marker, insert + "\n" + marker, 1)
        else:
            s += "\n" + insert

    # 3) Richiama installWindowOpenHandler(win) dentro createWindow dopo creazione win/mainWindow.
    if "installWindowOpenHandler(mainWindow)" not in s and "installWindowOpenHandler(win)" not in s:
        # Caso mainWindow = new BrowserWindow
        if "mainWindow = new BrowserWindow" in s:
            needle = "mainWindow = new BrowserWindow"
            pos = s.find(needle)
            # dopo il blocco BrowserWindow è difficile; inseriamo dopo loadURL se possibile
            if "mainWindow.loadURL" in s:
                s = s.replace("mainWindow.loadURL(APP_URL)", "mainWindow.loadURL(APP_URL)\n  installWindowOpenHandler(mainWindow)", 1)
            elif "mainWindow.loadFile" in s:
                s = s.replace("mainWindow.loadFile", "installWindowOpenHandler(mainWindow)\n  mainWindow.loadFile", 1)

        # Caso const win = new BrowserWindow
        if "const win = new BrowserWindow" in s and "installWindowOpenHandler(win)" not in s:
            if "win.loadURL(APP_URL)" in s:
                s = s.replace("win.loadURL(APP_URL)", "win.loadURL(APP_URL)\n  installWindowOpenHandler(win)", 1)
            elif "win.loadFile" in s:
                s = s.replace("win.loadFile", "installWindowOpenHandler(win)\n  win.loadFile", 1)

    # 4) DevTools opzionale per debug Electron.
    if "MN_DEBUG_ELECTRON" not in s:
        marker = "loadURL(APP_URL)"
        debug = '''
  if (process.env.MN_DEBUG_ELECTRON === "1") {
    try { mainWindow.webContents.openDevTools({ mode: "detach" }); } catch (e) {}
  }
'''
        if "mainWindow.loadURL(APP_URL)" in s:
            s = s.replace("mainWindow.loadURL(APP_URL)", "mainWindow.loadURL(APP_URL)" + debug, 1)

    p.write_text(s, encoding="utf-8")
    print("desktop/main.js patch Electron stabilità applicata")


def patch_css():
    p = CSS
    css = p.read_text(encoding="utf-8")

    if "/* v41.0.0 electron stability responsive */" not in css:
        css += r'''

/* v41.0.0 electron stability responsive */

/* Evita blocchi focus su Electron */
input,
textarea,
select,
button,
[contenteditable="true"] {
  -webkit-user-select: text;
  user-select: text;
  -webkit-app-region: no-drag;
}

button,
select,
input[type="button"],
input[type="submit"] {
  -webkit-user-select: none;
  user-select: none;
}

/* Modali sempre sopra, focus stabile */
.modal-back,
.detail-back,
.cmd-back,
.overlay,
.backdrop {
  z-index: 9000 !important;
}

.modal,
.detail-modal,
.cmd,
.popup,
.dialog {
  z-index: 9010 !important;
  pointer-events: auto !important;
}

.modal-back *,
.detail-back *,
.cmd-back * {
  pointer-events: auto;
}

/* Evita che backdrop invisibili blocchino input */
.hidden,
[hidden],
.modal-back[style*="display: none"],
.detail-back[style*="display: none"] {
  pointer-events: none !important;
}

/* PDF button e finestre documento */
.print-btn,
.print-button,
.print-actions {
  z-index: 99999 !important;
}

/* Card 4 categorie: configurazioni collegate scrollabile */
.catalog-config-card,
.config-linked-card,
.linked-config-card,
.setup-config-card {
  max-height: 620px;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  padding-right: 6px;
}

/* Fallback per la quarta colonna della gestione catalogo */
.catalog-board > *:nth-child(4),
.catalog-grid > *:nth-child(4),
.setup-catalog-grid > *:nth-child(4),
.category-manager-grid > *:nth-child(4) {
  max-height: 620px;
  overflow-y: auto !important;
  overflow-x: hidden !important;
}

/* Scrollbar più pulita */
.catalog-config-card::-webkit-scrollbar,
.config-linked-card::-webkit-scrollbar,
.linked-config-card::-webkit-scrollbar,
.setup-config-card::-webkit-scrollbar,
.catalog-board > *:nth-child(4)::-webkit-scrollbar,
.catalog-grid > *:nth-child(4)::-webkit-scrollbar {
  width: 8px;
}

.catalog-config-card::-webkit-scrollbar-thumb,
.config-linked-card::-webkit-scrollbar-thumb,
.linked-config-card::-webkit-scrollbar-thumb,
.setup-config-card::-webkit-scrollbar-thumb,
.catalog-board > *:nth-child(4)::-webkit-scrollbar-thumb,
.catalog-grid > *:nth-child(4)::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, .35);
  border-radius: 999px;
}

/* Responsive smartphone / LAN */
@media (max-width: 820px) {
  body {
    overflow-x: hidden;
  }

  .app,
  .layout,
  .shell {
    grid-template-columns: 1fr !important;
  }

  .sidebar {
    position: sticky;
    top: 0;
    z-index: 8000;
    width: 100% !important;
    max-width: none !important;
    height: auto !important;
    min-height: auto !important;
    border-right: 0 !important;
    border-bottom: 1px solid rgba(148, 163, 184, .16);
    overflow-x: auto;
  }

  .sidebar nav,
  .side-nav,
  .quick-nav {
    display: flex !important;
    flex-direction: row !important;
    gap: 8px;
    overflow-x: auto;
    padding-bottom: 8px;
  }

  .sidebar nav a,
  .sidebar nav button,
  .side-nav a,
  .side-nav button {
    flex: 0 0 auto;
    white-space: nowrap;
  }

  .main,
  main,
  .content {
    width: 100% !important;
    max-width: 100% !important;
    padding: 14px !important;
  }

  .hero,
  .page-title,
  .page-hero {
    padding: 20px !important;
    border-radius: 22px !important;
  }

  .hero h1,
  .page-title h1,
  .page-hero h1 {
    font-size: 34px !important;
    line-height: 1.02 !important;
  }

  .split-main,
  .settings-grid,
  .pdf-settings-layout,
  .buy-grid,
  .form-grid,
  .stats,
  .catalog-board,
  .catalog-grid,
  .setup-catalog-grid,
  .category-manager-grid {
    grid-template-columns: 1fr !important;
  }

  .card,
  .panel,
  .table-card {
    border-radius: 20px !important;
    padding: 16px !important;
  }

  .table-wrap {
    overflow-x: auto !important;
  }

  table {
    min-width: 680px;
  }

  .modal,
  .detail-modal {
    width: calc(100vw - 18px) !important;
    max-width: calc(100vw - 18px) !important;
    max-height: calc(100vh - 18px) !important;
    border-radius: 22px !important;
  }

  .modal-body,
  .detail-modal-body {
    max-height: calc(100vh - 120px) !important;
    overflow-y: auto !important;
    padding: 16px !important;
  }

  input,
  select,
  textarea {
    font-size: 16px !important; /* evita zoom automatico iPhone */
  }

  .quote-workflow-actions {
    flex-direction: column !important;
    align-items: stretch !important;
  }

  .quote-action,
  .workflow-action,
  .quote-workflow-actions button {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 520px) {
  .hero h1,
  .page-title h1,
  .page-hero h1 {
    font-size: 28px !important;
  }

  .stats {
    gap: 10px;
  }

  .stat {
    min-height: 94px;
  }

  .card-head,
  .panel-head {
    flex-direction: column;
    align-items: flex-start !important;
  }

  .card-head .actions,
  .panel-head .actions {
    width: 100%;
  }

  .card-head button,
  .panel-head button {
    width: 100%;
  }
}
'''
        p.write_text(css, encoding="utf-8")
        print("CSS Electron/mobile stabilità applicato")
    else:
        print("CSS v41.0.0 già presente")


def main():
    patch_desktop_main()
    patch_css()
    print("Patch v41.0.0 completata")


if __name__ == "__main__":
    main()
