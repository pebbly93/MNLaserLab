from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "frontend" / "src" / "main.jsx"
CSS = ROOT / "frontend" / "src" / "style.css"


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"Blocco non trovato: {label}")
    return text.replace(old, new, 1)


DETAIL_MODAL_COMPONENT = r'''
function DetailModal({ title, subtitle, icon: Icon, onClose, children }) {
  useEffect(() => {
    const onKey = e => {
      if (e.key === 'Escape') onClose?.();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return <div className="modal-backdrop" onMouseDown={onClose}>
    <div className="detail-modal" onMouseDown={e => e.stopPropagation()}>
      <div className="detail-modal-head">
        <div className="detail-modal-title">
          {Icon && <Icon />}
          <div>
            <h2>{title}</h2>
            {subtitle && <p>{subtitle}</p>}
          </div>
        </div>
        <button className="ghost modal-close" onClick={onClose}>Chiudi</button>
      </div>
      <div className="detail-modal-body">
        {children}
      </div>
    </div>
  </div>;
}
'''


def patch_main():
    s = MAIN.read_text(encoding="utf-8")

    # 1. Aggiunge componente modal dopo FlowPill, se assente
    if "function DetailModal" not in s:
        marker = "function FlowPill"
        idx = s.find(marker)
        if idx == -1:
            raise RuntimeError("Punto inserimento DetailModal non trovato")

        # Inserisce prima di FlowPill
        s = s[:idx] + DETAIL_MODAL_COMPONENT.strip() + "\n\n" + s[idx:]

    # 2. SmartInput: limita suggerimenti rapidi a 5 e migliora logica visuale
    old_smart = """    {filtered.length > 0 && <div className="suggestions">{filtered.map(v => <button type="button" key={v} onMouseDown={e => { e.preventDefault(); choose(v); }}>{v}</button>)}</div>}"""
    new_smart = """    {filtered.length > 0 && <div className="suggestions compact-suggestions">
      {filtered.slice(0, 5).map(v => <button type="button" key={v} onMouseDown={e => { e.preventDefault(); choose(v); }}>{v}</button>)}
      {filtered.length > 5 && <small>+{filtered.length - 5} altri suggerimenti: continua a scrivere per filtrare</small>}
    </div>}"""

    if old_smart in s:
      s = s.replace(old_smart, new_smart, 1)

    # 3. Sostituisce pannello dettaglio materiale sotto pagina con modal.
    material_pattern = re.compile(
        r"\s*\{materialDetail && <Card title=\"Dettaglio materiale\"[\s\S]*?</Card>\}",
        re.MULTILINE
    )

    if "DetailModal title=\"Dettaglio materiale\"" not in s:
        material_modal = r'''
    {materialDetail && <DetailModal title="Dettaglio materiale" subtitle="Storico acquisti, utilizzo nei prodotti e stato economico dell’articolo." icon={Archive} onClose={() => setMaterialDetail(null)}>
      <div className="detail-hero">
        <div>
          <span>Articolo</span>
          <strong>{materialDetail.name || '—'}</strong>
          <small>{[materialDetail.item?.section, materialDetail.item?.category, materialDetail.item?.subcategory].filter(Boolean).join(' · ')}</small>
        </div>
        <InventoryBadge item={materialDetail.item || {}} />
      </div>
      <div className="detail-grid">
        <Stat label="Stock" value={`${num(materialDetail.item?.stock)} ${materialDetail.item?.unit || ''}`} />
        <Stat label="Costo medio" value={money(materialDetail.item?.weighted_average_cost ?? materialDetail.item?.cost_per_unit)} />
        <Stat label="Ultimo costo" value={money(materialDetail.item?.last_unit_cost)} />
        <Stat label="Valore stock" value={money(materialDetail.stock_value)} />
      </div>
      <div className="detail-columns">
        <div>
          <h3>Storico acquisti</h3>
          <DataTable rows={list(materialDetail.purchase_history).slice(0, 12)} empty="Nessuno storico acquisti" columns={[
            { key: 'date', label: 'Data' },
            { key: 'supplier', label: 'Fornitore' },
            { key: 'qty', label: 'Q.tà', render: r => num(r.qty) },
            { key: 'unit_cost', label: 'Costo/u', render: r => money(r.unit_cost) },
            { key: 'total_cost', label: 'Totale', render: r => money(r.total_cost) }
          ]} />
        </div>
        <div>
          <h3>Usato nei prodotti</h3>
          <DataTable rows={list(materialDetail.used_in_products)} empty="Non risulta usato in prodotti" columns={[
            { key: 'product', label: 'Prodotto' },
            { key: 'qty', label: 'Q.tà BOM', render: r => `${num(r.qty)} ${r.unit || ''}` }
          ]} />
        </div>
      </div>
    </DetailModal>}'''
        s, n = material_pattern.subn(material_modal, s, count=1)
        if n == 0:
            print("Avviso: pannello dettaglio materiale non trovato, salto conversione materiale.")

    # 4. Sostituisce pannello dettaglio prodotto sotto pagina con modal.
    product_pattern = re.compile(
        r"\s*\{productDetail && <Card title=\"Dettaglio prodotto finito\"[\s\S]*?</Card>\}",
        re.MULTILINE
    )

    if "DetailModal title=\"Dettaglio prodotto finito\"" not in s:
        product_modal = r'''
    {productDetail && <DetailModal title="Dettaglio prodotto finito" subtitle="Distinta base, costi interni, movimenti e vendite collegate." icon={PackageCheck} onClose={() => setProductDetail(null)}>
      <div className="detail-hero">
        <div>
          <span>Prodotto</span>
          <strong>{productDetail.name || '—'}</strong>
          <small>{[productDetail.product?.category, productDetail.product?.subcategory, productDetail.product?.collection].filter(Boolean).join(' · ')}</small>
        </div>
        <span className="quote-status accepted">scheda prodotto</span>
      </div>
      <div className="detail-grid">
        <Stat label="Stock" value={`${num(productDetail.stock)} ${productDetail.product?.unit || 'pz'}`} />
        <Stat label="Costo interno/u" value={money(productDetail.unit_cost)} />
        <Stat label="Materiali/u" value={money(productDetail.material_cost)} />
        <Stat label="Valore stock" value={money(productDetail.value)} />
      </div>
      <div className="detail-grid compact-detail">
        <Stat label="Lavoro/u" value={money(productDetail.labor_cost)} />
        <Stat label="Extra/u" value={money(productDetail.extra_cost)} />
        <Stat label="Movimenti" value={list(productDetail.movements).length} />
      </div>
      <div className="detail-columns">
        <div>
          <h3>Distinta base</h3>
          <DataTable rows={list(productDetail.bom)} empty="Nessuna distinta base" columns={[
            { key: 'label', label: 'Materiale' },
            { key: 'qty', label: 'Q.tà', render: r => `${num(r.qty)} ${r.unit || ''}` },
            { key: 'unit_cost', label: 'Costo/u', render: r => money(r.unit_cost) },
            { key: 'cost', label: 'Costo', render: r => money(r.cost) },
            { key: 'ok', label: 'Stock', render: r => r.ok ? 'OK' : 'Da verificare' }
          ]} />
        </div>
        <div>
          <h3>Movimenti</h3>
          <DataTable rows={list(productDetail.movements).slice(0, 12)} empty="Nessun movimento" columns={[
            { key: 'date', label: 'Data' },
            { key: 'qty', label: 'Q.tà', render: r => num(r.qty) },
            { key: 'reason', label: 'Causale' },
            { key: 'note', label: 'Note' }
          ]} />
        </div>
      </div>
    </DetailModal>}'''
        s, n = product_pattern.subn(product_modal, s, count=1)
        if n == 0:
            print("Avviso: pannello dettaglio prodotto non trovato, salto conversione prodotto.")

    # 5. Hint logico sopra acquisto rapido, se non presente
    if "Percorso logico di compilazione" not in s:
        old = """      <form id="purchase" onSubmit={add} className="form-grid buy-grid">"""
        new = """      <div className="logic-path">
        <span>Percorso logico di compilazione</span>
        <b>Area</b><em>→</em><b>Fornitore</b><em>→</em><b>Categoria</b><em>→</em><b>Sottocategoria</b><em>→</em><b>Formato</b><em>→</em><b>Spessore</b>
      </div>
      <form id="purchase" onSubmit={add} className="form-grid buy-grid">"""
        s = replace_once(s, old, new, "logic path acquisti")

    MAIN.write_text(s, encoding="utf-8")
    print("Frontend UX polish applicato.")


