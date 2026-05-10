import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  AlertTriangle, Archive, ArrowRight, BarChart3, Boxes, Calculator, CheckCircle2,
  ChevronRight, CircleDollarSign, Command, Database, Factory, Gauge, Hammer,
  Layers3, Menu, PackageCheck, PackagePlus, Plus, RefreshCcw, Save, Search,
  Settings2, ShoppingCart, Sparkles, Tags, Trash2, Truck, Users, Wand2, X, Zap, Download, Upload, FileJson, ShieldCheck, Sun, Moon
} from 'lucide-react';
import { getJSON, postJSON, del } from './api';
import { ResponsiveContainer, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, CartesianGrid, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import './style.css';

const money = n => `€ ${Number(n || 0).toFixed(2)}`;
const num = n => Number(n || 0).toFixed(2);
const list = v => Array.isArray(v) ? v : [];
const unique = v => [...new Set(list(v).filter(x => x !== undefined && x !== null && String(x).trim() !== ''))];
const pick = (obj, path, fallback = []) => path.reduce((a, k) => (a && a[k] !== undefined ? a[k] : undefined), obj) ?? fallback;
const rawCats = (s, sec) => unique([...(pick(s, ['raw_categories_by_scope', sec], [])), ...(s?.raw_categories || [])]);
const rawSubs = (s, sec, cat) => unique([...(pick(s, ['raw_subcategories_by_scope_category', sec, cat], [])), ...(!cat ? (s?.raw_subcategories || []) : [])]);
const prodSubs = (s, cat) => unique([...(pick(s, ['product_subcategories_by_category', cat], [])), ...(!cat ? (s?.product_subcategories || []) : [])]);
const collections = (s, cat, sub) => unique([...(pick(s, ['collections_by_product_path', cat, sub], [])), ...(s?.collections || [])]);
const formats = (s, cat) => unique([...(pick(s, ['formats_by_category', cat], [])), ...(s?.formats || [])]);
const thicknesses = (s, cat) => unique([...(pick(s, ['thicknesses_by_category', cat], [])), ...(s?.thicknesses || [])]);
const typologies = (s, cat, sub) => unique([...(pick(s, ['typologies_by_category_subcategory', cat, sub], [])), ...(s?.typologies || [])]);
const rawCatsForSupplier = (s, supplier, sec) => {
  const linked = pick(s, ['raw_categories_by_supplier_scope', supplier, sec], []);
  return supplier ? unique(linked) : rawCats(s, sec);
};
const rawSubsForSupplier = (s, supplier, sec, cat) => {
  const linked = pick(s, ['raw_subcategories_by_supplier_scope_category', supplier, sec, cat], []);
  return supplier ? unique(linked) : rawSubs(s, sec, cat);
};
const suppliersForRaw = (s, sec, cat, sub) => {
  const exact = pick(s, ['suppliers_by_raw_path', sec, cat, sub], []);
  const scoped = pick(s, ['suppliers_by_raw_scope', sec], []);
  return unique([...(exact || []), ...(scoped || []), ...(s?.suppliers || [])]);
};

function useApi(path, initial) {
  const [data, setData] = useState(initial);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const refresh = async () => {
    setLoading(true);
    try {
      const value = await getJSON(path);
      setData(value);
      setError('');
      return value;
    } catch (e) {
      setError(e.message || String(e));
      return initial;
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { refresh(); }, [path]);
  return { data, loading, error, refresh, setData };
}

function useToasts() {
  const [items, setItems] = useState([]);
  const push = (text, type = 'ok') => {
    const id = Date.now() + Math.random();
    setItems(v => [...v, { id, text, type }]);
    setTimeout(() => setItems(v => v.filter(x => x.id !== id)), 3200);
  };
  const Toasts = () => <div className="toasts">{items.map(t => <div key={t.id} className={`toast ${t.type}`}>
    {t.type === 'err' ? <AlertTriangle /> : <CheckCircle2 />}{t.text}
  </div>)}</div>;
  return { push, Toasts };
}

function LaserBackdrop() {
  return <div className="laser-bg laser-bg-premium" aria-hidden="true">
    <svg className="laser-stage" viewBox="0 0 1440 900" preserveAspectRatio="none">
      <defs>
        <linearGradient id="laserBeamA" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="rgba(0,255,232,0)" />
          <stop offset="0.38" stopColor="rgba(0,255,232,.12)" />
          <stop offset="0.49" stopColor="#ffffff" />
          <stop offset="0.55" stopColor="#22fff0" />
          <stop offset="1" stopColor="rgba(0,255,232,0)" />
        </linearGradient>
        <linearGradient id="laserBeamB" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="rgba(255,120,42,0)" />
          <stop offset="0.52" stopColor="rgba(255,132,56,.9)" />
          <stop offset="1" stopColor="rgba(255,120,42,0)" />
        </linearGradient>
        <radialGradient id="hotPoint" cx="50%" cy="50%" r="50%">
          <stop offset="0" stopColor="#fff" />
          <stop offset=".25" stopColor="#8ffff7" />
          <stop offset=".7" stopColor="rgba(34,255,240,.35)" />
          <stop offset="1" stopColor="rgba(34,255,240,0)" />
        </radialGradient>
        <filter id="laserGlow" x="-80%" y="-80%" width="260%" height="260%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feColorMatrix in="blur" type="matrix" values="0 0 0 0 0.08 0 0 0 0 1 0 0 0 0 0.92 0 0 0 .95 0" result="glow"/>
          <feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <pattern id="precisionGrid" width="56" height="56" patternUnits="userSpaceOnUse">
          <path d="M56 0H0V56" fill="none" stroke="currentColor" strokeWidth=".8" opacity=".13"/>
          <circle cx="0" cy="0" r="1.2" fill="currentColor" opacity=".18"/>
        </pattern>
      </defs>

      <rect className="precision-grid" width="1440" height="900" fill="url(#precisionGrid)"/>
      <g className="cad-traces">
        <path d="M110 682 H1260"/>
        <path d="M182 604 H904"/>
        <path d="M214 720 L420 498 H1284"/>
        <path d="M895 124 h330 v260 h-330 z"/>
        <path d="M952 184 h160 v140 h-160 z"/>
        <circle cx="1110" cy="560" r="92"/>
        <path d="M1047 625 l132 -164"/>
      </g>

      <g className="laser-rays primary-rays" filter="url(#laserGlow)">
        <path className="ray ray-a" d="M-80 194 C198 126 342 214 564 196 S960 42 1510 156"/>
        <path className="ray ray-b" d="M-40 622 C224 498 448 608 680 462 S1010 338 1500 430"/>
        <path className="ray ray-c" d="M156 918 C386 660 604 642 842 514 S1116 290 1460 246"/>
      </g>

      <g className="laser-rays amber-rays">
        <path className="ray-hot hot-a" d="M-120 344 C182 382 328 318 548 354 S920 536 1510 512"/>
        <path className="ray-hot hot-b" d="M220 -40 C360 174 472 230 618 330 S838 610 1100 960"/>
      </g>

      <g className="cut-sketches">
        <path className="cutline cutline-a" d="M250 276 C376 132 540 164 620 284 S850 456 1045 282"/>
        <path className="cutline cutline-b" d="M300 526 H560 C648 526 670 410 765 410 H1134"/>
        <path className="cutline cutline-c" d="M195 138 L388 138 L444 244 L340 384 L142 350 Z"/>
      </g>

      <circle className="hot-point hot-point-a" cx="610" cy="284" r="11"/>
      <circle className="hot-point hot-point-b" cx="760" cy="410" r="9"/>
      <circle className="hot-point hot-point-c" cx="1045" cy="282" r="7"/>
    </svg>
  </div>;
}

function Field({ label, children, hint }) { return <label className="field"><span>{label}</span>{children}{hint && <small>{hint}</small>}</label>; }
function Input({ label, ...props }) { return <Field label={label}><input {...props} /></Field>; }
function Select({ label, children, ...props }) { return <Field label={label}><select {...props}>{children}</select></Field>; }
function SmartInput({ label, options = [], hint = '', value, onChange, ...props }) {
  const id = useMemo(() => 'dl_' + Math.random().toString(36).slice(2), []);
  const opts = unique(options);
  const typed = String(value || '').toLowerCase();
  const filtered = opts.filter(x => !typed || String(x).toLowerCase().includes(typed)).slice(0, 5);
  const choose = v => onChange?.({ target: { value: v } });
  return <Field label={label} hint={hint || (opts.length ? `${opts.length} suggerimenti collegati al database` : 'Puoi scrivere un nuovo valore')}>
    <input {...props} value={value ?? ''} onChange={onChange} list={opts.length ? id : undefined} autoComplete="off" />
    {opts.length > 0 && <datalist id={id}>{opts.slice(0, 250).map(v => <option key={v} value={v} />)}</datalist>}
    {filtered.length > 0 && <div className="suggestions">{filtered.map(v => <button type="button" key={v} onMouseDown={e => { e.preventDefault(); choose(v); }}>{v}</button>)}</div>}
  </Field>;
}
function Card({ title, icon: Icon, children, sub, action, className = '' }) { return <section className={`card ${className}`}><header><div>{title && <h2>{Icon && <Icon />}{title}</h2>}{sub && <p>{sub}</p>}</div>{action && <div className="card-actions">{action}</div>}</header>{children}</section>; }
function Stat({ label, value, sub, icon: Icon, tone = '' }) { return <div className={`stat ${tone}`}>{Icon && <Icon />}<span>{label}</span><strong>{value}</strong>{sub && <small>{sub}</small>}</div>; }
function ErrorBox({ msg }) { return msg ? <div className="error"><AlertTriangle />{msg}</div> : null; }
function Empty({ text = 'Nessun dato' }) { return <div className="empty"><Sparkles /><b>{text}</b><span>Inserisci i primi dati o importa il database della versione desktop.</span></div>; }
function Skeleton() { return <div className="skeleton"><i/><i/><i/></div>; }
function SearchBox({ value, onChange, placeholder = 'Cerca...' }) { return <div className="search"><Search /><input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} /></div>; }
function DataTable({ columns, rows, empty = 'Nessun risultato', meta = 'Dati aggiornati dal database', rowClassName }) { return <div className="table-card"><div className="table-meta"><b>{rows.length} righe</b><span>{meta}</span></div><div className="table-wrap"><table><thead><tr>{columns.map(c => <th key={c.key}>{c.label}</th>)}</tr></thead><tbody>{rows.length ? rows.map((r, i) => <tr className={rowClassName ? rowClassName(r, i) : ''} key={r._key || r.key || r.name || i}>{columns.map(c => <td key={c.key}>{c.render ? c.render(r, i) : r[c.key]}</td>)}</tr>) : <tr><td colSpan={columns.length}><Empty text={empty}/></td></tr>}</tbody></table></div></div>; }
function InventoryBadge({ item }) { const status = item?.inventory_status || 'da_verificare'; const label = item?.inventory_badge || 'da verificare'; return <span className={`inventory-badge ${status}`}>{label}</span>; }
function inventoryRowClass(r) { return `inventory-row ${r?.inventory_status || 'da_verificare'}`; }
const inventoryFilterLabel = {
  all: 'Tutti',
  attivo: 'Attivi',
  da_verificare: 'Da verificare',
  mai_acquistato: 'Mai acquistati',
  esaurito: 'Esauriti',
  sotto_scorta: 'Sotto scorta'
};
function PageTitle({ title, desc, children }) { return <div className="page-title"><div><p>Gestionale artigianale</p><h1>{title}</h1><span>{desc}</span></div>{children}</div>; }
function FlowPill({ n, title, desc, detail, icon: Icon, active }) { return <div className={`flow-pill ${active ? 'active' : ''}`}><div className="flow-pill-top"><b>{n}</b>{Icon && <Icon />}</div><div className="flow-pill-copy"><span>{title}</span><small>{desc}</small>{detail && <em>{detail}</em>}</div></div>; }

function Studio({ go }) {
  const { data: d, loading } = useApi('/dashboard', {});
  const { data: r } = useApi('/report', {});
  const { data: alerts } = useApi('/workflow/alerts', {});
  const stats = [
    ['Magazzino', money(d.inventory_value), 'materie prime', Boxes, 'cyan'],
    ['Prodotti', d.products || 0, 'creazioni MN', Factory, 'wood'],
    ['Valore prodotti', money(d.product_value), 'stock finito', PackageCheck, 'mint'],
    ['Vendite', money(d.sales), 'ricavi registrati', CircleDollarSign, 'ink'],
  ];
  return <>
    <PageTitle title="Laboratorio" desc="Una versione più semplice: acquisti, prodotti, produzione, preventivo e vendita restano nello stesso flusso artigianale.">
      <button className="primary" onClick={() => go('atelier')}><Wand2 /> Avvia percorso</button>
    </PageTitle>
    {loading ? <Skeleton /> : <div className="stats">{stats.map(([a,b,c,I,t]) => <Stat key={a} label={a} value={b} sub={c} icon={I} tone={t}/>)}</div>}
    <div className="wide-grid">
      <Card title="Percorso operativo" icon={Zap} sub="Flusso operativo MN Laser Lab: dalla materia prima acquistata al prodotto finito venduto.">
        <div className="flow-strip">
          <FlowPill n="1" icon={Truck} title="Acquisto" desc="Materie prime da fornitori" detail="Legno, acrilico, vernici, LED, componenti e costi reali di carico." />
          <FlowPill n="2" icon={PackagePlus} title="Creo" desc="Scheda prodotto + distinta" detail="Definisco il prodotto MN Laser Lab e collego i materiali necessari." />
          <FlowPill n="3" icon={Factory} title="Produco" desc="Scala materiali, aumenta stock" detail="La produzione scarica il magazzino materie prime e carica i pezzi finiti." />
          <FlowPill n="4" icon={CircleDollarSign} title="Vendo" desc="Preventivo e margine" detail="Calcolo prezzo, sconto, margine e registro la vendita finale." />
        </div>
        <div className="quick-actions"><button onClick={() => go('materials')}>Registra acquisto <ArrowRight /></button><button onClick={() => go('products')}>Crea prodotto finito <ArrowRight /></button><button onClick={() => go('quote')}>Calcola prezzo <ArrowRight /></button><button onClick={() => go('report')}>Controlla margini <ArrowRight /></button></div>
      </Card>
      <Card title="Margine attività" icon={BarChart3} sub="Sintesi economica per capire se ciò che produci conviene davvero.">
        <div className="mini-stats"><Stat label="Raw" value={money(r.raw_total)} /><Stat label="Prodotti" value={money(r.product_total)} /><Stat label="Margine" value={money(r.margin_total)} sub={`${num(r.margin_pct)} %`} /></div>
      </Card>
      <Card title="Da controllare oggi" icon={AlertTriangle} sub="L'app evidenzia le attività che possono bloccare produzione, preventivi o margini.">
        <div className="workflow-alert-grid">
          <button onClick={() => go('materials')}><b>{alerts.materials_to_check || 0}</b><span>Materiali da verificare</span></button>
          <button onClick={() => go('materials')}><b>{alerts.low_stock_materials || 0}</b><span>Sotto scorta</span></button>
          <button onClick={() => go('quote')}><b>{alerts.open_quotes || 0}</b><span>Preventivi aperti</span></button>
          <button onClick={() => go('quote')}><b>{money(alerts.potential_quotes_value)}</b><span>Valore potenziale</span></button>
        </div>
      </Card>
    </div>
  </>;
}

function Atelier({ go }) { return <>
  <PageTitle title="Percorso operativo" desc="Questa pagina è la bussola: meno menu, più processo. Ogni step porta al modulo giusto." />
  <div className="journey">
    <button onClick={() => go('materials')}><Truck /><b>1. Acquisti</b><span>Registra acquisti, fornitore, formato, spessore e costo reale.</span><ChevronRight /></button>
    <button onClick={() => go('products')}><Factory /><b>2. Prodotto MN</b><span>Definisci il prodotto finito, la collezione e la distinta base.</span><ChevronRight /></button>
    <button onClick={() => go('products')}><Hammer /><b>3. Produzione</b><span>Produci pezzi finiti scalando automaticamente i materiali disponibili.</span><ChevronRight /></button>
    <button onClick={() => go('quote')}><Calculator /><b>4. Prezzo</b><span>Calcola prezzo minimo, consigliato, scontato e premium.</span><ChevronRight /></button>
    <button onClick={() => go('sales')}><ShoppingCart /><b>5. Vendita</b><span>Registra vendita e aggiorna lo stock del prodotto finito.</span><ChevronRight /></button>
  </div>
</>; }

function Materials({ toast }) {
  const { data: items, loading, error, refresh } = useApi('/inventory', []);
  const { data: quality } = useApi('/inventory/quality', {});
  const { data: opt } = useApi('/options', {});
  const { data: sug, refresh: refreshSug } = useApi('/suggestions', {});
  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [materialDetail, setMaterialDetail] = useState(null);
  const [f, setF] = useState({ section: 'Falegnameria', supplier: '', category: '', subcategory: '', size: '', thickness: '', unit: 'pz', quantity: 1, total_cost: 0 });
  const generated = useMemo(() => {
    const isWood = f.section === 'Falegnameria';
    const parts = isWood ? [f.subcategory || f.category, f.size, f.thickness] : [f.category, f.subcategory !== f.category ? f.subcategory : '', f.size, f.thickness];
    return parts.filter(Boolean).join(' ');
  }, [f]);
  const rows = list(items).filter(x => {
    const matchesSearch = [x.name, x.section, x.category, x.subcategory, x.supplier_details, x.inventory_badge].join(' ').toLowerCase().includes(q.toLowerCase());
    const matchesStatus = statusFilter === 'all' || x.inventory_status === statusFilter;
    return matchesSearch && matchesStatus;
  });
  async function add(e) { e.preventDefault(); try { await postJSON('/purchase', { ...f, name: generated }); toast('Acquisto registrato'); setF(v => ({ ...v, quantity: 1, total_cost: 0, size: '', thickness: '' })); await refresh(); refreshSug(); } catch (e) { toast(e.message, 'err'); } }
  async function remove(r) { if (!confirm('Eliminare questo articolo?')) return; try { await del('/raw/' + encodeURIComponent(r.table) + '/' + encodeURIComponent(r.key)); toast('Articolo eliminato'); refresh(); } catch (e) { toast(e.message, 'err'); } }
  async function openMaterialDetail(r) {
    try {
      setMaterialDetail(await getJSON('/raw-detail/' + encodeURIComponent(r.table) + '/' + encodeURIComponent(r.key)));
    } catch (e) {
      toast(e.message, 'err');
    }
  }
  return <>
    <PageTitle title="Acquisti" desc="Gestisci materie prime e componenti acquistati: fornitore, categoria, sottocategoria, formato, costo e stock." />
    <ErrorBox msg={error} />
    <Card title="Acquisto rapido" icon={PackagePlus} sub="Compila da sinistra a destra: i suggerimenti cambiano in base a sezione e categoria." action={<button className="primary" form="purchase"><Save /> Salva acquisto</button>}>
      <form id="purchase" onSubmit={add} className="form-grid buy-grid">
        <Select label="Area" value={f.section} onChange={e => setF({ ...f, section: e.target.value, category: '', subcategory: '', size: '', thickness: '' })}>{list(opt.raw_sections).map(x => <option key={x}>{x}</option>)}</Select>
        <SmartInput label="Fornitore" options={suppliersForRaw(sug, f.section, f.category, f.subcategory)} value={f.supplier} onChange={e => setF({ ...f, supplier: e.target.value, category: '', subcategory: '', size: '', thickness: '' })} hint="Se scegli un fornitore già collegato, categorie e sottocategorie vengono filtrate su quel fornitore" />
        <SmartInput label="Categoria" placeholder="Legname, Acrilico, LED..." options={rawCatsForSupplier(sug, f.supplier, f.section)} value={f.category} onChange={e => setF({ ...f, category: e.target.value, subcategory: '', size: '', thickness: '' })} hint={f.supplier ? `Categorie collegate a ${f.supplier}` : 'Scegli prima il fornitore per filtrare il catalogo'} />
        <SmartInput label="Sottocategoria" placeholder="Betulla, Pioppo, Strisce LED..." options={rawSubsForSupplier(sug, f.supplier, f.section, f.category)} value={f.subcategory} onChange={e => setF({ ...f, subcategory: e.target.value, size: '' })} hint={f.supplier && f.category ? 'Sottocategorie filtrate per fornitore + categoria' : 'Seleziona categoria per filtrare'} />
        <SmartInput label="Formato / tipo" options={unique([...formats(sug, f.category), ...typologies(sug, f.category, f.subcategory)])} value={f.size} onChange={e => setF({ ...f, size: e.target.value })} />
        <SmartInput label="Spessore" options={thicknesses(sug, f.category)} value={f.thickness} onChange={e => setF({ ...f, thickness: e.target.value })} />
        <SmartInput label="Unità" options={sug.units} value={f.unit} onChange={e => setF({ ...f, unit: e.target.value })} />
        <Input label="Quantità" type="number" step="0.01" value={f.quantity} onChange={e => setF({ ...f, quantity: e.target.value })} />
        <Input label="Costo totale €" type="number" step="0.01" value={f.total_cost} onChange={e => setF({ ...f, total_cost: e.target.value })} />
        <div className="name-preview"><span>Nome articolo</span><b>{generated || 'Si genera automaticamente'}</b><small>{f.supplier ? `collegato a ${f.supplier}` : 'aggiungi fornitore per tracciabilità'}</small></div>
      </form>
    </Card>
    <div className="stats inventory-quality">
      <Stat label="Attivi" value={quality.active || 0} sub="utilizzabili nei preventivi" icon={CheckCircle2} tone="mint" />
      <Stat label="Da verificare" value={quality.to_check || 0} sub="stock presente ma costo mancante" icon={AlertTriangle} tone="wood" />
      <Stat label="Mai acquistati" value={quality.never_purchased || 0} sub="preset non operativi" icon={Archive} tone="ink" />
      <Stat label="Valore reale" value={money(quality.real_value)} sub="stock valorizzato" icon={CircleDollarSign} tone="cyan" />
    </div>
    <Card title="Stock materiali" icon={Archive} action={<SearchBox value={q} onChange={setQ} placeholder="Cerca materiale, categoria o fornitore..." />}>
      <div className="inventory-filters">
        {Object.entries(inventoryFilterLabel).map(([key, label]) => <button key={key} className={statusFilter === key ? 'active' : ''} onClick={() => setStatusFilter(key)}>{label}</button>)}
      </div>
      {loading ? <Skeleton /> : <DataTable rows={rows} empty="Nessun materiale caricato" rowClassName={inventoryRowClass} columns={[
        { key: 'status', label: 'Stato', render: r => <InventoryBadge item={r} /> },
        { key: 'name', label: 'Articolo' },
        { key: 'section', label: 'Area' },
        { key: 'category', label: 'Categoria' },
        { key: 'subcategory', label: 'Variante' },
        { key: 'qty', label: 'Stock', render: r => `${num(r.stock)} ${r.unit || ''}` },
        { key: 'cost', label: 'Costo medio', render: r => money(r.weighted_average_cost ?? r.cost_per_unit) },
        { key: 'last', label: 'Ultimo acquisto', render: r => <span className="muted-cell">{r.last_supplier ? `${r.last_supplier} · ${money(r.last_unit_cost)}` : '—'}</span> },
        { key: 'sup', label: 'Fornitori', render: r => <span className="muted-cell">{r.supplier_details || '—'}</span> },
        { key: 'act', label: 'Azioni', render: r => <div className="table-actions">
          <button className="ghost" onClick={() => openMaterialDetail(r)}>Dettaglio</button>
          <button className="ghost danger" onClick={() => remove(r)}><Trash2 /></button>
        </div> }
      ]} />}
    </Card>
    {materialDetail && <Card title="Dettaglio materiale" icon={Archive} sub="Storico acquisti, utilizzo nei prodotti e stato economico dell’articolo." action={<button className="ghost" onClick={() => setMaterialDetail(null)}>Chiudi</button>}>
      <div className="detail-grid">
        <Stat label="Articolo" value={materialDetail.name || '—'} />
        <Stat label="Stock" value={`${num(materialDetail.item?.stock)} ${materialDetail.item?.unit || ''}`} />
        <Stat label="Costo medio" value={money(materialDetail.item?.weighted_average_cost ?? materialDetail.item?.cost_per_unit)} />
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
    </Card>}
  </>;
}

function ProductionBox({ products, refresh, toast }) {
  const [name, setName] = useState('');
  const [qty, setQty] = useState(1);
  const [check, setCheck] = useState(null);
  async function checkNow() { if (!name) return; try { setCheck(await postJSON(`/products/${encodeURIComponent(name)}/check-production`, { qty })); } catch (e) { toast(e.message, 'err'); } }
  async function produce() { if (!name) return; try { await postJSON(`/products/${encodeURIComponent(name)}/produce`, { qty, substitutions: {} }); toast('Produzione completata'); setCheck(null); refresh(); } catch (e) { toast(e.message, 'err'); } }
  return <div className="production-panel"><div className="inline"><select value={name} onChange={e => { setName(e.target.value); setCheck(null); }}><option value="">Scegli prodotto</option>{list(products).map(p => <option key={p.name}>{p.name}</option>)}</select><input type="number" step="0.01" value={qty} onChange={e => setQty(e.target.value)} /><button onClick={checkNow}><Search /> Verifica</button><button className="primary" onClick={produce}><Hammer /> Produci</button></div>{check && <div className={check.can_produce ? 'notice ok' : 'notice warn'}>{check.can_produce ? <CheckCircle2 /> : <AlertTriangle />} {check.can_produce ? 'Materiali sufficienti per produrre.' : 'Alcuni materiali risultano insufficienti. Controlla BOM e magazzino.'}</div>}</div>;
}

function ProductWarehouse({ products, refresh, toast, onEdit, onDelete }) {
  const [q, setQ] = useState('');
  const [movement, setMovement] = useState({ product: '', qty: '', reason: 'Rettifica inventario', note: '' });
  const [productDetail, setProductDetail] = useState(null);
  const rows = list(products).filter(x => [x.name, x.category, x.subcategory, x.collection].join(' ').toLowerCase().includes(q.toLowerCase()));
  const totalStock = rows.reduce((a, r) => a + Number(r.stock || 0), 0);
  const totalValue = rows.reduce((a, r) => a + Number(r.value || 0), 0);
  const lowStock = rows.filter(r => Number(r.stock || 0) <= 1).length;
  async function openProductDetail(name) {
    try {
      setProductDetail(await getJSON(`/products/${encodeURIComponent(name)}/detail`));
    } catch (e) {
      toast(e.message, 'err');
    }
  }
  async function adjust(sign = 1) {
    if (!movement.product || Number(movement.qty || 0) <= 0) { toast('Scegli prodotto e quantità valida', 'err'); return; }
    try {
      await postJSON(`/products/${encodeURIComponent(movement.product)}/stock`, { qty: Number(movement.qty) * sign, reason: movement.reason, note: movement.note });
      toast(sign > 0 ? 'Carico prodotto registrato' : 'Scarico prodotto registrato');
      setMovement(v => ({ ...v, qty: '', note: '' }));
      refresh();
    } catch (e) { toast(e.message, 'err'); }
  }
  return <>
    <div className="stats compact-stats">
      <Stat label="Pezzi finiti" value={num(totalStock)} sub="stock prodotti" icon={PackageCheck} tone="mint" />
      <Stat label="Valore magazzino" value={money(totalValue)} sub="costo interno" icon={CircleDollarSign} tone="cyan" />
      <Stat label="Da controllare" value={lowStock} sub="stock ≤ 1" icon={AlertTriangle} tone="wood" />
    </div>
    <Card title="Movimento magazzino prodotti" icon={PackageCheck} sub="Usalo per rettifiche manuali, campioni, pezzi danneggiati o carichi non generati da produzione.">
      <div className="form-grid stock-form">
        <Select label="Prodotto" value={movement.product} onChange={e => setMovement({ ...movement, product: e.target.value })}><option value="">Scegli prodotto</option>{list(products).map(p => <option key={p.name}>{p.name}</option>)}</Select>
        <Input label="Quantità" type="number" step="0.01" value={movement.qty} onChange={e => setMovement({ ...movement, qty: e.target.value })} />
        <SmartInput label="Causale" value={movement.reason} onChange={e => setMovement({ ...movement, reason: e.target.value })} options={['Rettifica inventario','Campione showroom','Pezzo danneggiato','Reso cliente','Carico manuale','Scarico manuale']} />
        <Input label="Nota" value={movement.note} onChange={e => setMovement({ ...movement, note: e.target.value })} />
      </div>
      <div className="quick-actions"><button className="primary" onClick={() => adjust(1)}>+ Carica prodotti</button><button className="danger" onClick={() => adjust(-1)}>- Scarica prodotti</button></div>
    </Card>
    <Card title="Magazzino prodotti finiti" icon={Boxes} action={<SearchBox value={q} onChange={setQ} placeholder="Cerca prodotto, categoria, collezione..." />}>
      <DataTable rows={rows} empty="Nessun prodotto a magazzino" meta="Prodotti creati internamente" columns={[
        { key: 'name', label: 'Prodotto' }, { key: 'category', label: 'Categoria' }, { key: 'subcategory', label: 'Tipo' }, { key: 'collection', label: 'Collezione' },
        { key: 'unit_cost', label: 'Costo interno/u', render: r => <b>{money(r.unit_cost)}</b> },
        { key: 'stock', label: 'Disponibilità', render: r => <span className={Number(r.stock || 0) <= 1 ? 'stock-low' : 'stock-ok'}>{num(r.stock)} {r.unit || 'pz'}</span> },
        { key: 'value', label: 'Valore stock', render: r => money(r.value) },
        { key: 'act', label: 'Azioni', render: r => <div className="table-actions">
          <button className="ghost" onClick={() => openProductDetail(r.name)}>Dettaglio</button>
          <button className="ghost" onClick={() => onEdit(r)}>Modifica</button>
          <button className="ghost danger" onClick={() => onDelete(r.name)}>Elimina</button>
        </div> }
      ]} />
    </Card>
    {productDetail && <Card title="Dettaglio prodotto finito" icon={PackageCheck} sub="Distinta base, costi interni, movimenti e vendite collegate." action={<button className="ghost" onClick={() => setProductDetail(null)}>Chiudi</button>}>
      <div className="detail-grid">
        <Stat label="Prodotto" value={productDetail.name || '—'} />
        <Stat label="Stock" value={`${num(productDetail.stock)} ${productDetail.product?.unit || 'pz'}`} />
        <Stat label="Costo interno/u" value={money(productDetail.unit_cost)} />
        <Stat label="Valore stock" value={money(productDetail.value)} />
      </div>
      <div className="detail-grid compact-detail">
        <Stat label="Materiali/u" value={money(productDetail.material_cost)} />
        <Stat label="Lavoro/u" value={money(productDetail.labor_cost)} />
        <Stat label="Extra/u" value={money(productDetail.extra_cost)} />
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
    </Card>}
  </>;
}

function Products({ toast }) {
  const { data: products, refresh } = useApi('/products', []);
  const { data: inv } = useApi('/inventory', []);
  const { data: movements, refresh: refreshMovements } = useApi('/products/movements', []);
  const { data: opt } = useApi('/options', {});
  const { data: sug, refresh: refreshSug } = useApi('/suggestions', {});
  const [q, setQ] = useState('');
  const [area, setArea] = useState('warehouse');
  const [p, setP] = useState({ name: '', section: 'Prodotti Finiti / Semilavorati', category: '', subcategory: '', collection: '', unit: 'pz', stock: '', labor_hours: '', hourly_rate: '', extra_unit_cost: '', bom: [] });
  const [bom, setBom] = useState({ name: '', qty: '1' });
  const rows = list(products).filter(x => [x.name, x.category, x.subcategory, x.collection].join(' ').toLowerCase().includes(q.toLowerCase()));
  const selectedProduct = list(products).find(x => x.name === p.name);
  async function save(e) { e.preventDefault(); try { await postJSON('/products', p); toast('Scheda prodotto salvata'); setP(v => ({ ...v, name: '', stock: '', bom: [] })); refresh(); refreshSug(); } catch (e) { toast(e.message, 'err'); } }
  async function remove(name) { if (!confirm('Eliminare prodotto?')) return; try { await del('/products/' + encodeURIComponent(name)); toast('Prodotto eliminato'); refresh(); } catch (e) { toast(e.message, 'err'); } }
  function addBom() { if (!bom.name || Number(bom.qty || 0) <= 0) return; setP({ ...p, bom: [...(p.bom || []), { name: bom.name, qty: Number(bom.qty) }] }); setBom({ name: '', qty: '1' }); }
  function editProduct(r) { setP({ ...r, old_name: r.name, bom: r.bom || [], stock: String(r.stock ?? '') }); setArea('sheet'); window.scrollTo({ top: 0, behavior: 'smooth' }); }
  const movementRows = list(movements).slice(0, 12);
  return <>
    <PageTitle title="Produzione" desc="Gestisci schede prodotto, distinta base, produzione e magazzino dei prodotti finiti MN Laser Lab." />
    <div className="section-tabs">
      <button className={area === 'warehouse' ? 'active' : ''} onClick={() => setArea('warehouse')}>Magazzino prodotti</button>
      <button className={area === 'sheet' ? 'active' : ''} onClick={() => setArea('sheet')}>Scheda prodotto e BOM</button>
      <button className={area === 'produce' ? 'active' : ''} onClick={() => setArea('produce')}>Produci</button>
      <button className={area === 'movements' ? 'active' : ''} onClick={() => setArea('movements')}>Movimenti</button>
    </div>
    {area === 'warehouse' && <ProductWarehouse products={products} refresh={() => { refresh(); refreshMovements(); }} toast={toast} onEdit={editProduct} onDelete={remove} />}
    {area === 'sheet' && <div className="split-main">
      <Card title="Scheda prodotto" icon={Factory} sub="Una creazione MN Laser Lab non dipende da un fornitore: dipende da BOM, tempo, stile e magazzino interno." action={<button className="primary" form="product"><Save /> Salva</button>}>
        <form id="product" onSubmit={save} className="form-grid">
          <SmartInput label="Nome prodotto" options={sug.product_names} value={p.name} onChange={e => setP({ ...p, name: e.target.value })} />
          <Select label="Area prodotto" value={p.section} onChange={e => setP({ ...p, section: e.target.value })}>{list(opt.product_sections).map(x => <option key={x}>{x}</option>)}</Select>
          <SmartInput label="Categoria" options={sug.product_categories} value={p.category} onChange={e => setP({ ...p, category: e.target.value, subcategory: '', collection: '' })} />
          <SmartInput label="Sottocategoria" options={prodSubs(sug, p.category)} value={p.subcategory} onChange={e => setP({ ...p, subcategory: e.target.value, collection: '' })} />
          <SmartInput label="Collezione" options={collections(sug, p.category, p.subcategory)} value={p.collection} onChange={e => setP({ ...p, collection: e.target.value })} />
          <SmartInput label="Unità" options={sug.units} value={p.unit} onChange={e => setP({ ...p, unit: e.target.value })} />
          <Input label="Stock iniziale / rettifica" type="number" step="0.01" value={p.stock} onChange={e => setP({ ...p, stock: e.target.value })} />
          <Input label="Ore lavoro/u" type="number" step="0.01" value={p.labor_hours} onChange={e => setP({ ...p, labor_hours: e.target.value })} />
          <Input label="Tariffa €/h" type="number" step="0.01" value={p.hourly_rate} onChange={e => setP({ ...p, hourly_rate: e.target.value })} />
          <Input label="Extra/u €" type="number" step="0.01" value={p.extra_unit_cost} onChange={e => setP({ ...p, extra_unit_cost: e.target.value })} />
        </form>
        {selectedProduct && <div className="notice ok"><CheckCircle2 /> Stai modificando un prodotto esistente. Lo stock attuale è {num(selectedProduct.stock)} {selectedProduct.unit || 'pz'}.</div>}
      </Card>
      <Card title="Distinta base" icon={Layers3} sub="Materiali necessari per produrre 1 pezzo. La produzione scalerà questi articoli dal magazzino acquisti.">
        <div className="inline bom-inline"><select value={bom.name} onChange={e => setBom({ ...bom, name: e.target.value })}><option value="">Materiale</option>{list(inv).map(i => <option key={i.key} value={i.key}>{i.name} — {num(i.stock)} {i.unit}</option>)}</select><input type="number" step="0.01" value={bom.qty} onChange={e => setBom({ ...bom, qty: e.target.value })} /><button onClick={addBom}><Plus /> Aggiungi</button></div>
        <div className="bom-list">{(p.bom || []).length ? p.bom.map((r, i) => <span key={i}>{r.name} × {r.qty}<button onClick={() => setP({ ...p, bom: p.bom.filter((_, j) => j !== i) })}>×</button></span>) : <Empty text="Nessun materiale nel BOM" />}</div>
      </Card>
    </div>}
    {area === 'produce' && <Card title="Produzione rapida" icon={Hammer} sub="Controlla disponibilità materiali, produci e carica automaticamente il magazzino prodotti finiti."><ProductionBox products={products} refresh={() => { refresh(); refreshMovements(); }} toast={toast} /></Card>}
    {area === 'movements' && <Card title="Ultimi movimenti prodotti" icon={Archive} sub="Storico carichi, scarichi manuali e produzioni registrate.">
      <DataTable rows={movementRows} empty="Nessun movimento registrato" columns={[
        { key: 'date', label: 'Data' }, { key: 'product', label: 'Prodotto' }, { key: 'qty', label: 'Quantità', render: r => `${Number(r.qty || 0) > 0 ? '+' : ''}${num(r.qty)}` }, { key: 'reason', label: 'Causale' }, { key: 'note', label: 'Nota' }
      ]} />
    </Card>}
    {area !== 'warehouse' && <Card title="Catalogo produzione" icon={PackageCheck} action={<SearchBox value={q} onChange={setQ} placeholder="Cerca prodotto..." />}>
      <DataTable rows={rows} empty="Nessun prodotto creato" meta="Schede prodotto MN Laser Lab" columns={[
        { key: 'name', label: 'Prodotto' }, { key: 'category', label: 'Categoria' }, { key: 'subcategory', label: 'Tipo' }, { key: 'collection', label: 'Collezione' },
        { key: 'cost', label: 'Costo/u', render: r => <b>{money(r.unit_cost)}</b> }, { key: 'stock', label: 'Stock', render: r => `${num(r.stock)} ${r.unit || 'pz'}` }, { key: 'value', label: 'Valore', render: r => money(r.value) },
        { key: 'act', label: '', render: r => <div className="row-actions"><button onClick={() => editProduct(r)}>Modifica</button><button className="ghost danger" onClick={() => remove(r.name)}><Trash2 /></button></div> }
      ]} />
    </Card>}
  </>;
}

function Quote({ toast }) {
  const { data: inv } = useApi('/inventory', []);
  const { data: sug } = useApi('/suggestions', {});
  const { data: business } = useApi('/settings/business', {});
  const { data: savedQuotes, refresh: refreshQuotes } = useApi('/quotes', []);
  const [rows, setRows] = useState([]);
  const [item, setItem] = useState('');
  const [qty, setQty] = useState('1');
  const [res, setRes] = useState(null);
  const [quoteName, setQuoteName] = useState('');
  const [quoteCustomer, setQuoteCustomer] = useState('');
  const [quoteNotes, setQuoteNotes] = useState('');
  const [materialSearch, setMaterialSearch] = useState('');
  const [filters, setFilters] = useState({ supplier: '', section: '', category: '', subcategory: '' });
  const [cost, setCost] = useState({ hours: '', rate: '', packaging: '', energy: '', wear: '', commission: '', margin: '30', discount: '' });

  useEffect(() => {
    if (!business || Object.keys(business).length === 0) return;
    setCost(v => ({
      ...v,
      rate: v.rate || business.hourly_rate || '',
      packaging: v.packaging || business.default_packaging || '',
      energy: v.energy || business.default_energy || '',
      wear: v.wear || business.default_wear || '',
      commission: v.commission || business.default_commission || '',
      margin: v.margin || business.default_margin || '30',
      discount: v.discount || business.default_discount || ''
    }));
  }, [business]);

  const filteredMaterials = useMemo(() => {
    const q = materialSearch.toLowerCase().trim();
    return list(inv).filter(i => {
      if (!i.usable_in_quote) return false;
      const text = [i.name, i.section, i.category, i.subcategory, i.supplier_details, i.unit, i.size, i.thickness].join(' ').toLowerCase();
      if (q && !q.split(/\s+/).every(part => text.includes(part))) return false;
      if (filters.supplier && !String(i.supplier_details || '').toLowerCase().includes(filters.supplier.toLowerCase())) return false;
      if (filters.section && i.section !== filters.section) return false;
      if (filters.category && i.category !== filters.category) return false;
      if (filters.subcategory && i.subcategory !== filters.subcategory) return false;
      return true;
    }).slice(0, 120);
  }, [inv, materialSearch, filters]);

  const selectedMaterial = list(inv).find(x => x.key === item);
  const materialCost = selectedMaterial ? Number((selectedMaterial.weighted_average_cost ?? selectedMaterial.cost_per_unit) || 0) * Number(qty || 0) : 0;
  const supplierChoices = unique(list(inv).flatMap(i => String(i.supplier_details || '').split('|').map(x => x.split(':')[0].trim())));
  const sectionChoices = unique(list(inv).map(i => i.section));
  const categoryChoices = unique(list(inv).filter(i => !filters.section || i.section === filters.section).map(i => i.category));
  const subcategoryChoices = unique(list(inv).filter(i => (!filters.section || i.section === filters.section) && (!filters.category || i.category === filters.category)).map(i => i.subcategory));

  function addMaterial(materialKey = item, amount = qty) {
    const it = list(inv).find(x => x.key === materialKey);
    const qn = Number(amount || 0);
    if (!it || qn <= 0) {
      toast('Seleziona un materiale e una quantità valida', 'err');
      return;
    }
    if (!it.usable_in_quote) {
      toast('Materiale non utilizzabile: stock o costo medio non valorizzato', 'err');
      return;
    }
    if (Number(it.stock || 0) < qn) {
      toast(`Stock insufficiente: disponibile ${num(it.stock)} ${it.unit || ''}`, 'err');
      return;
    }
    const unitCost = Number((it.weighted_average_cost ?? it.cost_per_unit) || 0);
    setRows(v => [...v, {
      name: materialKey,
      key: materialKey,
      qty: qn,
      stock: Number(it.stock || 0),
      unit_cost: unitCost,
      cost_per_unit: unitCost,
      weighted_average_cost: unitCost,
      cost: qn * unitCost,
      label: it.name,
      unit: it.unit || '',
      category: it.category || '',
      supplier: it.supplier_details || '',
    }]);
    setQty('1');
    setRes(null);
  }

  async function calc() {
    try {
      setRes(await postJSON('/quote/calculate', { rows, estimated_materials: [], ...cost }));
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function sale() {
    if (!res) return;
    const name = prompt('Nome vendita', quoteName || 'Vendita da preventivo') || 'Vendita da preventivo';
    try {
      await postJSON('/quote/sale', { name, customer: quoteCustomer, qty: 1, unit_price: res.discounted || res.recommended, rows, estimated_materials: [], ...cost });
      toast('Vendita da preventivo registrata');
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function saveQuote(status = 'draft') {
    try {
      const payload = {
        name: quoteName || 'Preventivo senza nome',
        customer: quoteCustomer,
        notes: quoteNotes,
        status,
        rows,
        estimates: [],
        estimated_materials: [],
        ...cost
      };
      const saved = await postJSON('/quotes', payload);
      setRes(saved.result || res);
      await refreshQuotes();
      toast(status === 'sent' ? 'Preventivo salvato come inviato' : 'Preventivo salvato');
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function quoteToProduct(q) {
    const name = prompt('Nome prodotto da creare', q.name || 'Prodotto da preventivo');
    if (!name) return;
    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/to-product`, { name });
      await refreshQuotes();
      toast('Prodotto creato dal preventivo');
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function changeQuoteStatus(q, status) {
    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/status`, { status });
      await refreshQuotes();
      toast('Stato preventivo aggiornato');
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  const costLabels = {
    hours: 'Ore lavoro', rate: 'Tariffa €/h', packaging: 'Imballaggio €', energy: 'Energia €', wear: 'Usura macchina €', commission: 'Commissioni %', margin: 'Margine %', discount: 'Sconto %'
  };

  return <>
    <PageTitle title="Preventivi" desc="Costruisci il prezzo partendo dai materiali reali del magazzino, poi aggiungi lavoro, consumi, commissioni e margine." />

    <Card title="Dati preventivo" icon={FileJson} sub="Salva bozze, invia preventivi e trasformali in prodotti finiti quando diventano ripetibili.">
      <div className="form-grid">
        <Input label="Nome preventivo / prodotto" value={quoteName} onChange={e => setQuoteName(e.target.value)} placeholder="Es. Orologio One Piece 40 cm" />
        <SmartInput label="Cliente" options={sug.customers} value={quoteCustomer} onChange={e => setQuoteCustomer(e.target.value)} placeholder="Cliente o vendita diretta" />
        <Input label="Note" value={quoteNotes} onChange={e => setQuoteNotes(e.target.value)} placeholder="Dettagli lavorazione, personalizzazione, consegna..." />
      </div>
      <div className="quick-actions">
        <button onClick={() => saveQuote('draft')}><Save /> Salva bozza</button>
        <button onClick={() => saveQuote('sent')}><ArrowRight /> Segna inviato</button>
      </div>
    </Card>

    <div className="quote-layout">
      <Card title="Ricerca rapida materiali" icon={Search} sub="Cerca nel magazzino per nome, categoria, fornitore, formato o spessore. Aggiungi i materiali al preventivo con un click.">
        <div className="quote-search-head">
          <SearchBox value={materialSearch} onChange={setMaterialSearch} placeholder="Cerca: betulla 40x40, led, acrilico nero, fornitore..." />
          <button className="ghost" onClick={() => { setMaterialSearch(''); setFilters({ supplier: '', section: '', category: '', subcategory: '' }); }}><RefreshCcw /> Pulisci</button>
        </div>
        <div className="quote-filters">
          <SmartInput label="Fornitore" options={supplierChoices} value={filters.supplier} onChange={e => setFilters({ ...filters, supplier: e.target.value })} />
          <SmartInput label="Area" options={sectionChoices} value={filters.section} onChange={e => setFilters({ ...filters, section: e.target.value, category: '', subcategory: '' })} />
          <SmartInput label="Categoria" options={categoryChoices} value={filters.category} onChange={e => setFilters({ ...filters, category: e.target.value, subcategory: '' })} />
          <SmartInput label="Sottocategoria" options={subcategoryChoices} value={filters.subcategory} onChange={e => setFilters({ ...filters, subcategory: e.target.value })} />
        </div>
        <div className="material-browser">
          {filteredMaterials.length ? filteredMaterials.map(m => <button type="button" key={m.key} className={item === m.key ? 'material-pick active' : 'material-pick'} onClick={() => setItem(m.key)}>
            <span><b>{m.name}</b><small>{[m.section, m.category, m.subcategory, m.size, m.thickness].filter(Boolean).join(' · ')}</small><InventoryBadge item={m} /></span>
            <em>{num(m.stock)} {m.unit || ''}</em>
            <strong>{money(m.weighted_average_cost ?? m.cost_per_unit)}</strong>
          </button>) : <Empty text="Nessun materiale disponibile per preventivi" />}
        </div>
      </Card>

      <Card title="Materiali nel preventivo" icon={Boxes} sub="Seleziona un materiale dalla ricerca, imposta la quantità e aggiungilo al calcolo.">
        <div className="selected-material-box">
          {selectedMaterial ? <>
            <span>Materiale selezionato</span>
            <b>{selectedMaterial.name}</b>
            <small>{[selectedMaterial.section, selectedMaterial.category, selectedMaterial.subcategory].filter(Boolean).join(' · ') || 'Magazzino'}</small>
          </> : <Empty text="Seleziona un materiale" />}
        </div>
        <div className="inline quote-add-line">
          <input type="number" step="0.01" value={qty} onChange={e => setQty(e.target.value)} placeholder="Quantità" />
          <div className="quote-mini-total"><span>Costo riga</span><b>{money(materialCost)}</b></div>
          <button className="primary" onClick={() => addMaterial()}><Plus /> Aggiungi</button>
        </div>
        <div className="quote-rows">
          {rows.length ? rows.map((r, i) => <div className="quote-row" key={i}>
            <div><b>{r.label}</b><small>{r.category || 'Materiale'} · {r.qty} {r.unit}</small></div>
            <strong>{money(r.cost)}</strong>
            <button className="ghost danger" onClick={() => { setRows(rows.filter((_, j) => j !== i)); setRes(null); }}>×</button>
          </div>) : <Empty text="Nessun materiale aggiunto" />}
        </div>
      </Card>
    </div>

    <div className="split-main">
      <Card title="Costi e margini" icon={Calculator} action={<button className="primary" onClick={calc}><Calculator /> Calcola preventivo</button>}>
        <div className="form-grid small-grid">
          {Object.keys(cost).map(k => <Input key={k} label={costLabels[k] || k} type="number" step="0.01" value={cost[k]} onChange={e => setCost({ ...cost, [k]: e.target.value })} />)}
        </div>
        {res && <div className="quick-actions"><button onClick={sale}><ShoppingCart /> Registra vendita da preventivo</button><button onClick={() => saveQuote('draft')}><Save /> Salva preventivo</button></div>}
      </Card>
      <Card title="Riepilogo rapido" icon={Gauge} sub="Il prezzo consigliato tiene conto di costi reali, commissioni e margine desiderato.">
        {res ? <div className="quote-result-grid">
          <Stat label="Costo reale" value={money(res.real_cost)} />
          <Stat label="Prezzo minimo" value={money(res.min_price)} />
          <Stat label="Consigliato" value={money(res.recommended)} tone="mint" />
          <Stat label="Scontato" value={money(res.discounted)} />
          <Stat label="Premium" value={money(res.premium)} tone="wood" />
        </div> : <Empty text="Calcola il preventivo" />}
      </Card>
    </div>

    <Card title="Archivio preventivi" icon={FileJson} sub="Pipeline commerciale: bozze, inviati, accettati e rifiutati.">
      <DataTable rows={list(savedQuotes)} empty="Nessun preventivo salvato" columns={[
        { key: 'date', label: 'Data' },
        { key: 'name', label: 'Preventivo' },
        { key: 'customer', label: 'Cliente', render: r => r.customer || '—' },
        { key: 'status', label: 'Stato', render: r => <span className={`quote-status ${r.status || 'draft'}`}>{r.status_label || r.status || 'bozza'}</span> },
        { key: 'value', label: 'Valore', render: r => money(r.potential_value || r.recommended || r.discounted) },
        { key: 'act', label: 'Azioni', render: r => <div className="table-actions">
          <button className="ghost" onClick={() => changeQuoteStatus(r, 'sent')}>Inviato</button>
          <button className="ghost" onClick={() => changeQuoteStatus(r, 'accepted')}>Accettato</button>
          <button className="ghost" onClick={() => changeQuoteStatus(r, 'rejected')}>Rifiutato</button>
          <button className="ghost" onClick={() => quoteToProduct(r)}>Crea prodotto</button>
        </div> }
      ]} />
    </Card>
  </>;
}


function Sales({ toast }) {
  const { data: sales, refresh } = useApi('/sales', []);
  const { data: products } = useApi('/products', []);
  const { data: people } = useApi('/people', { customers: {} });
  const [f, setF] = useState({ product: '', customer: '', qty: 1, unit_price: 0 });
  async function add(e) { e.preventDefault(); try { await postJSON('/sales', f); toast('Vendita registrata'); setF({ product: '', customer: '', qty: 1, unit_price: 0 }); refresh(); } catch (e) { toast(e.message, 'err'); } }
  async function rem(id) { if (!confirm('Eliminare vendita e ripristinare stock se possibile?')) return; try { await del('/sales/' + id); toast('Vendita eliminata'); refresh(); } catch (e) { toast(e.message, 'err'); } }
  return <>
    <PageTitle title="Vendite" desc="Registra le uscite dei prodotti finiti e mantieni aggiornato lo stock." />
    <Card title="Nuova vendita da magazzino" icon={ShoppingCart} action={<button className="primary" form="sale"><Save /> Registra</button>}><form id="sale" onSubmit={add} className="form-grid"><Select label="Prodotto" value={f.product} onChange={e => setF({ ...f, product: e.target.value })}><option value="">Scegli prodotto</option>{list(products).map(p => <option key={p.name}>{p.name}</option>)}</Select><SmartInput label="Cliente" options={Object.keys(people.customers || {})} value={f.customer} onChange={e => setF({ ...f, customer: e.target.value })}/><Input label="Quantità" type="number" step="0.01" value={f.qty} onChange={e => setF({ ...f, qty: e.target.value })}/><Input label="Prezzo unitario €" type="number" step="0.01" value={f.unit_price} onChange={e => setF({ ...f, unit_price: e.target.value })}/></form></Card>
    <Card title="Registro vendite" icon={CircleDollarSign}><DataTable rows={list(sales)} empty="Nessuna vendita" columns={[{key:'date_normalized',label:'Data'},{key:'product',label:'Prodotto'},{key:'qty',label:'Q.tà',render:r=>num(r.qty)},{key:'unit_price',label:'Prezzo/u',render:r=>money(r.unit_price)},{key:'total',label:'Totale',render:r=>money(r.total)},{key:'source',label:'Origine'},{key:'act',label:'',render:r=><button className="ghost danger" onClick={()=>rem(r.id)}><Trash2/></button>}]} /></Card>
  </>;
}

function Setup({ toast }) {
  const { data: tax, refresh: refreshTax } = useApi('/taxonomy', { raw_tree: [], product_tree: [], supplier_matrix: [] });
  const { data: sug, refresh: refreshSug } = useApi('/suggestions', {});
  const [raw, setRaw] = useState({ scope: 'materials', category: '', subcategory: '' });
  const [prod, setProd] = useState({ category: '', subcategory: '', collection: '' });
  async function save(path, obj, msg) { try { await postJSON(path, obj); toast(msg); refreshTax(); refreshSug(); } catch (e) { toast(e.message, 'err'); } }
  const rawRows = list(tax.raw_tree).flatMap(sec => list(sec.categories).flatMap(c => list(c.subcategories).length ? list(c.subcategories).map(sub => ({ area: sec.label, category: c.name, subcategory: sub, suppliers: c.suppliers })) : [{ area: sec.label, category: c.name, subcategory: '—', suppliers: c.suppliers }]));
  const prodRows = Object.entries(sug.collections_by_product_path || {}).flatMap(([cat, subMap]) => Object.entries(subMap || {}).flatMap(([sub, cols]) => list(cols).map(col => ({ category: cat, subcategory: sub, collection: col }))));
  return <>
    <PageTitle title="Categorie" desc="Qui organizzi la struttura dati: materiali acquistati dai fornitori da una parte, prodotti finiti creati da MN Laser Lab dall’altra." />
    <div className="split-main">
      <Card title="Catalogo materiali" icon={Truck} sub="Categorie usate per acquisti, stock e fornitori. Esempio: Falegnameria → Legname → Betulla." action={<button onClick={() => save('/categories', raw, 'Categoria materiale salvata')}><Plus /> Salva</button>}>
        <div className="form-grid">
          <Select label="Area" value={raw.scope} onChange={e=>setRaw({...raw,scope:e.target.value,category:'',subcategory:''})}>
            <option value="materials">Falegnameria</option><option value="components">Ferramenta</option><option value="Illuminazione">Illuminazione</option>
          </Select>
          <SmartInput label="Categoria materiale" options={rawCats(sug, raw.scope)} value={raw.category} onChange={e=>setRaw({...raw,category:e.target.value,subcategory:''})}/>
          <SmartInput label="Sottocategoria / variante" options={rawSubs(sug, raw.scope, raw.category)} value={raw.subcategory} onChange={e=>setRaw({...raw,subcategory:e.target.value})}/>
        </div>
      </Card>
      <Card title="Catalogo prodotti finiti" icon={Tags} sub="Categorie commerciali dei prodotti che realizzi tu. Esempio: Orologi → Anime → One Piece." action={<button onClick={() => save('/product-links', prod, 'Collezione prodotto salvata')}><Plus /> Salva</button>}>
        <div className="form-grid">
          <SmartInput label="Categoria prodotto" options={sug.product_categories} value={prod.category} onChange={e=>setProd({...prod,category:e.target.value,subcategory:'',collection:''})}/>
          <SmartInput label="Sottocategoria prodotto" options={prodSubs(sug, prod.category)} value={prod.subcategory} onChange={e=>setProd({...prod,subcategory:e.target.value,collection:''})}/>
          <SmartInput label="Collezione / tema" options={collections(sug, prod.category, prod.subcategory)} value={prod.collection} onChange={e=>setProd({...prod,collection:e.target.value})}/>
        </div>
      </Card>
    </div>
    <div className="split-main">
      <Card title="Categorie materiali presenti" icon={Layers3}>
        <DataTable rows={rawRows} empty="Nessuna categoria materiale" columns={[{key:'area',label:'Area'},{key:'category',label:'Categoria'},{key:'subcategory',label:'Sottocategoria'},{key:'suppliers',label:'Fornitori',render:r=>r.suppliers || 0}]} />
      </Card>
      <Card title="Categorie prodotti presenti" icon={Factory}>
        <DataTable rows={prodRows} empty="Nessuna categoria prodotto" columns={[{key:'category',label:'Categoria'},{key:'subcategory',label:'Sottocategoria'},{key:'collection',label:'Collezione'}]} />
      </Card>
    </div>
  </>;
}

function People({ toast }) {
  const { data: people, refresh } = useApi('/people', { customers: {}, suppliers: {} });
  const { data: sug, refresh: refreshSug } = useApi('/suggestions', {});
  const { data: opt } = useApi('/options', {});
  const [supplier, setSupplier] = useState({ name: '', section: 'Falegnameria', category: '', subcategory: '' });
  const [customer, setCustomer] = useState({ name: '', notes: '' });
  async function saveSupplier(e) { e?.preventDefault?.(); try { await postJSON('/suppliers', supplier); toast('Fornitore salvato'); setSupplier({ name: '', section: supplier.section || 'Falegnameria', category: '', subcategory: '' }); refresh(); refreshSug(); } catch (e) { toast(e.message, 'err'); } }
  async function saveCustomer(e) { e?.preventDefault?.(); try { await postJSON('/customers', customer); toast('Cliente salvato'); setCustomer({ name: '', notes: '' }); refresh(); refreshSug(); } catch (e) { toast(e.message, 'err'); } }
  async function removeSupplier(name) { if (!confirm('Eliminare questo fornitore?')) return; try { await del('/suppliers/' + encodeURIComponent(name)); toast('Fornitore eliminato'); refresh(); refreshSug(); } catch (e) { toast(e.message, 'err'); } }
  async function removeCustomer(name) { if (!confirm('Eliminare questo cliente?')) return; try { await del('/customers/' + encodeURIComponent(name)); toast('Cliente eliminato'); refresh(); refreshSug(); } catch (e) { toast(e.message, 'err'); } }
  const supplierRows = Object.entries(people.suppliers || {}).map(([name, info]) => ({
    name,
    sections: list(info.sections).join(', ') || 'Tutte le aree',
    links: list(info.links).map(l => [l.section, l.category, l.subcategory].filter(Boolean).join(' → ')).join(' | ') || 'Nessuna categoria collegata'
  }));
  const customerRows = Object.entries(people.customers || {}).map(([name, info]) => ({ name, notes: info.notes || '' }));
  return <>
    <PageTitle title="Clienti e fornitori" desc="Sezione dedicata ai contatti: fornitori per acquistare materiali, clienti per preventivi e vendite." />
    <div className="split-main">
      <Card title="Nuovo fornitore" icon={Truck} sub="Collega il fornitore a un’area e, quando possibile, alla categoria/sottocategoria che vende. Così negli acquisti non vedrai più suggerimenti generici." action={<button className="primary" form="supplier-form"><Save /> Salva collegamento</button>}>
        <form id="supplier-form" onSubmit={saveSupplier} className="form-grid">
          <SmartInput label="Nome fornitore" options={sug.suppliers} value={supplier.name} onChange={e=>setSupplier({...supplier,name:e.target.value})}/>
          <Select label="Area collegata" value={supplier.section} onChange={e=>setSupplier({...supplier,section:e.target.value,category:'',subcategory:''})}>{list(opt.raw_sections).map(x=><option key={x}>{x}</option>)}</Select>
          <SmartInput label="Categoria fornita" options={rawCats(sug, supplier.section)} value={supplier.category} onChange={e=>setSupplier({...supplier,category:e.target.value,subcategory:''})} hint="Esempio: Legname, Acrilico, LED, Vernici"/>
          <SmartInput label="Sottocategoria fornita" options={rawSubs(sug, supplier.section, supplier.category)} value={supplier.subcategory} onChange={e=>setSupplier({...supplier,subcategory:e.target.value})} hint="Esempio: Betulla, Pioppo, Strisce LED"/>
        </form>
      </Card>
      <Card title="Nuovo cliente" icon={Users} sub="Usa i clienti per preventivi, vendite e storico lavori personalizzati." action={<button className="primary" form="customer-form"><Save /> Salva cliente</button>}>
        <form id="customer-form" onSubmit={saveCustomer} className="form-grid">
          <SmartInput label="Nome cliente" options={sug.customers} value={customer.name} onChange={e=>setCustomer({...customer,name:e.target.value})}/>
          <Input label="Note" value={customer.notes} onChange={e=>setCustomer({...customer,notes:e.target.value})}/>
        </form>
      </Card>
    </div>
    <div className="split-main">
      <Card title="Elenco fornitori" icon={Truck}>
        <DataTable rows={supplierRows} empty="Nessun fornitore salvato" columns={[{key:'name',label:'Fornitore'},{key:'sections',label:'Aree'},{key:'links',label:'Categorie collegate',render:r=><span className="muted-cell">{r.links}</span>},{key:'act',label:'',render:r=><button className="ghost danger" onClick={()=>removeSupplier(r.name)}><Trash2 /></button>}]} />
      </Card>
      <Card title="Elenco clienti" icon={Users}>
        <DataTable rows={customerRows} empty="Nessun cliente salvato" columns={[{key:'name',label:'Cliente'},{key:'notes',label:'Note',render:r=><span className="muted-cell">{r.notes || '—'}</span>},{key:'act',label:'',render:r=><button className="ghost danger" onClick={()=>removeCustomer(r.name)}><Trash2 /></button>}]} />
      </Card>
    </div>
  </>;
}


const chartColors = ['#058482', '#111827', '#b8894b', '#6b7280', '#94a3b8', '#d97706', '#0f766e'];
const shortMoney = v => `€ ${Math.round(Number(v || 0)).toLocaleString('it-IT')}`;
const percent = v => `${Number(v || 0).toFixed(1)}%`;

function ChartBox({ title, children, sub }) {
  return <div className="chart-box"><div className="chart-head"><b>{title}</b>{sub && <span>{sub}</span>}</div><div className="chart-body">{children}</div></div>;
}

function SimpleTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return <div className="chart-tooltip"><b>{label}</b>{payload.map((p, i) => <span key={i}>{p.name}: {typeof p.value === 'number' ? shortMoney(p.value) : p.value}</span>)}</div>;
}

function PivotTable({ rows }) {
  const months = unique(rows.map(r => r.month)).sort();
  const products = unique(rows.map(r => r.product)).sort();
  const value = (product, month, key='revenue') => rows.find(r => r.product === product && r.month === month)?.[key] || 0;
  return <div className="pivot-wrap"><table className="pivot-table"><thead><tr><th>Prodotto</th>{months.map(m => <th key={m}>{m}</th>)}<th>Totale</th></tr></thead><tbody>{products.length ? products.map(p => {
    const total = months.reduce((a,m)=>a+value(p,m),0);
    return <tr key={p}><td><b>{p}</b></td>{months.map(m => <td key={m}>{value(p,m) ? shortMoney(value(p,m)) : '—'}</td>)}<td><b>{shortMoney(total)}</b></td></tr>;
  }) : <tr><td colSpan={months.length + 2}>Nessun dato pivot disponibile</td></tr>}</tbody></table></div>;
}

function Report() {
  const { data: r, loading, refresh } = useApi('/report', {});
  const [view, setView] = useState('overview');
  const monthly = list(r.sales_by_month);
  const bySource = list(r.sales_by_source);
  const margins = list(r.margins_by_product || r.products);
  const stockSections = list(r.stock_by_section || r.sections);
  const stockCategories = list(r.stock_by_category);
  const details = list(r.sales_detail);
  const lowStock = list(r.low_stock);

  const bestProduct = margins[0]?.product || '—';
  const avgTicket = details.length ? Number(r.sales_total || 0) / details.length : 0;

  return <>
    <PageTitle title="Report e analisi" desc="Pivot, grafici e indicatori per capire cosa produce margine e dove intervenire.">
      <button className="ghost" onClick={refresh}><RefreshCcw /> Aggiorna</button>
    </PageTitle>

    {loading ? <Skeleton /> : <>
      <div className="stats report-stats">
        <Stat label="Valore materiali" value={money(r.raw_total)} icon={Boxes}/>
        <Stat label="Valore prodotti" value={money(r.product_total)} icon={PackageCheck}/>
        <Stat label="Vendite" value={money(r.sales_total)} sub={`${details.length} movimenti`} icon={ShoppingCart}/>
        <Stat label="Margine lordo" value={money(r.margin_total)} sub={percent(r.margin_pct)} icon={BarChart3} tone="mint"/>
        <Stat label="Scontrino medio" value={money(avgTicket)} sub={`Top: ${bestProduct}`} icon={CircleDollarSign}/>
      </div>

      <div className="report-tabs">
        {[['overview','Sintesi'], ['charts','Grafici'], ['pivot','Pivot'], ['details','Dettaglio']].map(([id,label]) => <button key={id} className={view === id ? 'on' : ''} onClick={()=>setView(id)}>{label}</button>)}
      </div>

      {view === 'overview' && <>
        <div className="report-grid two">
          <ChartBox title="Vendite e margine nel tempo" sub="Andamento mensile">
            <ResponsiveContainer width="100%" height="100%"><AreaChart data={monthly}><defs><linearGradient id="mnRevenue" x1="0" x2="0" y1="0" y2="1"><stop offset="5%" stopColor="#058482" stopOpacity={0.45}/><stop offset="95%" stopColor="#058482" stopOpacity={0.02}/></linearGradient></defs><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="month"/><YAxis tickFormatter={v=>`€${v}`}/><Tooltip content={<SimpleTooltip/>}/><Legend/><Area name="Vendite" type="monotone" dataKey="revenue" stroke="#058482" fill="url(#mnRevenue)"/><Area name="Margine" type="monotone" dataKey="margin" stroke="#111827" fill="#11182722"/></AreaChart></ResponsiveContainer>
          </ChartBox>
          <ChartBox title="Ricavi per origine" sub="Magazzino, preventivo, manuale">
            <ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={bySource} dataKey="revenue" nameKey="source" innerRadius={58} outerRadius={92} paddingAngle={4}>{bySource.map((_,i)=><Cell key={i} fill={chartColors[i%chartColors.length]}/>)}</Pie><Tooltip content={<SimpleTooltip/>}/><Legend/></PieChart></ResponsiveContainer>
          </ChartBox>
        </div>
        <div className="split-main">
          <Card title="Prodotti più redditizi" icon={BarChart3} sub="Classifica ordinata per margine lordo">
            <DataTable rows={margins.slice(0,8)} empty="Nessuna vendita registrata" columns={[{key:'product',label:'Prodotto'},{key:'revenue',label:'Ricavi',render:x=>money(x.revenue)},{key:'cost',label:'Costi',render:x=>money(x.cost)},{key:'margin',label:'Margine',render:x=><b>{money(x.margin)}</b>},{key:'margin_pct',label:'Margine %',render:x=>percent(x.margin_pct)}]} />
          </Card>
          <Card title="Materiali sotto controllo" icon={AlertTriangle} sub="Articoli con stock basso o nullo">
            <DataTable rows={lowStock.slice(0,10)} empty="Nessuna criticità evidente" columns={[{key:'name',label:'Articolo'},{key:'category',label:'Categoria'},{key:'supplier',label:'Fornitore'},{key:'qty',label:'Q.tà',render:x=>`${num(x.qty)} ${x.unit || ''}`}]} />
          </Card>
        </div>
      </>}

      {view === 'charts' && <>
        <div className="report-grid two">
          <ChartBox title="Margine per prodotto" sub="Confronto prodotti venduti">
            <ResponsiveContainer width="100%" height="100%"><BarChart data={margins.slice(0,10)} layout="vertical"><CartesianGrid strokeDasharray="3 3" horizontal={false}/><XAxis type="number" tickFormatter={v=>`€${v}`}/><YAxis type="category" dataKey="product" width={120}/><Tooltip content={<SimpleTooltip/>}/><Bar name="Margine" dataKey="margin" fill="#058482" radius={[0,8,8,0]}/></BarChart></ResponsiveContainer>
          </ChartBox>
          <ChartBox title="Valore stock per sezione" sub="Acquisti">
            <ResponsiveContainer width="100%" height="100%"><BarChart data={stockSections}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="section"/><YAxis tickFormatter={v=>`€${v}`}/><Tooltip content={<SimpleTooltip/>}/><Bar name="Valore" dataKey="value" fill="#b8894b" radius={[8,8,0,0]}/></BarChart></ResponsiveContainer>
          </ChartBox>
        </div>
        <Card title="Valore magazzino per categoria" icon={Boxes}>
          <DataTable rows={stockCategories} empty="Nessuna categoria valorizzata" columns={[{key:'category',label:'Categoria'},{key:'items',label:'Articoli'},{key:'qty',label:'Quantità',render:x=>num(x.qty)},{key:'value',label:'Valore',render:x=>money(x.value)}]} />
        </Card>
      </>}

      {view === 'pivot' && <>
        <Card title="Pivot ricavi: prodotto × mese" icon={BarChart3} sub="Serve a capire quando un prodotto funziona e quanto porta nel tempo.">
          <PivotTable rows={list(r.pivot_product_month)} />
        </Card>
        <Card title="Pivot origine vendita × mese" icon={ShoppingCart}>
          <DataTable rows={list(r.pivot_source_month)} empty="Nessun dato origine/mese" columns={[{key:'source',label:'Origine'},{key:'month',label:'Mese'},{key:'qty',label:'Quantità',render:x=>num(x.qty)},{key:'revenue',label:'Ricavi',render:x=>money(x.revenue)},{key:'margin',label:'Margine',render:x=>money(x.margin)}]} />
        </Card>
      </>}

      {view === 'details' && <>
        <Card title="Dettaglio vendite analitico" icon={ShoppingCart} sub="Ogni vendita con costi unitari, ricavo e margine.">
          <DataTable rows={details} empty="Nessuna vendita registrata" columns={[{key:'date',label:'Data'},{key:'product',label:'Prodotto'},{key:'source',label:'Origine'},{key:'qty',label:'Q.tà',render:x=>num(x.qty)},{key:'revenue',label:'Ricavo',render:x=>money(x.revenue)},{key:'cost_total',label:'Costo',render:x=>money(x.cost_total)},{key:'margin',label:'Margine',render:x=><b>{money(x.margin)}</b>},{key:'margin_pct',label:'%',render:x=>percent(x.margin_pct)}]} />
        </Card>
      </>}
    </>}
  </>;
}




const flowOrder = ['materials', 'sales', 'products', 'quote', 'report'];
const pageHelp = {
  studio: { title: 'Laboratorio', next: 'Controlla la situazione generale e scegli il prossimo passo operativo.', action: 'Vai al percorso', target: 'atelier' },
  atelier: { title: 'Percorso operativo', next: 'Segui il processo naturale: materiali, prodotti, preventivi, vendite e report.', action: 'Registra acquisti', target: 'materials' },
  materials: { title: 'Acquisti', next: 'Registra materie prime e componenti acquistati dai fornitori, con costo reale e disponibilità.', action: 'Produzione', target: 'products' },
  products: { title: 'Produzione', next: 'Gestisci prodotti finiti, distinta base e produzione interna MN Laser Lab.', action: 'Fai preventivo', target: 'quote' },
  quote: { title: 'Preventivi', next: 'Calcola un prezzo sostenibile partendo da costo reale e margine.', action: 'Registra vendita', target: 'sales' },
  sales: { title: 'Vendite', next: 'Registra le uscite e poi controlla la marginalità.', action: 'Apri report', target: 'report' },
  setup: { title: 'Categorie', next: 'Organizza categorie materiali e categorie prodotti senza mischiare i due mondi.', action: 'Vai ai materiali', target: 'materials' },
  people: { title: 'Clienti e fornitori', next: 'Gestisci i contatti separando chi ti vende materiali da chi compra i tuoi lavori.', action: 'Vai ai materiali', target: 'materials' },
  report: { title: 'Report', next: 'Usa i margini per capire quali prodotti conviene produrre e vendere.', action: 'Vai al laboratorio', target: 'studio' },
  settings: { title: 'Impostazioni', next: 'Gestisci backup, import, export, manutenzione e reset in modo controllato.', action: 'Vai al laboratorio', target: 'studio' },
};

function UsabilityBar({ tab, go, simple, setSimple }) {
  const idx = flowOrder.indexOf(tab);
  const prev = idx > 0 ? flowOrder[idx - 1] : null;
  const next = idx >= 0 && idx < flowOrder.length - 1 ? flowOrder[idx + 1] : null;
  const h = pageHelp[tab] || pageHelp.studio;
  return <div className="ux-bar">
    <div className="ux-current"><Sparkles /><div><b>{h.title}</b><span>{h.next}</span></div></div>
    <div className="ux-flow-mini">{flowOrder.map((id, i) => <button key={id} className={tab === id ? 'on' : ''} onClick={() => go(id)}><span>{i + 1}</span>{id === 'materials' ? 'Acquisti' : id === 'products' ? 'Produzione' : id === 'quote' ? 'Preventivi' : id === 'sales' ? 'Vendite' : 'Report'}</button>)}</div>
    <div className="ux-actions">
      {prev && <button className="ghost" onClick={() => go(prev)}>Indietro</button>}
      <button className="primary" onClick={() => go(h.target)}>{h.action}<ArrowRight /></button>
      {next && <button className="ghost" onClick={() => go(next)}>Avanti</button>}
      <button className={simple ? 'mode active' : 'mode'} onClick={() => setSimple(!simple)}>{simple ? 'Vista semplice' : 'Vista completa'}</button>
    </div>
  </div>;
}

function FocusStrip({ go }) {
  return <div className="focus-strip">
    <button onClick={() => go('materials')}><PackagePlus /> Nuovo acquisto</button>
    <button onClick={() => go('products')}><Factory /> Nuova produzione</button>
    <button onClick={() => go('quote')}><Calculator /> Calcola prezzo</button>
    <button onClick={() => go('sales')}><ShoppingCart /> Registra vendita</button>
  </div>;
}

function Maintenance({ toast }) {
  const [msg, setMsg] = useState('');
  async function act(path, label) { try { const r = await postJSON(path, {}); setMsg(r.backup || 'Operazione completata'); toast(label); } catch(e) { toast(e.message, 'err'); } }
  return <><PageTitle title="Archivio dati" desc="Vista rapida dell’archivio locale. Per backup, import, export e reset usa la pagina Impostazioni." /><Card title="Archivio locale" icon={Database} sub="Questa sezione resta come controllo rapido; la gestione completa è in Impostazioni."><div className="quick-actions"><button onClick={()=>act('/maintenance/backup','Backup creato')}>Backup rapido</button><button onClick={()=>window.dispatchEvent(new CustomEvent('mnll-go-settings'))}>Apri impostazioni</button></div>{msg && <pre>{msg}</pre>}</Card></>;
}


function downloadJson(filename, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function SettingsPage({ toast }) {
  const [info, setInfo] = useState({});
  const [msg, setMsg] = useState('');
  const [importText, setImportText] = useState('');
  const [biz, setBiz] = useState({});

  async function loadBusiness() {
    try {
      setBiz(await getJSON('/settings/business'));
    } catch (e) {}
  }
  async function loadInfo() { try { setInfo(await getJSON('/maintenance/info')); } catch(e) { setMsg(e.message || String(e)); } }
  useEffect(() => { loadInfo(); loadBusiness(); }, []);
  async function backup() { try { const r = await postJSON('/maintenance/backup', {}); setMsg(r.backup || 'Backup creato'); toast('Backup creato'); await loadInfo(); } catch(e) { toast(e.message, 'err'); } }
  async function cleanup() { try { const r = await postJSON('/maintenance/cleanup', {}); setMsg(r.backup || 'Pulizia completata'); toast('Pulizia completata'); await loadInfo(); } catch(e) { toast(e.message, 'err'); } }
  async function resetDb() { if (!confirm('Vuoi davvero svuotare l’archivio? Verrà creato un backup prima del reset.')) return; try { const r = await postJSON('/maintenance/reset', {}); setMsg(r.backup || 'Archivio resettato'); toast('Archivio resettato'); await loadInfo(); } catch(e) { toast(e.message, 'err'); } }
  async function exportDb() { try { const r = await getJSON('/maintenance/export'); downloadJson(r.filename || 'mn_laser_lab_export.json', r.data || {}); toast('Export JSON scaricato'); } catch(e) { toast(e.message, 'err'); } }
  async function importDb() { try { const parsed = JSON.parse(importText); await postJSON('/maintenance/import', { data: parsed }); setImportText(''); toast('Archivio importato'); await loadInfo(); } catch(e) { toast('JSON non valido o import non riuscito: ' + (e.message || e), 'err'); } }
  async function saveBusiness() { try { await postJSON('/settings/business', biz); await loadBusiness(); toast('Impostazioni economiche salvate'); } catch(e) { toast(e.message, 'err'); } }
  return <>
    <PageTitle title="Impostazioni" desc="Gestione professionale dell’archivio: backup, export, import, pulizia e reset controllato." />
    <Card title="Impostazioni economiche" icon={Settings2} sub="Valori standard usati nei preventivi: tariffa, margine, commissioni e costi ricorrenti." action={<button className="primary" onClick={saveBusiness}><Save /> Salva impostazioni</button>}>
      <div className="form-grid small-grid">
        <Input label="Tariffa oraria €/h" type="number" step="0.01" value={biz.hourly_rate ?? ''} onChange={e => setBiz({ ...biz, hourly_rate: e.target.value })} />
        <Input label="Margine standard %" type="number" step="0.01" value={biz.default_margin ?? ''} onChange={e => setBiz({ ...biz, default_margin: e.target.value })} />
        <Input label="Commissione standard %" type="number" step="0.01" value={biz.default_commission ?? ''} onChange={e => setBiz({ ...biz, default_commission: e.target.value })} />
        <Input label="Sconto standard %" type="number" step="0.01" value={biz.default_discount ?? ''} onChange={e => setBiz({ ...biz, default_discount: e.target.value })} />
        <Input label="Imballaggio €" type="number" step="0.01" value={biz.default_packaging ?? ''} onChange={e => setBiz({ ...biz, default_packaging: e.target.value })} />
        <Input label="Energia €" type="number" step="0.01" value={biz.default_energy ?? ''} onChange={e => setBiz({ ...biz, default_energy: e.target.value })} />
        <Input label="Usura laser €" type="number" step="0.01" value={biz.default_wear ?? ''} onChange={e => setBiz({ ...biz, default_wear: e.target.value })} />
        <Input label="Validità preventivo giorni" type="number" step="1" value={biz.quote_validity_days ?? ''} onChange={e => setBiz({ ...biz, quote_validity_days: e.target.value })} />
      </div>
    </Card>
    <div className="settings-grid">
      <Card title="Stato archivio" icon={ShieldCheck} sub="Percorsi e stato del database locale usato dall’app.">
        <div className="settings-info"><span>Database</span><b>{info.db_path || '—'}</b><span>Cartella dati</span><b>{info.data_dir || '—'}</b><span>Ultimo controllo</span><b>{info.checked_at || '—'}</b></div>
      </Card>
      <Card title="Azioni rapide" icon={Database} sub="Prima di operazioni importanti crea sempre un backup.">
        <div className="settings-actions">
          <button onClick={backup}><Archive /> Backup database</button>
          <button onClick={exportDb}><Download /> Esporta JSON</button>
          <button onClick={cleanup}><RefreshCcw /> Ripulisci archivio</button>
          <button className="danger" onClick={resetDb}><Trash2 /> Reset archivio</button>
        </div>
        {msg && <pre>{msg}</pre>}
      </Card>
    </div>
    <Card title="Import archivio" icon={Upload} sub="Incolla un file JSON esportato da questa app o lo stato compatibile della versione precedente.">
      <textarea className="import-box" value={importText} onChange={e=>setImportText(e.target.value)} placeholder="Incolla qui il JSON da importare..." />
      <div className="quick-actions"><button className="primary" onClick={importDb}><FileJson /> Importa dati</button><button className="ghost" onClick={()=>setImportText('')}>Svuota campo</button></div>
    </Card>
  </>;
}

function CommandPalette({ open, setOpen, nav, go }) {
  const [q, setQ] = useState('');
  const { data: results } = useApi(q ? `/global-search?q=${encodeURIComponent(q)}` : '/global-search?q=', {});
  if (!open) return null;
  const rows = nav.filter(n => n.label.toLowerCase().includes(q.toLowerCase()));
  const resultGroups = [
    ['Materiali', results.materials, 'materials'],
    ['Prodotti', results.products, 'products'],
    ['Clienti', results.customers, 'people'],
    ['Fornitori', results.suppliers, 'people'],
    ['Preventivi', results.quotes, 'quote'],
    ['Vendite', results.sales, 'sales'],
  ];
  return <div className="cmd-back" onMouseDown={() => setOpen(false)}>
    <div className="cmd cmd-wide" onMouseDown={e=>e.stopPropagation()}>
      <div><Command /><input autoFocus placeholder="Cerca o vai a..." value={q} onChange={e=>setQ(e.target.value)} /></div>
      {rows.map(n => <button key={n.id} onClick={() => { go(n.id); setOpen(false); }}><n.icon />{n.label}<ChevronRight /></button>)}
      {q && <div className="global-results">
        {resultGroups.map(([label, values, target]) => list(values).length ? <section key={label}>
          <b>{label}</b>
          {list(values).map((r, i) => <button key={label + i} onClick={() => { go(target); setOpen(false); }}>
            <Search />
            <span>{r.name || r.id}<small>{r.subtitle || r.status || ''}</small></span>
            {r.value !== undefined && <em>{money(r.value)}</em>}
          </button>)}
        </section> : null)}
      </div>}
    </div>
  </div>;
}

function App() {
  const [tab, setTab] = useState(() => localStorage.getItem('mnll_tab') === 'maintenance' ? 'settings' : (localStorage.getItem('mnll_tab') || 'studio'));
  const [mobile, setMobile] = useState(false);
  const [cmd, setCmd] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('mnll_theme') || 'light');
  const { push, Toasts } = useToasts();
  const nav = [
    { id: 'studio', label: 'Laboratorio', icon: Gauge },
    { id: 'materials', label: 'Acquisti', icon: PackagePlus },
    { id: 'sales', label: 'Vendite', icon: ShoppingCart },
    { id: 'products', label: 'Produzione', icon: Factory },
    { id: 'quote', label: 'Preventivi', icon: Calculator },
    { id: 'people', label: 'Clienti e fornitori', icon: Users },
    { id: 'setup', label: 'Categorie', icon: Tags },
    { id: 'report', label: 'Report', icon: BarChart3 },
    { id: 'settings', label: 'Impostazioni', icon: Settings2 },
  ];
  const pages = { studio: Studio, atelier: Atelier, materials: Materials, products: Products, quote: Quote, sales: Sales, people: People, setup: Setup, report: Report, settings: SettingsPage };
  const Page = pages[tab] || Studio;
  function go(id) { setTab(id); localStorage.setItem('mnll_tab', id); setMobile(false); window.scrollTo({ top: 0, behavior: 'smooth' }); }
  useEffect(() => { localStorage.setItem('mnll_theme', theme); document.documentElement.dataset.theme = theme; }, [theme]);
  useEffect(() => { const on = e => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setCmd(true); } }; window.addEventListener('keydown', on); return () => window.removeEventListener('keydown', on); }, []);
  useEffect(() => { const on = () => go('settings'); window.addEventListener('mnll-go-settings', on); return () => window.removeEventListener('mnll-go-settings', on); }, []);
  return <div className={`app full-mode theme-${theme}`}><LaserBackdrop/><button className="mobile" onClick={()=>setMobile(!mobile)}>{mobile ? <X/> : <Menu/>}</button><aside className={mobile ? 'open' : ''}><div className="brand">
  <img src={`${import.meta.env.BASE_URL}mn_laser_lab_logo.png`} alt="MN Laser Lab" />
  <div>
    <b>MN Laser Lab</b>
    <span>Versione v39.0 Professional</span>
  </div>
</div><button className="command" onClick={()=>setCmd(true)}><Command/> Cerca <kbd>⌘K</kbd></button><nav>{nav.map(n=><button key={n.id} className={tab===n.id?'active':''} onClick={()=>go(n.id)}><n.icon/>{n.label}</button>)}</nav><FocusStrip go={go}/><div className="side-note"><b>Flusso operativo</b><br/>Acquisti → Produzione → Preventivi → Vendite. Backup, import ed export sono in Impostazioni.</div></aside><main><div className="top-right-tools"><button className="theme-toggle" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} aria-label="Cambia modalità colore"><Sun/><span></span><Moon/></button></div><div className="content-main"><Page go={go} toast={push}/></div></main><Toasts/><CommandPalette open={cmd} setOpen={setCmd} nav={nav} go={go}/></div>;
}

createRoot(document.getElementById('root')).render(<App />);
