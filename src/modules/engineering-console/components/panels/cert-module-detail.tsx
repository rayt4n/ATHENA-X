"use client";

import { ArrowLeft, Beaker } from "lucide-react";
import { Panel } from "../panel";
import { CheckRow, ScoreRing, StatusBadge } from "../cert/cert-primitives";
import type { CertModule } from "@/modules/engineering-console/lib/certification-types";

interface Props {
  module: CertModule;
  onBack: () => void;
  children?: React.ReactNode;
}

export function CertModuleDetailPanel({ module, onBack, children }: Props) {
  return (
    <Panel
      title={module.name}
      subtitle={module.description}
      icon={<Beaker className="h-3.5 w-3.5" />}
      className="col-span-12"
      actions={
        <div className="flex items-center gap-2">
          <StatusBadge status={module.status} />
          <button
            onClick={onBack}
            className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-3 w-3" />
            back
          </button>
        </div>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-4">
        <div className="flex flex-col items-center justify-center py-2 lg:border-r border-border/40">
          <ScoreRing score={module.score} size={80} label="module" />
          <div className="mt-2 text-[10px] font-mono text-muted-foreground text-center">
            {module.checks.filter((c) => c.status === "pass").length} pass ·{" "}
            {module.checks.filter((c) => c.status === "warn").length} warn ·{" "}
            {module.checks.filter((c) => c.status === "fail").length} fail
          </div>
        </div>
        <div className="lg:col-span-3 grid grid-cols-2 md:grid-cols-4 gap-2">
          {module.checks.slice(0, 8).map((c) => (
            <div key={c.id} className="rounded-md border border-border/40 bg-background/30 p-2">
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-[9.5px] uppercase tracking-wider text-muted-foreground/70 truncate">{c.label}</span>
                <StatusBadge status={c.status} />
              </div>
              <div className="text-[14px] font-mono tabular-nums font-semibold" style={{
                color: c.status === "pass" ? "#34d399" : c.status === "warn" ? "#fbbf24" : "#f87171",
              }}>
                {c.value ?? "—"}
                {c.unit && <span className="ml-1 text-[9.5px] text-muted-foreground">{c.unit}</span>}
              </div>
              {c.target && <div className="text-[9px] font-mono text-muted-foreground/70 mt-0.5">target: {c.target}</div>}
            </div>
          ))}
        </div>
      </div>

      {children}

      <div className="rounded-md border border-border/40 overflow-hidden">
        <div className="grid grid-cols-12 px-3 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/40 border-b border-border/40">
          <div className="col-span-4">Check</div>
          <div className="col-span-2 text-right">Value</div>
          <div className="col-span-2 text-right">Target</div>
          <div className="col-span-3">Evidence</div>
          <div className="col-span-1 text-right">Status</div>
        </div>
        {module.checks.map((c) => (
          <CheckRow key={c.id} check={c} />
        ))}
      </div>
    </Panel>
  );
}
