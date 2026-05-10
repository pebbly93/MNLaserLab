from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "backend" / "app" / "legacy_logic.py"
MAIN_API = ROOT / "backend" / "app" / "main.py"
FRONTEND = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


BACKEND_CODE = r'''

# ---------------------------------------------------------------------------
# v40.5.0 - Dashboard operativa intelligente
# ---------------------------------------------------------------------------

def operational_dashboard(db):
    raw_items = aggregated_raw_items(db)

    zero_cost = []
    low_stock = []
    never_purchased = []

    for item in raw_items:
        stock = parse_float(item.get("stock"))
        cost = parse_float(item.get("cost_per_unit", item.get("weighted_average_cost", 0)))
        status = item.get("inventory_status", "")

        if stock > 0 and cost <= 0:
            zero_cost.append(item)

        if stock <= 1 and stock > 0:
            low_stock.append(item)

        if stock <= 0 and cost <= 0 or status == "mai_acquistato":
            never_purchased.append(item)

    products = []
    products_without_bom = []
    products_low_stock = []

    for name, info in db.get("products", {}).items():
        if not isinstance(info, dict):
            continue

        stock = parse_float(info.get("stock"))
        bom = info.get("bom", []) or []
        unit_cost = product_unit_cost(db, name)

        row = {
            "name": name,
            "category": info.get("category", ""),
            "subcategory": info.get("subcategory", ""),
            "collection": info.get("collection", ""),
            "stock": stock,
            "unit_cost": unit_cost,
            "bom_count": len(bom),
        }

        products.append(row)

        if not bom:
            products_without_bom.append(row)

        if stock <= 1:
            products_low_stock.append(row)

    quotes = db.get("quotes", []) or []
    quote_stats = {}
    quote_rows = []

    for q in quotes:
        if not isinstance(q, dict):
            continue

        status = q.get("status", "bozza") or "bozza"
        quote_stats[status] = quote_stats.get(status, 0) + 1

        if status in ("bozza", "inviato", "accettato", "da_modificare"):
            quote_rows.append({
                "id": q.get("id", ""),
                "name": q.get("name", ""),
                "customer": q.get("customer", ""),
                "status": status,
                "total": q.get("recommended") or q.get("discounted") or q.get("total") or 0,
                "date": q.get("date", ""),
            })

    sales_total = sum(parse_float(s.get("total")) for s in db.get("sales", []) if isinstance(s, dict))
    raw_value = sum(parse_float(x.get("value")) for x in raw_items)
    product_value = sum(parse_float(p.get("stock")) * product_unit_cost(db, name) for name, p in db.get("products", {}).items() if isinstance(p, dict))

    tasks = []

    def add_task(priority, title, detail, target, count=0):
        if count:
            tasks.append({
                "priority": priority,
                "title": title,
                "detail": detail,
                "target": target,
                "count": count,
            })

    add_task("alta", "Materiali con costo mancante", "Stock presente ma costo medio pari a zero", "materials", len(zero_cost))
    add_task("alta", "Prodotti senza distinta base", "Prodotti creati ma senza materiali collegati", "products", len(products_without_bom))
    add_task("media", "Materiali sotto scorta", "Stock basso o da ricontrollare", "materials", len(low_stock))
    add_task("media", "Prodotti con stock basso", "Prodotti finiti con disponibilità ≤ 1", "products", len(products_low_stock))
    add_task("bassa", "Preset mai acquistati", "Articoli presenti da catalogo ma non ancora valorizzati", "materials", len(never_purchased))
    add_task("media", "Preventivi accettati", "Da trasformare in produzione/consegna", "quote", quote_stats.get("accettato", 0))

    priority_order = {"alta": 0, "media": 1, "bassa": 2}
    tasks.sort(key=lambda x: (priority_order.get(x.get("priority"), 9), -x.get("count", 0)))

    return {
        "summary": {
            "raw_value": round(raw_value, 2),
            "product_value": round(product_value, 2),
            "sales_total": round(sales_total, 2),
            "raw_items": len(raw_items),
            "products": len(products),
            "quotes": len(quotes),
        },
        "tasks": tasks[:8],
        "zero_cost": zero_cost[:10],
        "low_stock": low_stock[:10],
        "products_without_bom": products_without_bom[:10],
        "products_low_stock": products_low_stock[:10],
        "quotes": quote_rows[:10],
        "quote_stats": quote_stats,
    }
'''


API_CODE = r'''

@app.get("/api/operations")
def operations_api():
    return operational_dashboard(load_db())
'''


def append_once(path: Path, marker: str, code: str):
    s = path.read_text(encoding="utf-8")
    if marker not in s:
        s += "\n\n" + code.strip() + "\n"
        path.write_text(s, encoding="utf-8")


def patch_backend():
    append_once(LEGACY, "def operational_dashboard", BACKEND_CODE)
    append_once(MAIN_API, "def operations_api", API_CODE)
    print("Backend dashboard operativa applicato.")


