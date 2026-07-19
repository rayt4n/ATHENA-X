"use client";

import { type ReactNode } from "react";
import { DashboardSidebar } from "@/modules/athena-dashboard/dashboard-sidebar";
import { DashboardTopBar } from "@/modules/athena-dashboard/dashboard-topbar";
import { AthenaProviders } from "@/lib/athena-providers";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <AthenaProviders>
      <div className="flex min-h-screen bg-background text-foreground">
        <DashboardSidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <DashboardTopBar />
          <main className="flex-1 overflow-y-auto p-4">{children}</main>
        </div>
      </div>
    </AthenaProviders>
  );
}
