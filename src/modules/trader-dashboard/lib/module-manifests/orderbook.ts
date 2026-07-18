import type { ModuleManifest } from "../workspace-types";

export const orderbookManifest: ModuleManifest = {
  id: "orderbook",
  name: "Order Book",
  description: "Live bid/ask depth with liquidity imbalance visualization.",
  category: "market_data",
  defaultSize: { w: 3, h: 8 },
  minSize: { w: 2, h: 5 },
  detachable: true,
  stateful: true,
  icon: "BookOpen",
  schemaVersion: "1.0",
  version: "1.0.0",
};
