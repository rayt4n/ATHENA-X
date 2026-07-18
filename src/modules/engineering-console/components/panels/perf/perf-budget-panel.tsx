"use client";

import { ArrowLeft, Gauge } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import type { BudgetItem } from "@/modules/engineering-console/lib/perf-types";

interface Props {
  budget: BudgetItem[];
  onBack: () => void;
}

const CAT_COLORS: Record<string, string> = { frontend: "#22d3ee", backend: "#34d399", agent: "#fbbf24", resource: "#a78bfa" };

export function PerfBudgetPanel({ budget, onBack }: Props) {
  const passing = budget.filter((b) => b.status === "pass").length;
  return (
    <PanelGrid>
      <Panel title="Performance Budget" subtitle="Budget thresholds vs actuals across frontend, backend, agent, resource" icon={<Gauge className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-9"
        actions={<button onClick={onBack} className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"><ArrowLeft className="h-3 w-3" /> back</button>}
        bodyClassName="p-0"
      >
        <div className="max-h-[500px] overflow-y-auto scroll-thin">
          <div className="grid grid-cols-12 px-3 py-1.5 text-[9px] uppercase tracking-wider text-muted-foreground/70 bg-background/40 border-b border-border/40 sticky top-0">
            <div className="col-span-3">Metric</div>
            <div className="col-span-2">Category</div>
            <div className="col-span-2 text-right">Budget</div>
            <div className="col-span-2 text-right">Actual</div>
            <div className="col-span-2 text-right">Utilization</div>
            <div className="col-span-1 text-right">Status</div>
          </div>
          {budget.map((b) => {
            const util = b.metric === "Frame Rate" ? (b.budget / b.actual) * 100 : (b.actual / b.budget) * 100;
            return (
              <div key={b.id} className="grid grid-cols-12 px-3 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
                <div className="col-span-3 font-medium">{b.metric}</div>
                <div className="col-span-2">
                  <span className="text-[8px] font-mono px-1 py-0.5 rounded" style={{ color: CAT_COLORS[b.category], backgroundColor: `${CAT_COLORS[b.category]}22` }}>{b.category}</span>
                </div>
                <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{b.budget} {b.unit}</div>
                <div className="col-span-2 text-right font-mono tabular-nums" style={{ color: b.status === "pass" ? "#34d399" : b.status === "warn" ? "#fbbf24" : "#f87171" }}>{b.actual} {b.unit}</div>
                <div className="col-span-2">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 rounded-full bg-background/60 overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${Math.min(100, util)}%`, backgroundColor: b.status === "pass" ? "#34d399" : b.status === "warn" ? "#fbbf24" : "#f87171" }} />
                    </div>
                    <span className="text-[9px] font-mono text-muted-foreground w-10 text-right">{util.toFixed(0)}%</span>
                  </div>
                </div>
                <div className="col-span-1 flex justify-end"><StatusBadge status={b.status} /></div>
              </div>
            );
          })}
        </div>
      </Panel>
      <Panel title="Budget Compliance" icon={<Gauge className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-3">
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Budget Items" value={budget.length} intent="info" />
          <Stat label="Within Budget" value={passing} unit={`/ ${budget.length}`} intent="healthy" />
          <Stat label="Compliance" value={`${((passing / budget.length) * 100).toFixed(0)}%`} intent="healthy" />
          <Stat label="Over Budget" value={budget.filter((b) => b.status === "fail").length} intent={budget.filter((b) => b.status === "fail").length > 0 ? "critical" : "healthy"} />
        </div>
        <div className="pt-3 border-t border-border/40">
          <div className="text-[9px] uppercase tracking-wider text-muted-foreground/70 mb-2">By Category</div>
          <div className="space-y-1">
            {Object.keys(CAT_COLORS).map((cat) => {
              const items = budget.filter((b) => b.category === cat);
              const passCount = items.filter((b) => b.status === "pass").length;
              return (
                <div key={cat} className="flex items-center justify-between text-[10px] font-mono">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: CAT_COLORS[cat] }} />
                    <span className="text-muted-foreground">{cat}</span>
                  </span>
                  <span style={{ color: passCount === items.length ? "#34d399" : "#fbbf24" }}>{passCount}/{items.length}</span>
                </div>
              );
            })}
          </div>
        </div>
      </Panel>
    </PanelGrid>
  );
}
