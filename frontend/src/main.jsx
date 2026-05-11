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

const quoteStatusLabels = {
  bozza: 'Bozza',
  inviato: 'Inviato',
  da_modificare: 'Da modificare',
  accettato: 'Accettato',
  in_produzione: 'In produzione',
  consegnato: 'Consegnato',
  rifiutato: 'Rifiutato',
  scaduto: 'Scaduto',
};

const quoteStatusFlow = ['bozza', 'inviato', 'da_modificare', 'accettato', 'in_produzione', 'consegnato', 'rifiutato', 'scaduto'];

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

const rawCatsStrict = (s, sec) => {
  if (!sec) return [];
  const scoped = pick(s, ['raw_categories_by_scope', sec], []);
  return unique(scoped);
};

const rawSubsStrict = (s, sec, cat) => {
  if (!sec || !cat) return [];
  const scoped = pick(s, ['raw_subcategories_by_scope_category', sec, cat], []);
  return unique(scoped);
};

const rawCatsForSupplierStrict = (s, supplier, sec) => {
  if (!sec) return [];
  const linked = pick(s, ['raw_categories_by_supplier_scope', supplier, sec], []);
  const scoped = rawCatsStrict(s, sec);
  if (supplier && linked.length) return unique(linked);
  return scoped;
};

const rawSubsForSupplierStrict = (s, supplier, sec, cat) => {
  if (!sec || !cat) return [];
  const linked = pick(s, ['raw_subcategories_by_supplier_scope_category', supplier, sec, cat], []);
  const scoped = rawSubsStrict(s, sec, cat);
  if (supplier && linked.length) return unique(linked);
  return scoped;
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
    {filtered.length > 0 && <div className="suggestions compact-suggestions">
      {filtered.slice(0, 5).map(v => <button type="button" key={v} onMouseDown={e => { e.preventDefault(); choose(v); }}>{v}</button>)}
      {filtered.length > 5 && <small>+{filtered.length - 5} altri suggerimenti: continua a scrivere per filtrare</small>}
    </div>}
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

function FlowPill({ n, title, desc, detail, icon: Icon, active }) { return <div className={`flow-pill ${active ? 'active' : ''}`}><div className="flow-pill-top"><b>{n}</b>{Icon && <Icon />}</div><div className="flow-pill-copy"><span>{title}</span><small>{desc}</small>{detail && <em>{detail}</em>}</div></div>; }

function Studio({ go }) {
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
    <Card title="Acquisto rapido" icon={PackagePlus}  action={<button className="primary" form="purchase"><Save /> Salva acquisto</button>}>
      <form id="purchase" onSubmit={add} className="form-grid buy-grid">
        <Select label="Area" value={f.section} onChange={e => setF({ ...f, section: e.target.value, supplier: '', category: '', subcategory: '', size: '', thickness: '' })}>{list(opt.raw_sections).map(x => <option key={x}>{x}</option>)}</Select>
        <SmartInput label="Fornitore" options={suppliersForRaw(sug, f.section, f.category, f.subcategory)} value={f.supplier} onChange={e => setF({ ...f, supplier: e.target.value, category: '', subcategory: '', size: '', thickness: '' })}  />
        <SmartInput label="Categoria" placeholder="Legname, Acrilico..." options={rawCatsForSupplierStrict(sug, f.supplier, f.section)} value={f.category} onChange={e => setF({ ...f, category: e.target.value, subcategory: '', size: '', thickness: '' })}  />
        <SmartInput label="Sottocategoria" placeholder="Betulla, Pioppo..." options={rawSubsForSupplierStrict(sug, f.supplier, f.section, f.category)} value={f.subcategory} onChange={e => setF({ ...f, subcategory: e.target.value, size: '' })}  />
        <SmartInput label="Formato / tipo" options={unique([...formats(sug, f.category), ...typologies(sug, f.category, f.subcategory)])} value={f.size} onChange={e => setF({ ...f, size: e.target.value })} />
        <SmartInput label="Spessore" options={thicknesses(sug, f.category)} value={f.thickness} onChange={e => setF({ ...f, thickness: e.target.value })} />
        <SmartInput label="Unità" options={sug.units} value={f.unit} onChange={e => setF({ ...f, unit: e.target.value })} />
        <Input label="Quantità" type="number" step="0.01" value={f.quantity} onChange={e => setF({ ...f, quantity: e.target.value })} />
        <Input label="Costo totale €" type="number" step="0.01" value={f.total_cost} onChange={e => setF({ ...f, total_cost: e.target.value })} />
        <div className="name-preview"><span>Nome articolo</span><b>{generated || 'Si genera automaticamente'}</b><small>{f.supplier || '—'}</small></div>
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
    </DetailModal>}
  </>;
}


