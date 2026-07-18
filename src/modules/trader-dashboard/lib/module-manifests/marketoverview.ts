import type { ModuleManifest } from "../workspace-types";

export const marketoverviewManifest: ModuleManifest = {
  id: "marketoverview",
  name: "Market Overview",
  description: "SPY, ES, SPX, QQQ, NQ, VIX, VVIX, MOVE, TNX, DXY, Gold, Oil, Copper, USDJPY with live prices and change %.",
  category: "market_data",
  defaultSize: { w: 6, h: 6 },
  minSize: { w: 4, h: 4 },
  detachable: true,
  stateful: true,
  icon: "BarChart3",
  schemaVersion: "1.0",
  version: "1.0.0",
};