def patch_frontend():
    s = FRONTEND.read_text(encoding="utf-8")

    start = s.find("function Studio")
    end = s.find("\nfunction Atelier", start)

    if start == -1 or end == -1:
        raise RuntimeError("Funzione Studio non trovata")

    new_studio = r'''function Studio({ go }) {
  const { data: d, loading } = useApi('/dashboard', {});
  const { data: r } = useApi('/report', {});
  const { data: ops, loading: opsLoading } = useApi('/operations', { summary: {}, tasks: [], zero_cost: [], low_stock: [], products_without_bom: [], products_low_stock: [], quotes: [], quote_stats: {} });

  const stats = [
    ['Magazzino', money(d.inventory_value), 'materie prime', Boxes, 'cyan'],
    ['Prodotti', d.products || 0, 'creazioni MN', Factory, 'wood'],
    ['Valore prodotti', money(d.product_value), 'stock finito', PackageCheck, 'mint'],
    ['Vendite', money(d.sales), 'ricavi registrati', CircleDollarSign, 'ink'],
  ];

  const priorityLabel = {
    alta: 'Alta',
    media: 'Media',
    bassa: 'Bassa',
  };

  const priorityIcon = {
    alta: AlertTriangle,
    media: Gauge,
    bassa: Archive,
  };

  const quickTasks = list(ops.tasks);

  return <>
    <PageTitle title="Laboratorio" desc="Panoramica operativa MN Laser Lab: cosa controllare, cosa produrre e dove intervenire.">
      <button className="primary" onClick={() => go('atelier')}><Wand2 /> Avvia percorso</button>
    </PageTitle>

    {loading ? <Skeleton /> : <div className="stats">{stats.map(([a,b,c,I,t]) => <Stat key={a} label={a} value={b} sub={c} icon={I} tone={t}/>)}</div>}

    <div className="wide-grid operational-grid">
      <Card title="Centro operativo" icon={Gauge} action={<button className="ghost" onClick={() => go('report')}><BarChart3 /> Report</button>}>
        {opsLoading ? <Skeleton /> : <div className="operations-list">
          {quickTasks.length ? quickTasks.map((task, i) => {
            const Icon = priorityIcon[task.priority] || Gauge;

            return <button key={i} className={`operation-task ${task.priority}`} onClick={() => go(task.target)}>
              <span><Icon /></span>
              <div>
                <b>{task.title}</b>
                <small>{task.detail}</small>
              </div>
              <strong>{task.count}</strong>
              <em>{priorityLabel[task.priority] || task.priority}</em>
            </button>;
          }) : <div className="operation-empty">
            <CheckCircle2 />
            <b>Tutto sotto controllo</b>
            <span>Nessuna criticità evidente in magazzino, prodotti e preventivi.</span>
          </div>}
        </div>}
      </Card>

      <Card title="Azioni rapide" icon={Zap}>
        <div className="quick-action-grid">
          <button onClick={() => go('materials')}><PackagePlus /><b>Registra acquisto</b><span>Carica stock e costo reale</span></button>
          <button onClick={() => go('products')}><Factory /><b>Crea prodotto</b><span>Wizard, BOM e produzione</span></button>
          <button onClick={() => go('quote')}><Calculator /><b>Fai preventivo</b><span>Prezzo e margine</span></button>
          <button onClick={() => go('sales')}><ShoppingCart /><b>Registra vendita</b><span>Scarico prodotto finito</span></button>
        </div>
      </Card>
    </div>

    <div className="split-main">
      <Card title="Materiali da controllare" icon={AlertTriangle}>
        <div className="mini-list">
          {list(ops.zero_cost).slice(0, 5).map((x, i) => <button key={i} onClick={() => go('materials')}>
            <b>{x.name}</b>
            <span>{[x.category, x.subcategory, x.size, x.thickness].filter(Boolean).join(' · ')}</span>
            <strong>{num(x.stock)} {x.unit || ''} · costo 0</strong>
          </button>)}
          {!list(ops.zero_cost).length && <Empty text="Nessun costo mancante" />}
        </div>
      </Card>

      <Card title="Prodotti da completare" icon={PackageCheck}>
        <div className="mini-list">
          {list(ops.products_without_bom).slice(0, 5).map((x, i) => <button key={i} onClick={() => go('products')}>
            <b>{x.name}</b>
            <span>{[x.category, x.subcategory, x.collection].filter(Boolean).join(' · ') || 'Prodotto'}</span>
            <strong>BOM mancante</strong>
          </button>)}
          {!list(ops.products_without_bom).length && <Empty text="Nessun prodotto senza BOM" />}
        </div>
      </Card>
    </div>

    <div className="wide-grid">
      <Card title="Percorso operativo" icon={Zap}>
        <div className="flow-strip">
          <FlowPill n="1" icon={Truck} title="Acquisto" desc="Materie prime" detail="Legno, acrilico, vernici, LED e componenti." />
          <FlowPill n="2" icon={PackagePlus} title="Creo" desc="Scheda prodotto" detail="Categoria, collezione e distinta base." />
          <FlowPill n="3" icon={Factory} title="Produco" desc="Scala materiali" detail="Controllo stock e alternative intelligenti." />
          <FlowPill n="4" icon={CircleDollarSign} title="Vendo" desc="Margine" detail="Preventivi, PDF e vendite." />
        </div>
      </Card>

      <Card title="Margine attività" icon={BarChart3}>
        <div className="mini-stats">
          <Stat label="Raw" value={money(r.raw_total)} />
          <Stat label="Prodotti" value={money(r.product_total)} />
          <Stat label="Margine" value={money(r.margin_total)} sub={`${num(r.margin_pct)} %`} />
        </div>
      </Card>
    </div>
  </>;
}'''

    s = s[:start] + new_studio + "\n\n" + s[end + 1:]
    FRONTEND.write_text(s, encoding="utf-8")
    print("Frontend dashboard operativa applicato.")