function ProductWizard({ inv, sug, refresh, refreshSug, toast }) {
  const [step, setStep] = useState(1);
  const [materialSearch, setMaterialSearch] = useState('');
  const [selectedMaterial, setSelectedMaterial] = useState('');
  const [materialQty, setMaterialQty] = useState('1');

  const [draft, setDraft] = useState({
    name: '',
    section: 'Prodotti Finiti / Semilavorati',
    category: '',
    subcategory: '',
    collection: '',
    unit: 'pz',
    stock: 0,
    labor_hours: '',
    hourly_rate: '',
    extra_unit_cost: '',
    description: '',
    bom: []
  });

  const filteredMaterials = useMemo(() => {
    const q = materialSearch.toLowerCase().trim();

    return list(inv).filter(i => {
      const text = [
        i.name,
        i.section,
        i.category,
        i.subcategory,
        i.size,
        i.thickness,
        i.supplier_details
      ].join(' ').toLowerCase();

      if (Number(i.stock || 0) <= 0) return false;
      if (Number(i.cost_per_unit || i.weighted_average_cost || 0) <= 0) return false;

      return !q || q.split(/\s+/).every(part => text.includes(part));
    }).slice(0, 80);
  }, [inv, materialSearch]);

  const selected = list(inv).find(x => x.key === selectedMaterial);

  const materialCost = draft.bom.reduce((sum, row) => {
    const item = list(inv).find(x => x.key === row.name || x.name === row.name);
    return sum + Number(row.qty || 0) * Number(item?.cost_per_unit || item?.weighted_average_cost || 0);
  }, 0);

  const laborCost = Number(draft.labor_hours || 0) * Number(draft.hourly_rate || 0);
  const extraCost = Number(draft.extra_unit_cost || 0);
  const unitCost = materialCost + laborCost + extraCost;

  const canNext = () => {
    if (step === 1) return draft.name.trim().length > 0;
    if (step === 2) return draft.category.trim().length > 0;
    if (step === 3) return draft.bom.length > 0;
    if (step === 4) return true;
    return true;
  };

  function next() {
    if (!canNext()) {
      toast('Completa i campi richiesti prima di continuare', 'err');
      return;
    }
    setStep(s => Math.min(5, s + 1));
  }

  function back() {
    setStep(s => Math.max(1, s - 1));
  }

  function addBomMaterial() {
    const item = list(inv).find(x => x.key === selectedMaterial);
    const q = Number(materialQty || 0);

    if (!item || q <= 0) {
      toast('Seleziona un materiale e una quantità valida', 'err');
      return;
    }

    const existingIndex = draft.bom.findIndex(x => x.name === item.key);

    if (existingIndex >= 0) {
      const nextBom = draft.bom.map((x, i) =>
        i === existingIndex ? { ...x, qty: Number(x.qty || 0) + q } : x
      );
      setDraft(v => ({ ...v, bom: nextBom }));
    } else {
      setDraft(v => ({
        ...v,
        bom: [
          ...v.bom,
          {
            name: item.key,
            label: item.name,
            qty: q,
            unit: item.unit || '',
            category: item.category || '',
            subcategory: item.subcategory || '',
            size: item.size || '',
            thickness: item.thickness || '',
            unit_cost: Number(item.cost_per_unit || item.weighted_average_cost || 0)
          }
        ]
      }));
    }

    setSelectedMaterial('');
    setMaterialQty('1');
  }

  function removeBomMaterial(index) {
    setDraft(v => ({
      ...v,
      bom: v.bom.filter((_, i) => i !== index)
    }));
  }

  async function saveWizardProduct() {
    if (!draft.name.trim()) {
      toast('Nome prodotto richiesto', 'err');
      return;
    }

    if (!draft.bom.length) {
      toast('Aggiungi almeno un materiale alla distinta base', 'err');
      return;
    }

    try {
      await postJSON('/products', {
        ...draft,
        stock: Number(draft.stock || 0),
        labor_hours: Number(draft.labor_hours || 0),
        hourly_rate: Number(draft.hourly_rate || 0),
        extra_unit_cost: Number(draft.extra_unit_cost || 0),
        bom: draft.bom.map(row => ({
          name: row.name,
          qty: Number(row.qty || 0)
        }))
      });

      toast('Prodotto creato con wizard');
      setStep(1);
      setMaterialSearch('');
      setSelectedMaterial('');
      setMaterialQty('1');
      setDraft({
        name: '',
        section: 'Prodotti Finiti / Semilavorati',
        category: '',
        subcategory: '',
        collection: '',
        unit: 'pz',
        stock: 0,
        labor_hours: '',
        hourly_rate: '',
        extra_unit_cost: '',
        description: '',
        bom: []
      });

      await refresh();
      await refreshSug();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  const steps = [
    ['Identità', 'Nome e descrizione'],
    ['Catalogo', 'Categoria e collezione'],
    ['Materiali', 'Distinta base'],
    ['Costi', 'Lavoro ed extra'],
    ['Riepilogo', 'Controllo finale']
  ];

  return <Card title="Wizard nuovo prodotto" icon={Wand2}>
    <div className="product-wizard">
      <div className="wizard-steps">
        {steps.map(([title, desc], i) => <button
          key={title}
          className={step === i + 1 ? 'active' : step > i + 1 ? 'done' : ''}
          onClick={() => setStep(i + 1)}
        >
          <span>{i + 1}</span>
          <div>
            <b>{title}</b>
            <small>{desc}</small>
          </div>
        </button>)}
      </div>

      {step === 1 && <div className="wizard-panel">
        <div className="wizard-section-title">
          <b>Identità prodotto</b>
          <span>Dai un nome chiaro alla creazione. Sarà usato in magazzino, preventivi e vendite.</span>
        </div>

        <div className="form-grid">
          <Input label="Nome prodotto" value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })} placeholder="Es. Orologio One Piece 40 cm" />
          <SmartInput label="Unità" options={sug.units} value={draft.unit} onChange={e => setDraft({ ...draft, unit: e.target.value })} />
          <Input label="Descrizione" value={draft.description} onChange={e => setDraft({ ...draft, description: e.target.value })} placeholder="Dettagli lavorazione, finitura, colore..." />
        </div>
      </div>}

      {step === 2 && <div className="wizard-panel">
        <div className="wizard-section-title">
          <b>Categoria e collezione</b>
          <span>Collega il prodotto al catalogo commerciale.</span>
        </div>

        <div className="form-grid">
          <SmartInput label="Categoria" options={sug.product_categories} value={draft.category} onChange={e => setDraft({ ...draft, category: e.target.value, subcategory: '', collection: '' })} />
          <SmartInput label="Sottocategoria" options={prodSubs(sug, draft.category)} value={draft.subcategory} onChange={e => setDraft({ ...draft, subcategory: e.target.value, collection: '' })} />
          <SmartInput label="Collezione" options={collections(sug, draft.category, draft.subcategory)} value={draft.collection} onChange={e => setDraft({ ...draft, collection: e.target.value })} />
        </div>
      </div>}

      {step === 3 && <div className="wizard-panel">
        <div className="wizard-section-title">
          <b>Materiali e distinta base</b>
          <span>Aggiungi i materiali reali dal magazzino. Verranno usati per calcolare il costo interno.</span>
        </div>

        <div className="wizard-material-layout">
          <div className="wizard-material-search">
            <SearchBox value={materialSearch} onChange={setMaterialSearch} placeholder="Cerca materiale: betulla, acrilico, led..." />

            <div className="wizard-material-results">
              {filteredMaterials.map(m => <button
                key={m.key}
                className={selectedMaterial === m.key ? 'selected' : ''}
                onClick={() => setSelectedMaterial(m.key)}
              >
                <div>
                  <b>{m.name}</b>
                  <small>{[m.category, m.subcategory, m.size, m.thickness].filter(Boolean).join(' · ')}</small>
                </div>
                <span>{num(m.stock)} {m.unit || ''}</span>
                <strong>{money(m.cost_per_unit || m.weighted_average_cost)}</strong>
              </button>)}

              {!filteredMaterials.length && <Empty text="Nessun materiale disponibile" />}
            </div>
          </div>

          <div className="wizard-bom-box">
            <div className="selected-material-box">
              {selected ? <>
                <span>Materiale selezionato</span>
                <b>{selected.name}</b>
                <small>{[selected.category, selected.subcategory, selected.size, selected.thickness].filter(Boolean).join(' · ')}</small>
              </> : <Empty text="Seleziona materiale" />}
            </div>

            <div className="quote-add-line">
              <input type="number" step="0.01" value={materialQty} onChange={e => setMaterialQty(e.target.value)} />
              <div className="quote-mini-total">
                <span>Costo riga</span>
                <b>{money(selected ? Number(selected.cost_per_unit || selected.weighted_average_cost || 0) * Number(materialQty || 0) : 0)}</b>
              </div>
              <button className="primary" onClick={addBomMaterial}><Plus /> Aggiungi</button>
            </div>

            <div className="wizard-bom-list">
              {draft.bom.map((row, i) => <div key={i} className="wizard-bom-row">
                <div>
                  <b>{row.label || row.name}</b>
                  <small>{row.qty} {row.unit || ''} · {row.category || 'materiale'}</small>
                </div>
                <strong>{money(Number(row.qty || 0) * Number(row.unit_cost || 0))}</strong>
                <button className="ghost danger" onClick={() => removeBomMaterial(i)}>×</button>
              </div>)}

              {!draft.bom.length && <Empty text="Nessun materiale aggiunto" />}
            </div>
          </div>
        </div>
      </div>}

      {step === 4 && <div className="wizard-panel">
        <div className="wizard-section-title">
          <b>Costi lavoro ed extra</b>
          <span>Imposta tempo di lavorazione, tariffa e costi aggiuntivi per calcolare il costo interno.</span>
        </div>

        <div className="form-grid">
          <Input label="Ore lavoro" type="number" step="0.01" value={draft.labor_hours} onChange={e => setDraft({ ...draft, labor_hours: e.target.value })} />
          <Input label="Tariffa €/h" type="number" step="0.01" value={draft.hourly_rate} onChange={e => setDraft({ ...draft, hourly_rate: e.target.value })} />
          <Input label="Extra per pezzo €" type="number" step="0.01" value={draft.extra_unit_cost} onChange={e => setDraft({ ...draft, extra_unit_cost: e.target.value })} />
        </div>

        <div className="wizard-cost-grid">
          <Stat label="Materiali" value={money(materialCost)} />
          <Stat label="Lavoro" value={money(laborCost)} />
          <Stat label="Extra" value={money(extraCost)} />
          <Stat label="Costo interno/u" value={money(unitCost)} tone="mint" />
        </div>
      </div>}

      {step === 5 && <div className="wizard-panel">
        <div className="wizard-section-title">
          <b>Riepilogo prodotto</b>
          <span>Controlla i dati prima di creare la scheda prodotto.</span>
        </div>

        <div className="wizard-summary">
          <div>
            <span>Nome</span>
            <b>{draft.name || '—'}</b>
          </div>
          <div>
            <span>Categoria</span>
            <b>{[draft.category, draft.subcategory, draft.collection].filter(Boolean).join(' · ') || '—'}</b>
          </div>
          <div>
            <span>Materiali BOM</span>
            <b>{draft.bom.length}</b>
          </div>
          <div>
            <span>Costo interno/u</span>
            <b>{money(unitCost)}</b>
          </div>
        </div>

        <div className="wizard-bom-list review">
          {draft.bom.map((row, i) => <div key={i} className="wizard-bom-row">
            <div>
              <b>{row.label || row.name}</b>
              <small>{row.qty} {row.unit || ''}</small>
            </div>
            <strong>{money(Number(row.qty || 0) * Number(row.unit_cost || 0))}</strong>
          </div>)}
        </div>
      </div>}

      <div className="wizard-actions">
        <button className="ghost" onClick={back} disabled={step === 1}>Indietro</button>
        {step < 5
          ? <button className="primary" onClick={next}>Continua <ArrowRight /></button>
          : <button className="primary" onClick={saveWizardProduct}><Save /> Salva prodotto</button>}
      </div>
    </div>
  </Card>;
}


