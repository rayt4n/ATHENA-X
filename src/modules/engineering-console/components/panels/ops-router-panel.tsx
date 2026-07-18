"use client";

import { useState } from "react";
import { useOps } from "@/modules/engineering-console/hooks/use-ops";
import { OpsOverviewPanel } from "./ops/ops-overview-panel";
import { OpsTracePanel } from "./ops/ops-trace-panel";
import { OpsLogsPanel } from "./ops/ops-logs-panel";
import { OpsBackupPanel } from "./ops/ops-backup-panel";
import { OpsHealthPanel } from "./ops/ops-health-panel";
import { OpsFailurePanel } from "./ops/ops-failure-panel";
import { OpsConfigPanel } from "./ops/ops-config-panel";
import { OpsPluginsPanel } from "./ops/ops-plugins-panel";
import { OpsReadinessPanel } from "./ops/ops-readiness-panel";

/**
 * Ops Router Panel — manages navigation between the 9 Stage 15.5
 * subsystem panels. The overview is the default view; clicking any
 * subsystem card drills into its detail panel.
 */
export function OpsRouterPanel() {
  const { ops, reset } = useOps(2000);
  const [drillTarget, setDrillTarget] = useState<string | null>(null);

  const back = () => setDrillTarget(null);

  if (drillTarget === "traceability") return <OpsTracePanel traces={ops.traces} onBack={back} />;
  if (drillTarget === "logging" || drillTarget === "aggregation") return <OpsLogsPanel logs={ops.logs} onBack={back} />;
  if (drillTarget === "backup") return <OpsBackupPanel backups={ops.backups} restoreTests={ops.restoreTests} onBack={back} />;
  if (drillTarget === "health") return <OpsHealthPanel checks={ops.healthChecks} onBack={back} />;
  if (drillTarget === "failure") return <OpsFailurePanel scenarios={ops.failureScenarios} onBack={back} />;
  if (drillTarget === "config") return <OpsConfigPanel configs={ops.configs} onBack={back} />;
  if (drillTarget === "plugins") return <OpsPluginsPanel plugins={ops.plugins} onBack={back} />;
  if (drillTarget === "readiness") return <OpsReadinessPanel readiness={ops.readiness} onBack={back} />;

  return <OpsOverviewPanel ops={ops} onReset={reset} onDrill={setDrillTarget} />;
}
