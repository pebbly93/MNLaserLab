const { app, BrowserWindow, dialog, ipcMain, Menu } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let mainWindow = null;
let backendProcess = null;
const PORT = process.env.MN_BACKEND_PORT || '8000';
const APP_URL = `http://127.0.0.1:${PORT}/`;

function isPackaged() {
  return app.isPackaged;
}

function resourcePath(...parts) {
  if (isPackaged()) {
    return path.join(process.resourcesPath, ...parts);
  }
  return path.join(__dirname, ...parts);
}

function backendExecutablePath() {
  const exeName = process.platform === 'win32' ? 'MN_Laser_Lab_Backend.exe' : 'MN_Laser_Lab_Backend';
  return resourcePath('backend', exeName);
}

function frontendDistPath() {
  return resourcePath('frontend');
}

function startBackend() {
  const env = {
    ...process.env,
    MN_BACKEND_PORT: PORT,
    MN_DESKTOP_DIST: frontendDistPath(),
    MN_USER_DATA_DIR: path.join(app.getPath('userData'), 'data')
  };

  if (isPackaged()) {
    const exe = backendExecutablePath();
    if (!fs.existsSync(exe)) {
      dialog.showErrorBox('Backend non trovato', `Non trovo il backend: ${exe}`);
      return;
    }
    backendProcess = spawn(exe, [], {
      env,
      windowsHide: true,
      stdio: 'ignore'
    });
  } else {
    const backendDir = path.join(__dirname, '..', 'backend');
    const script = path.join(backendDir, 'desktop_server.py');
    backendProcess = spawn('python', [script], {
      cwd: backendDir,
      env,
      windowsHide: true,
      stdio: 'inherit'
    });
  }

  backendProcess.on('exit', (code) => {
    if (code !== 0 && mainWindow) {
      console.warn(`Backend terminato con codice ${code}`);
    }
  });
}

async function waitForBackend(timeoutMs = 20000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/api/health`);
      if (res.ok) return true;
    } catch (err) {}
    await new Promise(resolve => setTimeout(resolve, 350));
  }
  return false;
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1360,
    height: 900,
    minWidth: 1120,
    minHeight: 720,
    title: 'MN Laser Lab Manager',
    backgroundColor: '#061214',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.loadURL(APP_URL);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}


function setupAppMenu() {
  const template = [
    {
      label: 'MN Laser Lab Manager',
      submenu: [
        { label: 'Controlla aggiornamenti', click: () => checkForUpdatesManual() },
        { type: 'separator' },
        { label: 'Esci', role: 'quit' }
      ]
    },
    {
      label: 'Visualizza',
      submenu: [
        { label: 'Ricarica', role: 'reload' },
        { label: 'Schermo intero', role: 'togglefullscreen' },
        { type: 'separator' },
        { label: 'Zoom +', role: 'zoomin' },
        { label: 'Zoom -', role: 'zoomout' },
        { label: 'Zoom predefinito', role: 'resetzoom' }
      ]
    }
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

async function checkForUpdatesManual() {
  if (!isPackaged()) {
    dialog.showMessageBox(mainWindow, {
      type: 'info',
      title: 'Aggiornamenti',
      message: 'Gli aggiornamenti automatici funzionano nella versione installata, non in sviluppo.'
    });
    return;
  }
  try {
    const { autoUpdater } = require('electron-updater');
    const result = await autoUpdater.checkForUpdates();
    if (!result || !result.updateInfo) {
      dialog.showMessageBox(mainWindow, { type: 'info', title: 'Aggiornamenti', message: 'Nessuna informazione aggiornamento disponibile.' });
    }
  } catch (err) {
    dialog.showMessageBox(mainWindow, { type: 'warning', title: 'Aggiornamenti', message: err.message || 'Controllo aggiornamenti non riuscito.' });
  }
}

function setupAutoUpdater() {
  if (!isPackaged()) return;
  try {
    const { autoUpdater } = require('electron-updater');
    autoUpdater.autoDownload = false;

    autoUpdater.on('update-available', () => {
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'Aggiornamento disponibile',
        message: 'È disponibile una nuova versione di MN Laser Lab Manager.',
        buttons: ['Scarica aggiornamento', 'Più tardi']
      }).then(({ response }) => {
        if (response === 0) autoUpdater.downloadUpdate();
      });
    });

    autoUpdater.on('update-downloaded', () => {
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'Aggiornamento pronto',
        message: 'Aggiornamento scaricato. Vuoi riavviare e installarlo ora?',
        buttons: ['Riavvia e installa', 'Dopo']
      }).then(({ response }) => {
        if (response === 0) autoUpdater.quitAndInstall();
      });
    });

    autoUpdater.on('error', (err) => {
      console.warn('Errore aggiornamento:', err == null ? '' : err.message);
    });

    setTimeout(() => autoUpdater.checkForUpdates().catch(() => {}), 5000);
  } catch (err) {
    console.warn('Auto-update non inizializzato:', err.message);
  }
}

ipcMain.handle('app-version', () => app.getVersion());
ipcMain.handle('check-for-updates', async () => {
  await checkForUpdatesManual();
  return { ok: true };
});

app.whenReady().then(async () => {
  startBackend();
  const ok = await waitForBackend();
  if (!ok) {
    dialog.showErrorBox(
      'Backend non avviato',
      'Non riesco ad avviare il motore locale FastAPI. Controlla antivirus/permessi e riprova.'
    );
  }
  setupAppMenu();
  createWindow();
  setupAutoUpdater();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
  }
});
