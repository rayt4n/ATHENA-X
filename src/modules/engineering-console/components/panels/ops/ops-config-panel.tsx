"use client";

import { ArrowLeft, ShieldCheck, GitBranch, AlertOctagon } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import { fmtAge, fmtCompact } from "@/modules/engineering-console/lib/format";
import type { ConfigFile } from "@/modules/engineering-console/lib/ops-types";

interface Props {
  configs: ConfigFile[];
  onBack: () => void;
}

export function OpsConfigPanel({ configs, onBack }: Props) {
  const valid = configs.filter((c) => c.status === "valid" && !c.secretsDetected).length;
  const drift = configs.filter((c) => c.status === "drift").length;
  const invalid = configs.filter((c) => c.status === "invalid").length;
  const secrets = configs.filter((c) => c.secretsDetected).length;

  return (
    <PanelGrid>
      <Panel
        title="Configuration Validation & Version Control"
        subtitle={`${configs.length} config files · validated against schema + git-pinned + secrets-scanned`}
        icon={<ShieldCheck className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-9"
        actions={
          <button
            onClick={onBack}
            className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-3 w-3" /> back
          </button>
        }
        bodyClassName="p-0"
      >
        <div className="max-h-[560px] overflow-y-auto scroll-thin">
          <div className="grid grid-cols-12 px-3 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/30 border-b border-border/40">
            <div className="col-span-4">Path</div>
            <div className="col-span-2">Module</div>
            <div className="col-span-2">Git Commit</div>
            <div className="col-span-1 text-right">Size</div>
            <div className="col-span-2">Last Validated</div>
            <div className="col-span-1 text-right">Status</div>
          </div>
          {configs.map((c) => (
            <div key={c.id} className="px-3 py-2 hover:bg-accent/30 border-b border-border/20">
              <div className="grid grid-cols-12 gap-2 items-center text-[11px]">
                <div className="col-span-4 font-mono truncate flex items-center gap-1.5">
                  {c.secretsDetected && <AlertOctagon className="h-3 w-3 shrink-0" style={{ color: "#f87171" }} />}
                  {c.path}
                </div>
                <div className="col-span-2 font-mono text-[9.5px] text-muted-foreground truncate">{c.module}</div>
                <div className="col-span-2 font-mono text-[9px] text-muted-foreground/70 truncate" title={c.gitCommit}>
                  <GitBranch className="h-2.5 w-2.5 inline mr-1" />{c.gitCommit.slice(0, 8)}
                </div>
                <div className="col-span-1 text-right font-mono text-[9.5px] text-muted-foreground">{fmtCompact(c.sizeBytes)}B</div>
                <div className="col-span-2 font-mono text-[9.5px] text-muted-foreground/70">{fmtAge(Date.now() - c.lastValidatedAt)}</div>
                <div className="col-span-1 flex justify-end">
                  <StatusBadge status={c.status === "valid" && !c.secretsDetected ? "pass" : c.status === "drift" ? "warn" : "fail"} />
                </div>
              </div>
              {c.findings.length > 0 && (
                <div className="mt-1.5 ml-4 space-y-0.5">
                  {c.findings.map((f, i) => (
                    <div key={i} className="text-[9.5px] font-mono text-muted-foreground/80">• {f}</div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </Panel>

      <Panel
        title="Config Health"
        icon={<ShieldCheck className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-3"
      >
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Valid" value={valid} unit={`/ ${configs.length}`} intent="healthy" />
          <Stat label="Drifted" value={drift} intent={drift > 0 ? "warning" : "healthy"} />
          <Stat label="Invalid" value={invalid} intent={invalid > 0 ? "critical" : "healthy"} />
          <Stat label="Secrets Found" value={secrets} intent={secrets > 0 ? "critical" : "healthy"} />
        </div>

        <div className="pt-3 border-t border-border/40">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Validation Pipeline</div>
          <div className="space-y-1.5 text-[10px] font-mono">
            <div className="flex justify-between"><span className="text-muted-foreground/70">1. schema check</span><span style={{ color: "#34d399" }}>✓</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">2. required fields</span><span style={{ color: "#34d399" }}>✓</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">3. type check</span><span style={{ color: "#34d399" }}>✓</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">4. secrets scan</span><span style={{ color: secrets > 0 ? "#f87171" : "#34d399" }}>{secrets > 0 ? "✗" : "✓"}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">5. git diff</span><span style={{ color: drift > 0 ? "#fbbf24" : "#34d399" }}>{drift > 0 ? "⚠" : "✓"}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">6. hash sign</span><span style={{ color: "#34d399" }}>✓</span></div>
          </div>
        </div>

        <div className="pt-3 mt-3 border-t border-border/40">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Version Control</div>
          <div className="space-y-1 text-[10px] font-mono">
            <div className="flex justify-between"><span className="text-muted-foreground/70">repo</span><span>athena-x-config</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">branch</span><span>main</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">signed commits</span><span style={{ color: "#34d399" }}>required</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">review</span><span>2 approvers</span></div>
          </div>
        </div>
      </Panel>
    </PanelGrid>
  );
}
