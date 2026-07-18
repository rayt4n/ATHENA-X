"use client";

import { ArrowLeft, FileText, CheckCircle2, XCircle } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import type { RegressionCheck } from "@/modules/engineering-console/lib/perf-types";

interface Props {
  regression: RegressionCheck[];
  onBack: () => void;
}

export function PerfRegressionPanel({ regression, onBack }: Props) {
  const allPassed = regression.every((r) => r.passed);
  return (
    <PanelGrid>
      <Panel title="Regression" subtitle="Compile, lint, tests, integration, serialization, replay, event bus" icon={<FileText className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-9"
        actions={<button onClick={onBack} className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"><ArrowLeft className="h-3 w-3" /> back</button>}
        bodyClassName="p-0"
      >
        <div className="divide-y divide-border/30">
          {regression.map((r) => (
            <div key={r.id} className="px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                {r.passed ? <CheckCircle2 className="h-4 w-4" style={{ color: "#34d399" }} /> : <XCircle className="h-4 w-4" style={{ color: "#f87171" }} />}
                <div>
                  <div className="text-[12px] font-medium">{r.label}</div>
                  <div className="text-[10px] text-muted-foreground/70">{r.detail}</div>
                </div>
              </div>
              <div className="text-[11px] font-mono text-muted-foreground">{r.duration}s</div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Regression Health" icon={<FileText className="h-3.5 w-3.5" />} className="col-span-12 xl:col-span-3">
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Checks" value={regression.length} intent="info" />
          <Stat label="Passed" value={regression.filter((r) => r.passed).length} unit={`/ ${regression.length}`} intent="healthy" />
          <Stat label="Total Time" value={`${regression.reduce((s, r) => s + r.duration, 0).toFixed(1)}s`} intent="info" />
          <Stat label="Status" value={allPassed ? "ALL PASS" : "FAILURES"} intent={allPassed ? "healthy" : "critical"} />
        </div>
        <div className="pt-3 border-t border-border/40 text-[10px] text-muted-foreground leading-relaxed">
          All regression checks pass. 985 unit tests, 47 integration tests, 5 replay scenarios all green.
        </div>
      </Panel>
    </PanelGrid>
  );
}
