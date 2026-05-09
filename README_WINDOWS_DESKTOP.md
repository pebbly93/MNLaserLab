# MN Laser Lab Manager v39.2 - Windows Desktop Packaging

Questo pacchetto trasforma la web app React + FastAPI in una app desktop Windows installabile.

## Cosa contiene

- `frontend/`: interfaccia React.
- `backend/`: API FastAPI + SQLite.
- `backend/desktop_server.py`: avvia FastAPI e serve anche il frontend compilato.
- `desktop/`: shell Electron.
- `build_windows_desktop.bat`: genera il setup Windows.

## Requisiti sul PC di build

Servono solo sul PC usato per creare il setup, non sui PC finali:

- Windows 10/11
- Node.js 20+
- Python 3.11
- npm

## Build setup.exe

Da Prompt dei comandi o PowerShell nella cartella del progetto:

```bat
build_windows_desktop.bat
```

Alla fine il setup sarà in:

```text
desktop\release\
```

Il file generato sarà simile a:

```text
MN Laser Lab Manager Setup 39.2.0.exe
```

## Come funziona l'app installata

Quando l'utente apre MN Laser Lab Manager:

1. Electron apre una finestra desktop.
2. Avvia automaticamente `MN_Laser_Lab_Backend.exe` in locale.
3. Il backend usa SQLite in `%LOCALAPPDATA%\MN Laser Lab Manager`.
4. La finestra carica la dashboard da `http://127.0.0.1:8000`.

L'utente finale non deve installare Python, Node o npm.

## Aggiornamenti remoti

La struttura include `electron-updater`, ma va configurato il server aggiornamenti.

Nel file:

```text
desktop/package.json
```

sostituisci:

```json
"url": "https://example.com/mn-laser-lab-manager/updates/"
```

con un URL reale, ad esempio:

```json
"url": "https://mnlaserlab.com/download/updates/"
```

Poi, quando compili una nuova versione, carichi nella cartella update i file generati da `electron-builder`:

- Setup `.exe`
- file `.yml`
- eventuali blocchi `.blockmap`

L'app installata controllerà gli aggiornamenti all'avvio e chiederà all'utente se scaricare e installare.

## Nota database

Gli aggiornamenti dell'app non cancellano il database perché NSIS è configurato con:

```json
"deleteAppDataOnUninstall": false
```

Il database resta nella cartella utente Windows.
