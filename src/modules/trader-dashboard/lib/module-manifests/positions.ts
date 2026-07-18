import type { ModuleManifest } from "../workspace-types";

export const positionsManifest: ModuleManifest = {
  id: "positions",
  name: "Positions",
  description: "Open and closed positions with P&L, R-multiple, and status.",
  category: "trading",
  defaultSize: { w: 5, h: 8 },
  minSize: { w: 3, h: 5 },
  detachable: true,
  stateful: true,
  icon: "Wallet",
  schemaVersion: "1.0",
  version: "1.0.0",
};
