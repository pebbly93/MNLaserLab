# GitHub Releases e aggiornamenti automatici

Questa versione è pensata per essere pubblicata su un repository GitHub privato o pubblico.

## Flusso corretto

1. Carichi il progetto su GitHub.
2. Configuri `desktop/package.json` sostituendo:
   - `TUO_USERNAME_GITHUB`
   - `mn-laser-lab-manager`
3. Crei un tag, ad esempio:

```bash
git tag v39.3.0
git push origin v39.3.0
```

4. GitHub Actions compila automaticamente:
   - frontend React;
   - backend FastAPI in `.exe`;
   - setup Electron/NSIS;
   - file `latest.yml` necessario per gli aggiornamenti.

5. La release GitHub conterrà:
   - `MN-Laser-Lab-Manager-Setup-39.3.0.exe`
   - `latest.yml`
   - file `.blockmap`

## Aggiornamenti automatici

L'app installata usa `electron-updater`.
Quando pubblicherai una versione successiva, ad esempio `v39.3.1`, l'app potrà rilevarla, scaricarla e proporre il riavvio.

## Requisiti PC finale

Sul PC dell'utente finale NON servono:

- Docker
- Python
- Node.js
- npm
- Git

Serve solo installare il setup `.exe`.

## Firma digitale

Senza certificato di firma Windows SmartScreen può mostrare un avviso.
Per distribuzione commerciale conviene valutare un certificato di code signing.
