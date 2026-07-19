"use client";

import { ArrowLeft, GitBranch, AlertTriangle, ShieldCheck } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import type { DependencyImpact, DependencyNode } from "@/modules/engineering-console/lib/ops-types";

interface Props {
  dependencies: DependencyImpact;
  onBack: () => void;
}

const TYPE_COLORS: Record<DependencyNode["type"], string> = {
  service: "#22d3ee",
  database: "#fbbf24",
  queue: "#a78bfa",
  provider: "#34d399",
  agent: "#fb923c",
  external: "#94a3b8",
};

export function OpsDependencyPanel({ dependencies, onBack }: Props) {
  const healthyCount = dependencies.nodes.filter((n) => n.status === "healthy").length;
  const spofCount = dependencies.singlePointsOfFailure.length;

  return (
    <PanelGrid>
      <Panel
        title="Dependency Impact Visualization"
        subtitle={`${dependencies.nodes.length} nodes · ${dependencies.edges.length} edges · max blast radius ${dependencies.maxBlastRadius}`}
        icon={<GitBranch className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-9"
        actions={
          <button
            onClick={onBack}
            className="flex items-center gap-1 px-2 py-1 rounded-md border border-border/60 hover:bg-accent/50 text-[10.5px] font-mono text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-3 w-3" /> back
          </button>
        }
      >
        {/* Dependency graph — grid layout */}
        <div className="mb-4 rounded-md border border-border/40 bg-background/30 p-4">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-3">Dependency Graph</div>
          <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
            {dependencies.nodes.map((node) => {
              const color = TYPE_COLORS[node.type];
              const isSpof = !node.hasFailover && node.blastRadius > 1;
              return (
                <div
                  key={node.id}
                  className="rounded-md border p-2 text-center"
                  style={{
                    borderColor: isSpof ? "rgba(248, 113, 113, 0.4)" : `${color}55`,
                    backgroundColor: isSpof ? "rgba(248, 113, 113, 0.05)" : `${color}08`,
                  }}
                >
                  <div className="w-2 h-2 rounded-full mx-auto mb-1" style={{ backgroundColor: color }} />
                  <div className="text-[9.5px] font-medium truncate" title={node.name}>{node.name}</div>
                  <div className="text-[8px] font-mono text-muted-foreground/70 uppercase mt-0.5">{node.type}</div>
                  <div className="mt-1 text-[8.5px] font-mono" style={{ color: node.blastRadius > 5 ? "#fbbf24" : "#94a3b8" }}>
                    blast: {node.blastRadius}
                  </div>
                  {isSpof && (
                    <div className="mt-0.5 text-[8px] font-mono" style={{ color: "#f87171" }}>
                      ⚠ SPOF
                    </div>
                  )}
                  {!node.hasFailover && node.blastRadius <= 1 && (
                    <div className="mt-0.5 text-[8px] font-mono text-muted-foreground/50">no failover</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Critical path */}
        <div className="mb-4 rounded-md border border-border/40 bg-background/30 p-3">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Critical Path</div>
          <div className="flex items-center gap-2 flex-wrap">
            {dependencies.criticalPath.map((node, i) => (
              <div key={node} className="flex items-center gap-2">
                <span className="text-[10px] font-mono px-2 py-1 rounded bg-primary/10 text-primary border border-primary/20">
                  {node}
                </span>
                {i < dependencies.criticalPath.length - 1 && (
                  <span className="text-primary/60 text-[10px]">→</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Node details table */}
        <div className="rounded-md border border-border/40 overflow-hidden">
          <div className="grid grid-cols-12 px-3 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/40 border-b border-border/40">
            <div className="col-span-4">Node</div>
            <div className="col-span-2">Type</div>
            <div className="col-span-1 text-right">Deps</div>
            <div className="col-span-1 text-right">Blast</div>
            <div className="col-span-2 text-right">Latency</div>
            <div className="col-span-1 text-right">Failover</div>
            <div className="col-span-1 text-right">Status</div>
          </div>
          {dependencies.nodes.map((n) => {
            const color = TYPE_COLORS[n.type];
            return (
              <div key={n.id} className="grid grid-cols-12 px-3 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
                <div className="col-span-4 font-medium truncate flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: color }} />
                  {n.name}
                </div>
                <div className="col-span-2">
                  <span className="text-[9px] font-mono px-1 py-0.5 rounded" style={{ color, backgroundColor: `${color}22` }}>{n.type}</span>
                </div>
                <div className="col-span-1 text-right font-mono tabular-nums text-muted-foreground">{n.dependents}</div>
                <div className="col-span-1 text-right font-mono tabular-nums" style={{ color: n.blastRadius > 5 ? "#fbbf24" : "#94a3b8" }}>{n.blastRadius}</div>
                <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{n.latencyMs.toFixed(1)}ms</div>
                <div className="col-span-1 text-right">
                  {n.hasFailover ? <span style={{ color: "#34d399" }}>✓</span> : <span style={{ color: "#f87171" }}>✗</span>}
                </div>
                <div className="col-span-1 flex justify-end">
                  <StatusBadge status={n.status === "healthy" ? "pass" : n.status === "degraded" ? "warn" : "fail"} />
                </div>
              </div>
            );
          })}
        </div>
      </Panel>

      <Panel
        title="Dependency Health"
        icon={<ShieldCheck className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-3"
      >
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Nodes" value={dependencies.nodes.length} intent="info" />
          <Stat label="Healthy" value={healthyCount} unit={`/ ${dependencies.nodes.length}`} intent="healthy" />
          <Stat label="Max Blast" value={dependencies.maxBlastRadius} intent={dependencies.maxBlastRadius < 10 ? "healthy" : "warning"} />
          <Stat label="SPOFs" value={spofCount} intent={spofCount === 0 ? "healthy" : "warning"} />
        </div>

        <div className="pt-3 border-t border-border/40">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">By Type</div>
          <div className="space-y-1.5">
            {(Object.keys(TYPE_COLORS) as DependencyNode["type"][]).map((type) => {
              const items = dependencies.nodes.filter((n) => n.type === type);
              if (items.length === 0) return null;
              const color = TYPE_COLORS[type];
              return (
                <div key={type} className="flex items-center justify-between text-[10px] font-mono">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                    <span className="text-muted-foreground">{type}</span>
                  </span>
                  <span className="text-foreground">{items.length}</span>
                </div>
              );
            })}
          </div>
        </div>

        {spofCount > 0 && (
          <div className="mt-3 pt-3 border-t border-border/40 rounded-md p-2" style={{ backgroundColor: "rgba(251, 191, 36, 0.08)", border: "1px solid rgba(251, 191, 36, 0.3)" }}>
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="h-3 w-3" style={{ color: "#fbbf24" }} />
              <span className="text-[10px] font-semibold" style={{ color: "#fbbf24" }}>{spofCount} SPOF{spofCount === 1 ? "" : "s"}</span>
            </div>
            <div className="text-[9.5px] font-mono text-muted-foreground/80">
              {dependencies.singlePointsOfFailure.join(", ")}
            </div>
          </div>
        )}

        <div className="pt-3 mt-3 border-t border-border/40">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Failover Coverage</div>
          <div className="space-y-1 text-[10px] font-mono">
            <div className="flex justify-between"><span className="text-muted-foreground/70">with failover</span><span style={{ color: "#34d399" }}>{dependencies.nodes.filter((n) => n.hasFailover).length}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground/70">no failover</span><span style={{ color: dependencies.nodes.filter((n) => !n.hasFailover).length > 0 ? "#fbbf24" : "#34d399" }}>{dependencies.nodes.filter((n) => !n.hasFailover).length}</span></div>
          </div>
        </div>
      </Panel>
    </PanelGrid>
  );
}
