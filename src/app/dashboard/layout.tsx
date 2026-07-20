"use client";

import { type ReactNode } from "react";
import { DashboardSidebar } from "@/modules/athena-dashboard/dashboard-sidebar";
import { AthenaProviders } from "@/lib/athena-providers";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <AthenaProviders>
      <div className="flex h-screen bg-background text-foreground overflow-hidden">
        <DashboardSidebar />
        <main className="flex-1 overflow-hidden">
          {children}
        </main>
      </div>
    </AthenaProviders>
  );
}
