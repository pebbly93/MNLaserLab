const { app, BrowserWindow, dialog, ipcMain, Menu } = require("electron");
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");

let mainWindow = null;
let backendProcess = null;


// v40.9.3 - LAN mode.
// Backend FastAPI ascolta su 0.0.0.0, ma Electron apre l'app su 127.0.0.1.
process.env.MN_BACKEND_HOST = process.env.MN_BACKEND_HOST || "0.0.0.0";
process.env.MN_BACKEND_PORT = process.env.MN_BACKEND_PORT || "8000";

const PORT = process.env.MN_BACKEND_PORT || "8000";
const APP_URL = `http://127.0.0.1:${PORT}/`;
const HEALTH_URL = `http://127.0.0.1:${PORT}/api/health`;

function isPackaged() {
  return app.isPackaged;
}

function resourcePath(...parts) {
  if (isPackaged()) {
    return path.join(process.resourcesPath, ...parts);
  }

  return path.join(__dirname, ...parts);
}

function appAssetPath(...parts) {
  return path.join(__dirname, "assets", ...parts);
}

function appIconPath() {
  return appAssetPath("mn_laser_lab_logo.ico");
}

function backendExecutablePath() {
  const exeName =
    process.platform === "win32"
      ? "MN_Laser_Lab_Backend.exe"
      : "MN_Laser_Lab_Backend";

  return resourcePath("backend", exeName);
}

function frontendDistPath() {
  return resourcePath("frontend");
}

function frontendIndexPath() {
  if (isPackaged()) {
    return path.join(process.resourcesPath, "frontend", "index.html");
  }

  return path.join(__dirname, "..", "frontend", "dist", "index.html");
}

function userDataDir() {
  return path.join(app.getPath("userData"), "data");
}

function logDir() {
  const dir = path.join(app.getPath("userData"), "logs");
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function writeLog(message) {
  try {
    const file = path.join(logDir(), "desktop.log");
    const line = `[${new Date().toISOString()}] ${message}\n`;
    fs.appendFileSync(file, line, "utf8");
  } catch (_) {}
}

function checkPackagedResources() {
  const backendExe = backendExecutablePath();
  const frontendIndex = frontendIndexPath();
  const icon = appIconPath();

  writeLog(`app.isPackaged: ${isPackaged()}`);
  writeLog(`process.resourcesPath: ${process.resourcesPath}`);
  writeLog(`Backend path: ${backendExe}`);
  writeLog(`Frontend folder: ${frontendDistPath()}`);
  writeLog(`Frontend index: ${frontendIndex}`);
  writeLog(`App icon: ${icon}`);

  if (isPackaged()) {
    if (!fs.existsSync(backendExe)) {
      return {
        ok: false,
        message: `Backend non trovato:\n${backendExe}`
      };
    }

    if (!fs.existsSync(frontendIndex)) {
      return {
        ok: false,
        message:
          `Frontend non trovato:\n${frontendIndex}\n\n` +
          "Manca index.html nella cartella resources/frontend."
      };
    }
  }

  if (!fs.existsSync(icon)) {
    writeLog(`Icona non trovata: ${icon}`);
  }

  return { ok: true };
}

function startBackend() {
  const frontendPath = frontendDistPath();
  const dataPath = userDataDir();

  fs.mkdirSync(dataPath, { recursive: true });

  const env = {
    ...process.env,
    MN_BACKEND_PORT: PORT,
    MN_DESKTOP_DIST: frontendPath,
    MN_USER_DATA_DIR: dataPath
  };

  writeLog(`MN_BACKEND_PORT=${PORT}`);
  writeLog(`MN_DESKTOP_DIST=${frontendPath}`);
  writeLog(`MN_USER_DATA_DIR=${dataPath}`);

  if (isPackaged()) {
    const exe = backendExecutablePath();

    if (!fs.existsSync(exe)) {
      dialog.showErrorBox("Backend non trovato", `Non trovo il backend:\n${exe}`);
      return false;
    }

    const stdoutLog = fs.openSync(path.join(logDir(), "backend.stdout.log"), "a");
    const stderrLog = fs.openSync(path.join(logDir(), "backend.stderr.log"), "a");

    backendProcess = spawn(exe, [], {
      env,
      windowsHide: true,
      stdio: ["ignore", stdoutLog, stderrLog]
    });
  } else {
    const backendDir = path.join(__dirname, "..", "backend");
    const script = path.join(backendDir, "desktop_server.py");

    backendProcess = spawn("python", [script], {
      cwd: backendDir,
      env,
      windowsHide: true,
      stdio: "inherit"
    });
  }

  backendProcess.on("error", (err) => {
    writeLog(`Backend spawn error: ${err.message}`);
    dialog.showErrorBox("Errore backend", err.message);
  });

  backendProcess.on("exit", (code) => {
    writeLog(`Backend terminato con codice ${code}`);
  });

  return true;
}

async function waitForBackend(timeoutMs = 30000) {
  const start = Date.now();

  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(HEALTH_URL);

      if (res.ok) {
        writeLog("Backend pronto.");
        return true;
      }
    } catch (_) {}

    await new Promise((resolve) => setTimeout(resolve, 400));
  }

  writeLog("Timeout attesa backend.");
  return false;
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function createErrorHtml(title, details) {
  const safeTitle = escapeHtml(title);
  const safeDetails = escapeHtml(details);

  return `
    <!doctype html>
    <html lang="it">
      <head>
        <meta charset="utf-8" />
        <title>MN Laser Lab Manager - Errore</title>
        <style>
          body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: radial-gradient(circle at top, #17333a, #061214 60%);
            color: #f8fafc;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          .box {
            width: min(820px, calc(100vw - 48px));
            background: rgba(15, 23, 42, 0.88);
            border: 1px solid rgba(148, 163, 184, 0.35);
            border-radius: 24px;
            padding: 28px;
            box-shadow: 0 24px 80px rgba(0, 0, 0, 0.45);
          }
          h1 {
            margin: 0 0 12px;
            font-size: 26px;
          }
          p {
            color: #cbd5e1;
            line-height: 1.5;
          }
          pre {
            white-space: pre-wrap;
            background: rgba(2, 6, 23, 0.65);
            padding: 16px;
            border-radius: 14px;
            color: #e2e8f0;
            overflow: auto;
            max-height: 360px;
          }
          button {
            margin-top: 14px;
            border: 0;
            padding: 12px 18px;
            border-radius: 12px;
            background: #22d3ee;
            color: #061214;
            font-weight: 700;
            cursor: pointer;
          }
        </style>
      </head>
      <body>
        <div class="box">
          <h1>${safeTitle}</h1>
          <p>L'app non è riuscita a caricare correttamente l'interfaccia.</p>
          <pre>${safeDetails}</pre>
          <button onclick="location.reload()">Riprova</button>
        </div>
      </body>
    </html>
  `;
}

