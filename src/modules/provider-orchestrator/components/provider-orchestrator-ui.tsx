"use client";

import { useState } from "react";
import { Activity, FileText, GitCompare, Radio, Database, CheckCircle2, AlertTriangle, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { useProviders } from "../hooks/use-providers";
import { ProviderSettings } from "./provider-settings";
import { ProviderDiagnostics } from "./provider-diagnostics";
import { RequestLog } from "./request-log";
import { DataComparison } from "./data-comparison";

type Tab = "settings" | "diagnostics" | "request-log" | "comparison";

export function ProviderOrchestratorUI() {
  const [tab, setTab] = useState<Tab>("settings");

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "settings", label: "Settings", icon: <Radio className="h-3.5 w-3.5" /> },
    { id: "diagnostics", label: "Diagnostics", icon: <Activity className="h-3.5 w-3.5" /> },
    { id: "request-log", label: "Request Log", icon: <FileText className="h-3.5 w-3.5" /> },
    { id: "comparison", label: "Data Comparison", icon: <GitCompare className="h-3.5 w-3.5" /> },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card/40 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Radio className="h-5 w-5 text-primary" />
            <div>
              <div className="text-[14px] font-semibold">Provider Orchestrator</div>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Stage 16A · Market Data Gateway</div>
            </div>
          </div>
        </div>
        {/* Tab bar */}
        <div className="max-w-6xl mx-auto px-6 flex gap-1">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium border-b-2 transition-colors",
                tab === t.id ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              {t.icon}
              {t.label}
            </button>
          ))}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6">
        {tab === "settings" && <ProviderSettings />}
        {tab === "diagnostics" && <ProviderDiagnostics />}
        {tab === "request-log" && <RequestLog />}
        {tab === "comparison" && <DataComparison />}
      </main>
    </div>
  );
}