def patch_css():
    css = CSS.read_text(encoding="utf-8")

    if "/* v39.6.1 UX polish modal */" not in css:
        css += r'''

/* v39.6.1 UX polish modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 999999;
  background: rgba(2, 6, 23, .68);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px;
}

.detail-modal {
  width: min(1180px, calc(100vw - 48px));
  max-height: min(860px, calc(100vh - 48px));
  overflow: hidden;
  border-radius: 28px;
  border: 1px solid rgba(148, 163, 184, .28);
  background:
    radial-gradient(circle at top left, rgba(34, 211, 238, .16), transparent 34%),
    linear-gradient(145deg, rgba(15, 23, 42, .98), rgba(2, 6, 23, .96));
  box-shadow: 0 28px 120px rgba(0, 0, 0, .62);
  color: var(--text);
  animation: modalIn .16s ease-out;
}

@keyframes modalIn {
  from { transform: translateY(12px) scale(.985); opacity: 0; }
  to { transform: translateY(0) scale(1); opacity: 1; }
}

.detail-modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 24px;
  border-bottom: 1px solid rgba(148, 163, 184, .16);
}

.detail-modal-title {
  display: flex;
  align-items: center;
  gap: 14px;
}

.detail-modal-title svg {
  width: 28px;
  height: 28px;
  color: #22d3ee;
}

.detail-modal-title h2 {
  margin: 0;
  font-size: 22px;
  letter-spacing: -.02em;
}

.detail-modal-title p {
  margin: 4px 0 0;
  color: var(--muted);
}

.detail-modal-body {
  padding: 22px 24px 26px;
  max-height: calc(100vh - 170px);
  overflow: auto;
}

.detail-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  padding: 18px;
  margin-bottom: 18px;
  border-radius: 22px;
  background: rgba(255,255,255,.055);
  border: 1px solid rgba(148, 163, 184, .16);
}

.detail-hero span {
  display: block;
  color: var(--muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: .08em;
  margin-bottom: 5px;
}

.detail-hero strong {
  display: block;
  font-size: 24px;
  line-height: 1.15;
}

.detail-hero small {
  display: block;
  margin-top: 8px;
  color: var(--muted);
}

.modal-close {
  white-space: nowrap;
}

.compact-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
  max-height: none !important;
  padding: 0;
  background: transparent;
  border: 0;
  box-shadow: none;
}

.compact-suggestions button {
  width: auto !important;
  min-height: 28px;
  padding: 6px 9px;
  border-radius: 999px;
  font-size: 11px;
  line-height: 1;
  border: 1px solid rgba(148, 163, 184, .24);
  background: rgba(255,255,255,.055);
  color: var(--muted);
}

.compact-suggestions button:hover {
  color: var(--text);
  border-color: rgba(34, 211, 238, .45);
  background: rgba(34, 211, 238, .10);
}

.compact-suggestions small {
  display: inline-flex;
  align-items: center;
  color: var(--muted);
  font-size: 11px;
  padding: 0 4px;
}

.logic-path {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 7px;
  margin: 0 0 14px;
  padding: 10px 12px;
  border-radius: 16px;
  background: rgba(34, 211, 238, .07);
  border: 1px solid rgba(34, 211, 238, .18);
}

.logic-path span {
  width: 100%;
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .08em;
}

.logic-path b {
  font-size: 12px;
  color: var(--text);
}

.logic-path em {
  font-style: normal;
  color: #22d3ee;
  opacity: .75;
}

@media (max-width: 900px) {
  .modal-backdrop {
    padding: 12px;
  }

  .detail-modal {
    width: calc(100vw - 24px);
    max-height: calc(100vh - 24px);
    border-radius: 22px;
  }

  .detail-modal-head {
    align-items: flex-start;
    padding: 18px;
  }

  .detail-modal-body {
    padding: 18px;
  }

  .detail-hero {
    flex-direction: column;
  }
}
'''
        CSS.write_text(css, encoding="utf-8")

    print("CSS UX polish applicato.")


def main():
    patch_main()
    patch_css()
    print("Patch v39.6.1 completata.")


if __name__ == "__main__":
    main()
