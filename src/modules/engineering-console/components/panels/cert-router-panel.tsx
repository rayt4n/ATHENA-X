"use client";

import { useState } from "react";
import { useCertification } from "@/modules/engineering-console/hooks/use-certification";
import { CertificationOverviewPanel } from "./cert-overview-panel";
import { CertModuleDetailPanel } from "./cert-module-detail";
import { CertificatePanel } from "./cert-certificate-panel";
import { StressScenariosBlock, ReplayScenariosBlock, IntelligenceDNABlock } from "./cert-special-blocks";
import type { DashboardTelemetry } from "@/modules/engineering-console/lib/types";
import type { ModuleId } from "@/modules/engineering-console/lib/certification-types";

interface Props {
  telemetry: DashboardTelemetry;
  onDownloadPdf: () => void;
  isGeneratingPdf: boolean;
}

export function CertificationRouterPanel({ telemetry, onDownloadPdf, isGeneratingPdf }: Props) {
  const { state, run, reset } = useCertification(telemetry);
  const [drillTarget, setDrillTarget] = useState<ModuleId | null>(null);

  // Drill-down view
  if (drillTarget === "certificate" && state.certificate) {
    return (
      <CertificatePanel
        certificate={state.certificate}
        onBack={() => setDrillTarget(null)}
        onDownloadPdf={onDownloadPdf}
        isGeneratingPdf={isGeneratingPdf}
      />
    );
  }

  if (drillTarget && drillTarget !== "certificate") {
    const mod = state.modules.find((m) => m.id === drillTarget);
    if (mod) {
      return (
        <CertModuleDetailPanel module={mod} onBack={() => setDrillTarget(null)}>
          {mod.id === "stress" && <StressScenariosBlock scenarios={state.stressScenarios} />}
          {mod.id === "replay" && <ReplayScenariosBlock scenarios={state.replayScenarios} />}
          {mod.id === "intelligence" && <IntelligenceDNABlock dnaResults={state.dnaResults} module={mod} />}
        </CertModuleDetailPanel>
      );
    }
  }

  // Default — overview
  return (
    <CertificationOverviewPanel
      state={state}
      telemetry={telemetry}
      onRun={run}
      onReset={reset}
      onDrill={setDrillTarget}
      onDownloadPdf={onDownloadPdf}
      isGeneratingPdf={isGeneratingPdf}
    />
  );
}