function loadErrorPage(title, details) {
  if (!mainWindow) return;

  mainWindow.loadURL(
    "data:text/html;charset=utf-8," +
      encodeURIComponent(createErrorHtml(title, details))
  );
}

function createWindow(backendReady) {
  const iconPath = appIconPath();

  mainWindow = new BrowserWindow({
    width: 1360,
    height: 900,
    minWidth: 1120,
    minHeight: 720,
    title: "MN Laser Lab Manager",
    backgroundColor: "#061214",
    icon: iconPath,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  mainWindow.webContents.on("before-input-event", (event, input) => {
    const key = String(input.key || "").toLowerCase();

    if (
      input.key === "F12" ||
      (input.control && input.shift && key === "i")
    ) {
      mainWindow.webContents.toggleDevTools();
      event.preventDefault();
    }
  });

  mainWindow.webContents.on(
    "did-fail-load",
    (_event, errorCode, errorDescription, validatedURL) => {
      const msg =
        `Caricamento fallito\n` +
        `URL: ${validatedURL}\n` +
        `Codice: ${errorCode}\n` +
        `Errore: ${errorDescription}`;

      writeLog(msg);
      loadErrorPage("Errore caricamento interfaccia", msg);
    }
  );

  mainWindow.webContents.on(
    "console-message",
    (_event, level, message, line, sourceId) => {
      writeLog(`Console level ${level}: ${message} (${sourceId}:${line})`);
    }
  );

  const indexPath = frontendIndexPath();

  writeLog(`Tentativo caricamento frontend locale: ${indexPath}`);
  writeLog(`Backend ready: ${backendReady}`);

  if (fs.existsSync(indexPath)) {
    mainWindow.loadFile(indexPath);
  } else if (backendReady) {
    mainWindow.loadURL(APP_URL);
  } else {
    loadErrorPage(
      "Frontend non trovato",
      `Non trovo il file index.html:\n${indexPath}\n\n` +
        `Backend disponibile: ${backendReady}\n` +
        `Cartella log:\n${logDir()}`
    );
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function setupAppMenu() {
  const template = [
    {
      label: "MN Laser Lab Manager",
      submenu: [
        {
          label: "Controlla aggiornamenti",
          click: () => checkForUpdatesManual()
        },
        { type: "separator" },
        { label: "Esci", role: "quit" }
      ]
    },
    {
      label: "Visualizza",
      submenu: [
        { label: "Ricarica", role: "reload" },
        { label: "Apri strumenti sviluppatore", role: "toggleDevTools" },
        { label: "Schermo intero", role: "togglefullscreen" },
        { type: "separator" },
        { label: "Zoom +", role: "zoomin" },
        { label: "Zoom -", role: "zoomout" },
        { label: "Zoom predefinito", role: "resetzoom" }
      ]
    }
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

async function checkForUpdatesManual() {
  if (!isPackaged()) {
    dialog.showMessageBox(mainWindow, {
      type: "info",
      title: "Aggiornamenti",
      message:
        "Gli aggiornamenti automatici funzionano nella versione installata, non in sviluppo."
    });
    return;
  }

  try {
    const { autoUpdater } = require("electron-updater");

    autoUpdater.setFeedURL({
      provider: "github",
      owner: "pebbly93",
      repo: "MNLaserLab"
    });

    const result = await autoUpdater.checkForUpdates();

    if (!result || !result.updateInfo) {
      dialog.showMessageBox(mainWindow, {
        type: "info",
        title: "Aggiornamenti",
        message: "Nessuna informazione aggiornamento disponibile."
      });
    }
  } catch (err) {
    dialog.showMessageBox(mainWindow, {
      type: "warning",
      title: "Aggiornamenti",
      message: err.message || "Controllo aggiornamenti non riuscito."
    });
  }
}

function setupAutoUpdater() {
  if (!isPackaged()) return;

  try {
    const { autoUpdater } = require("electron-updater");

    autoUpdater.setFeedURL({
      provider: "github",
      owner: "pebbly93",
      repo: "MNLaserLab"
    });

    autoUpdater.autoDownload = false;

    autoUpdater.on("update-available", () => {
      dialog
        .showMessageBox(mainWindow, {
          type: "info",
          title: "Aggiornamento disponibile",
          message: "È disponibile una nuova versione di MN Laser Lab Manager.",
          buttons: ["Scarica aggiornamento", "Più tardi"]
        })
        .then(({ response }) => {
          if (response === 0) autoUpdater.downloadUpdate();
        });
    });

    autoUpdater.on("update-not-available", () => {
      writeLog("Nessun aggiornamento disponibile.");
    });

    autoUpdater.on("update-downloaded", () => {
      dialog
        .showMessageBox(mainWindow, {
          type: "info",
          title: "Aggiornamento pronto",
          message: "Aggiornamento scaricato. Vuoi riavviare e installarlo ora?",
          buttons: ["Riavvia e installa", "Dopo"]
        })
        .then(({ response }) => {
          if (response === 0) autoUpdater.quitAndInstall();
        });
    });

    autoUpdater.on("error", (err) => {
      writeLog(`Errore aggiornamento: ${err == null ? "" : err.message}`);
    });

    setTimeout(() => {
      autoUpdater.checkForUpdates().catch((err) => {
        writeLog(`Check update automatico fallito: ${err.message}`);
      });
    }, 5000);
  } catch (err) {
    writeLog(`Auto-update non inizializzato: ${err.message}`);
  }
}

ipcMain.handle("app-version", () => app.getVersion());


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


ipcMain.handle("check-for-updates", async () => {
  await checkForUpdatesManual();
  return { ok: true };
});

app.setAppUserModelId("com.mnlaserlab.manager");

const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) {
        mainWindow.restore();
      }

      mainWindow.focus();
    }
  });

  app.whenReady().then(async () => {
    writeLog("Avvio applicazione.");

    const resourcesCheck = checkPackagedResources();

    if (!resourcesCheck.ok) {
      writeLog(`Risorse mancanti: ${resourcesCheck.message}`);
      dialog.showErrorBox("Risorse mancanti", resourcesCheck.message);
    }

    const backendStarted = startBackend();

    let backendReady = false;

    if (backendStarted) {
      backendReady = await waitForBackend();
    }

    setupAppMenu();

    createWindow(backendReady);

    if (!backendReady) {
      writeLog("Backend non pronto, ma provo comunque a mostrare il frontend locale.");
    }

    setupAutoUpdater();
  });
}

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
  }
});