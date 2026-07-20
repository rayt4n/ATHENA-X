"use client";

/**
 * Workspace Composition Layer
 *
 * The ONLY file that assembles the trading workspace.
 * Does NOT contain indicator logic, chart logic, or API calls.
 * It only:
 *   1. Registers widgets with the WorkspaceRegistry
 *   2. Renders WidgetSlot placeholders for each zone
 *
 * Adding a new widget (e.g., "Liquidity Heatmap"):
 *   1. Create the widget component
 *   2. Register it: workspaceRegistry.register({ zone: "left", id: "liquidity", component: MyWidget, order: 2 })
 *   3. Done — no composition changes.
 */

import { useEffect, useState } from "react";
import { workspaceRegistry, type WorkspaceWidget } from "@/lib/workspace-registry";
import { AthenaWidgets } from "./athena-widgets";

// ============================================================================
// Register ATHENA-X widgets
// ============================================================================

let registered = false;

function ensureRegistered() {
  if (registered) return;
  registered = true;

  const widgets: WorkspaceWidget[] = [
    { zone: "topbar", id: "workspace-topbar", component: AthenaWidgets.TopBar as unknown as React.ComponentType<Record<string, unknown>>, order: 1 },
    { zone: "left", id: "market-overview", component: AthenaWidgets.LeftPanel as unknown as React.ComponentType<Record<string, unknown>>, order: 1 },
    { zone: "center", id: "chart", component: AthenaWidgets.CenterChart as unknown as React.ComponentType<Record<string, unknown>>, order: 1 },
    { zone: "right", id: "institutional", component: AthenaWidgets.RightPanel as unknown as React.ComponentType<Record<string, unknown>>, order: 1 },
    { zone: "bottom", id: "intelligence-tabs", component: AthenaWidgets.BottomTabs as unknown as React.ComponentType<Record<string, unknown>>, order: 1 },
  ];

  widgets.forEach((w) => workspaceRegistry.register(w));
}

// ============================================================================
// WidgetSlot — renders all widgets registered for a zone
// ============================================================================

function WidgetSlot({ zone, className, widgetProps }: { zone: string; className?: string; widgetProps?: Record<string, unknown> }) {
  const [, forceUpdate] = useState(0);

  useEffect(() => {
    ensureRegistered();
    forceUpdate((n) => n + 1);
  }, []);

  const widgets = workspaceRegistry.getWidgets(zone);

  if (widgets.length === 0) {
    return <div className={className} />;
  }

  return (
    <div className={className}>
      {widgets.map((w) => {
        const Component = w.component;
        return <Component key={w.id} {...(w.props || {})} {...(widgetProps || {})} />;
      })}
    </div>
  );
}

// ============================================================================
// WorkspaceComposition — the composition layer
// ============================================================================

export function WorkspaceComposition() {
  const [symbol, setSymbol] = useState("SPY");

  useEffect(() => {
    ensureRegistered();
  }, []);

  return (
    <div className="flex flex-col h-full bg-background text-foreground overflow-hidden">
      <WidgetSlot zone="topbar" widgetProps={{ onSymbolSelect: setSymbol, selectedSymbol: symbol }} />
      <div className="flex flex-1 min-h-0">
        <WidgetSlot zone="left" />
        <WidgetSlot zone="center" className="flex-1 flex flex-col min-w-0" widgetProps={{ symbol }} />
        <WidgetSlot zone="right" />
      </div>
      <WidgetSlot zone="bottom" />
    </div>
  );
}
