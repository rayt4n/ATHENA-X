import type { ModuleManifest } from "../workspace-types";

export const watchlistManifest: ModuleManifest = {
  id: "watchlist",
  name: "Watchlist",
  description: "Symbol list with live prices, change %, and mini-sparklines. Click any symbol to set it as active across the workspace.",
  category: "market_data",
  defaultSize: { w: 3, h: 8 },
  minSize: { w: 2, h: 4 },
  detachable: true,
  stateful: true,
  icon: "List",
  schemaVersion: "1.0",
  version: "1.0.0",
};
