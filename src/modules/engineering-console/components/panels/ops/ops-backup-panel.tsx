"use client";

import { ArrowLeft, Database, ShieldCheck, CheckCircle2, AlertTriangle } from "lucide-react";
import { Panel, PanelGrid } from "../../panel";
import { Stat } from "../../stat";
import { StatusBadge } from "../../cert/cert-primitives";
import { fmtAge, fmtCompact } from "@/modules/engineering-console/lib/format";
import type { BackupJob, RestoreTest } from "@/modules/engineering-console/lib/ops-types";

interface Props {
  backups: BackupJob[];
  restoreTests: RestoreTest[];
  onBack: () => void;
}

const BACKUP_TYPE_COLORS: Record<BackupJob["type"], string> = {
  full: "#22d3ee",
  incremental: "#34d399",
  snapshot: "#a78bfa",
  wal: "#fbbf24",
};

export function OpsBackupPanel({ backups, restoreTests, onBack }: Props) {
  const verified = backups.filter((b) => b.restoreVerified).length;
  const failed = backups.filter((b) => b.status === "failed").length;
  const totalSize = backups.reduce((s, b) => s + b.sizeBytes, 0);
  const restorePassRate = restoreTests.filter((r) => r.status === "pass").length / Math.max(1, restoreTests.length);

  return (
    <PanelGrid>
      <Panel
        title="Backup & Restore Verification"
        subtitle={`${backups.length} backups across ${new Set(backups.map((b) => b.target)).size} targets · ${restoreTests.length} restore tests`}
        icon={<Database className="h-3.5 w-3.5" />}
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
            <div className="col-span-2">Target</div>
            <div className="col-span-1">Type</div>
            <div className="col-span-2 text-right">Size</div>
            <div className="col-span-2 text-right">Duration</div>
            <div className="col-span-2">Hash</div>
            <div className="col-span-2">Location</div>
            <div className="col-span-1 text-right">Status</div>
          </div>
          {backups.map((b) => (
            <div key={b.id} className="grid grid-cols-12 px-3 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
              <div className="col-span-2 font-mono font-semibold truncate">{b.target}</div>
              <div className="col-span-1">
                <span className="text-[9px] font-mono px-1 py-0.5 rounded" style={{ color: BACKUP_TYPE_COLORS[b.type], backgroundColor: `${BACKUP_TYPE_COLORS[b.type]}22` }}>
                  {b.type}
                </span>
              </div>
              <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{fmtCompact(b.sizeBytes)}B</div>
              <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{b.durationMs ? (b.durationMs / 1000).toFixed(1) : "—"}s</div>
              <div className="col-span-2 font-mono text-[9.5px] text-muted-foreground/80 truncate">{b.hash.slice(0, 16)}…</div>
              <div className="col-span-2 font-mono text-[9px] text-muted-foreground/60 truncate" title={b.location}>{b.location.split("/").slice(-2).join("/")}</div>
              <div className="col-span-1 flex justify-end">
                <StatusBadge status={b.status === "verified" ? "pass" : b.status === "completed" ? "pass" : b.status === "expired" ? "pending" : b.status === "failed" ? "fail" : "running"} />
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel
        title="Backup Health"
        subtitle="Aggregate metrics"
        icon={<Database className="h-3.5 w-3.5" />}
        className="col-span-12 xl:col-span-3"
      >
        <div className="grid grid-cols-2 gap-2 mb-3">
          <Stat label="Total Backups" value={backups.length} intent="info" />
          <Stat label="Restore Verified" value={verified} unit={`/ ${backups.length}`} intent="healthy" />
          <Stat label="Failed" value={failed} intent={failed > 0 ? "critical" : "healthy"} />
          <Stat label="Total Size" value={`${fmtCompact(totalSize)}B`} />
        </div>

        <div className="pt-3 border-t border-border/40">
          <div className="text-[9.5px] uppercase tracking-wider text-muted-foreground/80 mb-2">Restore Test Pass Rate</div>
          <div className="h-2 rounded-full bg-background/60 overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{
                width: `${restorePassRate * 100}%`,
                backgroundColor: restorePassRate >= 0.95 ? "#34d399" : restorePassRate >= 0.8 ? "#fbbf24" : "#f87171",
              }}
            />
          </div>
          <div className="mt-1 text-[10.5px] font-mono text-muted-foreground">
            {(restorePassRate * 100).toFixed(1)}% ({restoreTests.filter((r) => r.status === "pass").length}/{restoreTests.length})
          </div>
        </div>
      </Panel>

      {/* Restore tests */}
      <Panel
        title="Restore Verification Tests"
        subtitle="Automated sandbox restores verify backup integrity"
        icon={<ShieldCheck className="h-3.5 w-3.5" />}
        className="col-span-12"
        bodyClassName="p-0"
      >
        <div className="max-h-[280px] overflow-y-auto scroll-thin">
          <div className="grid grid-cols-12 px-3 py-1.5 text-[9.5px] uppercase tracking-wider text-muted-foreground/70 bg-background/30 border-b border-border/40">
            <div className="col-span-2">Backup</div>
            <div className="col-span-2">Sandbox</div>
            <div className="col-span-2 text-right">Rows Verified</div>
            <div className="col-span-1 text-right">Hash</div>
            <div className="col-span-2 text-right">Duration</div>
            <div className="col-span-2">When</div>
            <div className="col-span-1 text-right">Status</div>
          </div>
          {restoreTests.map((r) => (
            <div key={r.id} className="grid grid-cols-12 px-3 py-1.5 text-[11px] items-center hover:bg-accent/30 border-b border-border/20">
              <div className="col-span-2 font-mono text-[9.5px] text-muted-foreground truncate">{r.backupId}</div>
              <div className="col-span-2 font-mono text-[10px]">{r.sandbox}</div>
              <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{fmtCompact(r.rowsVerified)}</div>
              <div className="col-span-1 text-right">
                {r.hashMatch ? <CheckCircle2 className="h-3 w-3 inline" style={{ color: "#34d399" }} /> : <AlertTriangle className="h-3 w-3 inline" style={{ color: "#f87171" }} />}
              </div>
              <div className="col-span-2 text-right font-mono tabular-nums text-muted-foreground">{(r.durationMs / 1000).toFixed(1)}s</div>
              <div className="col-span-2 font-mono text-[9.5px] text-muted-foreground/70">{fmtAge(Date.now() - r.completedAt)}</div>
              <div className="col-span-1 flex justify-end">
                <StatusBadge status={r.status === "pass" ? "pass" : "fail"} />
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </PanelGrid>
  );
}
