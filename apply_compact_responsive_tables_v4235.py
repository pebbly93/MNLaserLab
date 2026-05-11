from pathlib import Path
import re

CSS = Path("frontend/src/style.css")

PATCH = r'''

/* v42.3.5 - Tabelle compatte e adattate alla larghezza card */
.table-card {
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
}

.table-wrap {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
}

.table-wrap table {
  width: 100%;
  max-width: 100%;
  border-collapse: collapse;
  table-layout: auto;
}

.table-wrap th,
.table-wrap td {
  max-width: 220px;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: normal;
  vertical-align: middle;
}

.table-wrap th {
  font-size: clamp(10px, 0.72vw, 12px);
  line-height: 1.2;
}

.table-wrap td {
  font-size: clamp(11px, 0.78vw, 13px);
  line-height: 1.25;
}

.table-wrap td b,
.table-wrap td strong {
  line-height: 1.2;
}

.table-wrap .quick-actions,
.table-wrap td:last-child > div {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
}

.table-wrap button {
  min-height: 30px;
  padding: 7px 10px;
  font-size: 12px;
  line-height: 1.1;
  white-space: nowrap;
}

.table-wrap .pill,
.table-wrap .badge,
.table-wrap .status,
.table-wrap span[class*="pill"],
.table-wrap span[class*="badge"] {
  max-width: 100%;
  white-space: normal;
  overflow-wrap: anywhere;
}

/* Tablet e schermi stretti */
@media (max-width: 1024px) {
  .table-card {
    border-radius: 18px;
  }

  .table-meta {
    gap: 8px;
    align-items: flex-start;
  }

  .table-wrap table {
    min-width: 720px;
  }

  .table-wrap th,
  .table-wrap td {
    padding: 10px 8px;
    max-width: 170px;
  }

  .table-wrap button {
    padding: 6px 8px;
    font-size: 11.5px;
  }
}

/* Smartphone: tabella ancora tabella, ma leggibile e dentro card */
@media (max-width: 720px) {
  .table-card {
    padding: 10px;
    overflow: hidden;
  }

  .table-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: 8px;
  }

  .table-meta b {
    font-size: 12px;
  }

  .table-meta span {
    font-size: 11px;
  }

  .table-wrap {
    border-radius: 14px;
    overflow-x: auto;
  }

  .table-wrap table {
    min-width: 620px;
  }

  .table-wrap th,
  .table-wrap td {
    padding: 8px 7px;
    max-width: 140px;
  }

  .table-wrap th {
    font-size: 9.5px;
    letter-spacing: .06em;
  }

  .table-wrap td {
    font-size: 11px;
  }

  .table-wrap td:last-child {
    max-width: 220px;
  }

  .table-wrap td:last-child > div,
  .table-wrap .quick-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
  }

  .table-wrap td:last-child button {
    min-height: 28px;
    padding: 6px 7px;
    font-size: 10.5px;
  }
}

/* Smartphone piccoli */
@media (max-width: 430px) {
  .table-wrap table {
    min-width: 560px;
  }

  .table-wrap th,
  .table-wrap td {
    padding: 7px 6px;
    max-width: 125px;
  }

  .table-wrap td {
    font-size: 10.5px;
  }

  .table-wrap th {
    font-size: 9px;
  }

  .table-wrap button {
    font-size: 10px;
    padding: 5px 6px;
  }
}
'''

def main():
    css = CSS.read_text(encoding="utf-8")

    # Rimuove eventuale vecchio tentativo mobile troppo aggressivo, se ancora presente.
    css = re.sub(
        r'\n/\* v42\.3\.4 - Smartphone refinement for quote page only via media queries \*/[\s\S]*?(?=\n/\*|\Z)',
        '\n',
        css,
        flags=re.DOTALL
    )

    # Evita duplicati.
    css = re.sub(
        r'\n/\* v42\.3\.5 - Tabelle compatte e adattate alla larghezza card \*/[\s\S]*?(?=\n/\*|\Z)',
        '\n',
        css,
        flags=re.DOTALL
    )

    css += "\n\n" + PATCH.strip() + "\n"

    CSS.write_text(css, encoding="utf-8")
    print("Patch v42.3.5 applicata: tabelle compatte e responsive.")

if __name__ == "__main__":
    main()
