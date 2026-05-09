# MN Laser Lab Manager - Desktop professionale

Questa struttura è pensata per lavorare bene con GitHub, Electron, FastAPI, React, SQLite e aggiornamenti tramite GitHub Releases.

## Struttura

```text
frontend/                 React + Vite
backend/                  FastAPI + SQLite
desktop/                  Electron shell
.github/workflows/        build automatico setup Windows
scripts/                  build locale Windows
docs/                     guide operative
docker/                   uso opzionale per test/server
```

## Build locale Windows

Requisiti solo sul PC di sviluppo/build:

- Windows
- Node.js 20+
- Python 3.11
- Git opzionale

Comando:

```bat
build_windows_desktop.bat
```

Output:

```text
desktop\release\MN-Laser-Lab-Manager-Setup-39.3.0.exe
```

## Build automatica GitHub

Fai push di un tag:

```bash
git tag v39.3.0
git push origin v39.3.0
```

GitHub Actions genera setup e release.

## Utente finale

L'utente finale installa solo il setup `.exe`.
Non servono Docker, Python o Node.

## Database locale

Il database viene salvato nella cartella dati utente, non dentro Program Files.
Su Windows:

```text
%LOCALAPPDATA%\MN Laser Lab Manager\
```

Nell'app desktop Electron viene usato l'userData path dell'app, così i dati restano persistenti anche dopo gli aggiornamenti.
