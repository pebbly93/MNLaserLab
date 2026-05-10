from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN_API = ROOT / "backend" / "app" / "main.py"

HELPERS = r'''

# ---------------------------------------------------------------------------
# v40.3.1 - SQLite WAL safe backup/restore
# ---------------------------------------------------------------------------

def sqlite_checkpoint():
    """Forza SQLite a scrivere il WAL nel file .db principale."""
    try:
        with connect() as conn:
            conn.execute("PRAGMA wal_checkpoint(FULL)")
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        pass


def sqlite_sidecar_paths(path):
    p = Path(path)
    return [
        Path(str(p) + "-wal"),
        Path(str(p) + "-shm"),
    ]


def remove_sqlite_sidecars(path):
    for p in sqlite_sidecar_paths(path):
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass


def backup_database(suffix="backup"):
    sqlite_checkpoint()

    source = db_path()
    if not source.exists():
        return ""

    dest = user_data_dir() / f"mn_laser_lab_{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(source, dest)
    return str(dest)


def restore_database_from_backup(filename):
    filename = str(filename or "").strip()
    if not filename:
        raise ValueError("Nome backup mancante")

    root = user_data_dir()
    source = root / filename

    if not source.exists() or source.suffix.lower() != ".db":
        raise ValueError("Backup non trovato")

    sqlite_checkpoint()

    # Backup di sicurezza prima del ripristino.
    safety = backup_database("prima_ripristino")

    target = db_path()

    # Fondamentale con journal_mode=WAL:
    # rimuove i file sidecar vecchi, altrimenti SQLite può leggere dati non ripristinati.
    remove_sqlite_sidecars(target)

    shutil.copy2(source, target)

    # Dopo la copia, elimina eventuali sidecar generati prima della prossima apertura.
    remove_sqlite_sidecars(target)

    # Riapre e normalizza il db ripristinato.
    restored_data = load_db()
    save_db(restored_data)

    return {
        "ok": True,
        "restored": str(source),
        "safety_backup": safety,
        "db_path": str(target),
        "items": {
            "materials": len(restored_data.get("materials", {})),
            "components": len(restored_data.get("components", {})),
            "products": len(restored_data.get("products", {})),
            "sales": len(restored_data.get("sales", [])),
            "quotes": len(restored_data.get("quotes", [])),
        }
    }
'''

def replace_function(source: str, name: str, new_code: str) -> str:
    start = source.find(f"def {name}(")
    if start == -1:
        return source

    next_def = source.find("\ndef ", start + 1)
    if next_def == -1:
        next_def = len(source)

    return source[:start] + new_code.rstrip() + "\n\n" + source[next_def + 1:]


def main():
    s = LEGACY.read_text(encoding="utf-8")

    # Se abbiamo già funzioni con questi nomi, le sostituiamo in modo sicuro.
    for fn in ["backup_database", "restore_database_from_backup"]:
        start = s.find(f"def {fn}(")
        if start != -1:
            next_def = s.find("\ndef ", start + 1)
            if next_def == -1:
                next_def = len(s)
            s = s[:start] + s[next_def + 1:]

    # Aggiunge blocco nuovo in fondo.
    if "def sqlite_checkpoint" not in s:
        s += "\n\n" + HELPERS.strip() + "\n"
    else:
        # Nel caso fosse già presente, sovrascrive solo backup/restore.
        s = replace_function(s, "backup_database", HELPERS)
    
    LEGACY.write_text(s, encoding="utf-8")
    print("Patch v40.3.1 applicata: restore SQLite WAL-safe.")

if __name__ == "__main__":
    main()
