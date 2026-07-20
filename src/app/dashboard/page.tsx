"use client";

import Link from "next/link";
import { TrendingUp, Activity, FileText, Cpu, Settings, ArrowRight } from "lucide-react";

export default function AdminDashboardPage() {
  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold mb-4">Dashboard</h1>
      <p className="text-[13px] text-muted-foreground mb-6">Welcome to the ATHENA-X Admin Dashboard. Select a section from the sidebar or click below.</p>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-w-3xl">
        <Link href="/dashboard/athena/workspace" className="block p-4 rounded-lg border border-border bg-card/50 hover:border-primary transition-colors">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="h-5 w-5 text-primary" />
            <span className="text-[14px] font-semibold">Trading Workspace</span>
          </div>
          <p className="text-[11px] text-muted-foreground">Institutional trading workspace with chart, market overview, and intelligence panels.</p>
          <div className="flex items-center gap-1 mt-2 text-[11px] text-primary">
            <span>Open</span>
            <ArrowRight className="h-3 w-3" />
          </div>
        </Link>

        <Link href="/dashboard/reports" className="block p-4 rounded-lg border border-border bg-card/50 hover:border-primary transition-colors">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="h-5 w-5 text-muted-foreground" />
            <span className="text-[14px] font-semibold">Reports</span>
          </div>
          <p className="text-[11px] text-muted-foreground">Generated institutional reports and PDF certificates.</p>
        </Link>

        <Link href="/dashboard/engineering" className="block p-4 rounded-lg border border-border bg-card/50 hover:border-primary transition-colors">
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="h-5 w-5 text-muted-foreground" />
            <span className="text-[14px] font-semibold">Engineering</span>
          </div>
          <p className="text-[11px] text-muted-foreground">Engineering console, provider orchestrator, and system health.</p>
        </Link>

        <Link href="/dashboard/settings" className="block p-4 rounded-lg border border-border bg-card/50 hover:border-primary transition-colors">
          <div className="flex items-center gap-2 mb-2">
            <Settings className="h-5 w-5 text-muted-foreground" />
            <span className="text-[14px] font-semibold">Settings</span>
          </div>
          <p className="text-[11px] text-muted-foreground">System configuration and preferences.</p>
        </Link>
      </div>
    </div>
  );
}