def patch_css():
    css = CSS.read_text(encoding="utf-8")

    if "/* v40.5 smart dashboard */" not in css:
        css += r'''

/* v40.5 smart dashboard */
.operational-grid {
  grid-template-columns: minmax(0, 1.2fr) minmax(360px, .8fr);
}

.operations-list {
  display: grid;
  gap: 10px;
}

.operation-task {
  width: 100%;
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  color: var(--text);
  border-radius: 18px;
  padding: 12px;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto auto;
  gap: 12px;
  align-items: center;
  text-align: left;
  cursor: pointer;
}

.operation-task:hover {
  background: rgba(34, 211, 238, .08);
  border-color: rgba(34, 211, 238, .34);
}

.operation-task > span {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: rgba(255,255,255,.06);
}

.operation-task > span svg {
  width: 20px;
  height: 20px;
}

.operation-task b,
.operation-task small {
  display: block;
}

.operation-task b {
  line-height: 1.2;
}

.operation-task small {
  color: var(--muted);
  margin-top: 3px;
  line-height: 1.35;
}

.operation-task strong {
  font-size: 22px;
  line-height: 1;
}

.operation-task em {
  font-style: normal;
  border-radius: 999px;
  padding: 6px 9px;
  font-size: 11px;
  font-weight: 900;
  background: rgba(255,255,255,.06);
  color: var(--muted);
}

.operation-task.alta {
  border-color: rgba(239, 68, 68, .32);
}

.operation-task.alta > span,
.operation-task.alta em {
  background: rgba(239, 68, 68, .12);
  color: #fecaca;
}

.operation-task.media {
  border-color: rgba(245, 158, 11, .30);
}

.operation-task.media > span,
.operation-task.media em {
  background: rgba(245, 158, 11, .12);
  color: #fde68a;
}

.operation-task.bassa > span,
.operation-task.bassa em {
  background: rgba(148, 163, 184, .12);
}

.operation-empty {
  min-height: 220px;
  display: grid;
  place-items: center;
  text-align: center;
  gap: 6px;
  color: var(--muted);
}

.operation-empty svg {
  width: 34px;
  height: 34px;
  color: #86efac;
}

.operation-empty b {
  color: var(--text);
  font-size: 18px;
}

.quick-action-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.quick-action-grid button {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  color: var(--text);
  border-radius: 18px;
  padding: 14px;
  display: grid;
  gap: 6px;
  text-align: left;
  cursor: pointer;
  min-height: 118px;
}

.quick-action-grid button:hover {
  background: rgba(34, 211, 238, .08);
  border-color: rgba(34, 211, 238, .34);
}

.quick-action-grid svg {
  width: 22px;
  height: 22px;
  color: #67e8f9;
}

.quick-action-grid b,
.quick-action-grid span {
  display: block;
}

.quick-action-grid span {
  color: var(--muted);
  line-height: 1.3;
}

.mini-list {
  display: grid;
  gap: 9px;
}

.mini-list button {
  border: 1px solid rgba(148, 163, 184, .16);
  background: rgba(255,255,255,.045);
  color: var(--text);
  border-radius: 16px;
  padding: 11px;
  display: grid;
  gap: 4px;
  text-align: left;
  cursor: pointer;
}

.mini-list button:hover {
  background: rgba(34, 211, 238, .08);
  border-color: rgba(34, 211, 238, .34);
}

.mini-list b,
.mini-list span,
.mini-list strong {
  display: block;
}

.mini-list b {
  line-height: 1.2;
}

.mini-list span {
  color: var(--muted);
  font-size: 12px;
}

.mini-list strong {
  color: #fde68a;
  font-size: 12px;
}

@media (max-width: 1100px) {
  .operational-grid,
  .quick-action-grid {
    grid-template-columns: 1fr;
  }

  .operation-task {
    grid-template-columns: 42px minmax(0, 1fr) auto;
  }

  .operation-task em {
    grid-column: 2 / -1;
    width: fit-content;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")


def main():
    patch_backend()
    patch_frontend()
    patch_css()
    print("Patch v40.5.0 dashboard operativa intelligente completata.")


if __name__ == "__main__":
    main()
