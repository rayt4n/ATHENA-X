"use client";

import { TrendingUp, Activity, BarChart3, Cpu, Brain, Target, FileText, ShieldCheck, Layers, Newspaper } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Market Overview", icon: Activity },
  { href: "/dashboard/chart", label: "Chart", icon: BarChart3 },
  { href: "/dashboard/technical", label: "Technical", icon: Layers },
  { href: "/dashboard/options", label: "Options", icon: Cpu },
  { href: "/dashboard/intelligence", label: "Market Intelligence", icon: TrendingUp },
  { href: "/dashboard/ai", label: "AI Analysis", icon: Brain },
  { href: "/dashboard/trade", label: "Trade Setup", icon: Target },
  { href: "/dashboard/evidence", label: "Evidence", icon: ShieldCheck },
  { href: "/dashboard/report", label: "Report", icon: FileText },
  { href: "/dashboard/plugins", label: "Plugin Status", icon: Newspaper },
];

export function DashboardSidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 border-r border-border bg-card/30 flex flex-col h-screen sticky top-0">
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-8 h-8 rounded-md bg-primary/15 border border-primary/30">
            <TrendingUp className="h-4 w-4 text-primary" />
          </div>
          <div>
            <div className="text-sm font-semibold tracking-wide">ATHENA-X</div>
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Trader Terminal</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto py-2">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-2 text-[12px] transition-colors border-l-2",
                active
                  ? "bg-primary/10 text-foreground border-primary font-medium"
                  : "text-muted-foreground border-transparent hover:text-foreground hover:bg-muted/50",
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-border text-[10px] text-muted-foreground">
        <div>v17.1.0 · Architecture Freeze</div>
        <div className="mt-1">30 agents · 280 components</div>
      </div>
    </aside>
  );
}
