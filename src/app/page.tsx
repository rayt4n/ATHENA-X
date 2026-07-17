"use client";

import { useState } from "react";
import { DashboardShell } from "@/components/dashboard/dashboard-shell";
import { useTelemetry } from "@/hooks/use-telemetry";
import { OverviewPanel } from "@/components/dashboard/panels/overview-panel";
import { DataFreshnessPanel } from "@/components/dashboard/panels/data-freshness-panel";
import { ProviderHealthPanel } from "@/components/dashboard/panels/provider-health-panel";
import { TAAccuracyPanel } from "@/components/dashboard/panels/ta-accuracy-panel";
import { OptionsAccuracyPanel } from "@/components/dashboard/panels/options-accuracy-panel";
import { ForecastPanel } from "@/components/dashboard/panels/forecast-panel";
import { TradeDNAPanel } from "@/components/dashboard/panels/trade-dna-panel";
import { EventBusPanel } from "@/components/dashboard/panels/event-bus-panel";
import { AgentHealthPanel } from "@/components/dashboard/panels/agent-health-panel";
import { DatabasePanel } from "@/components/dashboard/panels/database-panel";
import { DNAMatrixPanel } from "@/components/dashboard/panels/dna-matrix-panel";
import { AlarmsPanel } from "@/components/dashboard/panels/alarms-panel";

export default function Home() {
  const { telemetry, reset } = useTelemetry(1500);
  const [section, setSection] = useState("overview");

  return (
    <DashboardShell
      system={telemetry.system}
      onReset={reset}
      activeSection={section}
      onSectionChange={setSection}
    >
      {section === "overview" && <OverviewPanel t={telemetry} onJump={setSection} />}
      {section === "alarms" && <AlarmsPanel alarms={telemetry.alarms} />}
      {section === "freshness" && <DataFreshnessPanel entries={telemetry.freshness} />}
      {section === "providers" && <ProviderHealthPanel providers={telemetry.providers} />}
      {section === "ta" && <TAAccuracyPanel checks={telemetry.taChecks} />}
      {section === "options" && <OptionsAccuracyPanel checks={telemetry.optionsChecks} />}
      {section === "forecast" && <ForecastPanel t={telemetry} />}
      {section === "trade" && <TradeDNAPanel decisions={telemetry.tradeDecisions} />}
      {section === "eventbus" && <EventBusPanel eventBus={telemetry.eventBus} />}
      {section === "agents" && <AgentHealthPanel agents={telemetry.agents} />}
      {section === "database" && <DatabasePanel schemas={telemetry.database} />}
      {section === "dna" && <DNAMatrixPanel dna={telemetry.dna} />}
    </DashboardShell>
  );
}
