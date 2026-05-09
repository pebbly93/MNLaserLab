# Docker opzionale

Docker può essere utile per test e deploy tecnico, ma non è richiesto per il setup Windows.

## Avvio test con Docker

Da root progetto:

```bash
cd docker
docker compose up --build
```

Poi apri:

```text
http://127.0.0.1:8000
```

I dati vengono salvati nel volume Docker `mn_laser_lab_data`.

## Quando usare Docker

Usalo per:

- test su server;
- demo tecnica;
- ambiente controllato;
- sviluppo.

Non usarlo come requisito per l'utente finale desktop.
