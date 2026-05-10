from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"


def patch_backend():
    s = LEGACY.read_text(encoding="utf-8")

    # 1) Inserisce project_fee dentro calculate_quote: lo agganciamo a packaging/energy/wear se presenti.
    if "project_fee" not in s[s.find("def calculate_quote"):s.find("def", s.find("def calculate_quote") + 1)]:
        start = s.find("def calculate_quote")
        end = s.find("\ndef ", start + 1)
        block = s[start:end]

        # Aggiunge lettura project_fee vicino agli altri costi.
        candidates = [
            "wear = parse_float(payload.get(\"wear\"))",
            "wear = parse_float(payload.get('wear'))",
            "packaging = parse_float(payload.get(\"packaging\"))",
            "packaging = parse_float(payload.get('packaging'))",
        ]

        inserted = False
        for c in candidates:
            if c in block:
                block = block.replace(c, c + "\n    project_fee = parse_float(payload.get(\"project_fee\"))", 1)
                inserted = True
                break

        if not inserted:
            # fallback: subito dopo l'inizio funzione
            block = block.replace(
                "def calculate_quote(db, payload):",
                "def calculate_quote(db, payload):\n    project_fee = parse_float(payload.get(\"project_fee\"))",
                1
            )

        # Aggiunge project_fee nel costo reale. Cerchiamo formule comuni.
        replacements = [
            ("real_cost = materials_cost + labor_cost + packaging + energy + wear", "real_cost = materials_cost + labor_cost + packaging + energy + wear + project_fee"),
            ("real_cost = material_cost + labor_cost + packaging + energy + wear", "real_cost = material_cost + labor_cost + packaging + energy + wear + project_fee"),
            ("real_cost = base_cost + packaging + energy + wear", "real_cost = base_cost + packaging + energy + wear + project_fee"),
        ]

        changed_cost = False
        for old, new in replacements:
            if old in block:
                block = block.replace(old, new, 1)
                changed_cost = True
                break

        if not changed_cost:
            # fallback: se trova una riga real_cost = ..., aggiunge + project_fee alla prima occorrenza
            lines = block.splitlines()
            for i, line in enumerate(lines):
                if line.strip().startswith("real_cost =") and "project_fee" not in line:
                    lines[i] = line.rstrip() + " + project_fee"
                    changed_cost = True
                    break
            block = "\n".join(lines)

        # Aggiunge project_fee nella risposta.
        if '"project_fee"' not in block and "'project_fee'" not in block:
            # inserisce vicino a real_cost se è un dict return.
            if '"real_cost":' in block:
                block = block.replace('"real_cost":', '"project_fee": round(project_fee, 2),\n        "real_cost":', 1)
            elif "'real_cost':" in block:
                block = block.replace("'real_cost':", "'project_fee': round(project_fee, 2),\n        'real_cost':", 1)

        s = s[:start] + block + s[end:]

    # 2) Salvataggio preventivo: garantisce che project_fee venga mantenuto nei dati salvati.
    # Se save_quote copia già payload intero non serve, ma aggiungiamo un fallback non invasivo.
    if "quote[\"project_fee\"] = parse_float(payload.get(\"project_fee\"))" not in s:
        start = s.find("def save_quote")
        if start != -1:
            end = s.find("\ndef ", start + 1)
            block = s[start:end]

            if "project_fee" not in block:
                marker = "quote = {"
                if marker in block:
                    # non forziamo dentro dict perché fragile; inseriamo prima del salvataggio append/update.
                    insert_points = [
                        "quotes = db.setdefault(\"quotes\", [])",
                        "quotes = db.setdefault('quotes', [])",
                    ]
                    for p in insert_points:
                        if p in block:
                            block = block.replace(
                                p,
                                "quote[\"project_fee\"] = parse_float(payload.get(\"project_fee\"))\n    " + p,
                                1
                            )
                            break
                else:
                    # fallback verso fine funzione
                    block = block.replace(
                        "return quote",
                        "quote[\"project_fee\"] = parse_float(payload.get(\"project_fee\"))\n    return quote",
                        1
                    )

                s = s[:start] + block + s[end:]

    # 3) record_quote_sale: passa project_fee alla vendita da preventivo se presente.
    if "project_fee" not in s[s.find("def record_quote_sale"):s.find("def", s.find("def record_quote_sale") + 1)]:
        start = s.find("def record_quote_sale")
        if start != -1:
            end = s.find("\ndef ", start + 1)
            block = s[start:end]
            if "wear" in block:
                block = block.replace(
                    '"wear": payload.get("wear", 0),',
                    '"wear": payload.get("wear", 0),\n        "project_fee": payload.get("project_fee", 0),',
                    1
                )
                block = block.replace(
                    "'wear': payload.get('wear', 0),",
                    "'wear': payload.get('wear', 0),\n        'project_fee': payload.get('project_fee', 0),",
                    1
                )
            s = s[:start] + block + s[end:]

    # 4) PDF: se project_fee > 0 aggiunge una riga "Spese di progetto".
    # Inseriamo helper riutilizzabile.
    if "def quote_project_fee_html" not in s:
        helper = r'''

def quote_project_fee_html(quote):
    fee = parse_float((quote or {}).get("project_fee"))
    if fee <= 0:
        return ""
    return f"""
      <tr>
        <td>Spese di progetto</td>
        <td class="right">1.00 pz</td>
        <td class="right">€ {fee:.2f}</td>
      </tr>
    """
'''
        s += "\n\n" + helper.strip() + "\n"

    # Prova a inserire quote_project_fee_html nei template PDF cliente/interno prima del totale.
    for fn in ["quote_customer_html", "quote_internal_html"]:
        start = s.find(f"def {fn}")
        if start == -1:
            continue
        end = s.find("\ndef ", start + 1)
        if end == -1:
            end = len(s)
        block = s[start:end]

        if "quote_project_fee_html(quote)" not in block:
            # Cerca una chiusura tbody prima del totale. Inserimento molto conservativo.
            if "</tbody>" in block:
                block = block.replace("</tbody>", "{quote_project_fee_html(quote)}\n</tbody>", 1)
            elif "</table>" in block:
                block = block.replace("</table>", "{quote_project_fee_html(quote)}\n</table>", 1)

            s = s[:start] + block + s[end:]

    LEGACY.write_text(s, encoding="utf-8")
    print("Backend: project_fee preventivo/PDF applicato.")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    # 1) Aggiunge project_fee allo stato cost.
    old = "commission: '', margin: '30', discount: ''"
    if old in s and "project_fee" not in s[s.find("function Quote("):s.find("function Sales", s.find("function Quote("))]:
        s = s.replace(old, "commission: '', project_fee: '', margin: '30', discount: ''", 1)

    # 2) Aggiunge label.
    old_labels = "commission: 'Commissioni %', margin: 'Margine %', discount: 'Sconto %'"
    if old_labels in s:
        s = s.replace(
            old_labels,
            "commission: 'Commissioni %', project_fee: 'Spese di progetto €', margin: 'Margine %', discount: 'Sconto %'",
            1
        )

    # 3) Se c'è un altro formato costLabels multilinea, fallback.
    if "project_fee: 'Spese di progetto €'" not in s:
        marker = "commission: 'Commissioni %'"
        if marker in s:
            s = s.replace(marker, marker + ", project_fee: 'Spese di progetto €'", 1)

    # 4) Assicura che save quote / sale passino il cost già incluso:
    # di solito spread ...cost è già presente, quindi non serve altro.

    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend: campo Spese di progetto aggiunto.")


def main():
    patch_backend()
    patch_frontend()
    print("Patch v40.8.3 completata: spese di progetto nei preventivi e PDF.")


if __name__ == "__main__":
    main()
