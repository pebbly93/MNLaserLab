from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "frontend" / "src" / "main.jsx"

STEP4 = r'''{step === 4 && <div className="wizard-panel">
        <Card title="Trattamenti e finiture prodotto" icon={Settings2} sub="Finiture applicate al pezzo, gestite separatamente dalla distinta materiali.">
          <TreatmentCostPanel
            treatments={woodTreatments}
            selectedRows={draft.treatments}
            setSelectedRows={(fn) => setDraft(v => ({ ...v, treatments: typeof fn === 'function' ? fn(v.treatments || []) : fn }))}
            toast={toast}
            compact
          />
        </Card>

        <Card title="Lavoro, extra e costo interno" icon={Calculator}>
          <div className="muted-hint">
            <span>Imposta tempo di lavorazione, tariffa e costi aggiuntivi per calcolare il costo interno.</span>
          </div>

          <div className="form-grid">
            <Input label="Ore lavoro/u" type="number" step="0.01" value={draft.labor_hours} onChange={e => setDraft({ ...draft, labor_hours: e.target.value })} />
            <Input label="Tariffa €/h" type="number" step="0.01" value={draft.hourly_rate} onChange={e => setDraft({ ...draft, hourly_rate: e.target.value })} />
            <Input label="Extra per pezzo €" type="number" step="0.01" value={draft.extra_unit_cost} onChange={e => setDraft({ ...draft, extra_unit_cost: e.target.value })} />
          </div>

          <div className="wizard-cost-grid">
            <span>Materiali</span><b>{money(materialCost)}</b>
            <span>Trattamenti</span><b>{money(treatmentCost)}</b>
            <span>Lavoro</span><b>{money(laborCost)}</b>
            <span>Extra</span><b>{money(extraCost)}</b>
            <span>Totale costo interno</span><b>{money(totalCost)}</b>
          </div>
        </Card>
      </div>}'''

def main():
    s = MAIN.read_text(encoding="utf-8")

    start = s.find("{step === 4 && <div className=\"wizard-panel\">")
    if start == -1:
        raise RuntimeError("Blocco step 4 ProductWizard non trovato")

    next_step = s.find("{step === 5 &&", start)
    if next_step == -1:
        raise RuntimeError("Blocco step 5 non trovato: non posso delimitare lo step 4")

    s = s[:start] + STEP4 + "\n\n      " + s[next_step:]

    MAIN.write_text(s, encoding="utf-8")
    print("Fix v42.3.0b applicato: step 4 ProductWizard ricostruito correttamente.")

if __name__ == "__main__":
    main()