function ProductionBox({ products, refresh, toast }) {
  const [name, setName] = useState('');
  const [qty, setQty] = useState(1);
  const [check, setCheck] = useState(null);
  const [substitutions, setSubstitutions] = useState({});
  const [mixDrafts, setMixDrafts] = useState({});

  async function checkNow() {
    if (!name) return;
    try {
      const result = await postJSON(`/products/${encodeURIComponent(name)}/check-production`, { qty });
      setCheck(result);
      setSubstitutions({});
      setMixDrafts({});
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function produce() {
    if (!name) return;

    try {
      await postJSON(`/products/${encodeURIComponent(name)}/produce`, {
        qty,
        substitutions
      });

      toast('Produzione completata');
      setCheck(null);
      setSubstitutions({});
      setMixDrafts({});
      refresh();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  const rows = list(check?.rows);
  const missingRows = rows.filter(r => !r.ok);
  const isResolved = row => {
    const sub = substitutions[String(row.index)];
    if (!sub) return false;
    if (Array.isArray(sub.mix)) {
      const total = sub.mix.reduce((a, x) => a + Number(x.qty || 0), 0);
      return total + 0.000001 >= Number(row.needed || 0);
    }
    return true;
  };
  const allResolved = !missingRows.length || missingRows.every(isResolved);

  function originalPart(row) {
    const available = Number(row.available || 0);
    const needed = Number(row.needed || 0);
    const qtyUse = Math.max(0, Math.min(available, needed));
    if (qtyUse <= 0) return null;
    return {
      table: row.table,
      key: row.key,
      name: row.name,
      qty: qtyUse,
      original: true
    };
  }

  function chooseVariant(row, variant) {
    const needed = Number(row.needed || 0);
    const part = originalPart(row);
    const remaining = Math.max(0, needed - Number(part?.qty || 0));
    const variantQty = Math.min(Number(variant.stock || 0), remaining || needed);

    const mix = [];
    if (part) mix.push(part);
    mix.push({
      table: variant.table,
      key: variant.key,
      name: variant.name,
      qty: variantQty
    });

    setSubstitutions(v => ({
      ...v,
      [String(row.index)]: {
        mix
      }
    }));
  }

  function setMixQty(row, partIndex, value) {
    const key = String(row.index);
    const current = substitutions[key];
    if (!current?.mix) return;

    const nextMix = current.mix.map((part, i) => i === partIndex ? { ...part, qty: Number(value || 0) } : part);

    setSubstitutions(v => ({
      ...v,
      [key]: {
        mix: nextMix
      }
    }));
  }

  function addVariantToMix(row, variant) {
    const key = String(row.index);
    const current = substitutions[key]?.mix || [];
    const exists = current.some(x => x.table === variant.table && x.key === variant.key);

    if (exists) {
      toast('Alternativa già presente nel mix', 'err');
      return;
    }

    const covered = current.reduce((a, x) => a + Number(x.qty || 0), 0);
    const remaining = Math.max(0, Number(row.needed || 0) - covered);
    const qtyToUse = Math.min(Number(variant.stock || 0), remaining || 1);

    setSubstitutions(v => ({
      ...v,
      [key]: {
        mix: [
          ...current,
          {
            table: variant.table,
            key: variant.key,
            name: variant.name,
            qty: qtyToUse
          }
        ]
      }
    }));
  }

  function removeMixPart(row, partIndex) {
    const key = String(row.index);
    const current = substitutions[key]?.mix || [];
    const nextMix = current.filter((_, i) => i !== partIndex);

    setSubstitutions(v => ({
      ...v,
      [key]: nextMix.length ? { mix: nextMix } : undefined
    }));
  }

  function clearVariant(row) {
    setSubstitutions(v => {
      const next = { ...v };
      delete next[String(row.index)];
      return next;
    });
  }

  function mixTotal(row) {
    const sub = substitutions[String(row.index)];
    return list(sub?.mix).reduce((a, x) => a + Number(x.qty || 0), 0);
  }

  function mixRemaining(row) {
    return Math.max(0, Number(row.needed || 0) - mixTotal(row));
  }

  return <div className="production-panel">
    <div className="inline">
      <select value={name} onChange={e => { setName(e.target.value); setCheck(null); setSubstitutions({}); setMixDrafts({}); }}>
        <option value="">Scegli prodotto</option>
        {list(products).map(p => <option key={p.name}>{p.name}</option>)}
      </select>
      <input type="number" step="0.01" value={qty} onChange={e => setQty(e.target.value)} />
      <button onClick={checkNow}><Search /> Verifica</button>
      <button className="primary" onClick={produce} disabled={check && !allResolved}>
        <Hammer /> Produci
      </button>
    </div>

    {check && <div className={check.can_produce ? 'notice ok' : 'notice warn'}>
      {check.can_produce ? <CheckCircle2 /> : <AlertTriangle />}
      {check.can_produce
        ? 'Materiali sufficienti per produrre.'
        : allResolved
          ? 'Materiali mancanti risolti con alternative selezionate. Puoi produrre.'
          : 'Alcuni materiali risultano insufficienti. Scegli una sostituzione logica o crea un mix.'}
    </div>}

    {rows.length > 0 && <div className="production-check-list">
      {rows.map(row => {
        const selected = substitutions[String(row.index)];
        const total = mixTotal(row);
        const remaining = mixRemaining(row);

        return <div key={row.index} className={row.ok ? 'production-row ok' : 'production-row missing'}>
          <div className="production-row-head">
            <div>
              <b>{row.name}</b>
              <small>
                Richiesto: {num(row.needed)} {row.unit || ''} · Disponibile: {num(row.available)} {row.unit || ''}
              </small>
            </div>
            {row.ok
              ? <span className="quote-status accepted">Disponibile</span>
              : selected
                ? <span className={remaining <= 0 ? 'quote-status accepted' : 'quote-status sent'}>{remaining <= 0 ? 'Risolto' : 'Parziale'}</span>
                : <span className="quote-status rejected">Mancante</span>}
          </div>

          {!row.ok && <div className="variant-panel">
            {selected?.mix && <div className="mixed-production-box">
              <div className="mixed-production-head">
                <div>
                  <span>Mix produzione</span>
                  <b>{num(total)} / {num(row.needed)} {row.unit || ''}</b>
                  <small>{remaining > 0 ? `Mancano ancora ${num(remaining)} ${row.unit || ''}` : 'Quantità coperta'}</small>
                </div>
                <button className="ghost" onClick={() => clearVariant(row)}>Svuota mix</button>
              </div>

              <div className="mix-lines">
                {selected.mix.map((part, i) => <div className="mix-line" key={i}>
                  <div>
                    <b>{part.name}</b>
                    <small>{part.original ? 'materiale originale disponibile' : 'alternativa selezionata'}</small>
                  </div>
                  <input type="number" step="0.01" value={part.qty} onChange={e => setMixQty(row, i, e.target.value)} />
                  <button className="ghost danger" onClick={() => removeMixPart(row, i)}>×</button>
                </div>)}
              </div>
            </div>}

            <h4>Alternative consigliate in base a categoria, formato, spessore e stock</h4>
            {list(row.variants).length ? <div className="variant-grid">
              {list(row.variants).map(v => <button key={v.table + v.key} type="button" className="variant-card" onClick={() => selected?.mix ? addVariantToMix(row, v) : chooseVariant(row, v)}>
                <div>
                  <b>{v.name}</b>
                  <small>{[v.category, v.subcategory, v.size, v.thickness].filter(Boolean).join(' · ')}</small>
                </div>
                <span>Stock: {num(v.stock)} {v.unit || ''}</span>
                <em>{v.notes}</em>
                <strong>{v.can_cover ? 'Copre produzione' : 'Stock parziale'}</strong>
              </button>)}
            </div> : <Empty text="Nessuna alternativa logica trovata" />}
          </div>}
        </div>;
      })}
    </div>}
  </div>;
}

function ProductWarehouse({ products, refresh, toast, onEdit, onDelete, onDuplicate }) {
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
    <Card title="Movimento magazzino prodotti" icon={PackageCheck} >
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
          <button className="ghost" onClick={() => onDuplicate(r)}>Duplica</button>
          <button className="ghost" onClick={() => onEdit(r)}>Modifica</button>
          <button className="ghost danger" onClick={() => onDelete(r.name)}>Elimina</button>
        </div> }
      ]} />
    </Card>
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
    </DetailModal>}
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
  const [duplicateProduct, setDuplicateProduct] = useState(null);
  const [duplicateName, setDuplicateName] = useState('');
  const rows = list(products).filter(x => [x.name, x.category, x.subcategory, x.collection].join(' ').toLowerCase().includes(q.toLowerCase()));
  const selectedProduct = list(products).find(x => x.name === p.name);
  async function save(e) { e.preventDefault(); try { await postJSON('/products', p); toast('Scheda prodotto salvata'); setP(v => ({ ...v, name: '', stock: '', bom: [] })); refresh(); refreshSug(); } catch (e) { toast(e.message, 'err'); } }
  async function remove(name) { if (!confirm('Eliminare prodotto?')) return; try { await del('/products/' + encodeURIComponent(name)); toast('Prodotto eliminato'); refresh(); } catch (e) { toast(e.message, 'err'); } }
  function addBom() { if (!bom.name || Number(bom.qty || 0) <= 0) return; setP({ ...p, bom: [...(p.bom || []), { name: bom.name, qty: Number(bom.qty) }] }); setBom({ name: '', qty: '1' }); }
  function editProduct(r) { setP({ ...r, old_name: r.name, bom: r.bom || [], stock: String(r.stock ?? '') }); setArea('sheet'); window.scrollTo({ top: 0, behavior: 'smooth' }); }

  function openDuplicateProduct(r) {
    setDuplicateProduct(r);
    setDuplicateName(`${r.name} - variante`);
  }

  async function saveDuplicateProduct() {
    if (!duplicateProduct || !duplicateName.trim()) {
      toast('Inserisci il nome della variante', 'err');
      return;
    }

    const payload = {
      ...duplicateProduct,
      old_name: duplicateName.trim(),
      name: duplicateName.trim(),
      stock: 0,
      bom: duplicateProduct.bom || [],
      description: duplicateProduct.description || '',
    };

    delete payload.value;
    delete payload.unit_cost;
    delete payload.material_unit_cost;
    delete payload.labor_unit_cost;

    try {
      await postJSON('/products', payload);
      toast('Variante prodotto creata');
      setDuplicateProduct(null);
      setDuplicateName('');
      await refresh();
      await refreshSug();
      setArea('sheet');
    } catch (e) {
      toast(e.message, 'err');
    }
  }
  const movementRows = list(movements).slice(0, 12);
  return <>
    <PageTitle title="Produzione" desc="Gestisci prodotti, distinta base, produzione e magazzino." />
    <div className="section-tabs">
      <button className={area === 'warehouse' ? 'active' : ''} onClick={() => setArea('warehouse')}>Magazzino prodotti</button>
      <button className={area === 'wizard' ? 'active' : ''} onClick={() => setArea('wizard')}>Wizard prodotto</button>
      <button className={area === 'sheet' ? 'active' : ''} onClick={() => setArea('sheet')}>Scheda prodotto e BOM</button>
      <button className={area === 'produce' ? 'active' : ''} onClick={() => setArea('produce')}>Produci</button>
      <button className={area === 'movements' ? 'active' : ''} onClick={() => setArea('movements')}>Movimenti</button>
    </div>
    {area === 'warehouse' && <ProductWarehouse products={products} refresh={() => { refresh(); refreshMovements(); }} toast={toast} onEdit={editProduct} onDelete={remove} onDuplicate={openDuplicateProduct} />}
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
    {area === 'produce' && <Card title="Produzione rapida" icon={Hammer} ><ProductionBox products={products} refresh={() => { refresh(); refreshMovements(); }} toast={toast} /></Card>}
    {area === 'movements' && <Card title="Ultimi movimenti prodotti" icon={Archive} sub="Storico carichi, scarichi manuali e produzioni registrate.">
      <DataTable rows={movementRows} empty="Nessun movimento registrato" columns={[
        { key: 'date', label: 'Data' }, { key: 'product', label: 'Prodotto' }, { key: 'qty', label: 'Quantità', render: r => `${Number(r.qty || 0) > 0 ? '+' : ''}${num(r.qty)}` }, { key: 'reason', label: 'Causale' }, { key: 'note', label: 'Nota' }
      ]} />
    </Card>}
    {duplicateProduct && <DetailModal title="Crea variante prodotto" subtitle="Duplica una scheda esistente mantenendo categoria, collezione, costi e distinta base. Lo stock iniziale della variante sarà 0." icon={PackagePlus} onClose={() => setDuplicateProduct(null)}>
      <div className="duplicate-product-modal">
        <div className="detail-hero">
          <div>
            <span>Prodotto origine</span>
            <strong>{duplicateProduct.name}</strong>
            <small>{[duplicateProduct.category, duplicateProduct.subcategory, duplicateProduct.collection].filter(Boolean).join(' · ') || 'Scheda prodotto'}</small>
          </div>
          <span className="quote-status sent">variante</span>
        </div>

        <div className="form-grid">
          <Input label="Nome nuova variante" value={duplicateName} onChange={e => setDuplicateName(e.target.value)} />
          <Input label="Stock iniziale" value="0" disabled />
        </div>

        <div className="duplicate-summary">
          <div><span>Categoria</span><b>{duplicateProduct.category || '—'}</b></div>
          <div><span>Sottocategoria</span><b>{duplicateProduct.subcategory || '—'}</b></div>
          <div><span>Collezione</span><b>{duplicateProduct.collection || '—'}</b></div>
          <div><span>Materiali BOM</span><b>{list(duplicateProduct.bom).length}</b></div>
        </div>

        <div className="notice">
          <CheckCircle2 />
          La variante copierà distinta base, costi lavoro, costi extra, categoria e collezione. Potrai modificarla subito dopo dalla scheda prodotto.
        </div>

        <div className="quick-actions">
          <button className="primary" onClick={saveDuplicateProduct}><Save /> Crea variante</button>
          <button className="ghost" onClick={() => setDuplicateProduct(null)}>Annulla</button>
        </div>
      </div>
    </DetailModal>}

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
  const { data: workflow, refresh: workflowRefresh } = useApi('/quotes/workflow', { statuses: quoteStatusFlow, counts: {}, quotes: [] });
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
  const [cost, setCost] = useState({ hours: '', rate: '', packaging: '', energy: '', wear: '', commission: '', project_fee: '', margin: '30', discount: '' });

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


  async function startQuoteProduction(q) {
    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/start-production`, {});
      toast('Preventivo avviato in produzione');
      workflowRefresh?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function markQuoteDelivered(q) {
    if (!confirm('Segnare questo preventivo come consegnato?')) return;

    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/mark-delivered`, {});
      toast('Preventivo segnato come consegnato');
      workflowRefresh?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function registerQuoteSale(q) {
    const name = prompt('Nome vendita', q.name || 'Vendita da preventivo') || q.name || 'Vendita da preventivo';

    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/register-sale`, {
        name,
        customer: q.customer || '',
        qty: 1,
        unit_price: q.total || q.recommended || q.discounted || 0
      });

      toast('Vendita registrata da preventivo');
      workflowRefresh?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function createProductFromQuote(q) {
    const name = prompt('Nome prodotto da creare', q.name || 'Prodotto da preventivo');

    if (!name) return;

    try {
      await postJSON(`/quotes/${encodeURIComponent(q.id)}/to-product`, {
        name,
        stock: 0
      });

      toast('Prodotto creato da preventivo');
      workflowRefresh?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  
  async function openQuotePdf(q, type = 'customer') {
    const id = q?.id || q?.quote_id || q;
    if (!id) {
      toast('Preventivo non valido', 'err');
      return;
    }

    const host = window.location.hostname || '127.0.0.1';
    const protocol = window.location.protocol?.startsWith('http') ? window.location.protocol : 'http:';
    const apiRoot = `${protocol}//${host}:8000`;
    const url = `${apiRoot}/api/quote-pdf/${type}?id=${encodeURIComponent(id)}`;

    const isElectronRuntime = /Electron/i.test(navigator.userAgent || '');

    // In Electron evitiamo window.open perché spesso viene bloccato o non apre la finestra.
    // Apriamo il PDF/HTML nella stessa finestra.
    if (isElectronRuntime) {
      window.location.href = url;
      return;
    }

    // Browser normale: nuova scheda, con fallback sulla stessa finestra.
    const opened = window.open(url, '_blank', 'noopener,noreferrer');
    if (!opened) {
      window.location.href = url;
    }
  }



  const costLabels = {
    hours: 'Ore lavoro', rate: 'Tariffa €/h', packaging: 'Imballaggio €', energy: 'Energia €', wear: 'Usura macchina €', commission: 'Commissioni %', project_fee: 'Spese di progetto €', margin: 'Margine %', discount: 'Sconto %'
  };

  return <>
    <PageTitle title="Preventivi" desc="Calcola prezzi e margini partendo dai materiali reali." />

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
      <Card title="Ricerca rapida materiali" icon={Search} >
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

      <Card title="Materiali nel preventivo" icon={Boxes} >
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
          
          {(r.status === 'accettato' || r.status === 'in_produzione') && <button className="quote-action quote-action-production" onClick={() => startQuoteProduction(r)}>Produzione</button>}
          {r.status === 'accettato' && <button className="quote-action quote-action-product" onClick={() => createProductFromQuote(r)}>Crea prodotto</button>}
          {(r.status === 'accettato' || r.status === 'in_produzione') && <button className="quote-action quote-action-sale" onClick={() => registerQuoteSale(r)}>Registra vendita</button>}
          {r.status === 'in_produzione' && <button className="quote-action quote-action-delivered" onClick={() => markQuoteDelivered(r)}>Consegnato</button>}
          <button className="quote-action quote-action-pdf" onClick={() => openQuotePdf(r, 'customer')}>PDF cliente</button>
          <button className="quote-action quote-action-pdf-internal" onClick={() => openQuotePdf(r, 'internal')}>PDF interno</button>
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





function CatalogAreasSection({ toast, refreshTax, refreshSug }) {
  const { data: areas, refresh: refreshAreas } = useApi('/catalog/areas', []);
  const [areaName, setAreaName] = useState('');

  async function saveArea() {
    const name = areaName.trim();
    if (!name) {
      toast('Inserisci il nome area', 'err');
      return;
    }

    try {
      await postJSON('/catalog/areas', { name });
      setAreaName('');
      toast('Area catalogo salvata');
      refreshAreas();
      refreshTax?.();
      refreshSug?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function removeArea(name) {
    if (!confirm(`Eliminare l'area "${name}"? Puoi eliminarla solo se non è usata da materiali, categorie o fornitori.`)) return;

    try {
      await del('/catalog/areas/' + encodeURIComponent(name));
      toast('Area eliminata');
      refreshAreas();
      refreshTax?.();
      refreshSug?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  return <Card title="Gestione aree catalogo" icon={Layers3} sub="Crea e organizza gli ambiti principali del catalogo: materiali, componenti, finiture, packaging, vernici e lavorazioni.">
    <div className="area-manager-layout">
      <div className="area-create-box">
        <label>Nuova area</label>
        <div className="area-create-row">
          <input
            placeholder="Es. Finiture, Packaging, Vernici..."
            value={areaName}
            onChange={e => setAreaName(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') saveArea(); }}
          />
          <button className="primary" onClick={saveArea}><Plus /> Aggiungi</button>
        </div>
        <small>Le aree compariranno negli acquisti, nei fornitori e nella gestione categorie.</small>
      </div>

      <div className="area-table-box">
        <div className="area-table-head">
          <b>Aree disponibili</b>
          <span>{list(areas).length} aree</span>
        </div>

        <div className="area-table">
          {list(areas).map(a => <div className="area-table-row" key={a}>
            <div>
              <b>{a}</b>
              <small>Ambito catalogo</small>
            </div>
            <button className="ghost danger" onClick={() => removeArea(a)}><Trash2 /> Elimina</button>
          </div>)}
        </div>
      </div>
    </div>
  </Card>;
}


function CatalogAdvancedSettings({ toast, refreshSug }) {
  const { data: treatments, refresh: refreshTreatments } = useApi('/catalog/wood-treatments', []);
  const [tr, setTr] = useState({ name: '', type: 'pacchetto', steps: 'Fondo + Colore + Trasparente', unit_cost: '', labor_hours: '', notes: '' });

  async function saveTreatment() {
    if (!tr.name.trim()) { toast('Inserisci il nome trattamento', 'err'); return; }

    const payload = {
      ...tr,
      steps: String(tr.steps || '').split('+').map(x => x.trim()).filter(Boolean),
      unit_cost: Number(tr.unit_cost || 0),
      labor_hours: Number(tr.labor_hours || 0),
    };

    try {
      await postJSON('/catalog/wood-treatments', payload);
      toast('Trattamento legno salvato');
      setTr({ name: '', type: 'pacchetto', steps: 'Fondo + Colore + Trasparente', unit_cost: '', labor_hours: '', notes: '' });
      refreshTreatments();
      refreshSug?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function removeTreatment(name) {
    if (!confirm(`Eliminare il trattamento "${name}"?`)) return;

    try {
      await del('/catalog/wood-treatments/' + encodeURIComponent(name));
      toast('Trattamento eliminato');
      refreshTreatments();
      refreshSug?.();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  return <div className="catalog-treatments-section">
    <Card title="Trattamenti legno" icon={Sparkles} sub="Configura cicli di finitura semplici o pacchetti: mordente, smalto, fondo, trasparente, flatting.">
      <div className="form-grid treatment-form">
        <Input label="Nome trattamento" value={tr.name} onChange={e => setTr({ ...tr, name: e.target.value })} placeholder="Pacchetto smalto completo" />
        <Select label="Tipo" value={tr.type} onChange={e => setTr({ ...tr, type: e.target.value })}>
          <option value="semplice">Semplice</option>
          <option value="pacchetto">Pacchetto</option>
        </Select>
        <Input label="Fasi" value={tr.steps} onChange={e => setTr({ ...tr, steps: e.target.value })} placeholder="Fondo + Colore + Trasparente" />
        <Input label="Costo stimato €" type="number" step="0.01" value={tr.unit_cost} onChange={e => setTr({ ...tr, unit_cost: e.target.value })} />
        <Input label="Ore lavoro" type="number" step="0.01" value={tr.labor_hours} onChange={e => setTr({ ...tr, labor_hours: e.target.value })} />
        <Input label="Note" value={tr.notes} onChange={e => setTr({ ...tr, notes: e.target.value })} />
      </div>

      <div className="quick-actions">
        <button className="primary" onClick={saveTreatment}><Save /> Salva trattamento</button>
      </div>

      <div className="treatment-list">
        {list(treatments).map(t => <div key={t.name} className="treatment-row">
          <div>
            <b>{t.name}</b>
            <small>{[t.type, list(t.steps).join(' + ')].filter(Boolean).join(' · ') || '—'}</small>
            {t.notes && <em>{t.notes}</em>}
          </div>
          <div className="treatment-meta">
            <span>€ {Number(t.unit_cost || 0).toFixed(2)}</span>
            <span>{Number(t.labor_hours || 0).toFixed(2)} h</span>
            <button className="ghost danger" onClick={() => removeTreatment(t.name)}><Trash2 /></button>
          </div>
        </div>)}
      </div>
    </Card>
  </div>;
}


function Setup({ toast }) {
  const { data: tax, refresh: refreshTax } = useApi('/taxonomy', { raw_tree: [], product_tree: [], supplier_matrix: [] });
const { data: sug, refresh: refreshSug } = useApi('/suggestions', {});

  const [mode, setMode] = useState('raw');
  const [q, setQ] = useState('');
  const [selectedArea, setSelectedArea] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSubcategory, setSelectedSubcategory] = useState('');

  const [rawDraft, setRawDraft] = useState({ category: '', subcategory: '' });
  const [formatDraft, setFormatDraft] = useState('');
  const [thicknessDraft, setThicknessDraft] = useState('');
  const [typologyDraft, setTypologyDraft] = useState('');
  const [productDraft, setProductDraft] = useState({ category: '', subcategory: '', collection: '' });

  const rawAreas = list(tax.raw_tree);
  const activeArea = rawAreas.find(a => a.scope === selectedArea || a.label === selectedArea) || rawAreas[0] || { scope: 'materials', label: 'Falegnameria', categories: [] };
  const areaScope = activeArea.scope;
  const areaLabel = activeArea.label;

  useEffect(() => {
    if (!selectedArea && rawAreas[0]) setSelectedArea(rawAreas[0].scope);
  }, [tax.raw_tree]);

  const activeCategories = list(activeArea.categories).filter(c => {
    const text = [areaLabel, c.name, ...(list(c.subcategories))].join(' ').toLowerCase();
    return !q || q.toLowerCase().split(/\s+/).every(part => text.includes(part));
  });

  const activeCategory = activeCategories.find(c => c.name === selectedCategory) || activeCategories[0] || null;
  const activeSubcategories = list(activeCategory?.subcategories);
  const activeSubcategory = selectedSubcategory || activeSubcategories[0] || '';

  const productRows = Object.entries(sug.collections_by_product_path || {}).flatMap(([cat, subMap]) =>
    Object.entries(subMap || {}).flatMap(([sub, cols]) =>
      list(cols).map(col => ({ category: cat, subcategory: sub, collection: col }))
    )
  ).filter(r => {
    const text = [r.category, r.subcategory, r.collection].join(' ').toLowerCase();
    return !q || q.toLowerCase().split(/\s+/).every(part => text.includes(part));
  });
async function reloadCatalog() {
    await refreshTax();
await refreshSug();
  }

  async function save(path, obj, msg) {
    try {
      await postJSON(path, obj);
      toast(msg);
      await reloadCatalog();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function addRawCategory() {
    const payload = {
      scope: areaScope,
      category: rawDraft.category || selectedCategory,
      subcategory: rawDraft.subcategory
    };

    if (!payload.category) {
      toast('Inserisci una categoria', 'err');
      return;
    }

    await save('/categories', payload, 'Categoria salvata');
    setSelectedCategory(payload.category);
    setSelectedSubcategory(payload.subcategory || '');
    setRawDraft({ category: '', subcategory: '' });
  }

  async function removeCategory(scope, category, subcategory = '') {
    const label = subcategory
      ? `Eliminare la sottocategoria "${subcategory}" da "${category}"?`
      : `Eliminare tutta la categoria "${category}"?`;

    if (!confirm(label)) return;

    try {
      const params = new URLSearchParams({ scope, category, subcategory });
      await del('/categories?' + params.toString());
      toast(subcategory ? 'Sottocategoria eliminata' : 'Categoria eliminata');

      if (!subcategory && selectedCategory === category) {
        setSelectedCategory('');
        setSelectedSubcategory('');
      }

      if (subcategory && selectedSubcategory === subcategory) {
        setSelectedSubcategory('');
      }

      await reloadCatalog();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function addFormat() {
    const category = selectedCategory;
    if (!category || !formatDraft) {
      toast('Seleziona una categoria e inserisci un formato', 'err');
      return;
    }

    await save('/catalog/formats', { category, value: formatDraft }, 'Formato salvato');
    setFormatDraft('');
  }

  async function addThickness() {
    const category = selectedCategory;
    if (!category || !thicknessDraft) {
      toast('Seleziona una categoria e inserisci uno spessore', 'err');
      return;
    }

    await save('/catalog/thicknesses', { category, value: thicknessDraft }, 'Spessore salvato');
    setThicknessDraft('');
  }

  async function addTypology() {
    const category = selectedCategory;
    const subcategory = activeSubcategory;

    if (!category || !subcategory || !typologyDraft) {
      toast('Seleziona categoria/sottocategoria e inserisci una tipologia', 'err');
      return;
    }

    await save('/catalog/typologies', { category, subcategory, value: typologyDraft }, 'Tipologia salvata');
    setTypologyDraft('');
  }

  async function removeFormat(category, value) {
    if (!confirm(`Eliminare formato "${value}" da "${category}"?`)) return;
    try {
      const params = new URLSearchParams({ category, value });
      await del('/catalog/formats?' + params.toString());
      toast('Formato eliminato');
      await reloadCatalog();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function removeThickness(category, value) {
    if (!confirm(`Eliminare spessore "${value}" da "${category}"?`)) return;
    try {
      const params = new URLSearchParams({ category, value });
      await del('/catalog/thicknesses?' + params.toString());
      toast('Spessore eliminato');
      await reloadCatalog();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function removeTypology(category, subcategory, value) {
    if (!confirm(`Eliminare tipologia "${value}" da "${category} → ${subcategory}"?`)) return;
    try {
      const params = new URLSearchParams({ category, subcategory, value });
      await del('/catalog/typologies?' + params.toString());
      toast('Tipologia eliminata');
      await reloadCatalog();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function addProductLink() {
    if (!productDraft.category || !productDraft.subcategory || !productDraft.collection) {
      toast('Categoria, sottocategoria e collezione prodotto sono richieste', 'err');
      return;
    }

    await save('/product-links', productDraft, 'Collezione prodotto salvata');
    setProductDraft({ category: '', subcategory: '', collection: '' });
  }

  async function removeProductLink(r) {
    if (!confirm(`Eliminare il collegamento "${r.category} → ${r.subcategory} → ${r.collection}"?`)) return;

    try {
      const params = new URLSearchParams({
        category: r.category,
        subcategory: r.subcategory,
        collection: r.collection,
      });
      await del('/product-links?' + params.toString());
      toast('Collegamento prodotto eliminato');
      await reloadCatalog();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  const categoryFormats = list(pick(sug, ['formats_by_category', selectedCategory], []));
  const categoryThicknesses = list(pick(sug, ['thicknesses_by_category', selectedCategory], []));
  const subTypologies = list(pick(sug, ['typologies_by_category_subcategory', selectedCategory, activeSubcategory], []));

  const areaStats = {
    categories: list(activeArea.categories).length,
    subcategories: list(activeArea.categories).reduce((a, c) => a + list(c.subcategories).length, 0),
  };

  return <>
    <PageTitle title="Catalogo" desc="Gestisci aree, categorie, sottocategorie e configurazioni collegate." />
    <CatalogAreasSection toast={toast} refreshTax={refreshTax} refreshSug={refreshSug} />

    <Card title="Gestione catalogo" icon={Settings2} >
      <div className="catalog-topbar">
        <div className="catalog-mode-tabs">
          <button className={mode === 'raw' ? 'active' : ''} onClick={() => setMode('raw')}>Materiali e componenti</button>
          <button className={mode === 'products' ? 'active' : ''} onClick={() => setMode('products')}>Prodotti finiti</button>
        </div>
        <SearchBox value={q} onChange={setQ} placeholder="Cerca nel catalogo..." />
      </div>
    </Card>

    {mode === 'raw' && <div className="catalog-workbench">
      <section className="catalog-column catalog-areas">
        <div className="catalog-column-head">
          <span>1</span>
          <div>
            <b>Aree</b>
            <small>Ambito del materiale</small>
          </div>
        </div>

        <div className="catalog-list">
          {rawAreas.map(area => <button
            key={area.scope}
            className={(area.scope === areaScope || area.label === areaLabel) ? 'selected' : ''}
            onClick={() => {
              setSelectedArea(area.scope);
              setSelectedCategory('');
              setSelectedSubcategory('');
              setRawDraft({ category: '', subcategory: '' });
            }}
          >
            <b>{area.label}</b>
            <small>{list(area.categories).length} categorie</small>
          </button>)}
        </div>
      </section>

      <section className="catalog-column catalog-categories">
        <div className="catalog-column-head">
          <span>2</span>
          <div>
            <b>Categorie</b>
            <small>{areaLabel} · {areaStats.categories} categorie</small>
          </div>
        </div>

        <div className="catalog-create-box">
          <SmartInput label="Nuova categoria" options={rawCatsStrict ? rawCatsStrict(sug, areaScope) : rawCats(sug, areaScope)} value={rawDraft.category} onChange={e => setRawDraft({ ...rawDraft, category: e.target.value })} placeholder="Es. Legname, Acrilico, Alimentatori" />
          <SmartInput label="Sottocategoria opzionale" options={rawDraft.category ? (rawSubsStrict ? rawSubsStrict(sug, areaScope, rawDraft.category) : rawSubs(sug, areaScope, rawDraft.category)) : []} value={rawDraft.subcategory} onChange={e => setRawDraft({ ...rawDraft, subcategory: e.target.value })} placeholder="Es. Betulla, Pioppo, 12V" />
          <button className="primary" onClick={addRawCategory}><Plus /> Aggiungi</button>
        </div>

        <div className="catalog-list">
          {activeCategories.map(cat => <button
            key={cat.name}
            className={selectedCategory === cat.name || (!selectedCategory && activeCategory?.name === cat.name) ? 'selected' : ''}
            onClick={() => {
              setSelectedCategory(cat.name);
              setSelectedSubcategory('');
              setRawDraft({ category: cat.name, subcategory: '' });
            }}
          >
            <b>{cat.name}</b>
            <small>{list(cat.subcategories).length} sottocategorie · {cat.suppliers || 0} fornitori</small>
          </button>)}
          {!activeCategories.length && <Empty text="Nessuna categoria trovata" />}
        </div>
      </section>

      <section className="catalog-column catalog-subcategories">
        <div className="catalog-column-head">
          <span>3</span>
          <div>
            <b>Sottocategorie</b>
            <small>{activeCategory?.name || 'Seleziona categoria'}</small>
          </div>
        </div>

        <div className="catalog-selected-box">
          <span>Categoria selezionata</span>
          <b>{selectedCategory || activeCategory?.name || '—'}</b>
          {(selectedCategory || activeCategory?.name) && <button className="ghost danger" onClick={() => removeCategory(areaScope, selectedCategory || activeCategory?.name, '')}>Elimina categoria</button>}
        </div>

        <div className="catalog-list">
          {activeSubcategories.map(sub => <button
            key={sub}
            className={activeSubcategory === sub ? 'selected' : ''}
            onClick={() => setSelectedSubcategory(sub)}
          >
            <b>{sub}</b>
            <small>{selectedCategory || activeCategory?.name}</small>
          </button>)}
          {!activeSubcategories.length && <Empty text="Nessuna sottocategoria" />}
        </div>

        {activeSubcategory && <button className="ghost danger wide-action" onClick={() => removeCategory(areaScope, selectedCategory || activeCategory?.name, activeSubcategory)}>
          <Trash2 /> Elimina sottocategoria selezionata
        </button>}
      </section>

      <section className="catalog-column catalog-linked">
        <div className="catalog-column-head">
          <span>4</span>
          <div>
            <b>Configurazioni collegate</b>
            <small>{selectedCategory || activeCategory?.name || 'Nessuna categoria'}</small>
          </div>
        </div>

        <div className="catalog-config-card">
          <div className="catalog-config-head">
            <b>Formati</b>
            <small>Validi per la categoria</small>
          </div>
          <div className="catalog-inline-add">
            <SmartInput label="Aggiungi formato" options={formats(sug, selectedCategory || activeCategory?.name)} value={formatDraft} onChange={e => setFormatDraft(e.target.value)} placeholder="20x20, 40x40, Rotolo" />
            <button onClick={addFormat}><Plus /></button>
          </div>
          <div className="pill-list">
            {categoryFormats.map(v => <span key={v}>{v}<button onClick={() => removeFormat(selectedCategory || activeCategory?.name, v)}>×</button></span>)}
            {!categoryFormats.length && <small className="muted-cell">Nessun formato</small>}
          </div>
        </div>

        <div className="catalog-config-card">
          <div className="catalog-config-head">
            <b>Spessori</b>
            <small>Validi per la categoria</small>
          </div>
          <div className="catalog-inline-add">
            <SmartInput label="Aggiungi spessore" options={thicknesses(sug, selectedCategory || activeCategory?.name)} value={thicknessDraft} onChange={e => setThicknessDraft(e.target.value)} placeholder="2 mm, 4 mm, 10 mm" />
            <button onClick={addThickness}><Plus /></button>
          </div>
          <div className="pill-list">
            {categoryThicknesses.map(v => <span key={v}>{v}<button onClick={() => removeThickness(selectedCategory || activeCategory?.name, v)}>×</button></span>)}
            {!categoryThicknesses.length && <small className="muted-cell">Nessuno spessore</small>}
          </div>
        </div>

        <div className="catalog-config-card">
          <div className="catalog-config-head">
            <b>Tipologie</b>
            <small>Valide per la sottocategoria</small>
          </div>
          <div className="catalog-inline-add">
            <SmartInput label="Aggiungi tipologia" options={typologies(sug, selectedCategory || activeCategory?.name, activeSubcategory)} value={typologyDraft} onChange={e => setTypologyDraft(e.target.value)} placeholder="Da presa, Luce calda..." />
            <button onClick={addTypology}><Plus /></button>
          </div>
          <div className="pill-list">
            {subTypologies.map(v => <span key={v}>{v}<button onClick={() => removeTypology(selectedCategory || activeCategory?.name, activeSubcategory, v)}>×</button></span>)}
            {!subTypologies.length && <small className="muted-cell">Nessuna tipologia</small>}
          </div>
        </div>
      </section>
    </div>}

    {mode === 'products' && <div className="split-main">
      <Card title="Aggiungi collegamento prodotto" icon={Tags} sub="Esempio: Orologi → Anime → One Piece.">
        <div className="catalog-editor-grid">
          <SmartInput label="Categoria prodotto" options={sug.product_categories} value={productDraft.category} onChange={e=>setProductDraft({...productDraft,category:e.target.value,subcategory:'',collection:''})}/>
          <SmartInput label="Sottocategoria prodotto" options={prodSubs(sug, productDraft.category)} value={productDraft.subcategory} onChange={e=>setProductDraft({...productDraft,subcategory:e.target.value,collection:''})}/>
          <SmartInput label="Collezione / tema" options={collections(sug, productDraft.category, productDraft.subcategory)} value={productDraft.collection} onChange={e=>setProductDraft({...productDraft,collection:e.target.value})}/>
          <button className="primary" onClick={addProductLink}><Plus /> Salva</button>
        </div>
      </Card>

      <Card title="Categorie prodotti finiti" icon={Factory} sub={`${productRows.length} collegamenti visualizzati`}>
        <DataTable rows={productRows} empty="Nessuna categoria prodotto" columns={[
          {key:'category',label:'Categoria'},
          {key:'subcategory',label:'Sottocategoria'},
          {key:'collection',label:'Collezione'},
          {key:'act',label:'Azioni',render:r=><button className="ghost danger" onClick={()=>removeProductLink(r)}><Trash2 /> Elimina</button>}
        ]} />
      </Card>
    </div>}
  
    <CatalogAdvancedSettings toast={toast} refreshSug={refreshSug} />
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
    <PageTitle title="Clienti e fornitori" desc="Gestisci fornitori, clienti e collegamenti al catalogo." />
    <div className="split-main">
      <Card title="Nuovo fornitore" icon={Truck}  action={<button className="primary" form="supplier-form"><Save /> Salva collegamento</button>}>
        <form id="supplier-form" onSubmit={saveSupplier} className="form-grid">
          <SmartInput label="Nome fornitore" options={sug.suppliers} value={supplier.name} onChange={e=>setSupplier({...supplier,name:e.target.value})}/>
          <Select label="Area collegata" value={supplier.section} onChange={e=>setSupplier({...supplier,section:e.target.value,category:'',subcategory:''})}>{list(opt.raw_sections).map(x=><option key={x}>{x}</option>)}</Select>
          <SmartInput label="Categoria fornita" options={rawCats(sug, supplier.section)} value={supplier.category} onChange={e=>setSupplier({...supplier,category:e.target.value,subcategory:''})} />
          <SmartInput label="Sottocategoria fornita" options={rawSubs(sug, supplier.section, supplier.category)} value={supplier.subcategory} onChange={e=>setSupplier({...supplier,subcategory:e.target.value})} />
        </form>
      </Card>
      <Card title="Nuovo cliente" icon={Users}  action={<button className="primary" form="customer-form"><Save /> Salva cliente</button>}>
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



function parseCsvPurchases(text) {
  const raw = String(text || '').trim();
  if (!raw) return [];

  const lines = raw.split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) return [];

  function splitCsvLine(line) {
    const out = [];
    let cur = '';
    let quote = false;

    for (let i = 0; i < line.length; i++) {
      const ch = line[i];

      if (ch === '"') {
        if (quote && line[i + 1] === '"') {
          cur += '"';
          i++;
        } else {
          quote = !quote;
        }
      } else if ((ch === ',' || ch === ';') && !quote) {
        out.push(cur.trim());
        cur = '';
      } else {
        cur += ch;
      }
    }

    out.push(cur.trim());
    return out;
  }

  const headers = splitCsvLine(lines[0]).map(h => h.trim().toLowerCase());
  return lines.slice(1).map((line, index) => {
    const values = splitCsvLine(line);
    const row = { _row: index + 2 };

    headers.forEach((h, i) => {
      row[h] = values[i] ?? '';
    });

    return row;
  });
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


function PdfSettingsPanel({ toast }) {
  const { data: pdfSettings, refresh: refreshPdfSettings } = useApi('/settings/pdf', {});
  const [pdfForm, setPdfForm] = useState({});
  const [importModelText, setImportModelText] = useState('');

  useEffect(() => {
    setPdfForm(pdfSettings || {});
  }, [JSON.stringify(pdfSettings || {})]);

  function setPdf(key, value) {
    setPdfForm(v => ({ ...v, [key]: value }));
  }

  async function savePdfSettings() {
    try {
      await postJSON('/settings/pdf', pdfForm);
      toast('Modello PDF salvato');
      await refreshPdfSettings();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function exportPdfModel() {
    try {
      const r = await getJSON('/settings/pdf/export');
      downloadJson(r.filename || 'mn_laser_lab_pdf_template.json', r.data || {});
      toast('Modello PDF esportato');
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  async function importPdfModel() {
    try {
      const parsed = JSON.parse(importModelText);
      await postJSON('/settings/pdf/import', parsed);
      setImportModelText('');
      toast('Modello PDF importato');
      await refreshPdfSettings();
    } catch (e) {
      toast('Modello non valido: ' + (e.message || e), 'err');
    }
  }

  return <Card title="Modello PDF e dati azienda" icon={FileJson} action={<button className="primary" onClick={savePdfSettings}><Save /> Salva modello PDF</button>}>
    <div className="pdf-settings-layout">
      <div className="pdf-settings-form">
        <div className="form-grid">
          <Input label="Nome attività" value={pdfForm.company_name || ''} onChange={e => setPdf('company_name', e.target.value)} />
          <Input label="Autore / titolare" value={pdfForm.author || ''} onChange={e => setPdf('author', e.target.value)} />
          <Input label="Email" value={pdfForm.email || ''} onChange={e => setPdf('email', e.target.value)} />
          <Input label="Telefono" value={pdfForm.phone || ''} onChange={e => setPdf('phone', e.target.value)} />
          <Input label="Indirizzo" value={pdfForm.address || ''} onChange={e => setPdf('address', e.target.value)} />
          <Input label="Sito web" value={pdfForm.website || ''} onChange={e => setPdf('website', e.target.value)} />
          <Input label="P.IVA / CF" value={pdfForm.vat || ''} onChange={e => setPdf('vat', e.target.value)} />
          <Input label="Colore principale" value={pdfForm.primary_color || '#058482'} onChange={e => setPdf('primary_color', e.target.value)} />
        </div>

        <div className="form-grid">
          <Input label="Titolo PDF cliente" value={pdfForm.customer_title || ''} onChange={e => setPdf('customer_title', e.target.value)} />
          <Input label="Titolo PDF interno" value={pdfForm.internal_title || ''} onChange={e => setPdf('internal_title', e.target.value)} />
        </div>

        <Field label="Testo introduttivo">
          <textarea value={pdfForm.intro_text || ''} onChange={e => setPdf('intro_text', e.target.value)} />
        </Field>

        <Field label="Condizioni commerciali">
          <textarea value={pdfForm.terms || ''} onChange={e => setPdf('terms', e.target.value)} />
        </Field>

        <Field label="Footer PDF">
          <textarea value={pdfForm.footer || ''} onChange={e => setPdf('footer', e.target.value)} />
        </Field>

        <Field label="Logo Base64 / Data URL">
          <textarea value={pdfForm.logo_data_url || ''} onChange={e => setPdf('logo_data_url', e.target.value)} placeholder="data:image/png;base64,..." />
        </Field>
      </div>

      <div className="pdf-settings-preview">
        <div className="pdf-preview-page">
          <div className="pdf-preview-head" style={{ borderColor: pdfForm.primary_color || '#058482' }}>
            <div className="pdf-preview-logo">
              {pdfForm.logo_data_url ? <img src={pdfForm.logo_data_url} alt="Logo" /> : <span>Logo</span>}
            </div>
            <div>
              <h3>{pdfForm.company_name || 'MN Laser Lab'}</h3>
              <p>{pdfForm.author || 'Filippo Lolli'}</p>
              <p>{pdfForm.email || 'filippololli1@gmail.com'}</p>
            </div>
          </div>
          <h4>{pdfForm.customer_title || 'Preventivo cliente'}</h4>
          <p className="pdf-preview-intro">{pdfForm.intro_text || 'Testo introduttivo del preventivo.'}</p>
          <div className="pdf-preview-table">
            <span>Descrizione</span><span>Totale</span>
            <b>Creazione personalizzata</b><b>€ 120.00</b>
          </div>
          <p className="pdf-preview-terms">{pdfForm.terms || 'Condizioni commerciali.'}</p>
          <small>{pdfForm.footer || 'Footer PDF'}</small>
        </div>

        <div className="quick-actions">
          <button className="ghost" onClick={exportPdfModel}><Download /> Esporta modello</button>
        </div>

        <textarea className="import-box small" value={importModelText} onChange={e => setImportModelText(e.target.value)} placeholder="Incolla qui il JSON del modello PDF..." />
        <div className="quick-actions">
          <button className="primary" onClick={importPdfModel}><Upload /> Importa modello</button>
          <button className="ghost" onClick={() => setImportModelText('')}>Svuota</button>
        </div>
      </div>
    </div>
  </Card>;
}

function SettingsPage({ toast }) {
  const [info, setInfo] = useState({});
  const [msg, setMsg] = useState('');
  const [importText, setImportText] = useState('');
  const [backupName, setBackupName] = useState('backup manuale');
  const [backups, setBackups] = useState([]);
  const [csvText, setCsvText] = useState('');
  const [csvPreview, setCsvPreview] = useState([]);

  async function loadInfo() {
    try {
      setInfo(await getJSON('/maintenance/info'));
    } catch(e) {
      setMsg(e.message || String(e));
    }
  }

  async function loadBackups() {
    try {
      const r = await getJSON('/maintenance/backups');
      setBackups(list(r.backups));
    } catch(e) {
      toast(e.message || String(e), 'err');
    }
  }

  useEffect(() => {
    loadInfo();
    loadBackups();
  }, []);

  async function backup() {
    try {
      const r = await postJSON('/maintenance/backup-named', { name: backupName || 'manuale' });
      setMsg(r.backup || 'Backup creato');
      toast('Backup creato');
      await loadInfo();
      await loadBackups();
    } catch(e) {
      toast(e.message, 'err');
    }
  }

  async function cleanup() {
    try {
      const r = await postJSON('/maintenance/cleanup', {});
      setMsg(r.backup || 'Pulizia completata');
      toast('Pulizia completata');
      await loadInfo();
      await loadBackups();
    } catch(e) {
      toast(e.message, 'err');
    }
  }

  async function resetDb() {
    if (!confirm('Vuoi davvero svuotare l’archivio? Verrà creato un backup prima del reset.')) return;

    try {
      const r = await postJSON('/maintenance/reset', {});
      setMsg(r.backup || 'Archivio resettato');
      toast('Archivio resettato');
      await loadInfo();
      await loadBackups();
    } catch(e) {
      toast(e.message, 'err');
    }
  }

  async function exportDb() {
    try {
      const r = await getJSON('/maintenance/export');
      downloadJson(r.filename || 'mn_laser_lab_export.json', r.data || {});
      toast('Export JSON scaricato');
    } catch(e) {
      toast(e.message, 'err');
    }
  }

  async function importDb() {
    try {
      const parsed = JSON.parse(importText);
      await postJSON('/maintenance/import', { data: parsed });
      setImportText('');
      toast('Archivio importato');
      await loadInfo();
      await loadBackups();
    } catch(e) {
      toast('JSON non valido o import non riuscito: ' + (e.message || e), 'err');
    }
  }

  async function restoreBackup(filename) {
    if (!confirm(`Ripristinare il backup "${filename}"? Verrà creato un backup di sicurezza prima del ripristino.`)) return;

    try {
      const r = await postJSON('/maintenance/restore', { filename });
      setMsg(`Ripristinato: ${r.restored}\nBackup sicurezza: ${r.safety_backup}`);
      toast('Backup ripristinato. Ricarica l’app per vedere i dati aggiornati.');
      await loadInfo();
      await loadBackups();
    } catch(e) {
      toast(e.message, 'err');
    }
  }


  function previewCsv() {
    const rows = parseCsvPurchases(csvText);
    setCsvPreview(rows);
    if (!rows.length) {
      toast('Nessuna riga valida nel CSV', 'err');
    } else {
      toast(`${rows.length} righe pronte per import`);
    }
  }

  async function importPurchasesCsv() {
    const rows = csvPreview.length ? csvPreview : parseCsvPurchases(csvText);

    if (!rows.length) {
      toast('Nessuna riga da importare', 'err');
      return;
    }

    if (!confirm(`Importare ${rows.length} righe acquisto? Verrà creato un backup automatico prima dell’import.`)) return;

    try {
      const r = await postJSON('/maintenance/import-purchases', { rows });
      setMsg(`Importate: ${r.imported}\nErrori: ${list(r.errors).length}\nBackup: ${r.backup}`);

      if (list(r.errors).length) {
        toast(`Import completato con ${list(r.errors).length} errori`, 'err');
      } else {
        toast('Import acquisti completato');
        setCsvText('');
        setCsvPreview([]);
      }

      await loadInfo();
      await loadBackups();
    } catch(e) {
      toast(e.message, 'err');
    }
  }

  function backupSize(bytes) {
    const n = Number(bytes || 0);
    if (n > 1024 * 1024) return `${(n / 1024 / 1024).toFixed(2)} MB`;
    if (n > 1024) return `${(n / 1024).toFixed(1)} KB`;
    return `${n} B`;
  }

  return <>
    <PageTitle title="Impostazioni" desc="Backup, ripristino, export, import e manutenzione dell’archivio." />

    <div className="settings-grid">
      <Card title="Stato archivio" icon={ShieldCheck}>
        <div className="settings-info">
          <span>Database</span><b>{info.db_path || '—'}</b>
          <span>Cartella dati</span><b>{info.data_dir || '—'}</b>
          <span>Ultimo controllo</span><b>{info.checked_at || '—'}</b>
        </div>
      </Card>

      <Card title="Backup manuale" icon={Archive}>
        <div className="backup-create-row">
          <Input label="Nome backup" value={backupName} onChange={e => setBackupName(e.target.value)} />
          <button className="primary" onClick={backup}><Archive /> Crea backup</button>
        </div>

        <div className="settings-actions compact">
          <button onClick={exportDb}><Download /> Esporta JSON</button>
          <button onClick={cleanup}><RefreshCcw /> Ripulisci archivio</button>
          <button className="danger" onClick={resetDb}><Trash2 /> Reset archivio</button>
        </div>

        {msg && <pre>{msg}</pre>}
      </Card>
    </div>

    <Card title="Backup disponibili" icon={Database} action={<button className="ghost" onClick={loadBackups}><RefreshCcw /> Aggiorna</button>}>
      <div className="backup-list">
        {backups.length ? backups.map(b => <div key={b.filename} className="backup-row">
          <div>
            <b>{b.filename}</b>
            <small>{b.updated_at} · {backupSize(b.size)}</small>
          </div>
          <button className="ghost" onClick={() => restoreBackup(b.filename)}>Ripristina</button>
        </div>) : <Empty text="Nessun backup trovato" />}
      </div>
    </Card>


    <Card title="Import CSV acquisti" icon={Upload}>
      <div className="csv-import-grid">
        <div>
          <textarea
            className="import-box"
            value={csvText}
            onChange={e => setCsvText(e.target.value)}
            placeholder={'area,categoria,sottocategoria,formato,spessore,unita,fornitore,quantita,costo_totale\nFalegnameria,Legname,Betulla,20x20,2 mm,pz,Fornitore,10,25'}
          />
          <div className="quick-actions">
            <button className="ghost" onClick={previewCsv}><Search /> Anteprima</button>
            <button className="primary" onClick={importPurchasesCsv}><Upload /> Importa acquisti</button>
            <button className="ghost" onClick={() => { setCsvText(''); setCsvPreview([]); }}>Svuota</button>
          </div>
        </div>

        <div className="csv-preview">
          <b>Anteprima</b>
          {csvPreview.length ? csvPreview.slice(0, 8).map((r, i) => <div key={i} className="csv-preview-row">
            <span>{r.area || r.sezione || 'Area'}</span>
            <strong>{r.categoria || r.category || 'Categoria'}</strong>
            <small>{[r.sottocategoria, r.formato, r.spessore, r.quantita || r.quantità, r.costo_totale].filter(Boolean).join(' · ')}</small>
          </div>) : <Empty text="Nessuna anteprima" />}
        </div>
      </div>
    </Card>

    <PdfSettingsPanel toast={toast} />

    <Card title="Import archivio JSON" icon={Upload}>
      <textarea className="import-box" value={importText} onChange={e=>setImportText(e.target.value)} placeholder="Incolla qui il JSON da importare..." />
      <div className="quick-actions">
        <button className="primary" onClick={importDb}><FileJson /> Importa dati</button>
        <button className="ghost" onClick={()=>setImportText('')}>Svuota campo</button>
      </div>
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


function SystemStatusPanel({ toast }) {
  const { data: status, refresh } = useApi('/system/status', {});
  const lanUrl = status?.lan_url || '';
  const qrUrl = lanUrl ? `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(lanUrl)}` : '';

  async function copyLan() {
    try {
      await navigator.clipboard.writeText(lanUrl);
      toast('Link LAN copiato');
    } catch {
      toast(lanUrl || 'Link non disponibile');
    }
  }

  return <div className="system-status-grid">
    <Card title="Sistema" icon={Activity} sub="Stato runtime, backend e database locale.">
      <div className="system-kpi-grid">
        <div><span>Modalità</span><b>{status.mode || '—'}</b></div>
        <div><span>Ora</span><b>{status.time || '—'}</b></div>
        <div><span>Porta</span><b>{status.port || '—'}</b></div>
        <div><span>Python</span><b>{status.python || '—'}</b></div>
      </div>

      <div className="system-path-box">
        <span>Cartella runtime</span>
        <code>{status.cwd || '—'}</code>
      </div>

      <div className="quick-actions">
        <button className="ghost" onClick={refresh}><RefreshCw /> Aggiorna stato</button>
      </div>
    </Card>

    <Card title="Apri su smartphone" icon={Smartphone} sub="Usa l'app da telefono o tablet sulla stessa rete Wi-Fi.">
      <div className="lan-box">
        <div>
          <span>URL locale</span>
          <b>{status.local_url || '—'}</b>
        </div>
        <div>
          <span>URL rete LAN</span>
          <b>{lanUrl || '—'}</b>
        </div>
      </div>

      {qrUrl && <div className="qr-wrap">
        <img src={qrUrl} alt="QR LAN MN Laser Lab" />
        <small>Scansiona il QR dallo smartphone collegato alla stessa rete.</small>
      </div>}

      <div className="quick-actions">
        <button className="primary" onClick={copyLan}><Copy /> Copia link LAN</button>
      </div>
    </Card>

    <Card title="Archivio dati" icon={Database} sub="Riepilogo veloce del database locale.">
      <div className="system-counts">
        {Object.entries(status.db_counts || {}).map(([k,v]) => <div key={k}>
          <span>{k}</span>
          <b>{v}</b>
        </div>)}
      </div>
    </Card>
  </div>;
}



function MNLogoMark() {
  return (
    <div className="mn-logo-mark" aria-label="MN Laser Lab">
      <svg viewBox="0 0 120 120" role="img">
        <rect x="8" y="8" width="104" height="104" rx="26" fill="rgba(255,255,255,.96)" />
        <circle cx="60" cy="60" r="43" fill="none" stroke="#0f172a" strokeWidth="4" opacity=".16" />
        <path d="M25 68 L25 45 L36 45 L47 59 L58 45 L69 45 L69 75 L58 75 L58 61 L49 72 L45 72 L36 61 L36 75 L25 75 Z" fill="#0f172a"/>
        <path d="M73 45 L94 45 L94 55 L84 55 L84 75 L73 75 Z" fill="#058482"/>
        <path d="M30 84 C43 91 76 91 91 82" fill="none" stroke="#058482" strokeWidth="5" strokeLinecap="round"/>
      </svg>
    </div>
  );
}




function SystemPage({ toast }) {
  const { data: status, refresh } = useApi('/system/status', {});
  const { data: version } = useApi('/system/version', {});

  const lanUrl = status?.lan_url || '';
  const localUrl = status?.local_url || '';
  const qrSvg = lanUrl
    ? `https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(lanUrl)}`
    : '';

  async function copy(text, label = 'Copiato') {
    try {
      await navigator.clipboard.writeText(text || '');
      toast(label);
    } catch {
      toast(text || 'Dato non disponibile');
    }
  }

  return <>
    <PageTitle
      title="Sistema"
      subtitle="Stato dell'app, accesso da smartphone, rete locale e informazioni di servizio."
      icon={Activity}
    />

    <div className="system-page-grid">
      <Card title="Stato applicazione" icon={Server} sub="Backend locale e ambiente runtime.">
        <div className="system-kpi-grid">
          <div><span>Edizione</span><b>{status.edition || '—'}</b></div>
          <div><span>Versione</span><b>{status.version || version.current_version || '—'}</b></div>
          <div><span>Porta</span><b>{status.port || '—'}</b></div>
          <div><span>Ora</span><b>{status.time || '—'}</b></div>
        </div>

        <div className="system-path-box">
          <span>Cartella runtime</span>
          <code>{status.cwd || '—'}</code>
        </div>

        <div className="quick-actions">
          <button className="ghost" onClick={refresh}><RefreshCw /> Aggiorna stato</button>
        </div>
      </Card>

      <Card title="Accesso mobile" icon={Smartphone} sub="Apri il gestionale da smartphone o tablet sulla stessa rete Wi-Fi.">
        <div className="lan-access-box">
          <div>
            <span>Da questo PC</span>
            <b>{localUrl || '—'}</b>
            <button className="ghost" onClick={() => copy(localUrl, 'Link locale copiato')}><Copy /> Copia</button>
          </div>

          <div>
            <span>Da smartphone / rete LAN</span>
            <b>{lanUrl || '—'}</b>
            <button className="primary" onClick={() => copy(lanUrl, 'Link LAN copiato')}><Copy /> Copia link LAN</button>
          </div>
        </div>

        {qrSvg && <div className="mobile-qr-box">
          <img src={qrSvg} alt="QR code accesso mobile MN Laser Lab" />
          <small>Scansiona il QR con lo smartphone collegato alla stessa rete Wi-Fi del PC.</small>
        </div>}
      </Card>

      <Card title="Database locale" icon={Database} sub="Conteggio rapido dei dati principali salvati.">
        <div className="system-counts">
          {Object.entries(status.db_counts || {}).map(([k, v]) => (
            <div key={k}>
              <span>{k}</span>
              <b>{v}</b>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Aggiornamenti" icon={DownloadCloud} sub="Base per il futuro update manager della Browser Edition.">
        <div className="update-status-box">
          <div>
            <span>Canale</span>
            <b>{version.channel || 'browser-edition'}</b>
          </div>
          <div>
            <span>Aggiornamenti automatici</span>
            <b>{version.automatic_updates ? 'Attivi' : 'Non ancora attivi'}</b>
          </div>
        </div>
        <p className="muted">{version.message || 'Gli aggiornamenti automatici saranno integrati in una prossima versione.'}</p>
      </Card>
    </div>
  </>;
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
    { id: 'system', label: 'Sistema', icon: Activity },
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
</div><button className="command" onClick={()=>setCmd(true)}><Command/> Cerca <kbd>⌘K</kbd></button><nav>{nav.map(n=><button key={n.id} className={tab===n.id?'active':''} onClick={()=>go(n.id)}><n.icon/>{n.label}</button>)}</nav><FocusStrip go={go}/><div className="side-note"><b>Flusso operativo</b><br/>Acquisti → Produzione → Preventivi → Vendite.</div></aside><main><div className="top-right-tools"><button className="theme-toggle" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} aria-label="Cambia modalità colore"><Sun/><span></span><Moon/></button></div><div className="content-main"><Page go={go} toast={push}/></div></main><Toasts/><CommandPalette open={cmd} setOpen={setCmd} nav={nav} go={go}/></div>;
}

createRoot(document.getElementById('root')).render(<App />);
