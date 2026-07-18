"use client";

import { useState } from "react";
import { DashboardShell } from "@/modules/engineering-console/components/dashboard-shell";
import { useTelemetry } from "@/modules/engineering-console/hooks/use-telemetry";
import { OverviewPanel } from "@/modules/engineering-console/components/panels/overview-panel";
import { DataFreshnessPanel } from "@/modules/engineering-console/components/panels/data-freshness-panel";
import { ProviderHealthPanel } from "@/modules/engineering-console/components/panels/provider-health-panel";
import { TAAccuracyPanel } from "@/modules/engineering-console/components/panels/ta-accuracy-panel";
import { OptionsAccuracyPanel } from "@/modules/engineering-console/components/panels/options-accuracy-panel";
import { ForecastPanel } from "@/modules/engineering-console/components/panels/forecast-panel";
import { TradeDNAPanel } from "@/modules/engineering-console/components/panels/trade-dna-panel";
import { EventBusPanel } from "@/modules/engineering-console/components/panels/event-bus-panel";
import { AgentHealthPanel } from "@/modules/engineering-console/components/panels/agent-health-panel";
import { DatabasePanel } from "@/modules/engineering-console/components/panels/database-panel";
import { DNAMatrixPanel } from "@/modules/engineering-console/components/panels/dna-matrix-panel";
import { AlarmsPanel } from "@/modules/engineering-console/components/panels/alarms-panel";
import { CertificationRouterPanel } from "@/modules/engineering-console/components/panels/cert-router-panel";
import { ReportEnginePanel } from "@/modules/engineering-console/components/panels/report-engine-panel";
import { runFullCertification } from "@/modules/engineering-console/lib/certification-engine";

/**
 * Engineering Console entry — the validation cockpit.
 *
 * Formerly the root page. Now lives at /engineering-console so it is fully
 * decoupled from the trader dashboard at /.
 */
export default function EngineeringConsolePage() {
  const { telemetry, reset } = useTelemetry(1500);
  const [section, setSection] = useState("overview");
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);

  const handleDownloadPdf = async () => {
    setIsGeneratingPdf(true);
    try {
      // Compute the latest certification state and POST it to the PDF endpoint
      const certState = runFullCertification(telemetry);
      const res = await fetch("/api/certification-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(certState),
      });
      if (!res.ok) throw new Error(`PDF generation failed: ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `athena-x-certification-${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert("Failed to generate PDF. Check console for details.");
    } finally {
      setIsGeneratingPdf(false);
    }
  };

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
      {section === "certification" && (
        <CertificationRouterPanel
          telemetry={telemetry}
          onDownloadPdf={handleDownloadPdf}
          isGeneratingPdf={isGeneratingPdf}
        />
      )}
      {section === "report-engine" && <ReportEnginePanel />}
    </DashboardShell>
  );
}
