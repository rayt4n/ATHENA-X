"use client";

import { TrendingUp, Activity, FileText, Settings, Cpu, ChevronDown, ChevronRight } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { pluginRegistry } from "@/lib/plugin-registry";
import "@/lib/athena-plugin-manifest"; // registers ATHENA-X plugin

// ============================================================================
// Core navigation items (static — Admin Dashboard sections)
// ============================================================================

const CORE_NAV = [
  { href: "/dashboard", label: "Dashboard", icon: Activity },
  { href: "/dashboard/reports", label: "Reports", icon: FileText },
  { href: "/dashboard/engineering", label: "Engineering", icon: Cpu },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

// ============================================================================
// Sidebar — reads Core section + dynamic Plugins section from registry
// ============================================================================

export function DashboardSidebar() {
  const pathname = usePathname();
  const plugins = pluginRegistry.getPlugins();
  const [expandedPlugins, setExpandedPlugins] = useState<Set<string>>(new Set(["athena-x"]));

  const togglePlugin = (id: string) => {
    setExpandedPlugins((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  };

  return (
    <aside className="w-56 shrink-0 border-r border-border bg-card/30 flex flex-col h-screen sticky top-0">
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-8 h-8 rounded-md bg-primary/15 border border-primary/30">
            <TrendingUp className="h-4 w-4 text-primary" />
          </div>
          <div>
            <div className="text-sm font-semibold tracking-wide">ATHENA-X</div>
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Admin Dashboard</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto py-2">
        {/* Core section */}
        <div className="px-3 py-1 text-[9px] font-bold uppercase tracking-wider text-muted-foreground">Core</div>
        {CORE_NAV.map((item) => {
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

        {/* Plugins section (dynamic from registry) */}
        <div className="px-3 py-1 mt-3 text-[9px] font-bold uppercase tracking-wider text-muted-foreground">Plugins</div>
        {plugins.map((plugin) => {
          const expanded = expandedPlugins.has(plugin.id);
          return (
            <div key={plugin.id}>
              <button
                onClick={() => togglePlugin(plugin.id)}
                className="flex items-center gap-2 px-4 py-2 text-[12px] w-full text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
              >
                {expanded ? <ChevronDown className="h-3 w-3 shrink-0" /> : <ChevronRight className="h-3 w-3 shrink-0" />}
                <TrendingUp className="h-4 w-4 shrink-0" />
                <span className="font-medium">{plugin.name}</span>
                <span className="text-[8px] text-muted-foreground ml-auto">v{plugin.version}</span>
              </button>
              {expanded && (
                <div>
                  {plugin.routes.map((route) => {
                    const active = pathname === route.path;
                    return (
                      <Link
                        key={route.path}
                        href={route.path}
                        className={cn(
                          "flex items-center gap-3 pl-10 pr-4 py-1.5 text-[11px] transition-colors border-l-2",
                          active
                            ? "bg-primary/10 text-foreground border-primary font-medium"
                            : "text-muted-foreground border-transparent hover:text-foreground hover:bg-muted/50",
                        )}
                      >
                        <span>{route.label}</span>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      <div className="p-3 border-t border-border text-[10px] text-muted-foreground">
        <div>v17.4.0 · Plugin Architecture</div>
        <div className="mt-1">{plugins.length} plugin(s) registered</div>
      </div>
    </aside>
  );
}
