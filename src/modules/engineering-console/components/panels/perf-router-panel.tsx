"use client";

import { useState } from "react";
import { usePerf } from "@/modules/engineering-console/hooks/use-perf";
import { PerfOverviewPanel } from "./perf/perf-overview-panel";
import { PerfStartupPanel } from "./perf/perf-startup-panel";
import { PerfFrontendPanel } from "./perf/perf-frontend-panel";
import { PerfBackendPanel } from "./perf/perf-backend-panel";
import { PerfAgentsPanel } from "./perf/perf-agents-panel";
import { PerfPluginsPanel } from "./perf/perf-plugins-panel";
import { PerfLoadPanel } from "./perf/perf-load-panel";
import { PerfSoakPanel } from "./perf/perf-soak-panel";
import { PerfChaosPanel } from "./perf/perf-chaos-panel";
import { PerfRecoveryPanel } from "./perf/perf-recovery-panel";
import { PerfScalabilityPanel } from "./perf/perf-scalability-panel";
import { PerfResourcesPanel } from "./perf/perf-resources-panel";
import { PerfRegressionPanel } from "./perf/perf-regression-panel";
import { PerfBudgetPanel } from "./perf/perf-budget-panel";

/**
 * Performance Router — manages navigation between the 12 certification
 * areas + performance budget.
 */
export function PerfRouterPanel() {
  const { perf, reset } = usePerf(10000);
  const [drillTarget, setDrillTarget] = useState<string | null>(null);

  const back = () => setDrillTarget(null);

  if (drillTarget === "startup") return <PerfStartupPanel startup={perf.startup} onBack={back} />;
  if (drillTarget === "frontend") return <PerfFrontendPanel frontend={perf.frontend} onBack={back} />;
  if (drillTarget === "backend") return <PerfBackendPanel backend={perf.backend} onBack={back} />;
  if (drillTarget === "agents") return <PerfAgentsPanel agents={perf.agents} onBack={back} />;
  if (drillTarget === "plugins") return <PerfPluginsPanel plugins={perf.plugins} onBack={back} />;
  if (drillTarget === "load") return <PerfLoadPanel loadTests={perf.loadTests} onBack={back} />;
  if (drillTarget === "soak") return <PerfSoakPanel soak={perf.soak} onBack={back} />;
  if (drillTarget === "chaos") return <PerfChaosPanel chaos={perf.chaos} onBack={back} />;
  if (drillTarget === "recovery") return <PerfRecoveryPanel recovery={perf.recovery} onBack={back} />;
  if (drillTarget === "scalability") return <PerfScalabilityPanel scalability={perf.scalability} onBack={back} />;
  if (drillTarget === "resources") return <PerfResourcesPanel resources={perf.resources} onBack={back} />;
  if (drillTarget === "regression") return <PerfRegressionPanel regression={perf.regression} onBack={back} />;
  if (drillTarget === "budget") return <PerfBudgetPanel budget={perf.certification.budget} onBack={back} />;

  return <PerfOverviewPanel perf={perf} onReset={reset} onDrill={setDrillTarget} />;
}
