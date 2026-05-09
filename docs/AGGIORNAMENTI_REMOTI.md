# Aggiornamenti remoti

Sì, l'app può essere aggiornabile da remoto.

## Modalità consigliata

Per una prima versione professionale ma semplice:

- Electron + electron-builder
- installer NSIS
- electron-updater
- hosting statico dei file update

Non serve per forza un server backend dedicato per gli aggiornamenti: basta un hosting statico raggiungibile via HTTPS.

## Flusso di aggiornamento

1. Compili la nuova versione cambiando `desktop/package.json`, per esempio da `39.2.0` a `39.2.1`.
2. Lanci `build_windows_desktop.bat`.
3. Carichi i file generati in `desktop/release/` sul tuo hosting update.
4. L'app installata controlla gli aggiornamenti all'avvio.
5. Se trova una versione nuova, mostra il popup: scarica / più tardi.
6. Dopo il download, chiede riavvio e installazione.

## Esempio URL update

```text
https://mnlaserlab.com/app-updates/windows/
```

Dentro dovresti caricare file simili a:

```text
latest.yml
MN Laser Lab Manager Setup 39.2.1.exe
MN Laser Lab Manager Setup 39.2.1.exe.blockmap
```

## Firma digitale

Per evitare avvisi Windows SmartScreen, in futuro conviene usare un certificato di code signing.
Senza firma funziona comunque, ma Windows potrebbe mostrare un avviso alla prima installazione.

## Strategia sicura per i dati

L'aggiornamento deve aggiornare solo l'app, non cancellare il database SQLite.
Il database resta in:

```text
%LOCALAPPDATA%\MN Laser Lab Manager\mn_laser_lab.db
```

Prima di introdurre modifiche pesanti al database, conviene aggiungere migrazioni automatiche e backup pre-update.
