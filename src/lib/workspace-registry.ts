/**
 * Workspace Registry — the Trading Workspace reads this to discover
 * which widgets to render in each zone (topbar, left, center, right, bottom).
 *
 * Plugins register their widgets here. The WorkspaceComposition component
 * calls getWidgets(zone) for each zone and renders the results.
 *
 * Adding a new widget (e.g., "Liquidity Heatmap") = register it here.
 * Zero workspace code changes.
 */

import type { ComponentType } from "react";

export interface WorkspaceWidget {
  zone: "topbar" | "left" | "center" | "right" | "bottom";
  id: string;
  component: ComponentType<Record<string, unknown>>;
  order?: number;
  props?: Record<string, unknown>;
}

class WorkspaceRegistryImpl {
  private widgets = new Map<string, WorkspaceWidget[]>();

  register(widget: WorkspaceWidget): void {
    const zoneWidgets = this.widgets.get(widget.zone) || [];
    zoneWidgets.push(widget);
    zoneWidgets.sort((a, b) => (a.order || 999) - (b.order || 999));
    this.widgets.set(widget.zone, zoneWidgets);
  }

  getWidgets(zone: string): WorkspaceWidget[] {
    return this.widgets.get(zone) || [];
  }
}

export const workspaceRegistry = new WorkspaceRegistryImpl();
